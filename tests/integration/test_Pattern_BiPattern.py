import pytest

from lib.Stream import BipartiteStream
from lib.StreamProperties import StreamStarSat
from lib.patterns import *
from lib.TimeNode import *
import logging
import os


class TestPattern:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.fixture
    def test_stream(self):
        s = Stream()
        s.readStream("./tests/integration/fixtures/ChangingNeighbours-StSa.json")
        return s
    
    def test_pattern_creation(self, test_stream):
        p = Pattern(set("ab"), test_stream)
        
        assert(type(p) is Pattern)

    def test_pattern_add(self, test_stream):
        p = Pattern(set("ab"), test_stream)
        p.add("c")

        assert(p.lang == set("abc"))

    def test_pattern_intent(self, test_stream):
        p = Pattern()
        p.support_set = test_stream
        p.lang = p.intent()

        assert(p.lang == set("ab"))

    def test_pattern_elements(self):
        lang = set("abcd")
        p = Pattern(lang, Stream())

        expected = p.lang
        assert(p.elements() == expected)

    def test_copy_is_not_reference(self):
        lang = set("abcd")
        p = Pattern(lang, Stream())

        p2 = p.copy()

        assert(p2 is not p)

    def test_copy_is_identical(self):
        lang = set("abcd")
        p = Pattern(lang, Stream())

        p2 = p.copy()

        assert(p2 == p)

    def test_extent(self, test_stream):
        p = Pattern()
        p.lang = set("abd")
        
        result = p.extent(test_stream) 
        expected = TimeNodeSet([
                TimeNode("u", 1, 5),
                TimeNode("y", 2, 4),
                TimeNode("v", 1, 5)
            ])
        assert(result == expected)

class TestBiPattern:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.fixture
    def test_stream(self):
        s = BipartiteStream()
        s.readStream("./tests/integration/fixtures/Bipattern-ChangingNeighbours-StSa.json")
        return s
    
    def test_bipattern_creation(self, test_stream):
        bp = BiPattern({"left": set("ab"), "right": set("wx")}, test_stream)
        
        assert(type(bp) is BiPattern)

    def test_bipattern_add(self, test_stream):
        bp = BiPattern({"left": set("ab"), "right": set("wx")}, test_stream)
        bp.add("c", side=0)

        assert(bp.lang["left"] == set("abc") and bp.lang["right"] == set("wx"))

    def test_bipattern_intent(self, test_stream):
        bp = BiPattern()
        bp.support_set = test_stream
        bp.lang = bp.intent()

        assert(bp.lang["left"] == set("ab") and bp.lang["right"] == set("wx"))

    def test_bipattern_elements(self):
        lang = {
            "left": set("abcd"),
            "right": set("wxyz")
        }
        bp = BiPattern(lang, BipartiteStream())

        expected = bp.lang["left"].union(bp.lang["right"])
        assert(bp.elements() == expected)

    def test_copy_is_not_reference(self):
        lang = {
            "left": set("abcd"),
            "right": set("wxyz")
        }
        bp = BiPattern(lang, BipartiteStream())

        bp2 = bp.copy()

        assert(bp2 is not bp)

    def test_copy_is_identical(self):
        lang = {
            "left": set("abcd"),
            "right": set("wxyz")
        }
        bp = BiPattern(lang, BipartiteStream())

        bp2 = bp.copy()

        assert(bp2 == bp)

    def test_extent(self, test_stream):
        bp = BiPattern()
        bp.lang = {"left": set("abd"), "right": set("wx")}
        
        result = bp.extent(test_stream) 
        expected = TimeNodeSet([
                TimeNode("u", 1, 5),
                TimeNode("y", 2, 4),
                TimeNode("v", 1, 5)
            ])
        assert(result == expected)
