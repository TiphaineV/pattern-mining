import pytest

from lib.Stream import Stream, TimeNode, TimeNodeSet
from lib.StreamProperties import StreamStarSat
from lib.patterns import interior, get_stars_sats
import logging
import os
import ujson


class TestInterior:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.mark.datafiles(
        os.path.join(FIXTURE_DIR, "LongSatSmallStar.json")        
    )
    def test_interior_longsatsmallstar(self, datafiles):
        s = Stream(lang=set("abcd"), _loglevel=logging.INFO)
        core_property = StreamStarSat(s, threshold=2)
        s.setCoreProperty(core_property)
        s.readStream(datafiles.listdir()[0])

        # X1 = [TimeNode(x["u"], x["b"], x["e"]) for x in s.E ]
        # X2 = [TimeNode(x["v"], x["b"], x["e"]) for x in s.E ]

        # X = X1 + X2
        # X = TimeNodeSet([X)
        # s.W = X
        # int_val = interior(s, X, X)
        int_val = interior(s)

        expected = s.substream(TimeNodeSet([TimeNode('v', 2, 3), TimeNode('v', 4, 5)]),\
                    TimeNodeSet([TimeNode('u', 2, 3), TimeNode('y', 4, 5), TimeNode('u', 4, 5), TimeNode('y', 2, 3)]))
        assert(int_val == expected)


    @pytest.mark.datafiles(
        os.path.join(FIXTURE_DIR, "ChangingNeighbours-StSa.json")        
    )
    def test_interior_changing_neighbours(self, datafiles):
        s = Stream(lang=set("abcd"), _loglevel=logging.INFO)
        core_property = StreamStarSat(s, threshold=2)
        s.setCoreProperty(core_property)
        s.readStream(datafiles.listdir()[0])

        # X1 = [TimeNode(x["u"], x["b"], x["e"]) for x in s.E ]
        # X2 = [TimeNode(x["v"], x["b"], x["e"]) for x in s.E ]

        # X = X1 + X2
        # X = TimeNodeSet([X)
        # s.W = X
        # int_val = interior(s, X, X)
        int_val = interior(s)

        expected = s.substream(TimeNodeSet([TimeNode('v', 1, 4)]),\
                    TimeNodeSet([TimeNode('u', 1, 4), TimeNode('y', 2, 4), TimeNode('x', 1, 3)]))
        assert(int_val == expected)

    @pytest.mark.datafiles(
            os.path.join(FIXTURE_DIR, "3links-StSa.json")
    )
    def test_interior_3links_stsa(self, datafiles):
        s = Stream(lang=set("abcd"), _loglevel=logging.INFO)
        core_property = StreamStarSat(s, threshold=3)
        s.setCoreProperty(core_property)
        s.readStream(datafiles.listdir()[0])

        # X1 = [TimeNode(x["u"], x["b"], x["e"]) for x in s.E ]
        # X2 = [TimeNode(x["v"], x["b"], x["e"]) for x in s.E ]

        # X = X1 + X2
        # X = TimeNodeSet([X)
        # s.W = X
        # int_val = interior(s, X, X)
        int_val = interior(s)

        expected = s.substream(TimeNodeSet([TimeNode('v', 2, 4)]),\
                    TimeNodeSet([TimeNode('u', 2, 4), TimeNode('y', 2, 4), TimeNode('x', 2, 4)]))
        assert(int_val == expected)

    @pytest.mark.datafiles(
            os.path.join(FIXTURE_DIR, "3links-StSa-dupl.json")
    )
    def test_interior_3links_stsa_dupl(self, datafiles):
        s = Stream(lang=set("abcd"), _loglevel=logging.INFO)
        core_property = StreamStarSat(s, threshold=3)
        s.setCoreProperty(core_property)
        s.readStream(datafiles.listdir()[0])


        int_val = interior(s)

        expected = s.substream(TimeNodeSet([TimeNode('v', 2, 4), TimeNode('v', 5, 6) ]),\
                    TimeNodeSet([TimeNode('u', 2, 4), TimeNode('y', 2, 4), TimeNode('x', 2, 4), TimeNode('u', 5, 6), TimeNode('y', 5, 6), TimeNode('x', 5, 6)]))
        assert(int_val == expected)
