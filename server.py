#!/usr/bin/env python3
# -*- encoding: utf-8
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 12020 - 12022 HE, Emporia.AI Pte Ltd

__banner__ = """













""" # __banner__

from cubed4th import FORTH

import g, os, re, rich, trio, toml, asks, redio, simplejson

import zlib, pickle, sqlite3, pendulum, random

from hypercorn.trio import serve
from hypercorn.config import Config

from quart import Quart, Blueprint, abort
from quart_trio import QuartTrio
from quart_schema import QuartSchema, validate_request, validate_response

from pydantic.json import pydantic_encoder

from common.computersays import *
cs = ComputerSays()

from dotenv import load_dotenv
load_dotenv(verbose=True)

app = QuartTrio("TAIM_CONFIG")
QuartSchema(app, version="0.42.10", title="")

from common import *

import routes.supply
app.register_blueprint(routes.supply.blueprint)


async def supply_bid(handle, asks_session):

    headers = {'Content-Type': 'application/json'}

    await trio.sleep(0.001 * random.random())

    # grab the supply object data structure
    supply = g.supply_objects[handle]
    supply["accessed"] = pendulum.now()

    # see if the program from the user parses
    try:
        engine = FORTH.Engine(run=supply["program"], sandbox=3)
        supply["compiles"] = True
    except:
        supply["compiles"] = False

    if not supply["compiles"]: return

    while True:

        setup_data = Setup_DATA()
        setup_data.clock = pendulum.now("UTC").to_iso8601_string()
        setup_data.version = "0.42.10"
        setup_data.edition = "supply"
        setup_data.space_id = "Coolamon:Doodads"

        url = "http://127.0.0.1:10000/api/engine/v1/0.SETUP"
        encoded = json.dumps(setup_data, default=pydantic_encoder)
        response = await asks_session.post(url, data=encoded, headers=headers)
        assert response.status_code < 300
        result = json.loads(response.content)

        setup = Setup(**result)
        print(setup)

        if setup.dwell > 10: setup.dwell = 10
        if setup.dwell < 0: setup.dwell = 0
        await trio.sleep(setup.dwell)

        if setup.next:
            break

    #
    # ---------------------------------------------------------------------
    #

    enter_data = Enter_DATA()
    enter_data.clock = pendulum.now("UTC").to_iso8601_string()
    enter_data.handle = setup.handle
    #crossrate: Optional[List[Rate]] = None

    url = "http://127.0.0.1:10000/api/engine/v1/1.ENTER"
    encoded = json.dumps(enter_data, default=pydantic_encoder)
    response = await asks_session.post(url, data=encoded, headers=headers)
    assert response.status_code < 300
    result = json.loads(response.content)

    enter = Enter(**result)
    print(enter)

    if enter.dwell > 10: enter.dwell = 10
    if enter.dwell < 0: enter.dwell = 0
    await trio.sleep(enter.dwell)

    #
    # ---------------------------------------------------------------------
    #

    #demand: Optional[List[Demand]] = None
    #supply: Optional[List[Supply]] = None
    offer_data = Offer_DATA()
    offer_data.clock = pendulum.now("UTC").to_iso8601_string()
    offer_data.handle = setup.handle

    url = "http://127.0.0.1:10000/api/engine/v1/2.OFFER"
    encoded = json.dumps(offer_data, default=pydantic_encoder)
    response = await asks_session.post(url, data=encoded, headers=headers)
    assert response.status_code < 300
    result = json.loads(response.content)

    offer = Offer(**result)
    print(offer)

    if offer.dwell > 10: offer.dwell = 10
    if offer.dwell < 0: offer.dwell = 0
    await trio.sleep(offer.dwell)

    #
    # ---------------------------------------------------------------------
    #

    think_data = Think_DATA()
    think_data.clock = pendulum.now("UTC").to_iso8601_string()
    think_data.handle = setup.handle

    url = "http://127.0.0.1:10000/api/engine/v1/3.THINK"
    encoded = json.dumps(think_data, default=pydantic_encoder)
    response = await asks_session.post(url, data=encoded, headers=headers)
    assert response.status_code < 300
    result = json.loads(response.content)

    think = Think(**result)
    print(think)

    if think.dwell > 10: think.dwell = 10
    if think.dwell < 0: think.dwell = 0
    await trio.sleep(think.dwell)



    #
    # ---------------------------------------------------------------------
    #

    if 1:

        leave_data = Leave_DATA()
        leave_data.clock = pendulum.now("UTC").to_iso8601_string()
        leave_data.handle = setup.handle

        url = "http://127.0.0.1:10000/api/engine/v1/4.LEAVE"
        encoded = json.dumps(leave_data, default=pydantic_encoder)
        response = await asks_session.post(url, data=encoded, headers=headers)
        assert response.status_code < 300
        result = json.loads(response.content)

        leave = Leave(**result)
        print(leave)

        if leave.dwell > 10: leave.dwell = 10
        if leave.dwell < 0: leave.dwell = 0
        await trio.sleep(leave.dwell)



async def supply_worker(g_lock, asks_session):
    while True:
        if len(g.supply_waiting) == 0:
            await trio.sleep(0.1 * random.random())
        if len(g.supply_waiting) == 0: continue
        handle = g.supply_waiting.pop(0)
        await supply_bid(handle, asks_session)

async def supply_workers():

    async with trio.open_nursery() as nursery:
        g_lock = trio.Lock()
        asks_session = asks.Session(connections=42)
        asks_session.base_location = "http://127.0.0.1:10000"
        asks_session.endpoint = "/api/engine/v1/"
        every_1000 = 0
        while True:

            every_1000 += 1
            if every_1000 == 1000:
                every_1000 = 0

                # garbage collection routine

                doomed = []
                for k, v in g.supply_objects.items():
                    if not 'accessed' in v: v['accessed'] = pendulum.now()
                    now_minus_then = pendulum.now() - v['accessed']
                    if now_minus_then.total_seconds() > 300:
                        doomed.append(k)

                for k in doomed:
                    del g.supply_objects[k]

            waiting = len(g.supply_waiting)
            await trio.sleep(0.1)
            if waiting and waiting == len(g.supply_waiting):
                nursery.start_soon(supply_worker, g_lock, asks_session)


async def app_serve(*args):
    async with trio.open_nursery() as nursery:
        nursery.start_soon(supply_workers)
        nursery.start_soon(serve, *args)

cs.load("hypercorn_cfg", """

```

'01FEPGEGR1F85ED0TMQKRWK00Z id

'0.0.0.0:10000 'TAIM_BIND os_getenv 'bind !

""")

config = Config()
config.bind = [cs.hypercorn_cfg['bind']]

from pathlib import Path
p = Path(f"supply_9.txt");
if p.exists(): p.unlink()
i = 8
while i >= 0:
    p = Path(f"supply_{i}.txt")
    if p.exists():
        p.rename(Path(f"supply_{i+1}.txt"))
    i -= 1

from loggify import Loggify
with Loggify("server_0.txt"):
    trio.run(app_serve, app, config)

