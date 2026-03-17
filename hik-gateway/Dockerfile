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

# Inicializar e ativar configurações (ativando os serviços que vem desligados por padrão)
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml && \
    sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' Config.xml

# Garantir links simbólicos e diretórios de log
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run && \
    chmod +x -R /app

# Configurar o ambiente de bibliotecas
ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar script de inicialização usando printf para garantir espaços e quebras de linha corretas
RUN printf '#!/bin/bash\n\
echo "Iniciando Hik Device Gateway..."\n\
# Rodar em modo service (background)\n\
./DeviceGatewayService -service -instance=DeviceGatewayService\n\
sleep 5\n\
# Verificar se o Nginx subiu\n\
if ! pgrep -f "DeviceGateway-nginx" > /dev/null; then\n\
    echo "Nginx nao iniciou automaticamente, tentando inicio manual..."\n\
    ./nginx/DeviceGateway-nginx -p /app/nginx/ -c conf/nginx.conf\n\
fi\n\
echo "Gateway rodando. Monitorando logs..."\n\
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Expor portas
EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800

CMD ["/app/entrypoint.sh"]
