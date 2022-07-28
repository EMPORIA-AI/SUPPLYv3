#!/usr/bin/env python3
# -*- encoding: utf-8
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 12020 - 12022 HE, Emporia.AI Pte Ltd

__banner__ = """













""" # __banner__

from asks import BasicAuth

from common.computersays import *
cs = ComputerSays()

u_pw = (cs.config['username'], cs.config['password'])
auth = BasicAuth(u_pw)

supply_objects = {}

supply_waiting = []
