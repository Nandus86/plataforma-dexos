#!/bin/sh


bin_path=$1
lang_path=$2
lang_dir=$3

if [ -d  "${bin_path}/../conf/installedresourcelist" ]
then
	echo "conf/installedresourcelist exist"
else
	echo "create conf/installedresourcelist"
	mkdir "${bin_path}/../conf/installedresourcelist"
fi

if [ "${lang_dir}"_ != ""_ ]
then
	if [ -d "${bin_path}/../conf/installedresourcelist/${lang_dir}" ]
	then
		echo "../conf/installedresourcelist/${lang_dir} exist delete"
		rm -rf "${bin_path}/../conf/installedresourcelist/${lang_dir}"
	fi
	
	mkdir "${bin_path}/../conf/installedresourcelist/${lang_dir}"
	
	if [ -d "${lang_path}/META-INF" ]
	then
		echo "create conf/installedresourcelist/${lang_dir}/META-INF"
		mkdir "${bin_path}/../conf/installedresourcelist/${lang_dir}/META-INF"
		cp -rf "${lang_path}/META-INF" "${bin_path}/../conf/installedresourcelist/${lang_dir}"
	else
		echo "${lang_path}/META-INF not exist"
	fi
fi

