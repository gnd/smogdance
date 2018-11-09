#!/bin/bash
#########
source settings_bash

function usage() {
	echo "Usage:"
    echo "$0 <country_code/city_name/spider_name> [tor]"
	echo "eg.: $0 cz/praha/0"
	exit
}

if [[ -z "$1" ]]; then
	usage
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
