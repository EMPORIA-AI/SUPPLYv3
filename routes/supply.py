#!/usr/bin/env python3
# -*- encoding: utf-8
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 12020 - 12022 HE, Emporia.AI Pte Ltd

__banner__ = """













""" # __banner__

import g

from quart import Blueprint, request, abort
from quart_schema import *

from common import *
from common.sdk import *

from pydantic.json import pydantic_encoder

from ulid import ULID

blueprint = Blueprint('supply', __name__)

#
# the list of all named values
#

@dataclass
class Upload:
    handle: str = ""

@dataclass
class Upload_DATA:
    program: str = ""

@tag(['supply'])
@blueprint.route('/api/supply/v1/upload', methods=['POST'])
@validate_request(Upload_DATA)
@validate_response(Upload, 200)
async def upload_post(data: Upload_DATA):
    """
    """
    handle = str(ULID())[:-3] + '0SH'

    object = {"program":data.program}

    g.supply_objects[handle] = object
    g.supply_waiting.append(handle)

    results = Upload()
    results.handle = handle
    return results

@dataclass
class Market:
    handle: str = ""

@dataclass
class Market_DATA:
    handle: str = ""

@tag(['supply'])
@blueprint.route('/api/supply/v1/market', methods=['POST'])
@validate_request(Market_DATA)
@validate_response(Market, 200)
async def market_post(data: Market_DATA):
    if not data.handle in g.supply_objects:
        print("! data.handle not in g.supply_objects")
        abort(400)

    object = g.supply_objects[data.handle]

    while not 'compiles' in object:
        await trio.sleep(0.07)

    if not object['compiles']:
        print("! program does not compile")
        abort(400)

    results = Market()
    results.handle = handle
    return results



