import pytest

from lib.TimeNode import TimeNode, TimeNodeSet, Interval
import os
import ujson


class TestTimeNode:
    
    def test_get_TimeNode_interval(self):
        w = TimeNode("u", 2, 4)
        
        assert(w.interval.b == 2 and w.interval.e == 4)

    def test_TimeNode_eq(self):
        w = TimeNode("u", 2, 4)
        w2 = TimeNode("u", 2, 4)

        assert(w == w2)

    def test_TimeNode_neq(self):
        w = TimeNode("u", 2, 4)
        w2 = TimeNode("u", 1, 3)

        assert(w != w2)

class TestInterval:

    def test_interval_included(self):
        i = Interval(2, 4)
        i2 = Interval(3, 4)

        assert(i2.included(i))

    def test_interval_not_included(self):
        i = Interval(2, 4)
        i2 = Interval(5, 6)

        assert(not i2.included(i))

    def test_interval_intersection(self):
        i = Interval(2, 4)
        i2 = Interval(3, 6)
        
        assert(i.intersect(i2) == (True, Interval(3,4)))


    def test_Interval_union(self):
        i = Interval(2, 4)
        i2 = Interval(3, 6)
        
        assert(i.union(i2) == Interval(2,6) )

class TestTimeNodeSet:

    def test_len(self):
        W = TimeNodeSet()
        assert(len(W) == 0)
