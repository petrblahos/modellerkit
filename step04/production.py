from collections import namedtuple
import datetime
import random

import hotmodel


ProcessOperation = namedtuple("ProcessOperation", [
    "operation",
    "act",
])
ProductOperation = namedtuple("ProductOperation", [
    "operation",
    "tm",
    "workplace",
])

class Server(object):
    ACTS = [
        "Laser",
        "Automatic SMT placement", "Manual SMT placement",
        "AOI",
        "THT placement", "Optical inspection",
        "Selective soldering", "Wave", "Manual soldering",
    ]
    def __init__(self):
        pass
    def get_product_ops(self, article, sn):
        """
            Returns a list of operations done from the product process.
            Randomly skips some operations, and add random dates and
            workplaces.
        """
        ret = []
        dt0 = datetime.datetime.now() - datetime.timedelta(
            random.randint(3, 5),
            random.randint(0, 60*60*24),
        )
        proc = self.get_process(article, sn)
        for op in proc:
            if random.randint(0, 100) > 90:
                continue
            ret.append(ProductOperation(
                op.operation,
                dt0,
                random.randint(1, 5),
            ))
        return ret

    def get_process(self, article, sn):
        """
            Returns a list of operations (operation number, act) for this
            article/sn. For the articles ending with an even number, returns
            one set of operations, another set for all of the rest.
        """
        if article[-1] in ("0", "2", "4", "6", "8",):
            return [ # SMT both sides
                ProcessOperation(op*10, self.ACTS[act])
                for (op, act) in enumerate((0, 1, 2, 3, 1, 3,))
            ]
        if article[-1] in ("1", "3", "5", "7", "9",):
            return [ # SMT one side and THT
                ProcessOperation(op*10, self.ACTS[act])
                for (op, act) in enumerate((0, 1, 3, 4, 7, 5, 8, 5,))
            ]
        return [ # SMT one side, THT, selective soldering
            ProcessOperation(op*10, self.ACTS[act])
            for (op, act) in enumerate((0, 1, 3, 4, 6, 5,))
        ]

class ProductModel(hotmodel.HotObject):
    """
    """
    def __init__(self, server):
        super(ProductModel, self).__init__()
        self.server = server
        self.make_hot_property("article", str, True, None)
        self.make_hot_property("sn", int ,True, None)
        self.make_hot_constant(
            "process",
            hotmodel.TypedHotList,
            hotmodel.TypedHotList(ProcessOperation),
        )
        self.make_hot_constant(
            "operations",
            hotmodel.TypedHotList,
            hotmodel.TypedHotList(ProductOperation),
        )
        self.make_hot_property("process_selection", int ,True, None)
        self.make_hot_property("operation_selection", int ,True, None)

    def set_product(self, article, sn):
        self.article = article
        self.sn = sn
        self.process[:] = self.server.get_process(article, sn)
        self.operations[:] = self.server.get_product_ops(article, sn)
        self.process_selection = None
        self.operation_selection = None

    def select_operation(self, index):
        if index == self.operation_selection:
            return
        self.operation_selection = index
        self._fire("select", index)

    def select_process_operation(self, index):
        if index == self.process_selection:
            return
        self.process_selection = index
        self._fire("select", index)

if "__main__" == __name__:
    model = ProductModel(Server())
    model.set_product("AAAQA1", 1)
    model.set_product("AAAQA2", 2)
