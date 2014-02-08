#!/usr/bin/env python

from config import *
from lib.ripper import Ripper

import os

try:
    ripper = Ripper(config_get('username'), config_get('password'))
    ripper.connect()
except KeyboardInterrupt:
    os.kill(os.getpid(), 9)
