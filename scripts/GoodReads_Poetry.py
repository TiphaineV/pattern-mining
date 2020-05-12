#!/usr/bin/env python
# coding: utf-8
import ujson as json
import math
import sys

from lib.Stream import BipartiteStream
from lib.StreamProperties import *
from lib.TimeNode import TimeNode, TimeNodeSet
from datetime import datetime
from lib.Utils import Utils
from lib.patterns import interior, get_stars_sats, bipatterns

DELTA = 3600

data_file = sys.argv[1]

s = BipartiteStream()
s.readStream(data_file)
core_property = StreamStarSat(s, threshold=30)
s.setCoreProperty(core_property)

r = bipatterns(s, s=5)
