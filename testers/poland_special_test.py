#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
import base64
import hashlib
from Crypto.Cipher import AES

iteration_count = 1000
hashfunc = 'sha1'
salt = "dc0da04af8fee58593442bf834b30739"
iv = "dc0da04af8fee58593442bf834b30739"

def generate_key(salt, password):
    return hashlib.pbkdf2_hmac(hashfunc, password, salt.decode('hex'), iteration_count, 16)

def unpad(s):
    return s[:-ord(s[len(s)-1:])]

def decrypt(data, passphrase):
    key = generate_key(salt, passphrase)
    ciphertext = base64.b64decode(data)
    cipher = AES.new(key, AES.MODE_CBC, iv.decode('hex'))
    return unpad(cipher.decrypt(ciphertext)).decode('utf-8')

class SensorSpider(scrapy.Spider):
    name = "gios"
    csrf = ""
    start_url = 'http://powietrze.gios.gov.pl/pjp/current'
    aqi_url = 'http://powietrze.gios.gov.pl/pjp/current/getAQIDetailsList'
    custom_settings = { 'DOWNLOAD_FAIL_ON_DATALOSS': 'False', }

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.get_csrf)

    def get_csrf(self, response):
        self.csrf = response.xpath('//script/text()')[1].re('window.csrf = (.*);')[1].strip('"')
        print "-------- %s %s" % ("CSRF:",self.csrf)

        # get bulk data
        headers = {'_csrf_token': self.csrf,}
        post_data = {'param': 'AQI', 'station': '%',}
        yield scrapy.FormRequest(self.aqi_url, headers=headers, formdata=post_data, callback=self.get_aqi)

    def get_aqi(self, response):
        data = re.search('<a id="txt" tabindex="-1"></a>\r\n(.*)\r\n', response.text).group(1)
        decrypted = decrypt(data, self.csrf)
        file('/home/gnd/data/prace/web/smog.dance/smogdance/temp/gios.json','w').write(decrypted)
        print "OK"
