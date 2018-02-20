#!/usr/bin/env python
# # -*- coding: utf-8 -*-

""" Smogdance

    An open-source collection of scripts to collect, store and graph air quality data
    from publicly available sources.

    This polls SQL for the latest values of all sensors from a given city.

    gnd, 2017 - 2018
"""

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import MySQLdb
import ConfigParser

### load config
settings_file = os.path.join(sys.path[0], 'settings_python')
config = ConfigParser.ConfigParser()
config.readfp(open(settings_file))

all_substances = ["co","no2","o3","pm10","pm25","so2"]

### connect to the db
DB_HOST = config.get('database', 'DB_HOST')
DB_USER = config.get('database', 'DB_USER')
DB_PASS = config.get('database', 'DB_PASS')
DB_NAME = config.get('database', 'DB_NAME')
DB_TABLE = config.get('database', 'DB_TABLE')
DATA_TABLE = config.get('database', 'DATA_TABLE')
db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
cur = db.cursor()

# 1. all having x>13 get x+1 (add letiste as 14)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 13):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Letiste' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide1/mp_ALERA_CZ.html' 'https://STATS_URL/cz/praha' 'no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][14]/td[7]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][14]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][14]/td[13]//text()--n' 'cz' 'praha' '50° 6´ 25.510" 14° 15´ 26.014"' 'hourly' 'no2 pm10 pm25'

# 2. all having x>16 get x+1 (add kutna hora as 17)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 16):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Orebitska' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_SKHOA_CZ.html' 'https://STATS_URL/cz/kutna_hora' 'no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][17]/td[7]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][17]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][17]/td[13]//text()--n' 'cz' 'kutna hora' '49° 57´ 1.706" 15° 15´ 37.299"' 'hourly' 'no2 pm10 pm25'

# 3. delete plzen bory, all having x>=34 get x-1
query = "DELETE FROM %s WHERE name = 'Bory' and city = 'plzen'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 33):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)-1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 4. delete plzen skvrnany, all having x>=34 get x-1
query = "DELETE FROM %s WHERE name = 'skvrnany' and city = 'plzen'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 35):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)-1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 5. rename plzen litice to mobil - str8t in sql
#query = "UPDATE %s SET name = 'mobil', gps = '49° 44´ 18.911" 13° 23´ 14.124"' WHERE city = 'plzen' and name = 'Litice'" % (DB_TABLE)
#try:
#    cur.execute(query)
#except:
#    sys.exit("Something went wrong: " + query)

# 6. all having x>50 get x+1 (add steti as 51)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 50):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Steti' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide4/mp_USTEA_CZ.html' 'https://STATS_URL/cz/steti' 'so2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][51]/td[6]//text()--n;no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][51]/td[7]//text()--n;o3--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][51]/td[11]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][51]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][51]/td[13]//text()--n' 'cz' 'steti' '50° 27´ 14.958" 14° 22´ 26.986"' 'hourly' 'so2 no2 o3 pm10 pm25'

# 7. all having x>98 get x+1 (add sumperk as as 99)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 98):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# '5. ZS' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide2/mp_MSMSA_CZ.html' 'https://STATS_URL/cz/sumperk' 'no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][99]/td[7]//text()--n;o3--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][99]/td[11]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][99]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][99]/td[13]//text()--n' 'cz' 'sumperk' '49° 58´ 17.704" 16° 58´ 42.498"' 'hourly' 'no2 o3 pm10 pm25'

# 8. all having x>105 get x+1 (add zlin - kvitkova as 106)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 105):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Kvitkova' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide4/mp_ZZZSA_CZ.html' 'https://STATS_URL/cz/zlin' 'no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][106]/td[7]//text()--n;o3--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][106]/td[11]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][106]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][106]/td[13]//text()--n' 'cz' 'zlin' '49° 13´ 42.505" 17° 40´ 30.299"' 'hourly' 'no2 o3 pm10 pm25'

# 9. delete cesky tesin autobusove nadrazi, all having x>=110 get x-1
query = "DELETE FROM %s WHERE name = 'Autobusove nadrazi' and city = 'cesky tesin'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 109):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)-1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 10. all having x>110 get x+1 (add havirov II as 111)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 110):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Havirov - ZU' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_THAOA_CZ.html' 'https://STATS_URL/cz/havirov' 'pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][111]/td[9]//text()--n' 'cz' 'havirov' '49° 46´ 17.495" 18° 26´ 35.496"' 'hourly' 'pm10'

# 11. all having x>114 get x+1 (add nosovice as 115)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 114):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Nosovice' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TNSVA_CZ.html' 'https://STATS_URL/cz/nosovice' 'no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][115]/td[7]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][115]/td[9]//text()--n;pm25--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][115]/td[13]//text()--n' 'cz' 'nosovice' '49° 39´ 11.060" 18° 25´ 54.593"' 'hourly' 'no2 pm10 pm25'

# 12. all having x>117 get x+2 (add ostrava hrabova as 118 and ostrava kuncicky as 119)
query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 117):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)+2))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

# 'Hrabova' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TOHBA_CZ.html' 'https://STATS_URL/cz/ostrava' 'so2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][118]/td[6]//text()--n;no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][118]/td[7]//text()--n;co--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][118]/td[8]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][118]/td[9]//text()--n' 'cz' 'ostrava' '49° 46´ 42.997" 18° 16´ 43.704"' 'hourly' 'so2 no2 co pm10'

# 'Kuncicky' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TOKUA_CZ.html' 'https://STATS_URL/cz/ostrava' 'so2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][119]/td[6]//text()--n;no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][119]/td[7]//text()--n;co--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][119]/td[8]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][119]/td[9]//text()--n' 'cz' 'ostrava' '49° 48´ 34.893" 18° 17´ 32.998"' 'hourly' 'so2 no2 co pm10'

## 13. delete ostrava - nova ves, all having x>121 get x-1
query = "DELETE FROM %s WHERE name = 'Nova Ves Areal OVak' and city = 'ostrava'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 121):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)-1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

## 14. delete opava - univerzitni zahrada, all having x>126 get x-1
query = "DELETE FROM %s WHERE name = 'Univerzitni zahrada' and city = 'opava'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

query = "SELECT id, link_xpaths from %s WHERE link_xpaths like '%%table[1]%%'" % (DB_TABLE)
try:
    cur.execute(query)
except:
    sys.exit("Something went wrong: " + query)

for line in cur.fetchall():
    id = line[0]
    xpath = line[1]
    xx = xpath.split('odd"][')[1].split(']')[0]
    if (int(xx) > 126):
        xpath = xpath.replace('odd"]['+xx,'odd"]['+str(int(xx)-1))
        query = "UPDATE %s set link_xpaths = '%s' WHERE id = %d" % (DB_TABLE, xpath, id)
    try:
        cur.execute(query)
    except:
        sys.exit("Something went wrong: " + query)
    db.commit()

## 15. add vratimov as 133
# 'Vratimov' 'file://127.0.0.1TEMP_DIR/chmi.html' 'http://portal.chmi.cz/files/portal/docs/uoco/web_generator/aqindex_slide3/mp_TVRTA_CZ.html' 'https://STATS_URL/cz/vratimov' 'so2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][133]/td[6]//text()--n;no2--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][133]/td[7]//text()--n;co--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][133]/td[8]//text()--n;pm10--//div[@id="content"]/table[1]/tr[@class="list-row-odd"][133]/td[9]//text()--n' 'cz' 'vratimov' '49° 46´ 11.301" 18° 19´ 6.499"' 'hourly' 'so2 no2 co pm10'
