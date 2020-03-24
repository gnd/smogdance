import os
import sys
import ConfigParser
import unicodedata

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
       if unicodedata.category(c) != 'Mn')


def fill_spider_template(TEMP_DIR, template, name, link_src, link_xpaths):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("LINK_SRC", link_src)
    res = res.replace("TEMP_DIR", TEMP_DIR)

    ### build some outputs
    outputs = ""
    substances = []
    for line in link_xpaths.split(";"):
        tmp = ""
        substance = line.split("--")[0]
        substances.append(substance)
        xpath = line.split("--")[1]
        modifier = line.split("--")[2]
        if (modifier == 'hu_json'):
            tmp = "        xpath = \"%s\"\n" % (xpath)
            tmp += "        %s = j[\"data\"][xpath][\"value\"] if ((j[\"data\"] != {}) and (\"value\" in j[\"data\"][xpath])) else 'None'\n" % (substance)
            outputs += tmp
        elif (modifier == 'cz_chmi'):
            sensor_uid = xpath.split(":")[0]
            substance_row = xpath.split(":")[1]
            tmp = "        %s = ' '.join(response.xpath(\"//*[contains(text(), '%s')]/../../td[%s]//text()\").extract()).strip().replace(' ','')\n" % (substance, sensor_uid, substance_row)
            tmp += "        %s = 'None' if %s == '' else %s\n" % (substance, substance, substance)
            outputs += tmp
        else:
            tmp = "        %s = ' '.join(response.xpath('%s').extract()).strip().replace(' ','')\n" % (substance, xpath)
            tmp += "        %s = 'None' if %s == '' else %s\n" % (substance, substance, substance)
            if modifier == "int":
                tmp += "        %s = int(float(%s))\n" % (substance)
            outputs += tmp
    if (modifier == 'hu_json'):
        head = "        j = json.loads(json.loads(response.text))\n"
        outputs = head + outputs
    tmp = ""
    for substance in substances:
        tmp += '%s '
    outputs += '        print "' + tmp.strip() + '" % ' + "(%s)" % (','.join(substances))

    res = res.replace("OUTPUTS", outputs)
    return res


def fill_special_spider_template(TEMP_DIR, template, name, link_src, checks, type):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("LINK_SRC", link_src)
    outputs = ""
    if (type == 'bulk'):
        expected_string_all = []
        expected_string_safe_all = []
        remote_string_all = []
        response_size = int(checks.split('===')[0])
        checkpoints = checks.split('===')[1]
        if (checkpoints != ""):
            for line in checkpoints.split(";"):
                expected_string = line.split("--")[0]
                if (expected_string[0].isdigit()):
                    expected_string_safe = expected_string[1:]
                else:
                    expected_string_safe = expected_string
                remote_string = line.split("--")[1]
                expected_string_all.append(expected_string)
                expected_string_safe_all.append(expected_string_safe)
                remote_string_all.append("%s")
                outputs += "        %s = response.xpath('%s').extract()[1]\n" % (expected_string_safe, remote_string)
            outputs += "        EXPECTED = '%s'\n" % (' '.join(expected_string_all))
            outputs += "        REMOTE = \"%s\" %% (%s)\n" % (' '.join(remote_string_all), ','.join(expected_string_safe_all))
            outputs += "        if ((EXPECTED == REMOTE) and (response.status == 200) and (len(response.text) > %d)):\n" % (response_size)
            outputs += "            file('%s/%s.html','w').write(response.text)\n" % (TEMP_DIR, name)
            outputs += '            print "OK"\n'
            outputs += "        else:\n"
            outputs += "            if (os.path.isfile('%s/%s.html')):\n" % (TEMP_DIR, name)
            outputs += "                os.remove('%s/%s.html')\n" % (TEMP_DIR, name)
            outputs += '            print "------------------ !!! ------------------"\n'
            outputs += '            print "Integrity check failed"\n'
            outputs += '            print "EXPECTED: %s" % (EXPECTED)\n'
            outputs += '            print "REMOTE: %s" % (REMOTE)\n'
        else:
            outputs += "        if ((response.status == 200) and (len(response.text) > %d)):\n" % (response_size)
            outputs += "            file('%s/%s.html','w').write(response.text)\n" % (TEMP_DIR, name)
            outputs += '            print "OK"\n'
            outputs += "        else:\n"
            outputs += "            if (os.path.isfile('%s/%s.html')):\n" % (TEMP_DIR, name)
            outputs += "                os.remove('%s/%s.html')\n" % (TEMP_DIR, name)
            outputs += '            print "------------------ !!! ------------------"\n'
            outputs += '            print "Integrity check failed"\n'
    res = res.replace("OUTPUTS", outputs)
    return res


def fill_special_spider_template_pl(TEMP_DIR, template, name, decrypt_rounds, decrypt_hashfunc, decrypt_salt, decrypt_iv, link_csrf, link_aqi, data_regexp):
    f = file(template, 'r')
    tmp = f.read()
    f.close()
    res = tmp.replace("SPIDER_NAME", name)
    res = res.replace("DECRYPT_ROUNDS", decrypt_rounds)
    res = res.replace("DECRYPT_HASHFUNC", decrypt_hashfunc)
    res = res.replace("DECRYPT_SALT", decrypt_salt)
    res = res.replace("DECRYPT_IV", decrypt_iv)
    res = res.replace("LINK_CSRF", link_csrf)
    res = res.replace("LINK_AQI", link_aqi)
    res = res.replace("DATA_REGEXP", data_regexp)
    outfile = '%s/%s.json' % (TEMP_DIR, name)
    res = res.replace("OUTPUT_FILE", outfile)
    return res


def fill_mrtg_template(DATA_DIR, SPIDER_COMMAND, template, id, local_id, name, city, country, substance):
    f = file(template, 'r')
    tmp = f.read()
    f.close()

    name = "%s - %s" % (city.capitalize(), name)
    run_command = "%s/%s"  % (DATA_DIR, SPIDER_COMMAND)
    sensor_desc = "%s-%s" % (city, local_id)
    mrtg_id = "%s_%s" % (sensor_desc.replace(" ","_"), substance)

    res = tmp.replace("SENSOR_NAME", name)
    res = res.replace("RUN_COMMAND", run_command)
    res = res.replace("SENSOR_DESC", sensor_desc.upper())
    res = res.replace("SUBSTANCE_NAME", substance)
    res = res.replace("SUBSTANCE_DESC", substance.upper())
    res = res.replace("MRTG_ID", mrtg_id)
    res = res.replace("SPIDER_ID", str(id))
    maxbytes = 200
    absmax = 300
    if (substance == "pm10"):
        maxbytes = 160
        absmax = 500
    if (substance == "co"):
        maxbytes = 3000
        absmax = 5000
    res = res.replace("MAXBYTES", str(maxbytes))
    res = res.replace("ABSMAX", str(absmax))
    return res


def write_template(filename, template):
    f = file(filename, 'w')
    f.write(template)
    f.close()


def write_mrtg_template(filename, workdir, template):
    if os.path.isfile(filename):
        f = file(filename, 'a')
    else:
        f = file(filename, 'w')
        f.write("WorkDir: %s\n\n" % (workdir))
    f.write(template)
    f.close()
