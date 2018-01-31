#!/bin/bash
#########
source settings_bash

if [[ -z "$1" ]]; then
	echo "no spider to run"
	exit
fi

if [[ "$2" == "tor" ]]; then
	echo "Using tor"
	TOR=1
fi

### in order to make mrtg happy we need to output 4 values
if [[ $TOR == 1 ]]; then
	torify scrapy runspider $SPIDER_DIR"/"$1.py --nolog -o - -t csv
else
	scrapy runspider $SPIDER_DIR"/"$1.py --nolog -o - -t csv
fi
