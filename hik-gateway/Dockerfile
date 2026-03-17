FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libcap2 libcap2-bin net-tools iproute2 procps libxml2 psmisc dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Inicializa XMLs
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml

# Garante que as configuções limpas sejam copiadas
COPY nginx_clean.conf /app/nginx/conf/nginx.conf
COPY entrypoint.sh /app/entrypoint.sh

# CORREÇÃO CRÍTICA: Remove caracteres invisíveis do Windows (\r)
RUN dos2unix /app/entrypoint.sh /app/nginx/conf/nginx.conf && \
    chmod +x /app/entrypoint.sh && \
    ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run && \
    chmod +x -R /app

ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
