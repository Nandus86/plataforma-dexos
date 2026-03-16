#!/bin/bash

kill -9 `ps -ef|grep '[D]eviceGateway-nginx' | awk '{print $2}'`
kill -9 `ps -ef|grep '[n]ginx' | awk '{print $2}'`
service DeviceGatewayService restart
