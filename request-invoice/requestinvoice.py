#!/usr/bin/env python3

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from pyln.client import Plugin
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer


import asyncio
import os
import threading
import uuid

plugin = Plugin()
app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "20 per minute"]
)

jobs = {}



@limiter.limit("20 per minute")
@app.route('/invoice/<int:amount>/<description>')
def getinvoice(amount, description):
    global plugin
    label = "ln-getinvoice-{}".format(uuid.uuid4())
    invoice = plugin.rpc.invoice(int(amount)*1000, label, description)
    return invoice

@limiter.limit("20 per minute")
@app.route('/payRequest')
def getinvoiceLNUrl():
    global plugin
    amount = int(request.args.get('amount'))
    label = "ln-getinvoice-{}".format(uuid.uuid4())

    description = request.args.get('comment')

    if description is None:
        description = ""
    else:
        description = description[:640]

    invoice = plugin.rpc.invoice(amount, label, description)

    return {'pr': invoice['bolt11'], 'routes': []}

    
def worker(address, port):
    asyncio.set_event_loop(asyncio.new_event_loop())

    print('Starting server on port {port}'.format(
        port=port
    ))
    app.config['SECRET_KEY'] = os.getenv(
        "REQUEST_INVOICE_SECRET",
        default=uuid.uuid4())

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port, address)
    IOLoop.instance().start()


def start_server(address, port):
    if port in jobs:
        raise ValueError("server already running on port {port}".format(port=port))

    p = threading.Thread(
        target=worker, args=(address, port), daemon=True)

    jobs[port] = p
    p.start()


def stop_server(port):
    if port in jobs:
        jobs[port].terminate()
        del jobs[port]
    else:
        raise ValueError("No server listening on port {port}".format(port=port))


@plugin.method('invoiceserver')
def invoiceserver(request, command="start"):
    """Starts a server for requestiong invoices.

    A rate limited HTTP Server returns a invoice on the following GET request:
    /invoice/<amount>/<description>
    where amount is in Satoshis.
    The plugin takes one of the following commands:
    {start/stop/status/restart}.
    """
    commands = {"start", "stop", "status", "restart"}
    address = plugin.address
    port = plugin.port

    # if command unknown make start our default command
    if command not in commands:
        command = "start"

    if command == "start":
        try:
            start_server(address, port)
            return "Invoice server started successfully on port {}".format(port)
        except Exception as e:
            return "Error starting server on port {port}: {e}".format(
                port=port, e=e
            )

    if command == "stop":
        try:
            stop_server(port)
            return "Invoice server stopped on port {}".format(port)
        except Exception as e:
            return "Could not stop server on port {port}: {e}".format(
                port=port, e=e
            )

    if command == "status":
        if port in jobs:
            return "Invoice server active on port {}".format(port)
        else:
            return "Invoice server not active."

    if command == "restart":
        stop_server(port)
        start_server(address, port)
        return "Invoice server restarted"


@plugin.init()
def init(options, configuration, plugin):
    plugin.address = options["requestinvoice-addr"]
    plugin.port = int(options["requestinvoice-port"])

    start_server(plugin.address, plugin.port)


plugin.add_option(
    "requestinvoice-addr",
    "127.0.0.1",
    "Manually set the address to be used for the requestinvoice-plugin, default is 127.0.0.1"
)

plugin.add_option(
    "requestinvoice-port",
    "8809",
    "Manually set the port to be used for the requestinvoice-plugin, default is 8809"
)


plugin.run()
