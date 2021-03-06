import pytest

import hotmodel


def get_gather_func(l):
    def gather_firing(*args):
        l.append((args))
    return gather_firing


def test_container_01():
    " add_listener, _fire "
    l = []
    c = hotmodel.HotContainer()
    c.add_listener(get_gather_func(l))
    assert 1 == len(c.listeners)

    c._fire("model", "fqname", "eventname", "key")

    assert l == [
        ("model", "fqname", "eventname", "key", ),
    ]

class C1(hotmodel.HotContainer):
    p1 = hotmodel.HotProperty()

class C2(hotmodel.HotContainer):
    p1 = hotmodel.HotTypedProperty(hotmodel.HotList)

class C3(hotmodel.HotContainer):
    p1 = hotmodel.HotTypedProperty(hotmodel.HotDict)

def prepare_c(clazz):
    l = []
    c = clazz()
    c.add_listener(get_gather_func(l))
    return (l, c)

def test_property_01():
    "Basics: we cannot set mutable, but can set immutable."
    c = C1()
    with pytest.raises(TypeError):
        # assigning mutable
        c.p1 = []

    c.p1 = "HELLO"   # can assign a string
    assert "HELLO" == c.p1
    c.p1 = 312412
    assert 312412 == c.p1

    assert "p1" == C1.p1._get_name_within_parent(c)


def test_property_02():
    "Firing an event."
    (l, c) = prepare_c(C1)

    c.p1 = "HELLO"
    assert l == [
        ("HELLO", "p1", "reset", None),
    ]
    l[:] = []
    c.p1 = 200
    assert l == [
        (200, "p1", "reset", None),
    ]


def test_property_03():
    "The property can contain a HotContainee too."
    (l, c) = prepare_c(C1)

    c.p1 = hotmodel.HotList()
    assert l == [
        (c.p1, "p1", "reset", None),
    ]
    l[:] = []
    c.p1.append("HELLO")
    c.p1.append("HELLO")
    assert l == [
        (c.p1, "p1", "insert", 0),
        (c.p1, "p1", "insert", 1),
    ]
    l[:] = []
    c.p1[1] = 1
    assert l == [
        (c.p1, "p1", "update", 1),
    ]

def test_property_04():
    "Initialized containee."
    (l, c) = prepare_c(C1)

    c.p1 = hotmodel.HotList([1, 2, 3, 4])
    assert l == [
        (c.p1, "p1", "reset", None),
    ]

def test_property_05():
    " Can add a list after (wrongly) added to immutable "
    c = C1()

    hotmodel.add_immutable_type(list)

    c.p1 = [ 1, ]

    # XXX: INTERNAL KNOWLEDGE
    hotmodel.IMMUTABLE_TYPES.discard(list)

    with pytest.raises(TypeError):
        # assigning mutable
        c.p1 = []

def test_typed_property_01():
    " Typed property basic functionality. "
    (l, c) = prepare_c(C2)

    c.p1 = hotmodel.HotList([ 1, 2, 3, ])
    assert l == [
        (c.p1, "p1", "reset", None),
    ]

def test_typed_property_02():
    """ When not assigning exactly the type requested, pass it to
    the constructor """
    (l, c) = prepare_c(C2)

    c.p1 = [ 1, 2, 3, ]
    assert l == [
        (c.p1, "p1", "reset", None),
    ]

def test_hotdict_01():
    (l, c) = prepare_c(C3)
    c.p1 = {}
    assert l == [
        (c.p1, "p1", "reset", None,),
    ]
    assert 0 == len(c.p1)
    c.p1[12] = 342314
    assert c.p1[12] == 342314
    assert l == [
        (c.p1, "p1", "reset", None,),
        (c.p1, "p1", "insert", 12,),
    ]
    assert 1 == len(c.p1)
    l[:] = []
    c.p1[12] = "aksdjfha"
    assert l == [
        (c.p1, "p1", "update", 12,),
    ]
    assert 1 == len(c.p1)
    assert c.p1[12] == "aksdjfha"

def test_hotdict_02():
    (l, c) = prepare_c(C3)
    c.p1 = {}
    assert l == [
        (c.p1, "p1", "reset", None,),
    ]
    c.p1[12] = 342314
    assert l == [
        (c.p1, "p1", "reset", None,),
        (c.p1, "p1", "insert", 12,),
    ]
    l[:] = []
    c.p1[12] = "aksdjfha"
    assert l == [
        (c.p1, "p1", "update", 12,),
    ]

def test_hotdict_03():
    (l, c) = prepare_c(C3)
    c.p1 = { "a": 1111, "b": 2222, "c": 3333, }.items()
    assert l == [
        (c.p1, "p1", "reset", None,),
    ]
    l[:] = []
    c.p1["a"] = 1
    assert l == [
        (c.p1, "p1", "update", "a",),
    ]
    l[:] = []
    c.p1[12] = "aksdjfha"
    assert l == [
        (c.p1, "p1", "insert", 12,),
    ]
    l[:] = []
    del c.p1["b"]
    assert l == [
        (c.p1, "p1", "delete", "b",),
    ]
    assert 3 == len(c.p1)
    l[:] = []
    c.p1.clear()
    assert l == [
        (c.p1, "p1", "reset", "",),
    ]

def test_hotdict_04():
    (l, c) = prepare_c(C3)
    c.p1 = { "a": 1111, "b": 2222, "c": 3333, }.items()
    l[:] = []
    c.p1.update({"a": 1, "b": 2, "d": "4",})
    assert sorted(l, key=lambda x: x[3]) == [
        (c.p1, "p1", "update", "a",),
        (c.p1, "p1", "update", "b",),
        (c.p1, "p1", "insert", "d",),
    ]
    assert 4 == len(c.p1)


if "__main__" == __name__:
    pytest.main()

