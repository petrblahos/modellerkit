from collections import defaultdict
import datetime
import decimal
import itertools
import logging


LOGGER = logging.getLogger("hotmodel")
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(name)s]%(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
LOGGER.addHandler(ch)

IMMUTABLE_TYPES = set([
    int, float, str,
    datetime.datetime, datetime.date, datetime.time, datetime.timedelta,
    decimal.Decimal,
])

try:
    IMMUTABLE_TYPES.add(long)
    IMMUTABLE_TYPES.add(unicode)
except:
    pass



def add_immutable_type(type_name):
    """
        Immutable types can be added to the set of immutable types, which
        are allowed for hot properties.
    """
    IMMUTABLE_TYPES.add(type_name)


class HotContainer(object):
    """
        HotContainer can maintain listerners and fire events.

        Expected use:
            class MyContainer(HotContainer):
                property1 = HotProperty()
                property2 = HotProperty()
        These properties can be assigned only immutable values and whenever
        the property is assigned into, an event is fired.
    """
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        """
            Appends a listener to the listener list. The listeners are called
            in the order in which they were added.
        """
        self._listeners.append(listener)

    @property
    def listeners(self):
        return self._listeners

    def _fire(self, model, fqname, event_name, key):
        """
            Fire an event.
        """
        LOGGER.debug(
            "FIRE: from=%s event=%s key=%s",
            fqname, event_name, key,
        )
        for listener in self.listeners:
            try:
                listener(model, fqname, event_name, key)
            except Exception as dummy:
                LOGGER.exception(
                    "Error firing %s to %s",
                    event_name, listener,
                )


class HotContainee(object):
    """
        A base class for the data structures assignable to HotProperty.
        A Containee knows its container and uses it to fire events.
    """
    def __init__(self, name=None, container=None):
        self.set_rel(name, container)

    def _fire(self, event_name, key):
        self._container._fire(self, self._name, event_name, key)

    def set_rel(self, name, container):
        self._name = name
        self._container = container


class HotProperty(object):
    """
        A descriptor class for controlling a property, which fires an event
        when changed. See :HotContainer for details.

        Inserts the values into the containing object's dictionary under key
        "__hot_%s" % id(self). Apart from that, adds (name, containing_object)
        into containing object's dictionary under key self.key + "_rel"
    """
    def __init__(self, **kw):
        """
            Initialize the HotProperty.
        """
        super(HotProperty, self).__init__(**kw)
        self.key = "__hot_%s" % id(self)

    def __get__(self, obj, objtype):
        """
            Returns the value of the property within the object.
            Cannot be called on a class.
        """
        if None == obj:
            return self
        return getattr(obj, self.key, None)

    def __set__(self, obj, val):
        """
            Checks that the new value for the property is immutable.
            Checks that we are called on an object, not a class.
        """
        if val is None:
            pass
        elif type(val) in IMMUTABLE_TYPES:
            pass
        elif isinstance(val, HotContainee):
            pass
        else:
            raise TypeError(
                "Can only assign immutable types or Containees here.",
            )

        name = self._get_name_within_parent(obj)
        if isinstance(val, HotContainee):
            val.set_rel(name, obj)

        setattr(obj, self.key, val)
        obj._fire(val, name, "reset", None)

    def _get_name_within_parent(self, obj):
        """
            We need to know the name under shich
            Lookup self in the obj if not yet cached.
        """
        if (self.key + "_rel") in obj.__dict__:
            return obj.__dict__[self.key + "_rel"]

        for (k, v) in type(obj).__dict__.items():
            if v == self:
                setattr(obj, self.key + "_rel", k)
                return k
        raise Exception("Could not find parent")


class HotTypedProperty(HotProperty):
    """
        A hot property that limits its content to a pre-specified type, which
        must be a HotContainee subclass.
    """
    def __init__(self, target_type, **kw):
        assert issubclass(target_type, HotContainee)
        self.target_type = target_type
        super(HotTypedProperty, self).__init__(**kw)

    def __set__(self, obj, val):
        """
            Checks that the object being assigned is an instance of the right
            type.
        """
        name = self._get_name_within_parent(obj)
        if not isinstance(val, self.target_type):
            val = self.target_type(val, name=name, container=obj)
        setattr(obj, self.key, val)
        obj._fire(val, name, "reset", None)


class HotList(HotContainee):
    """
        A list that fires when changed.
    """
    def __init__(self, init_iterable=None, name=None, container=None, ):
        super(HotList, self).__init__(name=name, container=container)
        if init_iterable is None:
            init_iterable = []
        self.data = []
        if init_iterable:
            self.data = [self._validate_value(i) for i in init_iterable]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        if type(key) is slice:
            del self.data[key]
            self._fire("reset", key)
        else:
            key = self._natural_index(key)
            del self.data[key]
            self._fire("delete", key)

    def __setitem__(self, key, value):
        if type(key) is slice:
            for i in value:
                self._validate_value(i)
            self.data[key] = value
            self._fire("reset", key)
        else:
            self.data[key] = self._validate_value(value)
            self._fire("update", self._natural_index(key))

    def insert(self, key, value):
        self.data.insert(key, self._validate_value(value))
        self._fire("insert", self._natural_index(key))

    def append(self, value):
        self.data.append(self._validate_value(value))
        self._fire("insert", len(self.data) - 1)

    def extend(self, iterable):
        for i in iterable:
            self.append(i)

    def _validate_value(self, val):
        """
            The members may only be "primitive" types (int, str and such),
            or tuples of primitive types.
        """
        if val is None:
            return val
        if type(val) in IMMUTABLE_TYPES:
            return val
        if isinstance(val, tuple) or isinstance(val, frozenset):
            for i in val:
                self._validate_value(i)
            return val
        raise TypeError(
            "Only number/strings and tuples/frozensets allowed here.",
        )
    def _natural_index(self, index):
        """
            If we get a negative index, we must convert it to the "natural"
            0-based one.
        """
        if index < 0:
            return len(self.data) + index
        return index

    def __str__(self):
        return str(self.data)
    def __unicode__(self):
        return unicode(self.data)

class TypedHotList(HotList):
    """
        TypedHotList is a HotList variant that can restrict it's items to
        the provided type.
    """
    def __init__(self, type_constraint, init_iterable=None,
                 name=None, container=None,):
        """
            Initializes the structure, sets the type all items in the list
            must be.
        """
        assert type_constraint in IMMUTABLE_TYPES \
                or \
                issubclass(type_constraint, tuple) \
                or \
                issubclass(type_constraint, frozenset) \
                or \
                issubclass(type_constraint, HotProperty)
        self.type_constraint = type_constraint

        super(TypedHotList, self).__init__(init_iterable, name, container,)

    def _validate_value(self, val):
        """
            The members may only be self.type_constraint. If the
            type_constraint is a tuple (or set) then it is also checked
            that the member's members are unmutable.
        """
        if not isinstance(val, self.type_constraint):
            raise TypeError(
                "Only %s allowed here." % self.type_constraint,
            )
        if isinstance(val, tuple) or isinstance(val, frozenset):
            for i in val:
                self._validate_sub_value(i)
        return val

    def _validate_sub_value(self, val):
        """
            Called from _validate_value, checks that the supplied value
            is immutable.
        """
        if val is None:
            return val
        if type(val) in IMMUTABLE_TYPES:
            return val
        if isinstance(val, tuple) or isinstance(val, frozenset):
            for i in val:
                self._validate_sub_value(i)
            return val
        raise TypeError(
            "Only number/strings and tuples/frozensets allowed here.",
        )

class HotDict(HotContainee):
    """
        A dict that fires when changed.
    """
    def __init__(self, init_iterable=None, name=None, container=None, ):
        super(HotDict, self).__init__(name=name, container=container)
        if init_iterable is None:
            init_iterable = []
        self.data = {}
        if init_iterable:
            self.data = dict([
                (k,self._validate_value(v))
                for (k , v) in init_iterable
            ])

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]
        self._fire("delete", key)

    def items(self):
        return self.data.items()
    def keys(self):
        return self.data.keys()
    def values(self):
        return self.data.values()

    def __setitem__(self, key, value):
        event = "update" if key in self.data else "insert"
        self.data[key] = self._validate_value(value)
        self._fire(event, key)

    def clear(self):
        self.data.clear()
        self._fire("reset", "")

    def update(self, other):
        for (k, v) in other.items():
            self[k] = v

    def _validate_value(self, val):
        """
            The members may only be "primitive" types (int, str and such),
            or tuples of primitive types.
        """
        if type(val) in IMMUTABLE_TYPES:
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



class Mapper(object):
    """
        Mapper holds and resolves the mapping of the hot object's fqname
        and event_name to a callable. When the mapper is included into the
        view object it lets the user easily map events by their paths
        (fqnames) and event names to given callables.
    """
    def __init__(self):
        self._routes = defaultdict(lambda:[])

    def __call__(self, model, fqname, event_name, key):
        """
            Finds the callable for the (fqname, event_name) and calls them.
        """
        for callable_ in itertools.chain(
            self._routes[(fqname, event_name)],
            self._routes[(fqname, "")],
            self._routes[("", event_name)],
            self._routes[("", "")],
        ):
            try:
                callable_(model, fqname, event_name, key)
            except:
                logging.exception("Error calling %s", callable_)

    def listener(self, model, fqname, event_name, key):
        self(model, fqname, event_name, key)

    def add_route(self, fqname, event_name, callable):
        """
            Maps a (fully qualified name, event name) to a callable. Then,
        """
        self._routes[(fqname,event_name)].append(callable)
