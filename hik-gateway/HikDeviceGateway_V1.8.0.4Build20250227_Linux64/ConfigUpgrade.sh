#!/bin/bash

if [ -f Config_Backup.xml ]; then
   rm -f Config_Backup.xml
fi
if [ -f Config.xml ]; then
   mv Config.xml Config_Backup.xml
fi
if [ -f Config.xml ]; then
   rm -f Config.xml
fi
if [ -f Config_Template.xml ]; then
   mv Config_Template.xml Config.xml
fi

if [ -f PrivateConfig_Backup.xml ]; then
   rm -f PrivateConfig_Backup.xml
fi
if [ -f PrivateConfig.xml ]; then
   mv PrivateConfig.xml PrivateConfig_Backup.xml
fi
if [ -f PrivateConfig.xml ]; then
   rm -f PrivateConfig.xml
fi
if [ -f PrivateConfig_Template.xml ]; then
   mv PrivateConfig_Template.xml PrivateConfig.xml
fi

if [ -f ISAPIConfig_Backup.xml ]; then
   rm -f ISAPIConfig_Backup.xml
fi
if [ -f ISAPIConfig.xml ]; then
   mv ISAPIConfig.xml ISAPIConfig_Backup.xml
fi
if [ -f ISAPIConfig.xml ]; then
   rm -f ISAPIConfig.xml
fi
if [ -f ISAPIConfig_Template.xml ]; then
   mv ISAPIConfig_Template.xml ISAPIConfig.xml
fi