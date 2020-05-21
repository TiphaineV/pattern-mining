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

    def test_add_empty(self):
        W = TimeNodeSet()
        W.add(TimeNode("u", 2,4))

        expected = TimeNodeSet([TimeNode("u", 2, 4)])

        assert(W == expected)

    def test_add_existing(self):
        W = TimeNodeSet([TimeNode("u", 1, 3)])
        W.add(TimeNode("u", 2,4))

        expected = TimeNodeSet([TimeNode("u", 1, 4)])

        assert(W == expected)

    def test_set_intersection(self):
        W = TimeNodeSet([
                TimeNode("u", 2, 4)
            ])
        W2 = TimeNodeSet([
                TimeNode("u", 3, 5),
                TimeNode("v", 1, 6)
            ])

        expected = TimeNodeSet([
                TimeNode("u", 3, 4)
            ])

        assert(W.intersection(W2) == expected)

    def test_set_union(self):
        W = TimeNodeSet([
                TimeNode("u", 2, 4)
            ])
        W2 = TimeNodeSet([
                TimeNode("u", 3, 5),
                TimeNode("v", 1, 6)
            ])

        expected = TimeNodeSet([
                TimeNode("u", 2, 5),
                TimeNode("v", 1, 6)
            ])

        assert(W.union(W2) == expected)

    def test_set_disjoint_union(self):
        W = TimeNodeSet([
                TimeNode("u", 2, 4)
            ])
        W2 = TimeNodeSet([
                TimeNode("u", 5, 7)
            ])

        expected = TimeNodeSet([
                TimeNode("u", 2, 4),
                TimeNode("u", 5, 7)
            ])

        assert(W.union(W2) == expected)
