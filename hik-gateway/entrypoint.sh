#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO DE AMBIENTE ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# ==== CRIAR INTERFACE DUMMY PARA O MOTOR DETECTAR O IP ====
# O binário da Hikvision usa raw sockets ARP para detectar IPs.
# Interfaces virtuais do Docker (veth) não respondem corretamente a esse tipo de scan.
# Criar uma interface 'dummy' com um IP real resolve isso.
ip link add dummy0 type dummy 2>/dev/null || true
ip addr add 10.10.10.1/24 dev dummy0 2>/dev/null || true
ip link set dummy0 up 2>/dev/null || true

# ==== CONFIGURAÇÃO DE REDE ====
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "============================================="
echo "IP Interno Detectado: $IP_INTERNO"
echo "IP Dummy: 10.10.10.1"
echo "Todos os IPs: $(hostname -I)"
echo "============================================="

# Injetar IP no Config.xml
sed -i "s/<IP>0\.0\.0\.0<\/IP>/<IP>10.10.10.1<\/IP>/g" /app/Config.xml

# Ativar TODOS os serviços
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# ==== CONFIGURAÇÃO DE SYSCTL ====
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

# Aguardar a porta 8081
echo "Aguardando porta 8081..."
for i in $(seq 1 30); do
    if netstat -tlnp 2>/dev/null | grep -q ":8081"; then
        echo ">>> Porta 8081 ABERTA! Motor funcionando! <<<"
        break
    fi
    sleep 2
done

# Verificar se o motor está rodando
if ! kill -0 $ENGINE_PID 2>/dev/null; then
    echo "ERRO: Motor encerrou inesperadamente!"
fi

# ==== INICIAR O NGINX ====
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf

echo "============================================="
echo "Gateway ativo!"
echo "============================================="

# Manter container vivo
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null
