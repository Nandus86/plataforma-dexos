#!/bin/bash
# Garantir que o IP interno seja injetado corretamente
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "IP Detectado no Container: $IP_INTERNO"

# Injetar o IP no Config.xml
sed -i "s/<IP>0.0.0.0<\/IP>/<IP>$IP_INTERNO<\/IP>/g" /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml

echo "Iniciando Motor do Gateway..."
# Execução direta com argumentos bem definidos
/app/DeviceGatewayService -service -instance=DeviceGatewayService &

sleep 10

echo "Iniciando Interface Web (Nginx)..."
# Iniciar o nginx apontando para o binário customizado da Hikvision
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "Monitorando Logs..."
tail -f /app/logs/*.log 2>/dev/null
