FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libcap2 libcap2-bin net-tools iproute2 procps libxml2 \
    psmisc dos2unix curl kmod \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar TODOS os arquivos do SDK original
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# 1. Preparar XMLs a partir dos templates
RUN mv Config_Template.xml Config.xml && \
    mv PrivateConfig_Template.xml PrivateConfig.xml && \
    mv ISAPIConfig_Template.xml ISAPIConfig.xml

# 2. Copiar sfrzcfg para /etc
RUN cp -f /app/sfrzcfg /etc/sfrzcfg

# 3. Configurar ldconfig
RUN echo "/app" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/stream" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/plugins/ehomeV5_plugin" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/plugins/ehome_plugin" >> /etc/ld.so.conf && \
    ldconfig

# 4. Links SSL
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1

# 5. Diretórios
RUN mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# 6. Permissões
RUN chmod +x -R /app

# 7. Instalação oficial do binário
RUN cd /app && ./DeviceGatewayService -install || true

# 8. Substituir nginx.conf pelo nosso (baseado no original, sem blocos incompativeis)
COPY nginx_gateway.conf /app/nginx/conf/nginx.conf

# 9. Copiar entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh /app/nginx/conf/nginx.conf && \
    chmod +x /app/entrypoint.sh

ENV LD_LIBRARY_PATH=/app:/app/lib:/app/apps/das_media_x64/stream:$LD_LIBRARY_PATH

EXPOSE 80 443 7660-7667/tcp 7660-7667/udp 8081 9081 27000-27800

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
