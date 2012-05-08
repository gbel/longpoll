longpool
========

Long polling with Tornado and pika/RabbitMQ
-------------------------------------------
Proof of concept of a realtime long polling application with Tornado and pika/RabbitMQ.

It is a Web form to test a server connection receiving a random response, "Success" or "Error".

index.html
----------
html with the form and long polling javascript.

tester.py
---------
Python script that waits for test requests answering them with a random response.

tornado_conn.py
---------------
Tornado application serving the web form and handling assynchronous requests and responses.

pika_client.py
--------------
pika/RabbitMQ helper class for the Tornado webserver.

How to run it
-------------
Make sure you have pika and tornado python libs installed and your rabbitmq server running.

    $python tornado_conn.py

and

    $python tester.py

open your browser on http://localhost:8888

Bug/Problems
------------
- Test requests should be identified and isolated, only the requester gets the response.
