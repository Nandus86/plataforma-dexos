#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# Limpar estado stale do install (build-time tem rede diferente do runtime)
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

# Aumentar log level para debug
sed -i 's/<Level>3<\/Level>/<Level>6<\/Level>/g' /app/Config.xml

# Ativar serviços
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# sysctl
sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.arp_announce=2 2>/dev/null || true

# ==== INICIAR MOTOR ====
echo "Iniciando DeviceGatewayService..."
export LD_PRELOAD=/app/fakenet.so
./DeviceGatewayService -service -instance=DeviceGatewayService &
ENGINE_PID=$!
echo "Motor PID: $ENGINE_PID"

# ==== AGUARDAR PORTA 8081 ====
echo "Aguardando porta 8081 (timeout: 120s)..."
PORTA_OK=0
for i in $(seq 1 60); do
    if ! kill -0 $ENGINE_PID 2>/dev/null; then
        wait $ENGINE_PID 2>/dev/null
        EXIT_CODE=$?
        SIGNAL=""
        if [ $EXIT_CODE -gt 128 ]; then
            SIGNAL=" (sinal $(($EXIT_CODE - 128)))"
        fi
        echo "!!! Motor MORREU exit=$EXIT_CODE$SIGNAL na iteração $i !!!"
        echo "--- Log do motor ---"
        tail -50 /app/logs/ivms_service.log 2>/dev/null || echo "(vazio)"
        echo "--- dmesg (ultimas 10) ---"
        dmesg 2>/dev/null | tail -10 || true
        echo "--- core dumps ---"
        ls -la /app/core* /tmp/core* 2>/dev/null || echo "(nenhum)"
        break
    fi

    if ss -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA! Motor OK! <<<"
        break
    fi
    echo "[$i/60] Aguardando 8081... (PID $ENGINE_PID vivo)"
    sleep 2
done

if [ "$PORTA_OK" -eq 0 ]; then
    echo "!!! AVISO: Porta 8081 nao abriu !!!"
    echo "Portas abertas:"
    ss -tlnp 2>/dev/null || true
fi

# ==== NGINX ====
unset LD_PRELOAD
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf &
NGINX_PID=$!

echo "============================================="
echo "Gateway ativo! Motor PID=$ENGINE_PID | Nginx PID=$NGINX_PID"
echo "============================================="

touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null &
TAIL_PID=$!

while true; do
    if ! kill -0 $ENGINE_PID 2>/dev/null; then
        wait $ENGINE_PID 2>/dev/null
        EXIT_CODE=$?
        SIGNAL=""
        if [ $EXIT_CODE -gt 128 ]; then
            SIGNAL=" (sinal $(($EXIT_CODE - 128)))"
        fi
        echo "!!! Motor morreu exit=$EXIT_CODE$SIGNAL !!!"
        echo "--- Ultimas linhas do log ---"
        tail -30 /app/logs/ivms_service.log 2>/dev/null || true
        kill $NGINX_PID $TAIL_PID 2>/dev/null || true
        exit 1
    fi
    sleep 10
done
