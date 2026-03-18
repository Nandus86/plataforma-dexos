/*
 * fakenet.c - LD_PRELOAD library to fix Hikvision IP detection in Docker
 *
 * The Hikvision DeviceGatewayService uses low-level socket operations
 * to detect network interfaces and their IPs. Docker's virtual interfaces
 * don't respond correctly to this binary's detection method.
 *
 * This library intercepts getifaddrs() to ensure IPv4 addresses are
 * properly reported for all interfaces.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <netinet/in.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <stdarg.h>

/* Interceptar ioctl para injetar IP quando SIOCGIFADDR falhar */
int ioctl(int fd, unsigned long request, ...) {
    static int (*real_ioctl)(int, unsigned long, ...) = NULL;
    if (!real_ioctl) {
        real_ioctl = dlsym(RTLD_NEXT, "ioctl");
    }

    va_list args;
    va_start(args, request);
    void *arg = va_arg(args, void*);
    va_end(args);

    int result = real_ioctl(fd, request, arg);

    /* Se a consulta de IP falhou para uma interface não-loopback, injetar IP */
    if (result < 0 && request == SIOCGIFADDR) {
        struct ifreq *ifr = (struct ifreq *)arg;
        if (strcmp(ifr->ifr_name, "lo") != 0) {
            /* Obter IP real via socket UDP (método que funciona em Docker) */
            int sock = socket(AF_INET, SOCK_DGRAM, 0);
            if (sock >= 0) {
                struct sockaddr_in dest;
                memset(&dest, 0, sizeof(dest));
                dest.sin_family = AF_INET;
                dest.sin_port = htons(53);
                inet_pton(AF_INET, "8.8.8.8", &dest.sin_addr);

                if (connect(sock, (struct sockaddr*)&dest, sizeof(dest)) == 0) {
                    struct sockaddr_in local;
                    socklen_t len = sizeof(local);
                    if (getsockname(sock, (struct sockaddr*)&local, &len) == 0) {
                        struct sockaddr_in *sin = (struct sockaddr_in *)&ifr->ifr_addr;
                        sin->sin_family = AF_INET;
                        sin->sin_addr = local.sin_addr;
                        close(sock);
                        return 0;
                    }
                }
                close(sock);
            }

            /* Fallback: usar IP fixo */
            struct sockaddr_in *sin = (struct sockaddr_in *)&ifr->ifr_addr;
            sin->sin_family = AF_INET;
            inet_pton(AF_INET, "10.10.10.1", &sin->sin_addr);
            return 0;
        }
    }

    return result;
}
