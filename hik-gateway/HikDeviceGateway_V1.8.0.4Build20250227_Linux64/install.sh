#!/bin/bash

#安装路径
INSTALL_DIR=`pwd`
#遗留配置文件
Config_Backup_xml="Config_Backup.xml"
PrivateConfig_Backup_xml="PrivateConfig_Backup.xml"
Config_Template_xml="Config_Template.xml"
#配置文件
Config_xml="Config.xml"
PrivateConfig_xml="PrivateConfig.xml"
ISAPIConfig_xml="ISAPIConfig.xml"
PSS_Config_xml="apps/pss_x64/Config.xml"
PSS_StorageConfig_xml="apps/pss_x64/StorageConfig.xml"
nginx_key_pass="nginx/conf/key.pass"
nginx_certreq_pem="nginx/conf/certreq.pem"
nginx_cert_pem="nginx/conf/cert.pem"
nginx_cert_key="nginx/conf/cert.key"
#数据库文件
Config_DB="Config.db3"
Device_DB="Device.db3"
PSS_FILESTORAGE_DB="apps/pss_x64/FileStorage.db3"
#配置文件处理脚本
ConfigUpgrade_SH="ConfigUpgrade.sh"
#存放会生效的配置文件
Config_Temp_xml="";
Private_Temp_xml="";
#存放输入参数
INPUT_HTTP_PORT=0
INPUT_LEGACY_DIR=""
#支持的可选参数
PRARA_HEMP="--help"
PARAM_PORT="--port"
PARAM_PATH="--path"
#输入参数最大数目
INPUT_PARAM_MAX_NUM=3
#存放临时变量/传递入参/返回值
TEMP_VALUE=0
TEMP_PORT=0
#实际生效的端口
HTTP_PORT=0
PRIVATE_HTTP_PORT=0

checkInputPara(){
# 遍历处理输入参数
  for arg in "$@"
  do
    if [[  $arg =~ $PRARA_HEMP ]]; then
	    # help提示语
        if [ -f "${INSTALL_DIR}/${Config_Template_xml}" ]; then
			echo "Usage:"
			echo "./install.sh [--port=port number] [--path=the path of legacy configuration file]"
			echo "Options:"
			echo "--port=port number      HTTP port. if you enter nothing, the default port will be used."
			echo "--path=the path of legacy configuration file        it is the path of legacy configuration file. If there are any legacy configuration files, you can enter the path of it."
	        exit 0
	    else
			echo "Usage:"
			echo "./install.sh [--port=port number]"
			echo "Options:"
			echo "--port=port number      HTTP port. if you enter nothing, the default port will be used."
	        exit 0
	    fi
	elif [[  $arg =~ $PARAM_PORT ]]; then
	    # Http端口
        INPUT_HTTP_PORT=$arg
        INPUT_HTTP_PORT=${INPUT_HTTP_PORT#*=}
        if [ $INPUT_HTTP_PORT -le 0 ] || [ $INPUT_HTTP_PORT -gt 65535 ]; then
	        echo "Port No. is out of range…"
		    exit 1
	    fi
    elif [[ $arg =~ $PARAM_PATH ]]; then
	    # 遗留配置路径
        INPUT_LEGACY_DIR=$arg
        INPUT_LEGACY_DIR="${INPUT_LEGACY_DIR#*=}"
	# 后续新增输入参数，可在此处添加
    else
	   	echo "Installation failed."
		exit 1 
	fi
  done
}

addPermission()
{
    SVC_DIR=$( cd "$( dirname "$0"  )" && pwd )
    chmod u+x $SVC_DIR -R
	
    #当前目录逐级增加权限至根目录
    PARENT_DIR=$( dirname "${INSTALL_DIR}" )
    while [ "/" != "${PARENT_DIR}" -a "" != "${PARENT_DIR}" ]
    do
        chmod u+x "${PARENT_DIR}"
	    PARENT_DIR=$(dirname "${PARENT_DIR}")
    done
}

checkInstallPath(){ 
  # 安装路径仅能包含字母、数字、下划线、连字符、点			
  if [[ ! $INSTALL_DIR =~ ^[A-Za-z0-9._/-]+$ ]]; then  
	echo "Installation failed. The installation path can only contain letters, numbers, underscores, hyphens, and dots." 
	exit 1
  fi
}

readPortValueFromXml(){
# 读取文件中HTTP端口和HttpService端口
    HTTP_PORT=`sed -n '/<HTTP>/,+1p' "$1" | sed -n '/<Port>/p' | sed -E 's/^[^0-9]*([0-9]{1,5}).*/\1/'`
    PRIVATE_HTTP_PORT=`sed -n '/<HTTPService>/,+1p' "$2" | sed -n '/<Port>/p' | sed -E 's/^[^0-9]*([0-9]{1,5}).*/\1/'` 	
}

writePortValueToXml(){
# 修改文件中HTTP端口和HttpService端口
    sed -i '/<HTTP>/,+1s/[0-9]\{1,5\}/'"$HTTP_PORT"'/' "$1"
    sed -i '/<HTTPService>/,+1s/[0-9]\{1,5\}/'"$PRIVATE_HTTP_PORT"'/' "$2"
}

queryPortStatus()
{
  TEMP_VALUE=`netstat -lntu | grep ":$1 "`
  TEMP_VALUE=$? # 0-找到,表示端口已被占用,1-没有找到,表示端口空闲
}

getFreePort()
{
   TEMP_PORT=$1
   queryPortStatus "${TEMP_PORT}"
   while [ $TEMP_VALUE -eq 0 ]; do
        #如果port被占用,port+1检查是否被占用,直到找到空闲端口
		TEMP_PORT=$((TEMP_PORT + 1))
		if [ $TEMP_PORT -gt 65535 ]; then
		   echo "Port No. conflicted. Port No. is out of range…"
		   exit 1
		fi
		queryPortStatus "${TEMP_PORT}"
   done   
}

procPort(){
   if [ -f "${Config_Backup_xml}" -a -f "${PrivateConfig_Backup_xml}" ]; then
   #存在遗留配置
       Config_Temp_xml=$Config_Backup_xml;
	   PrivateConfig_Temp_xml=$PrivateConfig_Backup_xml;	
   elif [ -f "${Config_xml}" -a -f "${PrivateConfig_xml}" ]; then
   #不存在遗留配置，存在初始配置
       Config_Temp_xml=$Config_xml;
	   PrivateConfig_Temp_xml=$PrivateConfig_xml;
   else
   #必要配置缺少，无法安装
	   echo "Installation failed. Configuration file does not exist."
	   exit 1
   fi
   
   # 从配置文件中读取端口(HTTP/HTTPService)
   readPortValueFromXml "$Config_Temp_xml" "$PrivateConfig_Temp_xml"
   
   # 检查HTTP端口
   if [ $INPUT_HTTP_PORT -ne 0 ]; then
       # HTTP端口，以用户输入的值为准
	   if [ $INPUT_HTTP_PORT -le 0 ] || [ $INPUT_HTTP_PORT -gt 65535 ]; then
	       echo "Port No. is out of range…"
		   exit 1
	   fi
	   queryPortStatus "${INPUT_HTTP_PORT}"
	   if [ $TEMP_VALUE -eq 0 ]; then
	       echo "Port No. conflicted."
		   exit 1
	   fi
       HTTP_PORT=$INPUT_HTTP_PORT	
   else      
       #检查端口,若端口冲突则找到空闲端口
       getFreePort "${HTTP_PORT}"
       HTTP_PORT=$TEMP_PORT
   fi   
   echo "Checking ports completed. Port ${HTTP_PORT} will be used."
   
   # 检查HttpService端口
   getFreePort "${PRIVATE_HTTP_PORT}"
   PRIVATE_HTTP_PORT=$TEMP_PORT

   #将实际生效的端口，更新配置文件 
   writePortValueToXml "$Config_Temp_xml" "$PrivateConfig_Temp_xml"   
}

#第一个参数是文件名，第二个参数表示是否是必要文件
cpLeagcyFile(){
  TEMP_VALUE=$1
  if [ -f "${INPUT_LEGACY_DIR}/${TEMP_VALUE}" ]; then
     cp "${INPUT_LEGACY_DIR}/${TEMP_VALUE}"  "${INSTALL_DIR}/${TEMP_VALUE}"
  else
     if [ $2 -eq 1 ]; then
	    echo "Installation failed. This ${INPUT_LEGACY_DIR}/${TEMP_VALUE} required file is missing."
		exit 1
	 fi
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
   killProcess "drv_isup_dev"
   killProcess "drv_isapi_acs"
}

procLeagcyFile(){
  if [ -f "${INSTALL_DIR}/${Config_Template_xml}" ]; then # 只在第一次安装时调用（执行ConfigUpgrade_SH后，安装路径的Template文件会被删除）
   
  if [ -d "${INPUT_LEGACY_DIR}" ]; then
     #遗留路径是否存在配置，若存在且遗留路径不是当前路径，将遗留配置拷贝到当前路径	 
	 if [ -f "${INPUT_LEGACY_DIR}/${Config_xml}" ];then
       if [[ $(realpath "${INPUT_LEGACY_DIR}") != $(realpath "${INSTALL_DIR}") ]]; then	 
		 #拷贝配置文件
		 cpLeagcyFile "${Config_xml}"  1
		 cpLeagcyFile "${PrivateConfig_xml}" 1
		 cpLeagcyFile "${ISAPIConfig_xml}" 1
	   
		 cpLeagcyFile "${PSS_Config_xml}" 1
		 cpLeagcyFile "${PSS_StorageConfig_xml}" 1
	   
		 cpLeagcyFile "${nginx_key_pass}" 0
		 cpLeagcyFile "${nginx_certreq_pem}" 0
		 cpLeagcyFile "${nginx_cert_pem}" 0
		 cpLeagcyFile "${nginx_cert_key}" 0
		 	   
	     #拷贝数据库文件
		 cpLeagcyFile "${Config_DB}" 1
		 cpLeagcyFile "${Device_DB}" 1
	   
		 cpLeagcyFile "${PSS_FILESTORAGE_DB}" 1
		fi
	 fi
  fi  
  
  #替换保留的配置文件
  ./$ConfigUpgrade_SH  
  cd "${INSTALL_DIR}"/apps/pss_x64
    ./$ConfigUpgrade_SH
  cd "${INSTALL_DIR}"
  
  fi
}

deleteOldSoFile()
{
	find "${INSTALL_DIR}" -type f -name "libssl.so.1.0.0" -exec rm -f {} \;
	find "${INSTALL_DIR}" -type f -name "libcrypto.so.1.0.0" -exec rm -f {} \;
	find "${INSTALL_DIR}" -type f -name "pss.plugin" -exec rm -f {} \;
	find "${INSTALL_DIR}" -type f -name "pss" -exec rm -f {} \;
	find "${INSTALL_DIR}" -type f -name "das_media.plugin" -exec rm -f {} \;
	find "${INSTALL_DIR}" -type f -name "das_media" -exec rm -f {} \;
}

# 0-检查安装路径
checkInstallPath

# 1-增加路径权限
addPermission

# 2-检查服务是否已安装
IsSvcInstalled() {
    systemctl status "$1" >/dev/null 2>&1
    return $?
}

service_name="DeviceGatewayService"

if IsSvcInstalled "$service_name"; then
    echo "$service_name is already installed. Please uninstall before installing it again."
    exit 1
fi

# 3-检查输入参数
checkInputPara "$@"

# 4-处理残留进程和遗留配置
procRemainProcess
procLeagcyFile
deleteOldSoFile

# 5-处理端口
procPort

# 6-安装网关
./DeviceGatewayService -install

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
# 7-set firewall rules
echo "Port rules are added to firewalld by default."
if [[ "$os_type" == "centos" || "$os_type" == "rhel" ]]; then
  firewall-cmd --zone=public --add-port={$HTTP_PORT,443,554,7091,7661-7667,15000-17000}/tcp --add-port={7661,7662,15000-17000}/udp --permanent &> /dev/null
  firewall-cmd --reload
fi
