import pytest

from lib.Stream import Stream, TimeNode
from lib.StreamProperties import StreamStarSat
import logging
import os


class TestInterior:

    FIXTURE_DIR = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'fixtures',
        )

    @pytest.mark.datafiles(
        os.path.join(FIXTURE_DIR, "LongSatSmallStar.json")        
    )
    def test_interior(self, datafiles):
        s = Stream(lang=set("abcd"), _loglevel=logging.INFO)
        core_property = StreamStarSat(s, threshold=2)
        s.setCoreProperty(core_property)
        s.readStream(datafiles.listdir()[0])

        X1 = [(x["u"], (x["b"], x["e"])) for x in s.E ]
        X2 = [(x["v"], (x["b"], x["e"])) for x in s.E ]

        X = X1 + X2
        interior = s.interior(X, X)

        expected = (set([('v', 2, 3), ('v', 4, 5)]),\
                    set([('u', 2, 3), ('y', 4, 5), ('u', 4, 5), ('y', 2, 3)]))
        assert(interior == expected)


