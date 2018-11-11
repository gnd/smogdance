#!/bin/bash
#########
source settings_bash
LOG="--nolog"

function usage() {
	echo "Usage:"
    echo "$0 <country_code/city_name/spider_name> [--tor] [--debug]"
	echo "eg.: $0 cz/praha/0"
	exit
}

# Check if spidername provided
if [[ -z "$1" ]]; then
	usage
fi

# Check for other command-line options
for i in "$@"
do
	case $i in
		--tor)
	    PREFIX="torify"
	    shift
	    ;;
		--debug)
		LOG=""
		shift
		;;
	    *)
	    ;;
	esac
done

# Run the spider
$PREFIX scrapy runspider $SPIDER_DIR"/"$1.py $LOG -o - -t csv
