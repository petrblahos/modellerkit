import pytest

from collections import namedtuple

import hotlist

SampleItem = namedtuple("SampleItem", ["column0", "column1", ])

def get_gather_func(l):
    def gather_firing(*args, **kwargs):
        l.append((args, kwargs))
    return gather_firing

def test_check_type_1():
    """
        Only SampleItem types are allowed.
    """
    hl = hotlist.TypedHotList(type_constraint=SampleItem)

    hl._validate_value(SampleItem(1, 2,))
    hl._validate_value(SampleItem("1", "2",))
    hl._validate_value(SampleItem( 1, (1, 2), ))

    with pytest.raises(TypeError):
        hl._validate_value(( 1, 2, ))

    with pytest.raises(TypeError):
        hl._validate_value(SampleItem( 1, [1, 2], ))
