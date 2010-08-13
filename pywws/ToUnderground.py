#!/usr/bin/env python
"""
Post weather update to WeatherUnderground.

usage: python ToUnderground.py [options] data_dir
options are:
\t--help\t\tdisplay this help
\t-v or --verbose\tincrease amount of reassuring messages
data_dir is the root directory of the weather data

StationID and password are read from the weather.ini file in data_dir.
"""

import getopt
import sys
import urllib
import urllib2
from datetime import datetime, timedelta

import DataStore
from TimeZone import Local, utc
from WeatherStation import dew_point

def CtoF(C):
    return (C * 9.0 / 5.0) + 32.0
def ToUnderground(params, data, verbose=1):
    password = params.get('underground', 'password', 'undergroudpassword')
    station = params.get('underground', 'station', 'undergroundstation')
    # most recent data can't be to this very second so will always be before now
    data_now = data[data.before(datetime.max)]
    data_prev = data[data.nearest(data_now['idx'] - timedelta(hours=1))]
    midnight = data_now['idx'].replace(tzinfo=utc).astimezone(Local).replace(
        hour=0, minute=0, second=0)
    data_midnight = data[data.nearest(midnight.astimezone(utc).replace(tzinfo=None))]
    if verbose > 1:
        print data_now
    # create weather underground command
    getPars = {}
    getPars['action'] = 'updateraw'
    getPars['softwaretype'] = 'pywws'
    getPars['ID'] = station
    getPars['PASSWORD'] = password
    getPars['dateutc'] = data_now['idx'].isoformat(' ')
    if data_now['wind_dir'] != None and data_now['wind_dir'] <= 16:
        getPars['winddir'] = '%.0f' % (data_now['wind_dir'] * 22.5)
    if data_now['temp_out'] != None:
        getPars['tempf'] = '%.1f' % (CtoF(data_now['temp_out']))
        if data_now['hum_out'] != None:
            getPars['dewptf'] = '%.1f' % (
                CtoF(dew_point(data_now['temp_out'], data_now['hum_out'])))
            getPars['humidity'] = '%d' % (data_now['hum_out'])
    if data_now['wind_ave'] != None:
        getPars['windspeedmph'] = '%.2f' % (data_now['wind_ave'] * 3.6 / 1.609344)
    if data_now['wind_gust'] != None:
        getPars['windgustmph'] = '%.2f' % (data_now['wind_gust'] * 3.6 / 1.609344)
    getPars['rainin'] = '%g' % (
        max(data_now['rain'] - data_prev['rain'], 0.0) / 25.4)
    getPars['dailyrainin'] = '%g' % (
        max(data_now['rain'] - data_midnight['rain'], 0.0) / 25.4)
    if data_now.has_key('rel_pressure'):
        baromin = data_now['rel_pressure']
    else:
        baromin = (data_now['abs_pressure'] +
                   eval(params.get('fixed', 'pressure offset')))
    getPars['baromin'] = '%.2f' % (baromin * 0.02953)
    if verbose > 1:
        print getPars
    # convert command to URL
    url = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
    full_url = url + '?' + urllib.urlencode(getPars)
    if verbose > 2:
        print full_url
    wudata = urllib2.urlopen(full_url)
    moreinfo = wudata.read()
    if verbose > 0:
        print "Weather Underground returns: \"%s\"" % (moreinfo.strip())
    return 0
def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "hv", ['help', 'verbose'])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __doc__.strip()
        return 1
    # process options
    verbose = 0
    for o, a in opts:
        if o == '-h' or o == '--help':
            print __doc__.strip()
            return 0
        elif o == '-v' or o == '--verbose':
            verbose += 1
    # check arguments
    if len(args) != 1:
        print >>sys.stderr, "Error: 1 argument required"
        print >>sys.stderr, __doc__.strip()
        return 2
    return ToUnderground(
        DataStore.params(args[0]), DataStore.data_store(args[0]), verbose)
if __name__ == "__main__":
    sys.exit(main())