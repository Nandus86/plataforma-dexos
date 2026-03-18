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

# ==== AGUARDAR PORTA 8081 ====
echo "Aguardando porta 8081 (timeout: 120s)..."
PORTA_OK=0
for i in $(seq 1 60); do
    # Verificar se o processo ainda está vivo
    if ! kill -0 $ENGINE_PID 2>/dev/null; then
        echo "!!! Motor PID=$ENGINE_PID MORREU na iteração $i !!!"
        echo "Últimas linhas do log:"
        tail -20 /app/logs/ivms_service.log 2>/dev/null || true
        break
    fi

    # Tentar detectar a porta 8081 de múltiplas formas
    if ss -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA (ss)! Motor OK! <<<"
        break
    fi

    if grep -q '00000000:1F91 ' /proc/net/tcp 2>/dev/null; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA (/proc/net/tcp)! Motor OK! <<<"
        break
    fi

    if netstat -tlnp 2>/dev/null | grep -q ':8081'; then
        PORTA_OK=1
        echo ">>> PORTA 8081 ABERTA (netstat)! Motor OK! <<<"
        break
    fi

    echo "[$i/60] Aguardando 8081... (PID $ENGINE_PID vivo)"
    sleep 2
done

if [ "$PORTA_OK" -eq 0 ]; then
    echo "!!! AVISO: Porta 8081 nao detectada apos 120s. Iniciando Nginx mesmo assim para diagnóstico... !!!"
    echo "Portas abertas pelo motor:"
    ss -tlnp 2>/dev/null | grep "$ENGINE_PID" || true
    cat /proc/net/tcp 2>/dev/null | head -20 || true
fi

# ==== INICIAR NGINX (sem LD_PRELOAD) ====
unset LD_PRELOAD
echo "Iniciando Nginx..."
/app/nginx/DeviceGateway-nginx -p /app/nginx/ -c /app/nginx/conf/nginx.conf &
NGINX_PID=$!

echo "============================================="
echo "Gateway ativo! Motor PID=$ENGINE_PID | Nginx PID=$NGINX_PID"
echo "============================================="

# Manter container vivo e monitorar processos
touch /app/logs/ivms_service.log
tail -f /app/logs/*.log /app/nginx/logs/*.log 2>/dev/null &
TAIL_PID=$!

# Vigiar se o motor morreu
while true; do
    if ! kill -0 $ENGINE_PID 2>/dev/null; then
        echo "!!! Motor morreu (PID=$ENGINE_PID). Encerrando container... !!!"
        kill $NGINX_PID 2>/dev/null || true
        kill $TAIL_PID 2>/dev/null || true
        exit 1
    fi
    sleep 10
done
