"""
    An example of a hot object, which contains a list of hot objects.
"""
import hotmodel


class SecondMember(hotmodel.HotObject):
    " A data type with 2 primitive members. "
    def __init__(self, data=None, name=None, parent=None):
        super(SecondMember, self).__init__(name, parent)
        self.make_hot_property("second1", str, True, None)
        self.make_hot_property("second2", str, True, None)
        self.data = data

class FirstMember(hotmodel.HotObject):
    " A data type with a primitive member and a sub-container. "
    def __init__(self, data=None, name=None, parent=None):
        super(FirstMember, self).__init__(name, parent)
        self.make_hot_property("first1", str, True, None)
        self.make_hot_property(
            "first2",
            SecondMember,
            False,
            SecondMember(),
        )
        self.data = data


class Container(hotmodel.HotObject):
    " A container with 2 members of the same type. "
    def __init__(self):
        super(Container, self).__init__("", None)
        self.make_hot_property(
            "member1",
            FirstMember,
            False,
            FirstMember(),
        )
        self.make_hot_property(
            "member2",
            FirstMember,
            False,
            FirstMember(),
        )


if "__main__" == __name__:
    container = Container()
    container.member1.first1 = "data1"
    container.member2.first1 = "data2"
    container.member1.first2.second1 = "subdata1"
    container.member1.first2.second2 = "subdata2"
    container.member1.first2.second3 = "subdata3"


