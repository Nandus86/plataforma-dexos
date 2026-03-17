#!/bin/bash
# Forçar IP de escuta global
echo "Iniciando Hik Device Gateway..."

# Injetar 0.0.0.0 para que ele escute em qualquer interface do container
sed -i 's/<IP>.*<\/IP>/<IP>0.0.0.0<\/IP>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml

echo "Subindo Motor (Engine)..."
# Usando aspas para garantir que os espaços não sejam perdidos
exec /app/DeviceGatewayService -service -instance=DeviceGatewayService &

sleep 10

echo "Subindo Web Interface (Nginx)..."
# O prefixo -p já aponta para /app/nginx/, então o conf deve ser relativo ou absoluto direto
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "Logs ativos:"
tail -f /app/logs/*.log 2>/dev/null
