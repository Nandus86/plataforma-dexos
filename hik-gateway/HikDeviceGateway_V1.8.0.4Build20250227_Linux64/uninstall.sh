#!/bin/bash
	 
uninstallTips()
{
    # 1-检查服务是否已安装
    if [ -f "/etc/rc.d/init.d/DeviceGatewayService" ]; then
	   IS_RUNNING=`/etc/rc.d/init.d/DeviceGatewayService status | grep "active (running)"`
       IS_RUNNING=$?  # 0-找到,网关正在运行,1-没有找到,网关未在运行
	   if [ $IS_RUNNING -eq 0 ]; then
	       	NGINX_RUNNING=`/etc/rc.d/init.d/DeviceGatewayService status | grep "nginx: master process"`
            NGINX_RUNNING=$?  # 0-找到,nginx已启动,1-没有找到,nginx还未启动
			if [ $NGINX_RUNNING -eq 1 ]; then
			   echo "DeviceGatewayService is starting. Uninstall DeviceGatewayService failed."
			   exit 1
			fi
	   fi
       echo "The files in the directory will all be kept after uninstallation. "
	elif systemctl is-enabled DeviceGatewayService.service &> /dev/null; then
        # 服务已安装，检查是否正在运行
        IS_RUNNING=$(systemctl is-active DeviceGatewayService.service)
        if [ "$IS_RUNNING" = "active" ]; then
            # 网关正在运行，进一步检查nginx是否启动
            NGINX_RUNNING=$(pgrep -f "nginx: master process" > /dev/null 2>&1; echo $?)
            if [ "$NGINX_RUNNING" -ne 0 ]; then
                # nginx未启动
                echo "DeviceGatewayService is starting. Uninstall DeviceGatewayService failed."
                exit 1
            fi
        fi
        echo "The files in the directory will all be kept after uninstallation. "
   else
	   echo "DeviceGatewayService is not installed."
      exit 1
    fi
}

killProcess()
{
    PID=`ps ax | grep "$1" | grep -v grep | awk '{print $1}'`
	if [[ -n "${PID}" ]]; then
	   TEMP_VALUE=`kill "${PID}"`
	fi
}

procRemainProcess()
{
   killProcess "DeviceGatewayService"
   killProcess "DeviceGatewayGuard"
   killProcess "DeviceGateway-nginx"
   #↓兼容清理1.7版本以前的进程(老进程名不带dg前缀)
   killProcess "das_media"
   killProcess "pss"
   #↑兼容清理1.7版本以前的进程(老进程名不带dg前缀)
   killProcess "dg_das_media"
   killProcess "dg_pss"
   killProcess "drv_ehome2_video"
   killProcess "drv_ehome5_acs"
   killProcess "drv_ehome5_video"
   killProcess "drv_isapi_acs"
   killProcess "RegService"
}

# 0-卸载提示
uninstallTips

# 1-停止网关服务，卸载服务
systemctl stop DeviceGatewayService
./DeviceGatewayService -uninstall

# 2-清理残留进程
procRemainProcess

