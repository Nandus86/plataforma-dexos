/*
 * fakenet.c - LD_PRELOAD para injetar IP em respostas netlink
 *
 * O binário Hikvision usa AF_NETLINK + NETLINK_ROUTE para detectar IPs.
 * Em Docker, a resposta de RTM_GETADDR vem vazia (20 bytes = NLMSG_DONE).
 * Esta lib intercepta essa resposta e injeta um endereço IPv4 válido
 * com o índice de interface REAL do container.
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
static int injected = 0;

/* Ponteiros reais */
static int (*real_socket)(int, int, int) = NULL;
static ssize_t (*real_recvfrom)(int, void*, size_t, int, struct sockaddr*, socklen_t*) = NULL;

static void init_funcs(void) {
    if (!real_socket) real_socket = dlsym(RTLD_NEXT, "socket");
    if (!real_recvfrom) real_recvfrom = dlsym(RTLD_NEXT, "recvfrom");
}

/* Detectar IP e índice reais do container */
static uint32_t detect_ip(unsigned int *out_index) {
    struct ifaddrs *ifas, *ifa;
    uint32_t ip = 0;
    *out_index = 0;

    int (*real_getifaddrs)(struct ifaddrs **) = dlsym(RTLD_NEXT, "getifaddrs");
    void (*real_freeifaddrs)(struct ifaddrs *) = dlsym(RTLD_NEXT, "freeifaddrs");

    if (real_getifaddrs && real_getifaddrs(&ifas) == 0) {
        for (ifa = ifas; ifa; ifa = ifa->ifa_next) {
            if (!ifa->ifa_addr || ifa->ifa_addr->sa_family != AF_INET) continue;
            struct sockaddr_in *sin = (struct sockaddr_in *)ifa->ifa_addr;
            /* Ignorar loopback (127.x.x.x) */
            if ((ntohl(sin->sin_addr.s_addr) & 0xFF000000) == 0x7F000000) continue;
            ip = sin->sin_addr.s_addr;
            /* Obter o ÍNDICE REAL da interface */
            *out_index = if_nametoindex(ifa->ifa_name);
            break;
        }
        if (real_freeifaddrs) real_freeifaddrs(ifas);
    }

    if (!ip) {
        inet_pton(AF_INET, "10.10.10.1", &ip);
        *out_index = 2;
    }
    return ip;
}

/* Interceptar socket() */
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

/*
 * Construir resposta RTM_NEWADDR com IP e índice reais.
 * Gera múltiplas mensagens (uma por interface com IP) + NLMSG_DONE.
 */
static ssize_t build_response(void *buf, size_t buflen) {
    struct ifaddrs *ifas, *ifa;
    unsigned char *p = (unsigned char *)buf;
    size_t total = 0;

    int (*real_getifaddrs)(struct ifaddrs **) = dlsym(RTLD_NEXT, "getifaddrs");
    void (*real_freeifaddrs)(struct ifaddrs *) = dlsym(RTLD_NEXT, "freeifaddrs");

    if (!real_getifaddrs || real_getifaddrs(&ifas) != 0)
        return -1;

    for (ifa = ifas; ifa; ifa = ifa->ifa_next) {
        if (!ifa->ifa_addr || ifa->ifa_addr->sa_family != AF_INET) continue;
        struct sockaddr_in *sin = (struct sockaddr_in *)ifa->ifa_addr;
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
        nlh->nlmsg_seq = 0;
        nlh->nlmsg_pid = 0;

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

    /* NLMSG_DONE */
    struct nlmsghdr *done = (struct nlmsghdr *)(buf + total);
    memset(done, 0, 20);
    done->nlmsg_len = 20;
    done->nlmsg_type = NLMSG_DONE;
    done->nlmsg_flags = NLM_F_MULTI;
    total += 20;

    return (ssize_t)total;
}

/* Interceptar recvfrom() */
ssize_t recvfrom(int fd, void *buf, size_t len, int flags,
                 struct sockaddr *src, socklen_t *addrlen) {
    init_funcs();
    ssize_t result = real_recvfrom(fd, buf, len, flags, src, addrlen);

    /* Primeira resposta NLMSG_DONE em socket netlink = substituir */
    if (!injected && is_nl(fd) && result >= 16) {
        struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
        if (nlh->nlmsg_type == NLMSG_DONE) {
            ssize_t fake = build_response(buf, len);
            if (fake > 0) {
                injected = 1;
                return fake;
            }
        }
    }

    return result;
}
