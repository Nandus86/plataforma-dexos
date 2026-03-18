#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# ==== CONFIGURAÇÃO ====
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "============================================="
echo "IP Interno: $IP_INTERNO"
echo "Todos IPs: $(hostname -I)"
echo "============================================="

# Injetar IP no Config.xml
sed -i "s/<IP>0\.0\.0\.0<\/IP>/<IP>$IP_INTERNO<\/IP>/g" /app/Config.xml

# Ativar serviços
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# Configurar sysctl (ignorar erros se sem permissão)
sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.arp_announce=2 2>/dev/null || true

# ==== INICIAR MOTOR COM LD_PRELOAD ====
echo "Iniciando DeviceGatewayService com interceptação de rede..."
export LD_PRELOAD=/app/fakenet.so
./DeviceGatewayService -service -instance=DeviceGatewayService &
ENGINE_PID=$!
echo "Motor PID: $ENGINE_PID"

# Aguardar porta 8081
echo "Aguardando porta 8081..."
for i in $(seq 1 30); do
    if netstat -tlnp 2>/dev/null | grep -q ":8081"; then
        echo ">>> PORTA 8081 ABERTA! Motor OK! <<<"
        break
    fi
    sleep 2
done

# ==== INICIAR NGINX (sem LD_PRELOAD) ====
unset LD_PRELOAD
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "============================================="
echo "Gateway ativo! Motor PID=$ENGINE_PID"
echo "============================================="

# Manter container vivo
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null
