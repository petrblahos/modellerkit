import logging


LOGGER = logging.getLogger("hotlist")
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s[%(name)s]%(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
LOGGER.addHandler(ch)

class HotBase(object):
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        """
            Appends a listener to the listener list. The listeners are called
            in the order in which they were added.
        """
        self.listeners.append(listener)

    def _fire(self, name, key):
        """
            Called to fire an event with the given name and given key.
        """
        LOGGER.debug("FIRE: %s %s", name, key)
        for listener in self.listeners:
            try:
                listener(self, name, key)
            except Exception, dummy:
                LOGGER.exception("Error firing %s to %s", name, listener)

class HotList(HotBase):
    """
        A list that fires when changed.
    """
    def __init__(self, init_iterable=None):
        super(HotList, self).__init__()
        if init_iterable is None:
            init_iterable = []
        self.data = []
        if init_iterable:
            self.data = [self._validate_value(i) for i in init_iterable]
        self._fire("reset", None)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]
        if type(key) is slice:
            self._fire("reset", key)
        else:
            self._fire("delete", key)

    def __setitem__(self, key, value):
        if type(key) is slice:
            for i in value:
                self._validate_value(i)
            self.data[key] = value
            self._fire("reset", key)
        else:
            self.data[key] = self._validate_value(value)
            self._fire("update", key)

    def insert(self, key, value):
        self.data.insert(key, self._validate_value(value))
        self._fire("insert", key)

    def append(self, value):
        self.data.append(self._validate_value(value))
        self._fire("insert", len(self.data) - 1)

    def _validate_value(self, val):
        """
            The members may only be "primitive" types (int, str and such),
            or tuples of primitive types.
        """
        if type(val) in (int, long, float, str, unicode, ):
            return val
        if isinstance(val, tuple) or isinstance(val, frozenset):
            for i in val:
                self._validate_value(i)
            return val
        raise TypeError(
            "Only number/strings and tuples/frozensets allowed here.",
        )

    def __str__(self):
        return str(self.data)
    def __unicode__(self):
        return unicode(self.data)

if "__main__" == __name__:
    test1()
    test2()
