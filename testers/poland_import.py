#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
reload(sys)
import json
import time
import shlex
sys.setdefaultencoding('utf-8')
import scrapy
import base64
import hashlib
import subprocess
import unicodedata
import ConfigParser
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

        for sensor in decrypted_data:
            if sensor['valid']:

                # Get sensor data
                sensor_data = []
                sensor_id = sensor['stationId']
                city = sensor['stationName'].split(',')[0]
                name = sensor['stationName'].split(',')[1]
                link_src = 'file://127.0.0.1TEMP_DIR/gios.json'
                link_web = 'http://powietrze.gios.gov.pl/pjp/current/station_details/chart/' + str(sensor_id)
                link_stat = 'https://STATS_URL/pl/' + city.replace(" ","")
                link_xpaths = "dummy--%d--pl_json" % (sensor_id)
                country = 'pl';
                gps = '';
                sensor_type = 'hourly';
                substances = []
                for substance in sensor['values']:
                    substances.append(substance.lower().replace('.',''))

                # Insert the sensor into the db
                line = "'%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s' '%s'" % (name, link_src, link_web, link_stat, link_xpaths, country, city, gps, sensor_type, substances)
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

        # get detailed data for 612
        #headers = {'_csrf_token': self.csrf,}
        #post_data = {'days': '1', 'stationId': '612',}
        #print "------ SCRAPING SENSOR %d WITH CSRF %s" % (612, self.csrf)
        #yield scrapy.FormRequest(self.data_url, headers=headers, formdata=post_data, callback=self.parse_single_sensor)


    def parse_single_sensor(self, response):
        data = re.search('<a id="txt" tabindex="-1"></a>\r\n(.*)\r\n', response.text).group(1)
        decrypted = decrypt(data, self.csrf)
        decrypted_data = json.loads(decrypted)
        # TODO error handling - if sensor {u'errorMessage': None, u'isError': False,
        for substance_data in decrypted_data['chartElements']:
            substance_name = substance_data['key']
            #substance_time = time.ctime(substance_data['key']['values'][0][0]/1000)
            substance_value = substance_data['values'][0][1]
            print "%s: %s" % (substance_name, substance_value),
