import pytest

from lib.Stream import Stream, BipartiteStream
from lib.TimeNode import TimeNode, TimeNodeSet
from lib.StreamProperties import StreamStarSat
import logging
import os


class TestStream:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.fixture
    def test_stream(self):
        s = Stream()
        s.readStream("./tests/integration/fixtures/ChangingNeighbours-StSa.json")
        return s
    
    def test_label_simple(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 1, 5))
        assert(label == set("abcd"))

    def test_label_included(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 2, 4))
        assert(label == set("abcd"))
            
    def test_substream_simple(self, test_stream):
        s = test_stream
        mini_W = TimeNodeSet([
                TimeNode("u", s.T["alpha"], s.T["omega"]),
                TimeNode("v", s.T["alpha"], s.T["omega"]),
                TimeNode("x", s.T["alpha"], s.T["omega"]),
            ])
        sub = s.substream(mini_W, mini_W) 

        expected = Stream()
        expected.T = {"alpha": 0, "omega":10}
        expected.V = set("uvx")
        expected.W = TimeNodeSet([
                TimeNode("u", 1, 5),
                TimeNode("v", 1, 5),
                TimeNode("x", 1, 3)
            ])
        expected.E = [
        {
            "b": 1,
            "e": 5,
            "u": "u",
            "v": "v",
            "label": { "left": set(["a", "b", "c", "d"]),
                       "right": set(["a","b","c","d"]) }
        },
        {
            "b": 1,
            "e": 3,
            "u": "v",
            "v": "x",
            "label": { "left": set(["a", "b", "c", "d"]),
                       "right": set(["a","b","c"]) }
        }]

        assert(sub == expected)

class TestBipartiteStream:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.fixture
    def test_stream(self):
        s = BipartiteStream()
        s.readStream("./tests/integration/fixtures/Bipattern-ChangingNeighbours-StSa.json")
        return s
    
    def test_label_simple(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 1, 5))
        assert(label == set("abcd"))

    def test_label_included(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 2, 4))
        assert(label == set("abcd"))
            
    def test_substream_simple(self, test_stream):
        s = test_stream
        mini_W = TimeNodeSet([
                TimeNode("u", s.T["alpha"], s.T["omega"]),
                TimeNode("v", s.T["alpha"], s.T["omega"]),
                TimeNode("x", s.T["alpha"], s.T["omega"]),
            ])
        sub = s.substream(mini_W, mini_W) 

        expected = BipartiteStream()
        expected.T = {"alpha": 0, "omega":10}
        expected.V = { "left": set("ux"), "right": set("v") }
        expected.W = TimeNodeSet([
                TimeNode("u", 1, 5),
                TimeNode("v", 1, 5),
                TimeNode("x", 1, 3)
            ])
        expected.E = [
        {
            "b": 1,
            "e": 5,
            "u": "u",
            "v": "v",
            "label": {
                "left": set(["a", "b", "c", "d"]),
                "right": set(["w", "x"])
            }
        },
        {
            "b": 1,
            "e": 3,
            "u": "x",
            "v": "v",
            "label": {
                "left": set(["a", "b", "c"]),
                "right": set(["w", "x"])
            }
        }]

        assert(sub == expected)


