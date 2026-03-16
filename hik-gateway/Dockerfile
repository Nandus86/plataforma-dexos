FROM ubuntu:20.04

# Evitar prompts interativos durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    libcap2 \
    net-tools \
    iproute2 \
    procps \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar os arquivos extraídos (mantendo a estrutura)
# Assumindo que o conteúdo de HikDeviceGateway_V1.8.0.4Build20250227_Linux64 está em .
COPY HikDeviceGateway_V1.8.0.4Build20250227_Linux64/ .

# Dar permissão de execução em tudo
RUN chmod +x -R /app

# Configurar o ambiente de bibliotecas
ENV LD_LIBRARY_PATH=/app:/app/lib:$LD_LIBRARY_PATH

# Criar links simbólicos se necessário (baseado no que o install.sh faz)
RUN ln -sf /app/libssl.so.1.1 /usr/lib/libssl.so.1.1 && \
    ln -sf /app/libcrypto.so.1.1 /usr/lib/libcrypto.so.1.1

# Expor portas padrões baseadas nos templates da Hikvision
# 7660-7667: ISUP/EHome
# 8081: API do Gateway
# 80/443: Web Management
EXPOSE 7660-7667/tcp 7660-7667/udp 8081 80 443

# Rodar o serviço diretamente (sem o guard para simplificar o log do docker init)
# Ou rodar o start.sh ajustado
CMD ["./DeviceGatewayService"]
