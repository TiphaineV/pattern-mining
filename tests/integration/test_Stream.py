import pytest

from lib.Stream import Stream, TimeNode, TimeNodeSet
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
        s.readStream("./tests/integration/fixtures/ChangingNeighbours-StSa-Copy1.json")
        return s
    
    def test_label_simple(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 1, 5))
        assert(label == set("abcd"))

    def test_label_included(self, test_stream):
        s = test_stream
        label = s.label(TimeNode("u", 2, 4))
        assert(label == set("abcd"))
            


