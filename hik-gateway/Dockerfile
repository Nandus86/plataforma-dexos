FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libcap2 libcap2-bin net-tools iproute2 procps libxml2 psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar os arquivos extraídos
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Copiar scripts e configurações limpas
COPY entrypoint.sh /app/entrypoint.sh
COPY nginx_clean.conf /app/nginx/conf/nginx.conf

# Inicializa configurações
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml && \
    chmod +x /app/entrypoint.sh

# Garantir links e diretórios
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod +x -R /app

ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
