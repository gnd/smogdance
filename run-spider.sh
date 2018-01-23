#!/bin/bash
#########
source settings

if [[ -z "$1" ]]; then
	echo "no spider to run"
	exit
fi

### in order to make mrtg happy we need to output 4 values
scrapy runspider $DATA_DIR"/"$1.py --nolog -o - -t csv
