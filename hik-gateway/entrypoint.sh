#!/bin/bash
# Garantir permissões e diretórios no momento do boot
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db

# Injetar binding global no Config.xml
sed -i 's/<IP>.*<\/IP>/<IP>0.0.0.0<\/IP>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml

echo "IP Detectado no Container: $(hostname -I)"
echo "Iniciando Motor do Gateway em background..."

# Iniciar o motor em background e deixar ele rodando
/app/DeviceGatewayService -service -instance=DeviceGatewayService &

# Pequena pausa para o motor liberar a porta 8081
sleep 5

echo "Iniciando Interface Web (Nginx) em foreground..."
# Rodar o Nginx com 'exec' para ele ser o processo principal (PID 1) do container
# Isso evita que o container morra e entre em loop de reinicializacao
exec /app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf -g "daemon off;"
