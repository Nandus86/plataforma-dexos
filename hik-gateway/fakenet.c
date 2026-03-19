/*
 * fakenet.c - LD_PRELOAD para injetar IPv4 em respostas netlink
 * + Hook bind() para forçar escuta em 0.0.0.0 (todas interfaces)
 * + Filtro getifaddrs() para esconder IPv6
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

#define PHASE_IDLE           0
#define PHASE_SAW_NEWLINK    1
#define PHASE_EXPECT_GETADDR 2

struct nl_state { int fd; int phase; };
static struct nl_state nl_sockets[64];
static int nl_count = 0;

static int (*real_socket)(int, int, int) = NULL;
static ssize_t (*real_recvfrom)(int, void*, size_t, int, struct sockaddr*, socklen_t*) = NULL;
static int (*real_getifaddrs)(struct ifaddrs **) = NULL;
static void (*real_freeifaddrs)(struct ifaddrs *) = NULL;
static int (*real_bind)(int, const struct sockaddr*, socklen_t) = NULL;

static void init_funcs(void) {
    if (!real_socket)      real_socket      = dlsym(RTLD_NEXT, "socket");
    if (!real_recvfrom)    real_recvfrom    = dlsym(RTLD_NEXT, "recvfrom");
    if (!real_getifaddrs)  real_getifaddrs  = dlsym(RTLD_NEXT, "getifaddrs");
    if (!real_freeifaddrs) real_freeifaddrs = dlsym(RTLD_NEXT, "freeifaddrs");
    if (!real_bind)        real_bind        = dlsym(RTLD_NEXT, "bind");
}

/*
 * bind() hook: forçar 0.0.0.0 em vez de IP específico
 * O drv_isup_dev faz bind(10.132.0.2:7661) → aparelho não conecta
 * Com este hook: bind(0.0.0.0:7661) → aceita de qualquer interface
 */
int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    init_funcs();
    if (!real_bind) real_bind = dlsym(RTLD_NEXT, "bind");

    if (addr && addr->sa_family == AF_INET) {
        struct sockaddr_in *sin = (struct sockaddr_in *)addr;
        uint32_t ip = ntohl(sin->sin_addr.s_addr);

        /* Só interceptar IPs não-loopback e não-wildcard */
        if (ip != 0 && (ip & 0xFF000000) != 0x7F000000) {
            struct sockaddr_in modified = *sin;
            modified.sin_addr.s_addr = htonl(INADDR_ANY); /* 0.0.0.0 */

            char ipstr[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &sin->sin_addr, ipstr, sizeof(ipstr));
            fprintf(stderr, "fakenet: bind %s:%d -> 0.0.0.0:%d\n",
                    ipstr, ntohs(sin->sin_port), ntohs(sin->sin_port));

            return real_bind(sockfd, (struct sockaddr *)&modified, sizeof(modified));
        }
    }
    return real_bind(sockfd, addr, addrlen);
}

/*
 * getifaddrs: esconder IPv6 SEM liberar nos individuais
 * (glibc aloca ifaddrs como bloco unico - free individual = heap corruption)
 */
int getifaddrs(struct ifaddrs **ifap) {
    init_funcs();
    if (!real_getifaddrs) return -1;
    int ret = real_getifaddrs(ifap);
    if (ret != 0 || !ifap || !*ifap) return ret;
    struct ifaddrs *prev = NULL, *cur = *ifap;
    while (cur) {
        struct ifaddrs *next = cur->ifa_next;
        if (cur->ifa_addr && cur->ifa_addr->sa_family == AF_INET6) {
            if (prev) prev->ifa_next = next;
            else *ifap = next;
            /* NAO chamar freeifaddrs em no individual! */
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
            nl_sockets[nl_count].phase = PHASE_IDLE;
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

static ssize_t build_response(void *buf, size_t buflen, uint32_t seq, uint32_t pid) {
    struct ifaddrs *ifas, *ifa;
    size_t total = 0;
    init_funcs();
    if (!real_getifaddrs || real_getifaddrs(&ifas) != 0) return -1;

    for (ifa = ifas; ifa; ifa = ifa->ifa_next) {
        if (!ifa->ifa_addr || ifa->ifa_addr->sa_family != AF_INET) continue;
        struct sockaddr_in *sin = (struct sockaddr_in *)ifa->ifa_addr;
        if ((ntohl(sin->sin_addr.s_addr) & 0xFF000000) == 0x7F000000) continue;

        unsigned int idx = if_nametoindex(ifa->ifa_name);
        uint32_t ip = sin->sin_addr.s_addr;
        uint32_t bcast = 0;
        if (ifa->ifa_broadaddr) bcast = ((struct sockaddr_in *)ifa->ifa_broadaddr)->sin_addr.s_addr;

        size_t msg_len = NLMSG_SPACE(NLMSG_ALIGN(sizeof(struct ifaddrmsg)) + RTA_SPACE(4)*3);
        if (total + msg_len + 20 > buflen) break;

        struct nlmsghdr *nlh = (struct nlmsghdr *)(buf + total);
        memset(nlh, 0, msg_len);
        nlh->nlmsg_len = msg_len; nlh->nlmsg_type = RTM_NEWADDR;
        nlh->nlmsg_flags = NLM_F_MULTI; nlh->nlmsg_seq = seq; nlh->nlmsg_pid = pid;

        struct ifaddrmsg *ifam = (struct ifaddrmsg *)NLMSG_DATA(nlh);
        ifam->ifa_family = AF_INET; ifam->ifa_prefixlen = 24;
        ifam->ifa_flags = 0x80; ifam->ifa_scope = 0; ifam->ifa_index = idx;

        unsigned char *ap = (unsigned char *)ifam + NLMSG_ALIGN(sizeof(*ifam));
        struct rtattr *rta;
        rta = (struct rtattr *)ap; rta->rta_type = IFA_ADDRESS; rta->rta_len = RTA_LENGTH(4);
        memcpy(RTA_DATA(rta), &ip, 4); ap += RTA_SPACE(4);
        rta = (struct rtattr *)ap; rta->rta_type = IFA_LOCAL; rta->rta_len = RTA_LENGTH(4);
        memcpy(RTA_DATA(rta), &ip, 4); ap += RTA_SPACE(4);
        rta = (struct rtattr *)ap; rta->rta_type = IFA_BROADCAST; rta->rta_len = RTA_LENGTH(4);
        memcpy(RTA_DATA(rta), bcast ? &bcast : &ip, 4);
        total += msg_len;
    }
    if (real_freeifaddrs) real_freeifaddrs(ifas);
    if (total == 0) return -1;

    struct nlmsghdr *done = (struct nlmsghdr *)(buf + total);
    memset(done, 0, 20); done->nlmsg_len = 20; done->nlmsg_type = NLMSG_DONE;
    done->nlmsg_flags = NLM_F_MULTI; done->nlmsg_seq = seq; done->nlmsg_pid = pid;
    return (ssize_t)(total + 20);
}

static void drain_until_done(int fd, void *buf, size_t len) {
    for (int i = 0; i < 20; i++) {
        ssize_t r = real_recvfrom(fd, buf, len, 0, NULL, NULL);
        if (r <= 0) break;
        if (r >= 16 && ((struct nlmsghdr *)buf)->nlmsg_type == NLMSG_DONE) break;
    }
}

ssize_t recvfrom(int fd, void *buf, size_t len, int flags,
                 struct sockaddr *src, socklen_t *addrlen) {
    init_funcs();
    ssize_t result = real_recvfrom(fd, buf, len, flags, src, addrlen);
    struct nl_state *state = get_nl_state(fd);
    if (!state || result < 16) return result;

    struct nlmsghdr *nlh = (struct nlmsghdr *)buf;

    switch (state->phase) {
    case PHASE_IDLE:
        if (nlh->nlmsg_type == RTM_NEWLINK) state->phase = PHASE_SAW_NEWLINK;
        break;

    case PHASE_SAW_NEWLINK:
        if (nlh->nlmsg_type == NLMSG_DONE) state->phase = PHASE_EXPECT_GETADDR;
        else if (nlh->nlmsg_type != RTM_NEWLINK) state->phase = PHASE_IDLE;
        break;

    case PHASE_EXPECT_GETADDR: {
        uint32_t s = nlh->nlmsg_seq, p = nlh->nlmsg_pid;
        state->phase = PHASE_IDLE;

        if (nlh->nlmsg_type == NLMSG_DONE && result == 20) {
            /* GETADDR vazio - injetar IPv4 */
            ssize_t fake = build_response(buf, len, s, p);
            if (fake > 0) return fake;
        }
        else if (nlh->nlmsg_type == RTM_NEWADDR) {
            /* GETADDR retornou dados (IPv4 ou IPv6) - drenar e substituir */
            int found_done = 0;
            struct nlmsghdr *cur = nlh;
            unsigned int rem = (unsigned int)result;
            while (NLMSG_OK(cur, rem)) {
                if (cur->nlmsg_type == NLMSG_DONE) { found_done = 1; break; }
                cur = NLMSG_NEXT(cur, rem);
            }
            if (!found_done) drain_until_done(fd, buf, len);
            ssize_t fake = build_response(buf, len, s, p);
            if (fake > 0) return fake;
        }
        break;
    }
    }
    return result;
}
