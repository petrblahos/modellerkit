import hotmodel


class HotSample(hotmodel.HotObject):
    def __init__(self):
        super(HotSample, self).__init__()
        self.make_hot_property("counter", int, False, 2)
        self.make_hot_constant(
            "records",
            hotmodel.HotList,
            hotmodel.HotList(),
        )



if "__main__" == __name__:
    sample = HotSample()

    print sample.counter
    sample.counter = 10
    print sample.counter
    sample.counter = 20
    print sample.counter

    sample.records.append(0)
    sample.records.append(1)
    sample.records.append(2)

    sample.records[1] = 1111


