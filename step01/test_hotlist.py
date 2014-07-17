import pytest

import hotlist

def get_gather_func(l):
    def gather_firing(*args, **kwargs):
        l.append((args, kwargs))
    return gather_firing

def test_append_1():
    """
        Simple append.
    """
    l = []
    hl = hotlist.HotList()
    hl.add_listener(get_gather_func(l))
    hl.append("item1")
    hl.append("item2")
    hl.append("item3")
    assert l == [
        ((hl, "insert", 0), {},),
        ((hl, "insert", 1), {},),
        ((hl, "insert", 2), {},),
    ]

def test_insert_1():
    """
        Simple insert.
    """
    l = []
    hl = hotlist.HotList()
    hl.add_listener(get_gather_func(l))
    hl.insert(0, "item1")
    hl.insert(0, "item2")
    hl.insert(0, "item3")
    print l
    assert l == [
        ((hl, "insert", 0), {},),
        ((hl, "insert", 0), {},),
        ((hl, "insert", 0), {},),
    ]

def test_insert_2():
    """
        Negative insert.
    """
    l = []
    hl = hotlist.HotList()
    hl.add_listener(get_gather_func(l))
    hl.insert(0, "item1")
    hl.insert(0, "item2")
    hl.insert(-1, "item3")
    hl.insert(-2, "item4")
    hl.insert(-3, "item5")
    assert l == [
        ((hl, "insert", 0), {},),
        ((hl, "insert", 0), {},),
        ((hl, "insert", 2), {},),
        ((hl, "insert", 2), {},),
        ((hl, "insert", 2), {},),
    ]

def test_setitem_1():
    """
        __setitem__ variants
    """
    l = []
    hl = hotlist.HotList()
    hl.add_listener(get_gather_func(l))
    hl.append("item0")
    hl.append("item1")
    hl.append("item2")
    hl.append("item3")
    hl.append("item4")
    del l[:]
    hl[2] = "changed_item2"
    assert l == [ ((hl, "update", 2), {}, ), ]
    hl[-1] = "changed_item4"
    assert l == [
        ((hl, "update", 2), {}, ),
        ((hl, "update", 4), {}, ),
    ]
    hl[-4] = "changed_item1"
    assert l == [
        ((hl, "update", 2), {}, ),
        ((hl, "update", 4), {}, ),
        ((hl, "update", 1), {}, ),
    ]
    del l[:]
    hl[1:2] = []
    assert l == [
        ((hl, "reset", slice(1, 2, None)), {}, ),
    ]

def test_delitem_1():
    """
        __delitem__ variants
    """
    l = []
    hl = hotlist.HotList()
    hl.add_listener(get_gather_func(l))
    hl.append("item0")
    hl.append("item1")
    hl.append("item2")
    hl.append("item3")
    hl.append("item4")
    del l[:]
    del hl[2]
    assert l == [ ((hl, "delete", 2), {}, ), ]
    del l[:]
    del hl[-3]
    assert l == [ ((hl, "delete", 1), {}, ), ]
    del l[:]
    del hl[0:1]
    assert l == [ ((hl, "reset", slice(0, 1, None)), {}, ), ]

def test_check_type_1():
    """
        Only some types are allowed.
    """
    hl = hotlist.HotList()
    hl._validate_value(1)
    hl._validate_value(1L)
    hl._validate_value(1.5)
    hl._validate_value("abc")
    hl._validate_value(u"abc")
    hl._validate_value((1, 2, 3,))
    hl._validate_value((1, "AAA", 3,))
    hl._validate_value((1, ("AAA", 2, 3,) , 3,))
    hl._validate_value((1, frozenset(["AAA", 2, 3,]) , 3,))

    with pytest.raises(TypeError):
        hl._validate_value([ 1, 2, 3,])

    with pytest.raises(TypeError):
        hl._validate_value(( 1, 2, [ 3, 4, 5,],))

    with pytest.raises(TypeError):
        hl._validate_value({})

    with pytest.raises(TypeError):
        hl._validate_value(hotlist.HotList())

if "__main__" == __name__:
    pytest.main()
