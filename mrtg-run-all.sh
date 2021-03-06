#!/bin/bash
#
# runs all mrtg data collection
###############################
source settings_bash

# Process all sensor mrtg's
for CITY in `cat $RUNLIST`; do
	CITY_DIR=$SPIDER_DIR/$CITY
	for SENSOR_CONFIG in `ls $CITY_DIR|grep cfg`; do
		CONF=$CITY_DIR/$SENSOR_CONFIG
		echo $CONF
		env LANG=C /usr/bin/mrtg $CONF
	done
done
