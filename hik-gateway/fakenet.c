/*
 * fakenet.c - LD_PRELOAD para injetar IP em respostas netlink
 *
 * O binário Hikvision usa AF_NETLINK + NETLINK_ROUTE para detectar IPs.
 * Em Docker, a resposta de RTM_GETADDR vem vazia (20 bytes = NLMSG_DONE).
 * Esta lib intercepta as mensagens NLMSG_DONE e injeta um endereço IPv4
 * com o índice de interface real, PRESERVANDO nlmsg_seq e nlmsg_pid 
 * (vital para o parser do binário aceitar a mensagem).
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <sys/socket.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <linux/if_addr.h>
#include <net/if.h>
#include <netinet/in.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <ifaddrs.h>
#include <sys/uio.h>

/* Rastreia estado por socket netlink */
struct nl_state {
    int fd;
    int last_request_type;
    unsigned char last_request_family;
};
static struct nl_state nl_sockets[64];
static int nl_count = 0;

/* Ponteiros reais */
static int (*real_socket)(int, int, int) = NULL;
static ssize_t (*real_recvfrom)(int, void*, size_t, int, struct sockaddr*, socklen_t*) = NULL;
static ssize_t (*real_sendto)(int, const void*, size_t, int, const struct sockaddr*, socklen_t) = NULL;
static ssize_t (*real_send)(int, const void*, size_t, int) = NULL;
static ssize_t (*real_sendmsg)(int, const struct msghdr*, int) = NULL;
static ssize_t (*real_write)(int, const void*, size_t) = NULL;
static ssize_t (*real_writev)(int, const struct iovec *, int) = NULL;
static int (*real_getifaddrs)(struct ifaddrs **) = NULL;
static void (*real_freeifaddrs)(struct ifaddrs *) = NULL;

static void init_funcs(void) {
    if (!real_socket) real_socket = dlsym(RTLD_NEXT, "socket");
    if (!real_recvfrom) real_recvfrom = dlsym(RTLD_NEXT, "recvfrom");
    if (!real_sendto) real_sendto = dlsym(RTLD_NEXT, "sendto");
    if (!real_send) real_send = dlsym(RTLD_NEXT, "send");
    if (!real_sendmsg) real_sendmsg = dlsym(RTLD_NEXT, "sendmsg");
    if (!real_write) real_write = dlsym(RTLD_NEXT, "write");
    if (!real_writev) real_writev = dlsym(RTLD_NEXT, "writev");
    if (!real_getifaddrs) real_getifaddrs = dlsym(RTLD_NEXT, "getifaddrs");
    if (!real_freeifaddrs) real_freeifaddrs = dlsym(RTLD_NEXT, "freeifaddrs");
}

int getifaddrs(struct ifaddrs **ifap) {
    init_funcs();
    if (!real_getifaddrs) return -1;
    int ret = real_getifaddrs(ifap);
    if (ret != 0 || !ifap || !*ifap) return ret;

    struct ifaddrs *prev = NULL;
    struct ifaddrs *cur = *ifap;
    while (cur) {
        struct ifaddrs *next = cur->ifa_next;
        int is_v6 = (cur->ifa_addr && cur->ifa_addr->sa_family == AF_INET6);
        if (is_v6) {
            if (prev) prev->ifa_next = next;
            else *ifap = next;
            cur->ifa_next = NULL;
            real_freeifaddrs(cur);
        } else {
            prev = cur;
        }
        cur = next;
    }
    return 0;
}

int socket(int domain, int type, int protocol) {
    init_funcs();
    int fd = real_socket(domain, type, protocol);
    if (fd >= 0 && domain == AF_NETLINK && protocol == NETLINK_ROUTE) {
        if (nl_count < 64) {
            nl_sockets[nl_count].fd = fd;
            nl_sockets[nl_count].last_request_type = 0;
            nl_sockets[nl_count].last_request_family = 0;
            nl_count++;
        }
    }
    return fd;
}

static struct nl_state* get_nl_state(int fd) {
    for (int i = 0; i < nl_count; i++)
        if (nl_sockets[i].fd == fd) return &nl_sockets[i];
    return NULL;
}

static void inspect_outgoing(int fd, const void *buf, size_t len) {
    struct nl_state *state = get_nl_state(fd);
    if (!state || len < sizeof(struct nlmsghdr)) return;
    
    struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
    state->last_request_type = nlh->nlmsg_type;
    
    if (nlh->nlmsg_type == RTM_GETADDR && len >= NLMSG_SPACE(sizeof(struct rtgenmsg))) {
        struct rtgenmsg *rtgen = (struct rtgenmsg *)NLMSG_DATA(nlh);
        state->last_request_family = rtgen->rtgen_family;
    } else {
        state->last_request_family = AF_UNSPEC;
    }
}

ssize_t sendto(int fd, const void *buf, size_t len, int flags,
               const struct sockaddr *dest_addr, socklen_t addrlen) {
    init_funcs();
    if (get_nl_state(fd)) inspect_outgoing(fd, buf, len);
    return real_sendto(fd, buf, len, flags, dest_addr, addrlen);
}

ssize_t send(int fd, const void *buf, size_t len, int flags) {
    init_funcs();
    if (get_nl_state(fd)) inspect_outgoing(fd, buf, len);
    return real_send(fd, buf, len, flags);
}

ssize_t sendmsg(int fd, const struct msghdr *msg, int flags) {
    init_funcs();
    if (get_nl_state(fd) && msg && msg->msg_iov && msg->msg_iovlen > 0) {
        inspect_outgoing(fd, msg->msg_iov[0].iov_base, msg->msg_iov[0].iov_len);
    }
    return real_sendmsg(fd, msg, flags);
}

ssize_t write(int fd, const void *buf, size_t count) {
    init_funcs();
    if (get_nl_state(fd)) inspect_outgoing(fd, buf, count);
    return real_write(fd, buf, count);
}

ssize_t writev(int fd, const struct iovec *iov, int iovcnt) {
    init_funcs();
    if (get_nl_state(fd) && iov && iovcnt > 0) {
        inspect_outgoing(fd, iov[0].iov_base, iov[0].iov_len);
    }
    return real_writev(fd, iov, iovcnt);
}

static ssize_t build_response(void *buf, size_t buflen, uint32_t seq, uint32_t pid) {
    struct ifaddrs *ifas, *ifa;
    unsigned char *p = (unsigned char *)buf;
    size_t total = 0;

    init_funcs();

    if (!real_getifaddrs || real_getifaddrs(&ifas) != 0)
        return -1;

    for (ifa = ifas; ifa; ifa = ifa->ifa_next) {
        if (!ifa->ifa_addr) continue;
        if (ifa->ifa_addr->sa_family != AF_INET) continue;
        
        struct sockaddr_in *sin = (struct sockaddr_in *)ifa->ifa_addr;
        /* Ignorar loopback (127.x.x.x) */
        if ((ntohl(sin->sin_addr.s_addr) & 0xFF000000) == 0x7F000000) continue;

        unsigned int idx = if_nametoindex(ifa->ifa_name);
        uint32_t ip = sin->sin_addr.s_addr;
        uint32_t bcast = 0;
        if (ifa->ifa_broadaddr) {
            struct sockaddr_in *b = (struct sockaddr_in *)ifa->ifa_broadaddr;
            bcast = b->sin_addr.s_addr;
        }

        size_t addr_data = NLMSG_ALIGN(sizeof(struct ifaddrmsg))
                         + RTA_SPACE(4)   /* IFA_ADDRESS */
                         + RTA_SPACE(4)   /* IFA_LOCAL */
                         + RTA_SPACE(4);  /* IFA_BROADCAST */
        size_t msg_len = NLMSG_SPACE(addr_data);

        if (total + msg_len + 20 > buflen) break;

        /* nlmsghdr */
        struct nlmsghdr *nlh = (struct nlmsghdr *)(buf + total);
        memset(nlh, 0, msg_len);
        nlh->nlmsg_len = msg_len;
        nlh->nlmsg_type = RTM_NEWADDR;
        nlh->nlmsg_flags = NLM_F_MULTI;
        nlh->nlmsg_seq = seq;
        nlh->nlmsg_pid = pid;

        /* ifaddrmsg */
        struct ifaddrmsg *ifam = (struct ifaddrmsg *)NLMSG_DATA(nlh);
        ifam->ifa_family = AF_INET;
        ifam->ifa_prefixlen = 24;
        ifam->ifa_flags = 0x80; /* IFA_F_PERMANENT */
        ifam->ifa_scope = 0;    /* RT_SCOPE_UNIVERSE */
        ifam->ifa_index = idx;  /* ÍNDICE REAL */

        /* Atributos */
        unsigned char *attr_p = (unsigned char *)ifam + NLMSG_ALIGN(sizeof(struct ifaddrmsg));
        struct rtattr *rta;

        /* IFA_ADDRESS */
        rta = (struct rtattr *)attr_p;
        rta->rta_type = IFA_ADDRESS;
        rta->rta_len = RTA_LENGTH(4);
        memcpy(RTA_DATA(rta), &ip, 4);
        attr_p += RTA_SPACE(4);

        /* IFA_LOCAL */
        rta = (struct rtattr *)attr_p;
        rta->rta_type = IFA_LOCAL;
        rta->rta_len = RTA_LENGTH(4);
        memcpy(RTA_DATA(rta), &ip, 4);
        attr_p += RTA_SPACE(4);

        /* IFA_BROADCAST */
        rta = (struct rtattr *)attr_p;
        rta->rta_type = IFA_BROADCAST;
        rta->rta_len = RTA_LENGTH(4);
        if (bcast) memcpy(RTA_DATA(rta), &bcast, 4);
        else memcpy(RTA_DATA(rta), &ip, 4);
        attr_p += RTA_SPACE(4);

        total += msg_len;
    }
    if (real_freeifaddrs) real_freeifaddrs(ifas);

    if (total == 0) return -1;

    /* NLMSG_DONE */
    struct nlmsghdr *done = (struct nlmsghdr *)(buf + total);
    memset(done, 0, 20);
    done->nlmsg_len = 20;
    done->nlmsg_type = NLMSG_DONE;
    done->nlmsg_flags = NLM_F_MULTI;
    done->nlmsg_seq = seq;
    done->nlmsg_pid = pid;
    total += 20;

    return (ssize_t)total;
}

ssize_t recvfrom(int fd, void *buf, size_t len, int flags,
                 struct sockaddr *src, socklen_t *addrlen) {
    init_funcs();
    ssize_t result = real_recvfrom(fd, buf, len, flags, src, addrlen);

    struct nl_state *state = get_nl_state(fd);
    if (state && result >= 16) {
        struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
        
        if (result == 20 && nlh->nlmsg_type == NLMSG_DONE) {
            uint32_t orig_seq = nlh->nlmsg_seq;
            uint32_t orig_pid = nlh->nlmsg_pid;
            
            // Só injetar se o último pedido a este socket foi um GETADDR para IPv4 ou UNSPEC
            if (state->last_request_type == RTM_GETADDR) {
                if (state->last_request_family == AF_INET || state->last_request_family == AF_UNSPEC) {
                    /* Realizamos injeção falsa apenas 1 vez por loop de GETADDR para evitar loops infinitos se ele processar múltiplas mensagens */
                    state->last_request_type = 0; 
                    
                    ssize_t fake = build_response(buf, len, orig_seq, orig_pid);
                    if (fake > 0) return fake;
                }
            }
        }
        else if (result > 20 && nlh->nlmsg_type == RTM_NEWADDR) {
            struct ifaddrmsg *ifa = (struct ifaddrmsg *)NLMSG_DATA(nlh);
            if (ifa->ifa_family == AF_INET6) {
                uint32_t seq = nlh->nlmsg_seq;
                uint32_t pid = nlh->nlmsg_pid;
                
                memset(buf, 0, 20);
                struct nlmsghdr *done = (struct nlmsghdr *)buf;
                done->nlmsg_len = 20;
                done->nlmsg_type = NLMSG_DONE;
                done->nlmsg_flags = NLM_F_MULTI;
                done->nlmsg_seq = seq;
                done->nlmsg_pid = pid;
                return 20;
            }
        }
    }

    return result;
}
