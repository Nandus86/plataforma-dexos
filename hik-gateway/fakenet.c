/*
 * fakenet.c - LD_PRELOAD para injetar IP em respostas netlink
 *
 * O binário Hikvision usa AF_NETLINK + NETLINK_ROUTE para detectar IPs.
 * Em Docker, a resposta de RTM_GETADDR vem vazia (20 bytes = NLMSG_DONE).
 * Esta lib intercepta essa resposta e injeta um endereço IPv4 válido.
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

/* Guarda FDs de sockets netlink */
static int nl_fds[64];
static int nl_count = 0;
/* Flag: já injetamos IP? */
static int injected = 0;

/* Ponteiros para funções reais */
static int (*real_socket)(int, int, int) = NULL;
static ssize_t (*real_recvfrom)(int, void*, size_t, int, struct sockaddr*, socklen_t*) = NULL;

static void init_real_funcs(void) {
    if (!real_socket) real_socket = dlsym(RTLD_NEXT, "socket");
    if (!real_recvfrom) real_recvfrom = dlsym(RTLD_NEXT, "recvfrom");
}

/* Detectar IP real do container */
static uint32_t detect_ip(void) {
    struct ifaddrs *ifas, *ifa;
    uint32_t ip = 0;

    /* Chamar getifaddrs real (usa RTLD_NEXT para evitar recursão) */
    int (*real_getifaddrs)(struct ifaddrs **) = dlsym(RTLD_NEXT, "getifaddrs");
    void (*real_freeifaddrs)(struct ifaddrs *) = dlsym(RTLD_NEXT, "freeifaddrs");

    if (real_getifaddrs && real_getifaddrs(&ifas) == 0) {
        for (ifa = ifas; ifa; ifa = ifa->ifa_next) {
            if (ifa->ifa_addr && ifa->ifa_addr->sa_family == AF_INET) {
                struct sockaddr_in *sin = (struct sockaddr_in *)ifa->ifa_addr;
                /* Ignorar loopback */
                if ((ntohl(sin->sin_addr.s_addr) & 0xFF000000) != 0x7F000000) {
                    ip = sin->sin_addr.s_addr;
                    break;
                }
            }
        }
        if (real_freeifaddrs) real_freeifaddrs(ifas);
    }

    if (!ip) inet_pton(AF_INET, "10.10.10.1", &ip);
    return ip;
}

/* Interceptar socket() para rastrear sockets netlink */
int socket(int domain, int type, int protocol) {
    init_real_funcs();
    int fd = real_socket(domain, type, protocol);
    if (fd >= 0 && domain == AF_NETLINK && protocol == NETLINK_ROUTE) {
        if (nl_count < 64) nl_fds[nl_count++] = fd;
    }
    return fd;
}

static int is_netlink(int fd) {
    for (int i = 0; i < nl_count; i++)
        if (nl_fds[i] == fd) return 1;
    return 0;
}

/*
 * Construir resposta RTM_NEWADDR com IP real.
 * Formato:
 *   [nlmsghdr][ifaddrmsg][RTA IFA_ADDRESS (4 bytes)][RTA IFA_LOCAL (4 bytes)]
 *   [nlmsghdr NLMSG_DONE]
 */
static ssize_t build_addr_response(void *buf, size_t buflen) {
    uint32_t ip = detect_ip();
    unsigned char *p = (unsigned char *)buf;
    size_t total = 0;

    /* === RTM_NEWADDR message === */
    /* nlmsghdr */
    int addr_payload_len = NLMSG_ALIGN(sizeof(struct ifaddrmsg)) +
                           RTA_SPACE(4) + /* IFA_ADDRESS */
                           RTA_SPACE(4);  /* IFA_LOCAL */
    int addr_msg_len = NLMSG_ALIGN(NLMSG_HDRLEN + addr_payload_len);

    if (total + addr_msg_len + NLMSG_ALIGN(NLMSG_HDRLEN + 4) > buflen)
        return -1; /* buffer muito pequeno */

    struct nlmsghdr *nlh = (struct nlmsghdr *)p;
    memset(nlh, 0, addr_msg_len);
    nlh->nlmsg_len = addr_msg_len;
    nlh->nlmsg_type = RTM_NEWADDR;
    nlh->nlmsg_flags = NLM_F_MULTI;
    nlh->nlmsg_seq = 0;
    nlh->nlmsg_pid = 0;
    p += NLMSG_HDRLEN;

    /* ifaddrmsg */
    struct ifaddrmsg *ifa = (struct ifaddrmsg *)p;
    ifa->ifa_family = AF_INET;
    ifa->ifa_prefixlen = 24;
    ifa->ifa_flags = 0x80; /* IFA_F_PERMANENT */
    ifa->ifa_scope = 0;    /* RT_SCOPE_UNIVERSE */
    ifa->ifa_index = 2;    /* eth0 normalmente é index 2 */
    p += NLMSG_ALIGN(sizeof(struct ifaddrmsg));

    /* RTA: IFA_ADDRESS */
    struct rtattr *rta = (struct rtattr *)p;
    rta->rta_type = IFA_ADDRESS;
    rta->rta_len = RTA_LENGTH(4);
    memcpy(RTA_DATA(rta), &ip, 4);
    p += RTA_SPACE(4);

    /* RTA: IFA_LOCAL */
    rta = (struct rtattr *)p;
    rta->rta_type = IFA_LOCAL;
    rta->rta_len = RTA_LENGTH(4);
    memcpy(RTA_DATA(rta), &ip, 4);
    p += RTA_SPACE(4);

    total += addr_msg_len;

    /* === NLMSG_DONE message === */
    nlh = (struct nlmsghdr *)(buf + total);
    memset(nlh, 0, NLMSG_ALIGN(NLMSG_HDRLEN + 4));
    nlh->nlmsg_len = NLMSG_ALIGN(NLMSG_HDRLEN + 4);
    nlh->nlmsg_type = NLMSG_DONE;
    nlh->nlmsg_flags = NLM_F_MULTI;
    int *done_data = (int *)NLMSG_DATA(nlh);
    *done_data = 0;
    total += NLMSG_ALIGN(NLMSG_HDRLEN + 4);

    return (ssize_t)total;
}

/* Interceptar recvfrom() em sockets netlink */
ssize_t recvfrom(int fd, void *buf, size_t len, int flags,
                 struct sockaddr *src, socklen_t *addrlen) {
    init_real_funcs();
    ssize_t result = real_recvfrom(fd, buf, len, flags, src, addrlen);

    /*
     * Se é um socket netlink E a resposta é 20 bytes (NLMSG_DONE vazio)
     * E ainda não injetamos, substituir pela nossa resposta com IP.
     */
    if (!injected && is_netlink(fd) && result == 20) {
        struct nlmsghdr *nlh = (struct nlmsghdr *)buf;
        if (nlh->nlmsg_type == NLMSG_DONE) {
            ssize_t fake_len = build_addr_response(buf, len);
            if (fake_len > 0) {
                injected = 1;
                return fake_len;
            }
        }
    }

    return result;
}
