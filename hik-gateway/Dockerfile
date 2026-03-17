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

# Inicializar configurações e FORÇAR ativação de IP e HTTP
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml && \
    # Ativa todos os <Enable>0 para 1 no Config.xml
    sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' Config.xml && \
    # Garante que o IP de escuta seja 0.0.0.0 (todas interfaces)
    sed -i 's/<IP>127.0.0.1<\/IP>/<IP>0.0.0.0<\/IP>/g' Config.xml 2>/dev/null || true

# Garantir links simbólicos e diretórios de log/run
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod +x -R /app

# Configurar o ambiente de bibliotecas
ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar script de inicialização robusto
RUN printf '#!/bin/bash\n\
echo "Preparando ambiente..."\n\
# O Gateway precisa encontrar o IP, tentamos forçar a detecção\n\
export IP=$(hostname -I | awk "{print \$1}")\n\
echo "IP detectado no container: $IP"\n\
\n\
echo "Iniciando Hik Device Gateway..."\n\
# Rodar o serviço principal\n\
./DeviceGatewayService -service -instance=DeviceGatewayService &\n\
\n\
sleep 8\n\
\n\
# Iniciar o Nginx manualmente garantindo os caminhos\n\
echo "Iniciando Nginx do Gateway..."\n\
./nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf\n\
\n\
echo "Monitorando logs ativos..."\n\
# Se o log de erro do nginx existir, mostra ele também\n\
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Expor portas completas
EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800

CMD ["/app/entrypoint.sh"]
