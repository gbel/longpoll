#!/usr/bin/env python
# coding: utf-8

import pika
import json
import tornado.ioloop

from pika.adapters.tornado_connection import TornadoConnection


class PikaClient(object):
    '''
    Helper class to manage RabbitMQ/Pika interface
    '''
    def __init__(self):
        # Construct queue names request and response
        self.queue_name_req = 'request'
        self.queue_name_resp = 'response'

        # A place to keep requests and reponses from Rabbitmq
        self.req_listeners = set([])
        self.resp_listeners = set([])

    def connect(self):
        pika.log.info('PikaClient: Connecting to RabbitMQ on localhost:5672')

        credentials = pika.PlainCredentials('guest', 'guest')
        param = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          virtual_host="/",
                                          credentials=credentials)
        self.connection = TornadoConnection(param,
                                            on_open_callback=self.on_connected)
        self.connection.add_on_close_callback(self.on_closed)

    def on_connected(self, connection):
        pika.log.info('PikaClient: Connected to RabbitMQ on localhost:5672')
        self.connection = connection
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        pika.log.info('PikaClient: Channel Open, Declaring Exchange')
        self.channel = channel
        self.channel.exchange_declare(exchange='tornado',
                                      type="topic",
                                      auto_delete=True,
                                      durable=False,
                                      callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        pika.log.info('PikaClient: Exchange Declared, Declaring Queues')
        self.channel.queue_declare(queue=self.queue_name_req,
                                   auto_delete=True,
                                   durable=False,
                                   exclusive=False)

        self.channel.queue_declare(queue=self.queue_name_resp,
                                   auto_delete=True,
                                   durable=False,
                                   exclusive=False,
                                   callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        pika.log.info('PikaClient: Queues Declared, Binding Queues')
        self.channel.queue_bind(exchange='tornado',
                                queue=self.queue_name_req,
                                routing_key='*.longpoll.request')

        self.channel.queue_bind(exchange='tornado',
                                queue=self.queue_name_resp,
                                routing_key='*.longpoll.response',
                                callback=self.on_queue_bound)

    def on_queue_bound(self, frame):
        pika.log.info('PikaClient: Queue Bound, Issuing Basic Consume')
        self.channel.basic_consume(consumer_callback=self.on_pika_req_message,
                                   queue=self.queue_name_req,
                                   no_ack=True)

        self.channel.basic_consume(consumer_callback=self.on_pika_resp_message,
                                   queue=self.queue_name_resp,
                                   no_ack=True)

    def on_pika_req_message(self, channel, method, header, body):
        log = 'PikaCient: Request Message received: %s'
        pika.log.info(log % body)
        self.notify_listeners(body, 'request')

    def on_pika_resp_message(self, channel, method, header, body):
        log = 'PikaCient: Response Message received: %s'
        pika.log.info(log % body)
        self.notify_listeners(body, 'response')

    def on_basic_cancel(self, frame):
        pika.log.info('PikaClient: Basic Cancel Ok')
        # If we don't have any more consumer processes running close
        self.connection.close()

    def on_closed(self, connection):
        # We've closed our pika connection so stop the demo
        tornado.ioloop.IOLoop.instance().stop()

    def server_test(self, tornado_request, action):
        # Prepare POST information for RabbitMQ
        if action == 'request':
            body = json.dumps(tornado_request.arguments)
        elif action == 'response':
            body = tornado_request.body

        # Send the message
        properties = pika.BasicProperties(
            content_type="application/json",
            delivery_mode=1
            )

        self.channel.basic_publish(exchange='tornado',
                                   routing_key='*.longpoll.' + action,
                                   properties=properties,
                                   body=body)

    def notify_listeners(self, message, action):
        # Deliver the message from RabbitMQ and finish the connection
        if action == 'request':
            listeners = self.req_listeners.copy()
        elif action == 'response':
            listeners = self.resp_listeners.copy()

        for listener in listeners:
            listener.finish(json.dumps(message))
            pika.log.info('PikaClient: notified %s' % repr(listener))
            self.remove_listener(listener, action)

    def add_listener(self, listener, action):
        if action == 'request':
            self.req_listeners.add(listener)
        elif action == 'response':
            self.resp_listeners.add(listener)
        pika.log.info('PikaClient: listener %s added' % repr(listener))

    def remove_listener(self, listener, action):
        try:
            if action == 'request':
                self.req_listeners.remove(listener)
            elif action == 'response':
                self.resp_listeners.remove(listener)
            pika.log.info('PikaClient: listener %s removed' % repr(listener))
        except KeyError:
            pass
