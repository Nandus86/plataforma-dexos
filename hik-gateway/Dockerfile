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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar os arquivos extraídos
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Criar diretórios de log que o Nginx e o serviço esperam
RUN mkdir -p /app/nginx/logs /app/logs /app/nginx/temp && \
    chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp

# Dar permissão de execução em tudo
RUN chmod +x -R /app

# Configurar o ambiente de bibliotecas
ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar links simbólicos se necessário
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1

# Expor portas
EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443

# Rodar o serviço
CMD ["./DeviceGatewayService"]
