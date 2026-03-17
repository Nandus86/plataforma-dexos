FROM ubuntu:20.04

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    libcap2 \
    libcap2-bin \
    net-tools \
    iproute2 \
    procps \
    libxml2 \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar os arquivos extraídos
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Inicializar configurações
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml

# Garantir links simbólicos e diretórios de log/run
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod +x -R /app

# Configurar o ambiente de bibliotecas
ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar script de inicialização usando comandos individuais para garantir espaços
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'IP_INTERNO=$(hostname -I | awk "{print \$1}")' >> /app/entrypoint.sh && \
    echo 'echo "IP Detectado: $IP_INTERNO"' >> /app/entrypoint.sh && \
    # Injetar o IP real no Config.xml antes de rodar o serviço
    echo 'sed -i "s/<IP>0.0.0.0<\/IP>/<IP>$IP_INTERNO<\/IP>/g" /app/Config.xml' >> /app/entrypoint.sh && \
    echo 'sed -i "s/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g" /app/Config.xml' >> /app/entrypoint.sh && \
    # Comando de inicialização com espaços garantidos
    echo './DeviceGatewayService -service -instance=DeviceGatewayService &' >> /app/entrypoint.sh && \
    echo 'sleep 10' >> /app/entrypoint.sh && \
    echo 'if ! pgrep -f "DeviceGateway-nginx" > /dev/null; then' >> /app/entrypoint.sh && \
    echo '  echo "Iniciando Nginx manualmente..."' >> /app/entrypoint.sh && \
    echo '  /app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh && \
    echo 'tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expor portas completas
EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800

CMD ["/app/entrypoint.sh"]
