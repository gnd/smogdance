#!/bin/bash
#
# report a state change on a sensor
#
##########################################
source settings_bash

if [[ -z $1 ]]; then
	echo "Missing sensor ID"
	exit
fi
if [[ -z $2 ]]; then
        echo "Missing sensor STATE"
        exit
fi

SENSOR_ID=$1
SENSOR_STATE=$2
SUBJECT="Sensor $SENSOR_ID $SENSOR_STATE"
MAIL="subject:$SUBJECT\nfrom:$REPORT_FROM\nLOAD: $LOAD"

echo -e $MAIL | /usr/sbin/sendmail "$REPORT_RECPS"
