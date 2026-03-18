#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO DE AMBIENTE ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# ==== CONFIGURAÇÃO DE REDE ====
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "============================================="
echo "IP Interno Detectado: $IP_INTERNO"
echo "Todos os IPs: $(hostname -I)"
echo "============================================="

# Injetar o IP interno no Config.xml para rede
sed -i "s/<IP>0\.0\.0\.0<\/IP>/<IP>$IP_INTERNO<\/IP>/g" /app/Config.xml

# Ativar TODOS os serviços necessários
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# ==== CONFIGURAÇÃO DE SYSCTL (ignorar erros em containers) ====
sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.arp_announce=2 2>/dev/null || true
sysctl -w net.ipv4.conf.default.arp_announce=2 2>/dev/null || true
sysctl -w net.ipv4.conf.lo.arp_announce=2 2>/dev/null || true

# ==== INICIAR O MOTOR ====
echo "Iniciando DeviceGatewayService..."
./DeviceGatewayService -service -instance=DeviceGatewayService &
ENGINE_PID=$!
echo "Motor PID: $ENGINE_PID"

# Aguardar o motor abrir a porta 8081
echo "Aguardando porta 8081 ficar disponível..."
for i in $(seq 1 30); do
    if netstat -tlnp 2>/dev/null | grep -q ":8081"; then
        echo "Porta 8081 aberta! Motor pronto."
        break
    fi
    echo "Tentativa $i/30 - aguardando..."
    sleep 2
done

# ==== INICIAR O NGINX ====
echo "Iniciando Nginx (DeviceGateway-nginx)..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "============================================="
echo "Gateway em execução!"
echo "  Motor: PID $ENGINE_PID"
echo "  Nginx: porta 80"
echo "  API:   porta 8081"
echo "============================================="

# Manter o container vivo monitorando logs
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null
