#!/usr/bin/python3

import http.client
import json
import argparse
import sys
import datetime
import time
import random
import math

# I'm lazy so take some globs
timeout = None
gauss_mean = None
gauss_sigma = None

def get_json():
    dps_con = http.client.HTTPSConnection('publicapi.txdpsscheduler.com')
    dps_con.request('POST',
                    '/api/AvailableLocation',
                    headers={
                        "Content-Type" : "application/json",
                        "Origin" : "https://public.txdpsscheduler.com",
                        "Referer" : "https://public.txdpsscheduler.com",
                        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
                    },
                    body='{"TypeId":21,"ZipCode":"75001","CityName":"","PreferredDay":0}')
    resp = dps_con.getresponse()
    if resp.status != 200:
        dps_con.close()
        print("Can't get response, code: " + resp.status)
        return {}

    body = json.load(resp)
    dps_con.close()

    return body


def print_data(body):
    for x in body:
        print('='*8 + ' ' + x["Name"])
        print('='*4 + ' First Available Date: ' + x["NextAvailableDate"])
        print('='*4 + ' Map Url: ' + x["MapUrl"])
        if x["Availability"] == None:
            continue
        if x["Availability"]["MoreDatesAvailable"] != True:
            continue
        for y in x["Availability"]["LocationAvailabilityDates"]:
            print('='*4 + ' Date: ' + y["AvailabilityDate"] + ' (' + y["DayOfWeek"] + ')')
            print('='*4 + ' Service Type: ' + str(y["ServiceTypeId"]))
            print('='*4 + ' Available Time Slots:')
            for z in y["AvailableTimeSlots"]:
                print('='*2 + ' Slot: ' + z["FormattedStartDateTime"])
                print('='*2 + ' Duration: ' + str(z["Duration"]) + ' min')


def filter_data(body, day, month, year):
    today = datetime.date.today()
    if day == None:
        day = today.day
    if month == None:
        month = today.month
    if year == None:
        year = today.year

    filter_date = datetime.date(year, month, day)


    for x in body:
        available_date = datetime.date(int(x["NextAvailableDateYear"]), int(x["NextAvailableDateMonth"]), int(x["NextAvailableDateDay"]))

        print('Checking ' + str(available_date) + ' <= ' + str(filter_date))
        if available_date <= filter_date:
            print('='*8 + 'FOUND')
            print('='*8 + ' ' + x["Name"])
            print('='*4 + ' First Available Date: ' + x["NextAvailableDate"])
            print('='*4 + ' Map Url: ' + x["MapUrl"])
            return False

    return True


def parse_data(day, month, year):
    global timeout, gauss_mean, gauss_sigma

    # Without any date to filter just output and exit
    filter = True
    if day == None and month == None and year == None:
        filter = False

    body=get_json()
    if (len(body) == 0):
        print('Received empty data. Exiting...')
        sys.exit(1)

    if not filter:
        print_data(body)
        sys.exit(1)

    n=0
    while filter:
        print('Try #' + str(n))
        n=n+1
        # Filter
        filter = filter_data(body, day, month, year)
        if filter:
            body=get_json()
            if (len(body) == 0):
                print('Received empty data. Exiting...')
                sys.exit(1)

        # Let's hide behind Gauss to not be spotted just in case
        if timeout == None:
            sleep_time = random.gauss(gauss_mean, gauss_sigma)
        else:
            sleep_time = timeout
        sleep_time = math.fabs(sleep_time)
        print('sleeping for ' + str(sleep_time))
        time.sleep(sleep_time*60)

    sys.exit(2)


def main():
    global timeout, gauss_mean, gauss_sigma

    aparser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description="Find your place in DPS. This program returns:\n0 -- just print and exit (no filter)\n1 -- on error\n2 -- found filtered data"
    )
    aparser.add_argument('-d', required = False, help = '<= day, default: today', type = int)
    aparser.add_argument('-m', required = False, help = '<= month, default: today', type = int)
    aparser.add_argument('-y', required = False, help = '<= year, default: yesterday :)', type = int)
    aparser.add_argument('-t', required = False, help = 'timeout in minutes, default: use Gauss(4.0,2.0)', type = float)
    aparser.add_argument('-gm', required = False, help = 'Gauss mean [minute], default: 4.0', default = 4.0, type = float)
    aparser.add_argument('-gs', required = False, help = 'Gauss sigma [minute], default: 2.0', default = 2.0, type = float)
    args = aparser.parse_args()

    timeout = args.t
    gauss_mean = args.gm
    gauss_sigma = args.gs

    parse_data(args.d, args.m, args.y)

if __name__ == '__main__':
    main()
