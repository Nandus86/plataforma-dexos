#!/bin/bash
# Garantir permissões e diretórios no momento do boot
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db

# Injetar binding global no Config.xml para garantir que o gateway aceite conexões
sed -i 's/<IP>.*<\/IP>/<IP>0.0.0.0<\/IP>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml

echo "IP Detectado no Container: $(hostname -I)"

echo "Iniciando Motor do Gateway (Background)..."
/app/DeviceGatewayService -service -instance=DeviceGatewayService &

sleep 5

echo "Iniciando Interface Web (Nginx Background)..."
# Iniciar o Nginx sem o 'exec' para que o script continue
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "Gateway em execução. Monitorando logs para manter o container vivo..."
# O tail -f mantém o container rodando e permite que ambos os serviços (Gateway + Nginx) funcionem em paralelo
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log
