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

# Aguardar o launcher sair (faz fork e sai com 0)
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
    # Tentar nome alternativo
    SERVICE_PID=$(pgrep -f "DeviceGateway" 2>/dev/null | head -1)
    if [ -n "$SERVICE_PID" ]; then
        echo ">>> Daemon encontrado! DeviceGateway PID=$SERVICE_PID <<<"
        break
    fi
    echo "Procurando daemon filho... ($i/10)"
    sleep 2
done

if [ -z "$SERVICE_PID" ]; then
    echo "!!! Nenhum daemon DeviceGateway ativo. Usando subprocessos..."
    # Tentar monitorar qualquer subprocesso do gateway (dg_pss, dg_das_media)
    SERVICE_PID=$(pgrep -f "dg_" 2>/dev/null | head -1)
fi

if [ -z "$SERVICE_PID" ]; then
    echo "!!! ERRO: Nenhum processo gateway encontrado !!!"
    echo "Processos:" && ps aux 2>/dev/null
    echo "Logs:"
    find /app/logs -name "*.log" -exec echo "=== {} ===" \; -exec tail -20 {} \; 2>/dev/null || true
    exit 1
fi

echo "Monitorando PID=$SERVICE_PID"

# ==== AGUARDAR PORTA 8081 ====
echo "Aguardando porta 8081 (timeout: 120s)..."
PORTA_OK=0
for i in $(seq 1 60); do
    if ! kill -0 $SERVICE_PID 2>/dev/null; then
        echo "!!! Daemon PID=$SERVICE_PID morreu na iteração $i !!!"
        echo "--- Logs ---"
        find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -20 {} \; 2>/dev/null || true
        break
    fi

    if ss -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA! Gateway OK! <<<"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "[$i/60] Portas ativas:"
        ss -tlnp 2>/dev/null | grep -v "127.0.0.11" || true
    else
        echo "[$i/60] Aguardando 8081... (PID $SERVICE_PID vivo)"
    fi
    sleep 2
done

if [ "$PORTA_OK" -eq 0 ]; then
    echo "!!! Porta 8081 nao abriu !!!"
    echo "Portas:" && ss -tlnp 2>/dev/null || true
    echo "Processos:" && ps aux 2>/dev/null | grep -i "device\|dg_\|gateway" || true
    echo "--- Todos os logs ---"
    find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -30 {} \; 2>/dev/null || true
fi

# ==== NGINX ====
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf &
NGINX_PID=$!

echo "============================================="
echo "Gateway ativo! Daemon PID=$SERVICE_PID | Nginx PID=$NGINX_PID"
echo "============================================="

# Manter container vivo
touch /app/logs/ivms_service.log
(tail -f /app/logs/*.log /app/logs/**/*.log /app/nginx/logs/*.log 2>/dev/null || true) &

while true; do
    # Verificar se ALGUM processo gateway esta vivo
    if ! pgrep -f "DeviceGateway\|dg_pss\|dg_das" >/dev/null 2>&1; then
        echo "!!! Todos os processos gateway morreram !!!"
        echo "--- Logs finais ---"
        find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -20 {} \; 2>/dev/null || true
        kill $NGINX_PID 2>/dev/null || true
        exit 1
    fi
    sleep 10
done
