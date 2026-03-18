FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libcap2 libcap2-bin net-tools iproute2 procps libxml2 \
    psmisc dos2unix curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar TODOS os arquivos do SDK original (inclui o nginx customizado da Hikvision)
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# ==== PASSO CRÍTICO: Seguir o processo oficial de instalação ====

# 1. Preparar XMLs a partir dos templates (como faz o ConfigUpgrade.sh)
RUN mv Config_Template.xml Config.xml && \
    mv PrivateConfig_Template.xml PrivateConfig.xml && \
    mv ISAPIConfig_Template.xml ISAPIConfig.xml

# 2. Copiar sfrzcfg para /etc (exigido pelo binário para licenciamento)
RUN cp -f /app/sfrzcfg /etc/sfrzcfg

# 3. Configurar ldconfig para encontrar as bibliotecas (como faz o ivmsservice.sh)
RUN echo "/app" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/stream" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/plugins/ehomeV5_plugin" >> /etc/ld.so.conf && \
    echo "/app/apps/das_media_x64/plugins/ehome_plugin" >> /etc/ld.so.conf && \
    ldconfig

# 4. Criar links SSL para compatibilidade
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1

# 5. Criar diretorios necessários
RUN mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# 6. Tornar tudo executável
RUN chmod +x -R /app

# 7. Rodar o passo de instalação do binário (cria bancos de dados, etc)
RUN cd /app && ./DeviceGatewayService -install || true

# 8. Copiar entrypoint e converter line endings
COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# ==== REMOVER APENAS o bloco problemático do nginx.conf (linhas 64-71 com host_flag) ====
# Essas linhas usam 'set $host_flag' que o nginx customizado NÃO suporta em certas configurações
RUN sed -i '63,77{/host_flag/d; /exter_addr/d; /\$host != \$server_addr/d; /\$host != \$exter_addr/d}' /app/nginx/conf/nginx.conf

ENV LD_LIBRARY_PATH=/app:/app/lib:/app/apps/das_media_x64/stream:$LD_LIBRARY_PATH

EXPOSE 80 443 7660-7667/tcp 7660-7667/udp 8081 9081 27000-27800

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
