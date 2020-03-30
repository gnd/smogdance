#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
reload(sys)
import json
import shlex
sys.setdefaultencoding('utf-8')
import scrapy
import base64
import hashlib
import MySQLdb
import subprocess
import unicodedata
import ConfigParser
from datetime import datetime
from Crypto.Cipher import AES

# # #
# This is reverse-engineered from http://powietrze.gios.gov.pl/pjp/current/station_details/chart/612
# 1. First we need the CSRF token, eg. window.csrf = (.*); from:
#    http://powietrze.gios.gov.pl/pjp/current/station_details/chart/612
#
# 2. In chart.js we have getData(base, d, station_id, optional)
#    - where base is /pjp, d is days (1, 3, 10, 30), station_id is selfexplaining
#    - getData does a POST request to: http://powietrze.gios.gov.pl/pjp/current/get_data_chart
#
#    This should be basically be enough to get the data with the right CSRF token:
#    curl -H "X-Requested-With: XMLHttpRequest" -H "_csrf_token: 15077437-4fcc-48f8-8cc1-4d77e1356e52" --data "days=1&stationId=612" "http://powietrze.gios.gov.pl/current/get_data_chart"
#    However the data is encrypted
#
# 3. Decrypting is done with encryptData(data) in chart.js, which calls functions from http://powietrze.gios.gov.pl/pjp/assets-0.0.31/js/AesUtil.js and CryptoJS
#    - first we need to generate encryption key with PBKDF2, using salt (hex decoded) and pass whch is the CSRF token:
#      the implementation uses sha1, 1000 iteration, 16bit keysize
#    - next we use AES to decrypt the base64decoded ciphertext, with the salt as iv
# # #

### load smog.dance config
settings_file = os.path.join(sys.path[0], '../settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))
DATA_DIR = config.get('globals', 'DATA_DIR')

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
DATA_TABLE_TEMP = config.get('database', 'DATA_TABLE_TEMP')
DATA_TABLE_MONTH = config.get('database', 'DATA_TABLE_MONTH')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, use_unicode=True, charset="utf8")
cur = db.cursor()

all_substances = ["co","no2","o3","pm10","pm25","so2"]

# decryption settings from http://powietrze.gios.gov.pl/pjp/assets-0.0.31/js/chart.js
iteration_count = 1000
hashfunc = 'sha1' # keySize = 128
salt = "dc0da04af8fee58593442bf834b30739"
iv = "dc0da04af8fee58593442bf834b30739"

def generate_key(salt, password):
    return hashlib.pbkdf2_hmac(hashfunc, password, salt.decode('hex'), iteration_count, 16) # from http://powietrze.gios.gov.pl/pjp/assets-0.0.31/js/chart.js

def unpad(s):
    return s[:-ord(s[len(s)-1:])]

def decrypt(data, passphrase):
    key = generate_key(salt, passphrase)
    ciphertext = base64.b64decode(data)
    cipher = AES.new(key, AES.MODE_CBC, iv.decode('hex'))
    return unpad(cipher.decrypt(ciphertext)).decode('utf-8')

class SensorSpider(scrapy.Spider):
    name = "PL test"
    csrf = ""
    sensors = []
    start_url = 'http://powietrze.gios.gov.pl/pjp/current'
    data_url = 'http://powietrze.gios.gov.pl/pjp/current/get_data_chart'
    aqi_url = 'http://powietrze.gios.gov.pl/pjp/current/getAQIDetailsList'
    custom_settings = { 'DOWNLOAD_FAIL_ON_DATALOSS': 'False', }

    def start_requests(self):
        # first, get CSRF
        yield scrapy.Request(self.start_url, callback=self.get_csrf)

    def get_csrf(self, response):
        self.csrf = response.xpath('//script/text()')[1].re('window.csrf = (.*);')[1].strip('"')
        print "-------- %s %s" % ("CSRF:",self.csrf)

        # get bulk data
        headers = {'_csrf_token': self.csrf,}
        post_data = {'param': 'AQI', 'station': '%',}
        print "------ SCRAPING AQI WITH CSRF %s" % (self.csrf)
        yield scrapy.FormRequest(self.aqi_url, headers=headers, formdata=post_data, callback=self.parse_aqi)


    def parse_aqi(self, response):
        data = re.search('<a id="txt" tabindex="-1"></a>\r\n(.*)\r\n', response.text).group(1)
        decrypted = decrypt(data, self.csrf)
        decrypted_data = json.loads(decrypted)

        self.sensors = []
        for sensor in decrypted_data:
            if sensor['valid']:

                # Get sensor data
                sensor_data = []
                sensor_id = sensor['stationId']
                self.sensors.append(sensor_id)
                city = sensor['stationName'].split(',')[0].strip().lower().replace('ł','l')
                name = sensor['stationName'].split(',')[1].strip().lower().replace('ł','l')
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
                import_cmd = "%s/add-sensor.py %s" % (DATA_DIR, line)
                import_args = shlex.split(import_cmd)
                ### run the import
                try:
                    print "Trying to run %s/add-sensor.py %s" % (DATA_DIR, line)
                    process = subprocess.Popen(import_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    out = process.communicate()[1]
                    if (process.returncode != 0):
                        print "Import failed:\n%s" % (out)
                except:
                    print "Couldnt run %s/add-sensor.py %s" % (DATA_DIR, line)

        for sensor_id in self.sensors:
            # now get historical data (starting from 00:00 1.3.2020)
            headers = {'_csrf_token': self.csrf,}
            post_data = {'days': '30', 'stationId': str(sensor_id),}
            print "------ SCRAPING SENSOR %d WITH CSRF %s" % (sensor_id, self.csrf)
            yield scrapy.FormRequest(self.data_url, headers=headers, formdata=post_data, callback=self.parse_single_sensor, meta={'sensor_id': str(sensor_id)})


    def parse_single_sensor(self, response):
        data_array = {}
        sensor_id = response.meta.get('sensor_id')
        data = re.search('<a id="txt" tabindex="-1"></a>\r\n(.*)\r\n', response.text).group(1)
        decrypted = decrypt(data, self.csrf)
        decrypted_data = json.loads(decrypted)

        print "Scraping data for GIOS sensor id: %s" % sensor_id
        for substance_data in decrypted_data['chartElements']:
            substance_name = substance_data['key'].lower().replace('.','')
            if (substance_name in all_substances):
                for substance_datapoint in substance_data['values']:
                    substance_time = datetime.fromtimestamp(substance_datapoint[0]/1000).strftime("%Y-%m-%d %H:%M:%S")
                    substance_value = substance_datapoint[1]
                    if not substance_value:
                        substance_value = "NULL"
                    if substance_time not in data_array:
                        data_array[substance_time] = {}
                    data_array[substance_time][substance_name] = str(substance_value)

        query = "SELECT id FROM %s WHERE link_xpaths like '%%--%s--pl%%'" % (DB_TABLE, sensor_id)
        cur.execute(query)
        row = cur.fetchone()
        sensor_db_id = row[0]
        print "GIOS sensor %s has smog.dance id %s" % (sensor_id, sensor_db_id)

        print "Storing data for GIOS id %s under smog.dance id %s" % (sensor_id, sensor_db_id)
        print data_array
        for timestamp in data_array:
            substances = ", ".join(data_array[timestamp].keys())
            values = ", ".join(data_array[timestamp].values())
            # last month storage
            query = "INSERT INTO %s (sensor_id, timestamp, %s) VALUES(%s, '%s', %s)" % (DATA_TABLE_MONTH, substances, sensor_db_id, timestamp, values)
            cur.execute(query)
            # long term storage
            #query = "INSERT INTO %s (sensor_id, timestamp, %s) VALUES(%s, '%s', %s)" % (DATA_TABLE, substances, sensor_db_id, timestamp, values)
            #cur.execute(query)
            db.commit()
