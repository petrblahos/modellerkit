from collections import defaultdict
import datetime
import itertools
import logging


LOGGER = logging.getLogger("hotlist")
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(name)s]%(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
LOGGER.addHandler(ch)


IMMUTABLE_TYPES = set([
    int, long, float, str, unicode,
    datetime.datetime, datetime.date, datetime.time, datetime.timedelta,
])

def add_immutable_type(tp):
    """
        Immutable types can be added to the set of immutable types, which
        are allowed for hot properties.
    """
    IMMUTABLE_TYPES.add(tp)

class HotBase(object):
    def __init__(self, name=None, parent=None):
        self._listeners = []
        if parent:
            assert name, "For non-root object, you must set a name too"
        if not parent:
            assert not name, "For root object, you may not set a name"
        self._parent = parent
        self._name = name

    def set_relation(self, name, parent):
        self._name = name
        self._parent = parent

    def get_fqname(self):
        """
            Returns the "path" from the parent to this object in the hierarchy
            of the hot objects, where the path is the list of names from the
            parent to this object. More formally, it is the parent's
            get_fqname extended with the name of this.
        """
        if self._parent is None:
            return "/"
        parent_name = self._parent.get_fqname()
        if not parent_name.endswith("/"):
            parent_name += "/"
        return parent_name + self._name

    def add_listener(self, listener):
        """
            Appends a listener to the listener list. The listeners are called
            in the order in which they were added. Listeners can be only added
            to the top-most object in the model's hierarchy.
        """
        assert self._parent is None
        self._listeners.append(listener)

    def get_listeners(self):
        """
            If this object does not have a parent, returns it's list of
            listeners. Otherwise returns parent's get_listeners.
        """
        if self._parent is None:
            return self._listeners
        return self._parent.get_listeners()

    def _fire(self, event_name, key):
        """
            Called to fire an event with the given name and given key.
        """
        fqname = self.get_fqname()
        LOGGER.debug(
            "FIRE: from=%s event=%s key=%s",
            fqname, event_name, key,
        )
        for listener in self.get_listeners():
            try:
                listener(self, fqname, event_name, key)
            except Exception, dummy:
                LOGGER.exception(
                    "Error firing %s to %s",
                    event_name, listener,
                )

    def _copy(self, the_other):
        """
            Copy the data from the_other instance of this class to self.
            Should be implemented in the subclasses, in which we want to be
            able to assign when they are part of a HotObject instance.

            _copy must fire events if applicable.
        """
        assert False, """_copy "constructor" not implemented"""


class HotObject(HotBase):
    """
        HotObject can mark some of it's properties hot, meaning when their
        content is changed, the object "fires" an event.
    """
    def __init__(self, name, parent):
        super(HotObject, self).__init__(name, parent)
        self._hot_properties = {}

    def make_hot_property(self, name, type_info, allow_none, initial_value):
        """
            make_hot_property registers the name to be a "hot" property.
            If the type is immutable, the this will be a property to which
            things can be assigned. If the type is a HotBase, the property
            itself will be readonly, but it's contents will be modifiable.
            Other values are not allowed.
        Params:
            name            The name of the property to be created.
            type_info       The allowed type for the property.
            allow_none      If type_info is HotBase, None may not be allowed.
            initial_value   This value is assigned to the property. Must be
                            None if type_info is a HotBase
        Returns:
            The value of the newly made property.
        """
        assert not name in self._hot_properties
        if type_info in IMMUTABLE_TYPES or issubclass(type_info, HotBase):
            pass
        else:
            raise TypeError(
                "Type not allowed as a hot property: %s" % type_info,
            )

        self._hot_properties[name] = (type_info, allow_none, )
        if issubclass(type_info, HotBase):
            assert not allow_none
        else:
            if not allow_none and initial_value is None:
                raise ValueError("None not allowed for %s" % name)
        if not initial_value is None and not isinstance(
            initial_value, type_info,
        ):
            raise TypeError(
                "Only %s allowed for %s" % (type_info.__name__, name),
            )
        if isinstance(initial_value, HotBase):
            initial_value.set_relation(name, self,)
        super(HotObject, self).__setattr__(name, initial_value)
        return initial_value

    def __setattr__(self, name, val):
        """
            If setting one of the hot properties, check the type. Otherwise
            just assign the value.
        """
        if name.startswith("_"):
            return super(HotObject, self).__setattr__(name, val)

        if name in self._hot_properties:
            (type_info, allow_none) = self._hot_properties[name]

            if issubclass(type_info, HotBase):
                target = getattr(self, name)
                target._copy(val)
                return

            # check if the value has changed
            if getattr(self, name) == val:
                return

            if not val is None and not isinstance(val, type_info):
                raise TypeError(
                    "Only %s allowed for %s" % (type_info.__name__, name),
                )
            if val is None and not allow_none:
                raise ValueError("None not allowed for %s" % name)

            ret = super(HotObject, self).__setattr__(name, val)
            self._fire("update", name)
            return ret
        # normal (not hot) properties
        return super(HotObject, self).__setattr__(name, val)


class HotList(HotBase):
    """
        A list that fires when changed.
    """
    def __init__(self, init_iterable=None, name=None, parent=None, ):
        super(HotList, self).__init__(name, parent)
        if init_iterable is None:
            init_iterable = []
        self.data = []
        if init_iterable:
            self.data = [self._validate_value(i) for i in init_iterable]
        self._fire("reset", None)

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

    def _copy(self, the_other):
        """
            Set the data.
        """
        self.data = []
        for i in the_other:
            self.data.append(self._validate_value(i))
        self._fire("reset", None)

class TypedHotList(HotList):
    """
        TypedHotList is a HotList variant that can restrict it's items to
        the provided type.
    """
    def __init__(self, type_constraint, init_iterable=None,
                 name=None, parent=None,):
        """
            Initializes the structure, sets the type all items in the list
            must be.
        """
        super(TypedHotList, self).__init__(init_iterable, name, parent,)

        assert type_constraint in IMMUTABLE_TYPES \
                or \
                issubclass(type_constraint, tuple) \
                or \
                issubclass(type_constraint, frozenset)
        self.type_constraint = type_constraint

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
        if type(val) in IMMUTABLE_TYPES:
            return val
        if isinstance(val, tuple) or isinstance(val, frozenset):
            for i in val:
                self._validate_sub_value(i)
            return val
        raise TypeError(
            "Only number/strings and tuples/frozensets allowed here.",
        )

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
        for callable in itertools.chain(
            self._routes[(fqname, event_name)],
            self._routes[(fqname, "")],
            self._routes[("", event_name)],
            self._routes[("", "")],
        ):
            try:
                callable(model, fqname, event_name, key)
            except:
                logging.exception("Error calling %s", callable)

    def listener(self, model, fqname, event_name, key):
        self(model, fqname, event_name, key)

    def add_route(self, fqname, event_name, callable):
        """
            Maps a (fully qualified name, event name) to a callable. Then,
        """
        self._routes[(fqname,event_name)].append(callable)
