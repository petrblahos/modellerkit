from collections import namedtuple
import datetime
import logging
import random
import sys

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

class HotProcessList(hotmodel.TypedHotList):
    """
        A hot list that can have only ProcessOperation assigned as members
    """
    def __init__(self, init_iterable=None, name=None, container=None):
        super(HotProcessList, self).__init__(
            ProcessOperation, init_iterable,
            name, container,
        )

class HotOperationsList(hotmodel.TypedHotList):
    """
        A hot list that can have only ProductOperation assigned as members
    """
    def __init__(self, init_iterable=None, name=None, container=None):
        super(HotOperationsList, self).__init__(
            ProductOperation, init_iterable,
            name, container,
        )

class Server(object):
    """
        A mock server. Can answer questions about a process for an
        (article, serial_number) and about operations done on the
        same.
    """
    ACTS = [
        "Laser",
        "Automatic SMT placement", "Manual SMT placement",
        "AOI",
        "THT placement", "Optical inspection",
        "Selective soldering", "Wave", "Manual soldering",
    ]
    def __init__(self, op_done_rate=90):
        self.op_done_rate = op_done_rate
        pass
    def get_product_ops(self, article, serial_num,):
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
        proc = self.get_process(article, serial_num)
        for operation in proc:
            if random.randint(0, 100) > self.op_done_rate:
                continue
            ret.append(ProductOperation(
                operation.operation,
                dt0,
                random.randint(1, 5),
            ))
            dt0 += datetime.timedelta(0, random.randint(10, 14400))
        return ret

    def get_process(self, article, dummy_sn):
        """
            Returns a list of operations (operation number, act) for this
            article/sn. For the articles ending with an even number, returns
            one set of operations, another set for all of the rest.
        """
        if article[-1] in ("0", "1", "2", "3", ):
            return [ # SMT both sides
                ProcessOperation(op*10, self.ACTS[act])
                for (op, act) in enumerate((0, 1, 2, 3, 1, 3,))
            ]
        if article[-1] in ("4", "5", "6", ):
            return [ # SMT one side and THT
                ProcessOperation(op*10, self.ACTS[act])
                for (op, act) in enumerate((0, 1, 3, 4, 7, 5, 8, 5,))
            ]
        return [ # SMT one side, THT, selective soldering
            ProcessOperation(op*10, self.ACTS[act])
            for (op, act) in enumerate((0, 1, 3, 4, 6, 5,))
        ]


class ProductModel(hotmodel.HotContainer):
    """
        Holds information about a product (article/serial number). When told
        a new (article, serial_number), fetches the information about it's
        process and performed operations from the server. Manages the selected
        operation in the list of performed operations and the selected
        operation in the process.
    """
    article = hotmodel.HotProperty()
    sn = hotmodel.HotProperty()
    operations = hotmodel.HotTypedProperty(HotOperationsList)
    process = hotmodel.HotTypedProperty(HotProcessList)
    operation_selection = hotmodel.HotProperty()
    process_selection = hotmodel.HotProperty()

    def __init__(self, server):
        """
            Set-up the read-only properties.
        """
        super(ProductModel, self).__init__()
        self.server = server

    def set_product(self, article, sn):
        """
            Set the current product.
        """
        self.article = article
        self.sn = sn
        self.process = self.server.get_process(article, sn)
        self.operations = self.server.get_product_ops(article, sn)
        self.operation_selection = -1
        self.process_selection = -1

    def select_operation(self, index):
        """
            Set the selected operation in the list of performed operations.
        """
        if index == self.operation_selection:
            return
        self.operation_selection = index

    def select_process_operation(self, index):
        """
            Set the selected operation in the process.
        """
        if index == self.process_selection:
            return
        self.process_selection = index


def sample_handler(handler_name, model, fqname, event_name, key):
    print(handler_name, "-->", fqname, event_name, key)


if "__main__" == __name__:
    MODEL = ProductModel(Server())

    MAPPER = hotmodel.Mapper()
    MAPPER.add_route("process", "", lambda a,b,c,d: sample_handler("/process-HANDLER-1", a,b,c,d),)
    MAPPER.add_route("", "reset", lambda a,b,c,d: sample_handler("!!RESET-handler-1", a,b,c,d),)
    MAPPER.add_route("", "", lambda a,b,c,d: sample_handler("*-handler-1", a,b,c,d),)
    MODEL.add_listener(MAPPER)

    MODEL.set_product("AAAQA1", 1)

    MODEL.operations.append(ProductOperation(
        operation=MODEL.process[0].operation,
        tm=datetime.datetime.now(),
        workplace=100,
    ))

    MODEL.set_product("AAAQA2", 2)
    MODEL.select_operation(3)
    MODEL.select_process_operation(1)
    MODEL.select_process_operation(2)
    MODEL.select_process_operation(2)
