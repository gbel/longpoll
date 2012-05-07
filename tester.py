#!/usr/bin/env python
# coding: utf-8

import time
import sys
import json
import random

import urllib2


def test_conn():
    '''
    Fake server connection test result that randomly returns json 200 or 400
    '''
    conn_ok = {'status': 'SUCCESS',
               'response_code': 200,
               'timestamp': time.strftime('%H:%M:%S')
               }

    conn_err = {'status': 'ERROR',
                'response_code': 400,
                'timestamp': time.strftime('%H:%M:%S')
                }
    return random.choice([conn_ok, conn_err])


def rec_request(url, data=None):
    '''
    Connect to the Tornado server wait for ServerTest Requests
    and/or post test response
    '''
    request = urllib2.Request(url)
    if data:
        request.add_data(data)
        try:
            print urllib2.urlopen(request).read()
        except Exception as e:
            print e
            sys.exit(1)
        print
        print 'TEST DATA RETURN:'
        print request.get_data()
        rec_request(url)
    else:
        print 'WAITING FOR TEST REQUEST:'
        try:
            print urllib2.urlopen(request).read()
        except Exception as e:
            print e
            sys.exit(1)
        #When got something back from server post response
        rec_request(url, json.dumps(test_conn()))

if __name__ == '__main__':
    rec_request('http://localhost:8888/webtest/server')
