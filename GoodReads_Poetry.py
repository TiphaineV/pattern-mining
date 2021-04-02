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
from lib.patterns import interior, bipatterns

DELTA = 3600

data_file = sys.argv[1]

h = 2
a = 2

s = BipartiteStream()
s.readStream(data_file)
# s.E = s.E[0:10]
print(len(s.E))
# print(s.E)
core_property = StreamBHACore(s, h=h, a=a)
s.setCoreProperty(core_property)

r = bipatterns(s, s=2)
bip_fp = open(f"gr-stream-{h}-{a}.json", "w+")
json.dump([ x[0].json() for x in s.pattern_list ], bip_fp)
bip_fp.close()
