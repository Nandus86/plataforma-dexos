#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# Limpar estado stale do install
rm -f /app/db/*.db /app/db/*.dat 2>/dev/null || true

# Core dumps
ulimit -c unlimited 2>/dev/null || true

# ==== CONFIGURAÇÃO ====
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "============================================="
echo "IP Interno: $IP_INTERNO"
echo "Todos IPs: $(hostname -I)"
echo "============================================="

# Injetar IP no Config.xml
sed -i "s/<IP>0\.0\.0\.0<\/IP>/<IP>$IP_INTERNO<\/IP>/g" /app/Config.xml

# Log level debug
sed -i 's/<Level>3<\/Level>/<Level>6<\/Level>/g' /app/Config.xml

# Ativar serviços
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# sysctl
sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.arp_announce=2 2>/dev/null || true

# ==== INICIAR MOTOR (daemon que faz fork) ====
echo "Iniciando DeviceGatewayService..."
export LD_PRELOAD=/app/fakenet.so
./DeviceGatewayService -service -instance=DeviceGatewayService &
LAUNCHER_PID=$!
echo "Launcher PID: $LAUNCHER_PID"

# Aguardar o launcher sair (ele faz fork e sai com 0)
echo "Aguardando daemon fazer fork..."
sleep 5

# Encontrar o PID real do daemon filho
unset LD_PRELOAD
SERVICE_PID=""
for i in $(seq 1 10); do
    SERVICE_PID=$(pgrep -f "DeviceGatewaySe" 2>/dev/null | head -1)
    if [ -n "$SERVICE_PID" ]; then
        echo ">>> Daemon encontrado! DeviceGatewaySe PID=$SERVICE_PID <<<"
        break
    fi
    echo "Procurando daemon filho... ($i/10)"
    sleep 2
done

if [ -z "$SERVICE_PID" ]; then
    echo "!!! Daemon filho nao encontrado. Tentando PID alternativo..."
    SERVICE_PID=$(pgrep -f "DeviceGateway" 2>/dev/null | grep -v "nginx" | head -1)
fi

if [ -z "$SERVICE_PID" ]; then
    echo "!!! ERRO FATAL: Nenhum processo DeviceGateway encontrado !!!"
    echo "Processos rodando:"
    ps aux 2>/dev/null || true
    exit 1
fi

echo "Monitorando daemon PID=$SERVICE_PID"

# ==== AGUARDAR PORTA 8081 ====
echo "Aguardando porta 8081 (timeout: 120s)..."
PORTA_OK=0
for i in $(seq 1 60); do
    # Verificar se o daemon filho ainda esta vivo
    if ! kill -0 $SERVICE_PID 2>/dev/null; then
        echo "!!! Daemon PID=$SERVICE_PID morreu na iteração $i !!!"
        echo "--- Log ---"
        tail -30 /app/logs/ivms_service.log 2>/dev/null || echo "(vazio)"
        break
    fi

    if ss -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA! Gateway OK! <<<"
        break
    fi

    # A cada 10 iterações, mostrar portas abertas
    if [ $((i % 10)) -eq 0 ]; then
        echo "[$i/60] Portas ativas:"
        ss -tlnp 2>/dev/null | grep -v "127.0.0.11" || true
    else
        echo "[$i/60] Aguardando 8081... (daemon PID $SERVICE_PID vivo)"
    fi
    sleep 2
done

if [ "$PORTA_OK" -eq 0 ]; then
    echo "!!! AVISO: Porta 8081 nao abriu !!!"
    echo "Portas abertas:"
    ss -tlnp 2>/dev/null || true
    echo "Processos:"
    ps aux 2>/dev/null | grep -i "device\|dg_\|gateway" || true
    echo "Log:"
    tail -30 /app/logs/ivms_service.log 2>/dev/null || echo "(vazio)"
    ls -la /app/logs/ 2>/dev/null || true
    cat /app/logs/*.log 2>/dev/null | tail -50 || true
fi

# ==== NGINX ====
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf &
NGINX_PID=$!

echo "============================================="
echo "Gateway ativo! Daemon PID=$SERVICE_PID | Nginx PID=$NGINX_PID"
echo "============================================="

# Manter container vivo monitorando o daemon
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null &
TAIL_PID=$!

while true; do
    if ! kill -0 $SERVICE_PID 2>/dev/null; then
        echo "!!! Daemon morreu (PID=$SERVICE_PID) !!!"
        echo "--- Log ---"
        tail -30 /app/logs/ivms_service.log 2>/dev/null || true
        kill $NGINX_PID $TAIL_PID 2>/dev/null || true
        exit 1
    fi
    sleep 10
done
