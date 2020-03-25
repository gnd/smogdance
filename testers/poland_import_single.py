#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
import json
import time
import shlex
sys.setdefaultencoding('utf-8')
import subprocess
import unicodedata
import ConfigParser

### load smog.dance config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')
TEMP_DIR = config.get('globals', 'TEMP_DIR')

all_substances = ["co","no2","o3","pm10","pm25","so2"]

def parse_aqi():
    data = json.load(file("%s/%s" % (TEMP_DIR, 'gios.json'), 'r'))

    for sensor in data:
        if sensor['valid']:

            # Get sensor data
            sensor_data = []
            sensor_id = sensor['stationId']
            city = sensor['stationName'].split(',')[0].strip().lower()
            name = sensor['stationName'].split(',')[1].strip().lower()
            if name == "":
                name = city
            link_src = 'file://127.0.0.1TEMP_DIR/gios.json'
            link_web = 'http://powietrze.gios.gov.pl/pjp/current/station_details/chart/' + str(sensor_id)
            link_stat = 'https://STATS_URL/pl/' + city.replace(" ","")
            link_xpaths = []
            country = 'pl';
            gps = '';
            sensor_type = 'hourly';
            substances = []
            for substance in sensor['values']:
                if substance.lower().replace('.','') in all_substances:
                    substance_name = substance.lower().replace('.','')
                    substances.append(substance_name)
                    link_xpaths.append("%s--%d--pl_json" % (substance_name,sensor_id))

            # Insert the sensor into the db
            line = "'%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'" % (name, link_src, link_web, link_stat, ";".join(link_xpaths), country, city, gps, sensor_type, " ".join(substances))
            print line
            #import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
            #import_args = shlex.split(import_cmd)
            ### run the import
            #try:
                #print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
                #process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                #out = process.communicate()[1]
                #if (process.returncode != 0):
                #    print "Import failed:\n%s" % (out)
            #except:
            #    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)


parse_aqi()
