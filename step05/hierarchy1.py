"""
    An example of a hot object, which contains a list of hot objects.
"""
import hotmodel


class SecondMember(hotmodel.HotObject):
    def __init__(self, data=None, name=None, parent=None):
        super(SecondMember, self).__init__(name, parent)
        self.make_hot_property("data", str, True, None)
        self.make_hot_property("karel", str, True, None)
        self.data = data

class ArrayMemeber(hotmodel.HotObject):
    def __init__(self, data=None, name=None, parent=None):
        super(ArrayMemeber, self).__init__(name, parent)
        self.make_hot_property("data", str, True, None)
        self.make_hot_property(
            "second",
            SecondMember,
            False,
            SecondMember(),
        )
        self.data = data


class Container(hotmodel.HotObject):
    def __init__(self):
        super(Container, self).__init__("", None)
        self.make_hot_property(
            "member1",
            ArrayMemeber,
            False,
            ArrayMemeber(),
        )
        self.make_hot_property(
            "member2",
            ArrayMemeber,
            False,
            ArrayMemeber(),
        )


if "__main__" == __name__:
    container = Container()
    container.member1.data = "data1"
    container.member2.data = "data2"
    container.member1.second.data = "subdata"
    container.member1.second.karel = "subdata"

