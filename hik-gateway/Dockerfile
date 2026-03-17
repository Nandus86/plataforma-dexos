FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libcap2 libcap2-bin net-tools iproute2 procps libxml2 psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Inicializa configurações e corrige arquivos problemáticos
RUN cp Config_Template.xml Config.xml && \
    cp PrivateConfig_Template.xml PrivateConfig.xml && \
    cp ISAPIConfig_Template.xml ISAPIConfig.xml && \
    # Remove a proteção de "host head attack" do Nginx que está causando erro de sintaxe
    sed -i '60,75d' /app/nginx/conf/nginx.conf && \
    # Ativa os serviços básicos no XML
    sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' Config.xml

# Garantir links e diretórios
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1 && \
    mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db && \
    chmod +x -R /app

ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar o entrypoint usando um método que GARANTE a preservação de espaços
RUN printf '#!/bin/bash\n\
IP_INTERNO=$(hostname -I | awk "{print \$1}")\n\
echo "IP Detectado: $IP_INTERNO"\n\
# Forçar o IP no Config.xml para o Gateway "enxergar" a rede\n\
sed -i "s/<IP>0.0.0.0<\\/IP>/<IP>$IP_INTERNO<\\/IP>/g" /app/Config.xml\n\
\n\
echo "Iniciando Hik Device Gateway Engine..."\n\
# Executando com espaços explícitos\n\
./DeviceGatewayService -service -instance=DeviceGatewayService &\n\
\n\
sleep 10\n\
\n\
echo "Iniciando Hik Device Gateway Web (Nginx)..."\n\
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf\n\
\n\
echo "Monitorando..."\n\
tail -f /app/logs/*.log 2>/dev/null' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443 27000-27800
CMD ["/app/entrypoint.sh"]
