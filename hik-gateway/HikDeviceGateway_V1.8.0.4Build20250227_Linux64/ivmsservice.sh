#!/bin/bash
#
# chkconfig: 2345 58 74
# description: DESCRIPTION
#

# service bash flag
IVMS_SERVICE=0

CORE_DUMP_DIR=IVMS_SERVICE_DUMP_DIR
CORE_DUMP_NUM=IVMS_SERVICE_CORE_NUM
DAEMON_COREFILE_LIMIT=unlimited
SVC_SYS_DIR=/etc/init.d
SVC_SYS_SVR=/usr/lib/systemd/system

SVC_PROG=IVMS_SERVICE_PROG
SVC_NAME=IVMS_SERVICE_NAME
WATCH_DOG_SVC=DeviceGatewayGuard
SYSTEMD_SVC=DeviceGatewayService
WATCH_DOG_PROC=DeviceGatewayGuard.service
SYSTEMD_PROC=DeviceGatewayService.service
SVC_DIR=IVMS_SERVICE_DIR
SVC_LOCK_FILE=/var/lock/subsys/$SVC_PROG
SVC_PID_FILE=/var/run/$SVC_NAME.pid

check_os_and_source_functions() {
    local os_type=""
    if [ -f /etc/os-release ]; then
        . /etc/os-release

        if [[ "$ID" == "centos" ]]; then
            os_type="centos"
        elif [[ "$ID" == "ubuntu" ]]; then
            os_type="ubuntu"
        elif [[ "$ID" == "rhel" ]]; then
            os_type="rhel"
        else
            os_type="centos"
        fi
    else
        os_type="centos"
    fi

    echo "$os_type"
}

os_type=$(check_os_and_source_functions)
echo "Operating System Type: $os_type"

if [ "$os_type" = "centos" ]; then
	# common function
	. /etc/init.d/functions
else
	CUR_DIR=$( cd "$( dirname "$0"  )" && pwd )
	. $CUR_DIR/functions
fi

# install service, $1 service name, $2 executable name
InstallSvc()
{
	if [ -z "$1" ]; then
		echo $"service name is needed by ivmsservice."
		return -1
	fi
	
	if [ -n "$4" ]; then
		echo $"set core num $4."
    else
		echo $"no core num limit."
	fi

	SVC_NAME=$1
	SVC_PROG=${2:-$SVC_NAME}
	SVC_DIR=$( cd "$( dirname "$0"  )" && pwd )
	SVC_DIR_MEDIA=$SVC_DIR/apps/das_media_x64/stream
	SVC_DIR_MEDIA_PLUGIN_ISUP5=$SVC_DIR/apps/das_media_x64/plugins/ehomeV5_plugin
	SVC_DIR_MEDIA_PLUGIN_ISUP2=$SVC_DIR/apps/das_media_x64/plugins/ehome_plugin

	SVC_SYS_FILE=$SVC_SYS_DIR/$SVC_NAME

	SVC_SYSD_FILE=$SVC_SYS_SVR/$SVC_NAME.service
	SVC_SCRIPT_FILE=$SVC_DIR/$SVC_NAME.service.sh
	CORE_DUMP_DIR=$SVC_DIR
	CORE_DUMP_NUM=$3

	if [ ! -f $SVC_DIR/$SVC_PROG ]; then
		echo $"$SVC_DIR/$SVC_PROG does not exist."
		return -1
	fi

	echo $"installing $SVC_NAME service, executable file $SVC_DIR/$SVC_PROG ..."

	# set suid_dumpable on
	if [ -e /proc/sys/kernel/suid_dumpable ]; then
		echo 1 > /proc/sys/kernel/suid_dumpable
	else
		echo 1 > /proc/sys/fs/suid_dumpable
	fi

	echo core-%e-%p-%t | sudo dd of=/proc/sys/kernel/core_pattern

	chmod u+x $SVC_DIR -R
	if [ "$os_type" = "centos" ]; then
		# create service bash
		sed -e "s%IVMS_SERVICE=0%IVMS_SERVICE=1%g" $0 | \
		sed -e "s%IVMS_SERVICE_PROG%$SVC_PROG%g" | \
		sed -e "s%IVMS_SERVICE_NAME%$SVC_NAME%g" | \
		sed -e "s%DESCRIPTION%$SVC_NAME%g" | \
		sed -e "s%IVMS_SERVICE_DUMP_DIR%$SVC_DIR%g" | \
		sed -e "s%IVMS_SERVICE_CORE_NUM%$CORE_DUMP_NUM%g" | \
		sed -e "s%IVMS_SERVICE_DIR%$SVC_DIR%g" > $SVC_SYS_FILE
		chmod u+x $SVC_SYS_FILE
		# chmod u+x $SVC_DIR/$SVC_PROG
		chkconfig --add $SVC_NAME
	else
		# create service systemd
		sed -e "s%IVMS_SERVICE=0%IVMS_SERVICE=1%g" $SVC_DIR/DeviceGatewayService.service | \
		sed -e "s%IVMS_SERVICE_NAME%$SVC_NAME%g" | \
		sed -e "s%IVMS_SERVICE_SCRIPT%$SVC_SCRIPT_FILE%g" > $SVC_SYSD_FILE

		# create service bash
		sed -e "s%IVMS_SERVICE=0%IVMS_SERVICE=1%g" $0 | \
		sed -e "s%IVMS_SERVICE_PROG%$SVC_PROG%g" | \
		sed -e "s%IVMS_SERVICE_NAME%$SVC_NAME%g" | \
		sed -e "s%DESCRIPTION%$SVC_NAME%g" | \
		sed -e "s%IVMS_SERVICE_CORE_NUM%$CORE_DUMP_NUM%g" | \
		sed -e "s%IVMS_SERVICE_DIR%$SVC_DIR%g" > $SVC_SCRIPT_FILE
		systemctl enable $SVC_NAME.service
		chmod u+x $SVC_SCRIPT_FILE
	fi

	echo "[Unit]" > $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "Description=DeviceGatewayGuard servcie" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "[Service]" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "ExecStart="$SVC_DIR/$WATCH_DOG_SVC >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "KillSignal=SIGQUIT" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "TimeoutStopSec=30" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "KillMode=process" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "[Install]" >> $SVC_SYS_SVR/$WATCH_DOG_PROC
	echo "WantedBy=multi-user.target" >> $SVC_SYS_SVR/$WATCH_DOG_PROC

	systemctl daemon-reload
	if [ -f /etc/selinux/config ]; then
		setenforce 0 
		sed -i '/SELINUX/s/enforcing/permissive/' /etc/selinux/config
	fi
	
	echo $SVC_DIR >> /etc/ld.so.conf
	echo $SVC_DIR_MEDIA  >> /etc/ld.so.conf
	echo $SVC_DIR_MEDIA_PLUGIN_ISUP5  >> /etc/ld.so.conf
	echo $SVC_DIR_MEDIA_PLUGIN_ISUP2  >> /etc/ld.so.conf
	ldconfig
	
	cp -f ./sfrzcfg /etc/sfrzcfg
	
	cp -f /etc/systemd/system.conf ./
	sed -e '/DefaultLimitMEMLOCK/d' ./system.conf | \
	sed -e '/DefaultLimitNOFILE/d' > /etc/systemd/system.conf
	echo "DefaultLimitMEMLOCK=infinity" >> /etc/systemd/system.conf
	echo "DefaultLimitNOFILE=1000000" >> /etc/systemd/system.conf
	rm -f ./system.conf
	systemctl daemon-reexec

    #set tcp param
    sysctl net.ipv4.neigh.default.gc_stale_time=120
    sysctl net.ipv4.conf.all.rp_filter=0
    sysctl net.ipv4.conf.default.rp_filter=0
    sysctl net.ipv4.conf.default.arp_announce=2
    sysctl net.ipv4.conf.all.arp_announce=2
    sysctl net.ipv4.tcp_max_tw_buckets=6000
    sysctl net.ipv4.tcp_syncookies=1
    sysctl net.ipv4.tcp_max_syn_backlog=262144
    sysctl net.core.netdev_max_backlog=262144
    sysctl net.core.somaxconn=32768
    sysctl net.core.wmem_default=8388608
    sysctl net.core.rmem_default=8388608
    sysctl net.core.rmem_max=33554432
    sysctl net.core.wmem_max=33554432
    sysctl net.ipv4.conf.lo.arp_announce=2
    sysctl net.ipv4.tcp_timestamps=1
    sysctl net.ipv4.tcp_synack_retries=1
    sysctl net.ipv4.tcp_syn_retries=1
    sysctl net.ipv4.tcp_tw_reuse=1
    sysctl net.ipv4.tcp_mem="94500000 915000000 927000000"
    sysctl net.ipv4.tcp_fin_timeout=1
    sysctl net.ipv4.tcp_keepalive_time=600
    sysctl net.ipv4.ip_local_port_range="1024 65000"
	if [ "$os_type" = "centos" ] || [ "$os_type" = "rhel" ]; then
		sysctl fs.file-max=65535000
	fi
    sysctl -p
    
	if [ "$os_type" = "ubuntu" ] || [ "$os_type" = "rhel" ]; then
		systemctl enable $SYSTEMD_PROC
	fi
    if [ "$os_type" = "centos" ]; then
		systemctl enable $WATCH_DOG_SVC
	fi

	echo $"install $SVC_NAME service successfully."
	systemctl start $SVC_NAME
	return 0
}

# uninstall service, $1 service name
UninstallSvc()
{
	if [ -z "$1" ]; then
		echo $"service name is needed by ivmsservice."
		return -1
	fi

	SVC_NAME=$1
	SVC_SYS_FILE=$SVC_SYS_DIR/$SVC_NAME

	echo $"uninstalling $SVC_NAME service ..."

	if [ "$os_type" = "centos" ]; then
		# rm service bash
		if [ -f $SVC_SYS_FILE ]; then
			chkconfig --del $SVC_NAME
			rm -f $SVC_SYS_FILE
		else
			warning $"$SVC_NAME service does not exist."
		fi
	else
		systemctl stop $SVC_NAME
        service_file="$SVC_SYS_SVR/$SVC_NAME.service"
        echo "Removing service file: $service_file"
        rm -f "$service_file"
		# rm -f $SVC_SYS_SVR/$SVC_NAME.service
	fi

	SVC_DIR=$( cd "$( dirname "$0"  )" && pwd )
	var1=`echo $SVC_DIR | sed 's#\/#\\\/#g'`
	sed -i '/'"$var1"'/d' /etc/ld.so.conf
	ldconfig
	
	rm -f /etc/sfrzcfg	
	rm -f $SVC_SYS_SVR/$WATCH_DOG_PROC
	systemctl daemon-reload

	echo $"uninstall $SVC_NAME service successfully."
	return 0
}

#clean CORE
CleanCore()
{
	echo $"start cleaning $SVC_NAME cores..."
	cd $CORE_DUMP_DIR
	N=$1
	COUNT=1
	files=$(ls -t core-*)
	for file in $files
	do
	    if [ $COUNT -gt $N ]; then
		    rm -rf $file
		fi
		let COUNT=${COUNT}+1
	done	
}

# start service
StartSvc()
{
	echo $"starting $SVC_NAME service ..."

	# set core unlimited, replaced by DAEMON_COREFILE_LIMIT
	#ulimit -c unlimited
	if [ -n "$1" ]; then
        if [ $1 -gt -1 ]; then
			CleanCore $1
		fi
	fi 	

	# create lockfile, run program
	touch $SVC_LOCK_FILE
	cd $SVC_DIR
	daemon --pidfile=$SVC_PID_FILE $SVC_DIR/$SVC_PROG -service -instance=$SVC_NAME
	if [ $? -eq 0 ]; then
		# created by the program
		#pidof $SVC_DIR/$SVC_PROG > $SVC_PID_FILE
		echo $"start $SVC_NAME service successfully."
		return 0
	else
		echo $"start $SVC_NAME service failure."
		return -1
	fi
}

# get service status
IsSvcRunning()
{
	local pid
	__pids_var_run $SVC_NAME $SVC_PID_FILE
	[ -n "$pid" ] && return 0 || return 1
}

# stop service
StopSvc()
{
	echo $"stopping $SVC_NAME service ..."
		# remove lockfile
	rm -f $SVC_LOCK_FILE

	# wait for exit
	local i RC
	for (( i=0; i < 10; i++ )); do
		if IsSvcRunning; then
			sleep 1
		else
			break
		fi
	done

	if [ $i -eq 10 ] && IsSvcRunning; then
		killproc -p $SVC_PID_FILE $SVC_NAME
		RC=$?
	else
		rm -f $SVC_PID_FILE
		RC=0
	fi

	if [ $RC -eq 0 ]; then
		echo $"stop $SVC_NAME service successfully."
		return 0
	else
		echo $"stop $SVC_NAME service failure."
		return -1
	fi
}

# restart service
RestartSvc()
{
	echo $"restarting $SVC_NAME service ..."

	StopSvc
	if [ $? -eq 0 ]; then
		StartSvc $1
		if [ $? -eq 0 ]; then
			echo $"restart $SVC_NAME service successfully."
			return 0
		fi
	fi

	echo $"restart $SVC_NAME service failure."
	return -1
}

RETVAL=0

if [ $IVMS_SERVICE -eq 0 ]; then
	# setup
	case $1 in
		install | i)
			InstallSvc $2 $3 $4
			RETVAL=$?
			;;
		uninstall | u)
			UninstallSvc $2
			RETVAL=$?
			;;
		*)
			echo $"Usage: $0 {i, install NAME [EXEC] | u, uninstall NAME}"
			;;
	esac
else
	# service
	case $1 in
		start | r)
			StartSvc $CORE_DUMP_NUM
			RETVAL=$?
			;;
		stop | p)
			StopSvc
			RETVAL=$?
			;;
		restart | e)
			RestartSvc $CORE_DUMP_NUM
			RETVAL=$?
			;;
		status | s)
			status -p $SVC_PID_FILE $SVC_NAME
			RETVAL=$?
			;;
		status2)
			IsSvcRunning && echo $"$SVC_NAME service is running." || echo $"$SVC_NAME service has been stopped."
			;;
		*)
			echo $$"Usage: $0 {start|stop|status|restart}"
			;;
	esac
fi

exit $RETVAL
