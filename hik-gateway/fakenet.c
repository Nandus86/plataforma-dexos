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

/* Rastreia sockets netlink */
static int nl_fds[64];
static int nl_count = 0;

/* Tracks the family requested by each sequence number */
struct seq_info {
    uint32_t seq;
    unsigned char family;
    int is_getaddr;
};
static struct seq_info seq_history[256];
static int seq_hist_idx = 0;

/* Ponteiros reais */
static int (*real_socket)(int, int, int) = NULL;
static ssize_t (*real_recvfrom)(int, void*, size_t, int, struct sockaddr*, socklen_t*) = NULL;
static ssize_t (*real_sendto)(int, const void*, size_t, int, const struct sockaddr*, socklen_t) = NULL;
static ssize_t (*real_send)(int, const void*, size_t, int) = NULL;
static ssize_t (*real_sendmsg)(int, const struct msghdr*, int) = NULL;
static int (*real_getifaddrs)(struct ifaddrs **) = NULL;
static void (*real_freeifaddrs)(struct ifaddrs *) = NULL;

static void init_funcs(void) {
    if (!real_socket) real_socket = dlsym(RTLD_NEXT, "socket");
    if (!real_recvfrom) real_recvfrom = dlsym(RTLD_NEXT, "recvfrom");
    if (!real_sendto) real_sendto = dlsym(RTLD_NEXT, "sendto");
    if (!real_send) real_send = dlsym(RTLD_NEXT, "send");
    if (!real_sendmsg) real_sendmsg = dlsym(RTLD_NEXT, "sendmsg");
    if (!real_getifaddrs) real_getifaddrs = dlsym(RTLD_NEXT, "getifaddrs");
    if (!real_freeifaddrs) real_freeifaddrs = dlsym(RTLD_NEXT, "freeifaddrs");
}

/*
 * Interceptar getifaddrs() para esconder completamente o IPv6 da Hikvision.
 */
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
        if (nl_count < 64) nl_fds[nl_count++] = fd;
    }
    return fd;
}

static int is_nl(int fd) {
    for (int i = 0; i < nl_count; i++)
        if (nl_fds[i] == fd) return 1;
    return 0;
}

static void record_seq(uint32_t seq, int is_getaddr, unsigned char family) {
    seq_history[seq_hist_idx].seq = seq;
    seq_history[seq_hist_idx].is_getaddr = is_getaddr;
    seq_history[seq_hist_idx].family = family;
    seq_hist_idx = (seq_hist_idx + 1) % 256;
}

/* Returns a pointer to the tracking info, or NULL if not found */
static struct seq_info* get_seq_info(uint32_t seq) {
    for (int i = 0; i < 256; i++) {
        if (seq_history[i].seq == seq && seq_history[i].is_getaddr != 0) {
            return &seq_history[i];
        }
    }
    return NULL;
}

static void inspect_outgoing(int fd, const void *buf, size_t len) {
    if (!is_nl(fd) || len < sizeof(struct nlmsghdr)) return;
    struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
    
    if (nlh->nlmsg_type == RTM_GETADDR) {
        struct rtgenmsg *rtgen = (struct rtgenmsg *)NLMSG_DATA(nlh);
        record_seq(nlh->nlmsg_seq, 1, rtgen->rtgen_family);
    } else {
        /* Record other requests as not-GETADDR so we never inject on them */
        record_seq(nlh->nlmsg_seq, 0, 0);
    }
}

ssize_t sendto(int fd, const void *buf, size_t len, int flags,
               const struct sockaddr *dest_addr, socklen_t addrlen) {
    init_funcs();
    inspect_outgoing(fd, buf, len);
    return real_sendto(fd, buf, len, flags, dest_addr, addrlen);
}

ssize_t send(int fd, const void *buf, size_t len, int flags) {
    init_funcs();
    inspect_outgoing(fd, buf, len);
    return real_send(fd, buf, len, flags);
}

ssize_t sendmsg(int fd, const struct msghdr *msg, int flags) {
    init_funcs();
    if (msg && msg->msg_iov && msg->msg_iovlen > 0) {
        inspect_outgoing(fd, msg->msg_iov[0].iov_base, msg->msg_iov[0].iov_len);
    }
    return real_sendmsg(fd, msg, flags);
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
        
        // We only inject IPv4 
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

        /* Calcular tamanho da mensagem */
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
        nlh->nlmsg_seq = seq; /* PRESERvA SEQUENCE */
        nlh->nlmsg_pid = pid; /* PRESERVA PID */

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
        if (bcast)
            memcpy(RTA_DATA(rta), &bcast, 4);
        else
            memcpy(RTA_DATA(rta), &ip, 4);
        attr_p += RTA_SPACE(4);

        total += msg_len;
    }
    if (real_freeifaddrs) real_freeifaddrs(ifas);

    if (total == 0) return -1;

    /* NLMSG_DONE finalizamos a lista */
    struct nlmsghdr *done = (struct nlmsghdr *)(buf + total);
    memset(done, 0, 20);
    done->nlmsg_len = 20;
    done->nlmsg_type = NLMSG_DONE;
    done->nlmsg_flags = NLM_F_MULTI;
    done->nlmsg_seq = seq; /* PRESERVA SEQUENCE */
    done->nlmsg_pid = pid; /* PRESERVA PID */
    total += 20;

    return (ssize_t)total;
}

/* Interceptar recvfrom() */
ssize_t recvfrom(int fd, void *buf, size_t len, int flags,
                 struct sockaddr *src, socklen_t *addrlen) {
    init_funcs();
    ssize_t result = real_recvfrom(fd, buf, len, flags, src, addrlen);

    if (is_nl(fd) && result >= 16) {
        struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
        
        if (result == 20 && nlh->nlmsg_type == NLMSG_DONE) {
            uint32_t orig_seq = nlh->nlmsg_seq;
            uint32_t orig_pid = nlh->nlmsg_pid;
            
            struct seq_info *info = get_seq_info(orig_seq);
            
            // Only inject if we KNOW this sequence was an RTM_GETADDR for IPv4 / UNSPEC
            if (info != NULL && info->is_getaddr) {
                if (info->family == AF_INET || info->family == AF_UNSPEC) {
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
