#!/bin/bash
set -e

cd /app

# ==== PREPARAÇÃO ====
mkdir -p /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys
chmod -R 777 /app/nginx/logs /app/logs /app/nginx/temp /var/run /app/db /var/lock/subsys

# sysctl
sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.default.rp_filter=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.arp_announce=2 2>/dev/null || true

# ==== CONFIGURAÇÃO ====
IP_INTERNO=$(hostname -I | awk '{print $1}')
echo "============================================="
echo "IP Interno: $IP_INTERNO"
echo "Todos IPs: $(hostname -I)"
echo "============================================="

# NÃO alterar IP - deixar 0.0.0.0 para escutar em todas as interfaces

# Ativar TODOS os serviços em Config.xml
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/Config.xml

# Desabilitar HTTPS (não temos certificados)
sed -i '/<HTTPS>/,/<\/HTTPS>/s/<Enable>1<\/Enable>/<Enable>0<\/Enable>/' /app/Config.xml

# Ativar ISAPI
sed -i 's/<Enable>0<\/Enable>/<Enable>1<\/Enable>/g' /app/ISAPIConfig.xml

# Log level debug
sed -i 's/<Level>3<\/Level>/<Level>6<\/Level>/g' /app/Config.xml

echo "Config.xml Enable status:"
grep -n "Enable" /app/Config.xml

# ==== NGINX PORT (para --network=host, porta 80 já está em uso) ====
NGINX_PORT=${NGINX_PORT:-80}
if [ "$NGINX_PORT" != "80" ]; then
    sed -i "s/listen       80;/listen       $NGINX_PORT;/" /app/nginx/conf/nginx.conf
    echo "Nginx configurado para porta: $NGINX_PORT"
fi

# ==== INICIAR MOTOR (daemon que faz fork) ====
echo "Iniciando DeviceGatewayService..."
# fakenet.so SEMPRE necessário: filtra IPv6 que confunde o gateway
# Sem ele: 19 IPs (IPv4+IPv6) → gateway trava em 10s
# Com ele: 5 IPs (só IPv4) → porta 8081 abre OK
export LD_PRELOAD=/app/fakenet.so
echo ">>> fakenet.so ATIVADO (filtro IPv6 essencial) <<<"

./DeviceGatewayService -service -instance=DeviceGatewayService &
LAUNCHER_PID=$!
echo "Launcher PID: $LAUNCHER_PID"

# Aguardar daemon fazer fork
echo "Aguardando daemon fazer fork..."
sleep 5

# Encontrar PID real do daemon filho
unset LD_PRELOAD
SERVICE_PID=""
for i in $(seq 1 10); do
    SERVICE_PID=$(pgrep -f "DeviceGatewaySe" 2>/dev/null | head -1)
    [ -n "$SERVICE_PID" ] && echo ">>> Daemon: DeviceGatewaySe PID=$SERVICE_PID <<<" && break

    SERVICE_PID=$(pgrep -f "dg_pss" 2>/dev/null | head -1)
    [ -n "$SERVICE_PID" ] && echo ">>> Subprocesso: dg_pss PID=$SERVICE_PID <<<" && break

    SERVICE_PID=$(pgrep -f "dg_das_media" 2>/dev/null | head -1)
    [ -n "$SERVICE_PID" ] && echo ">>> Subprocesso: dg_das_media PID=$SERVICE_PID <<<" && break

    echo "Procurando daemon... ($i/10)"
    sleep 2
done

if [ -z "$SERVICE_PID" ]; then
    echo "!!! ERRO: Nenhum processo gateway encontrado !!!"
    ps aux 2>/dev/null
    find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -30 {} \; 2>/dev/null
    exit 1
fi

# Funcao para checar se algum processo gateway esta vivo
gateway_alive() {
    pgrep -f "DeviceGatewaySe" >/dev/null 2>&1 && return 0
    pgrep -f "dg_pss" >/dev/null 2>&1 && return 0
    pgrep -f "dg_das_media" >/dev/null 2>&1 && return 0
    return 1
}

# ==== AGUARDAR PORTA 8081 ====
echo "Aguardando porta 8081 (timeout: 120s)..."
PORTA_OK=0
for i in $(seq 1 60); do
    if ! gateway_alive; then
        echo "!!! Todos processos gateway morreram na iteração $i !!!"
        find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -30 {} \; 2>/dev/null
        break
    fi

    if ss -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA! Gateway OK! <<<"
        break
    fi

    if [ $((i % 10)) -eq 0 ]; then
        echo "[$i/60] Portas:"
        ss -tlnp 2>/dev/null | grep -v "127.0.0.11" || true
    else
        echo "[$i/60] Aguardando 8081..."
    fi
    sleep 2
done

if [ "$PORTA_OK" -eq 0 ]; then
    echo "!!! Porta 8081 nao abriu !!!"
    echo "Portas:" && ss -tlnp 2>/dev/null || true
    echo "Processos:" && ps aux 2>/dev/null | grep -iE "device|dg_|gateway" || true
    echo "--- Logs ---"
    find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -30 {} \; 2>/dev/null
fi

# ==== NGINX ====
# O gateway já inicia seu próprio nginx internamente.
# Só iniciamos manualmente se o gateway NÃO tiver feito isso.
sleep 2
if ! pgrep -f "DeviceGateway-nginx" >/dev/null 2>&1; then
    echo "Iniciando Nginx manualmente..."
    /app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf &
    NGINX_PID=$!
    echo "Nginx PID=$NGINX_PID"
else
    NGINX_PID=$(pgrep -f "DeviceGateway-nginx" 2>/dev/null | head -1)
    echo "Nginx ja iniciado pelo gateway (PID=$NGINX_PID)"
fi

echo "============================================="
echo "Gateway ativo! Daemon PID=$SERVICE_PID | Nginx PID=$NGINX_PID"
echo "============================================="

touch /app/logs/ivms_service.log
(tail -f /app/logs/*.log /app/logs/**/*.log /app/nginx/logs/*.log 2>/dev/null || true) &

while true; do
    if ! gateway_alive; then
        echo "!!! Todos processos gateway morreram !!!"
        find /app/logs -name "*.log" -size +0c -exec echo "=== {} ===" \; -exec tail -20 {} \; 2>/dev/null
        kill $NGINX_PID 2>/dev/null || true
        exit 1
    fi
    sleep 10
done
