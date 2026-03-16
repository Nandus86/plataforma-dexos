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