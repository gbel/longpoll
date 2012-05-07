#!/usr/bin/env python
# coding: utf-8

import json
import time
import pika
import tornado.httpserver
import tornado.ioloop
import tornado.web

from pika_client import PikaClient

PORT = 8888


class BaseHandler(tornado.web.RequestHandler):
    '''
    Identify Client/Consumer
    '''
    pass


class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        # main document
        self.render("index.html")


class AjaxHandler(BaseHandler):
    '''
    Handler that serve server test request from the user browser.
    post() method add request to it's queue
    get() serve the long polling message system
    '''
    @tornado.web.asynchronous
    def post(self):
        # Receive the server test form information and post it to
        # Rabbitmq request queue
        self.application.pika.server_test(self.request, 'request')

        # Send success output
        self.set_header("Content-type", "application/json")
        self.write(json.dumps({'status': 'Success'}))
        self.finish()

    @tornado.web.asynchronous
    def get(self):
        self.application.pika.add_listener(self, 'response')

    def on_connection_close(self):
        self.application.pika.remove_listener(self, 'response')


class TesterHandler(BaseHandler):
    '''
    Handler to serve server test requests for consumers.
    get() serve the device with test information
    post() method add server test result to it's queue
    '''
    @tornado.web.asynchronous
    def post(self):
        # Receive the server test result and add it to its queue
        self.application.pika.server_test(self.request, 'response')

        self.set_header("Content-type", "application/json")
        self.write(json.dumps({'status': 'Success'}))
        self.finish()

    @tornado.web.asynchronous
    def get(self):
        self.application.pika.add_listener(self, 'request')

    def on_connection_close(self):
        self.application.pika.remove_listener(self, 'request')

if __name__ == '__main__':
    # Setup the Tornado Application
    settings = {"debug": True}
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/webtest", AjaxHandler),
        (r"/webtest/server", TesterHandler)
    ], **settings)

    # Helper class PikaClient
    application.pika = PikaClient()

    # Set our pika.log options
    pika.log.setup(color=True)
    # Start the HTTP Server
    pika.log.info("Starting Tornado HTTPServer on port %i" % PORT)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(PORT)

    # Get a handle to the instance of IOLoop
    ioloop = tornado.ioloop.IOLoop.instance()

    # Add our Pika connect to the IOLoop with a deadline in 0.1 seconds
    ioloop.add_timeout(time.time() + .1, application.pika.connect)

    # Start the IOLoop
    ioloop.start()
