from collections import namedtuple
import datetime
import random

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
    def __init__(self):
        pass
    def get_product_ops(self, article, serial_num):
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
            if random.randint(0, 100) > 90:
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

if "__main__" == __name__:
    pass
