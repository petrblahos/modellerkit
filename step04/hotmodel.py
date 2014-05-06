import datetime
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


IMMUTABLE_TYPES = (
    int, long, float, str, unicode,
    datetime.datetime, datetime.date, datetime.time, datetime.timedelta,
)


class HotBase(object):
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        """
            Appends a listener to the listener list. The listeners are called
            in the order in which they were added.
        """
        self._listeners.append(listener)

    def _fire(self, name, key):
        """
            Called to fire an event with the given name and given key.
        """
        LOGGER.debug("FIRE: %s %s", name, key)
        for listener in self._listeners:
            try:
                listener(self, name, key)
            except Exception, dummy:
                LOGGER.exception("Error firing %s to %s", name, listener)



class HotObject(HotBase):
    """
        HotObject can mark some of it's properties hot, meaning when their
        content is changed, the object "fires" an event.
    """
    def __init__(self):
        super(HotObject, self).__init__()
        self._hot_properties = {}

    def make_hot_property(self, name, type_info, allow_none, initial_value):
        """
            make_hot_property registers the name to be a "hot" property.
            If the type is immutable, the this will be a property to which
            things can be assigned. If the type is a HotObject, the property
            itself will be readonly, but it's contents will be modifiable.
            Other values are not allowed.
        Params:
            name            The name of the property to be created.
            type_info       The allowed type for the property.
            allow_none      If type_info is HotObject, None may not be allowed.
            initial_value   This value is assigned to the property. Must be
                            None if type_info is a HotObject
        Returns:
            The value of the newly made property.
        """
        assert not name in self._hot_properties
        if type_info in IMMUTABLE_TYPES \
           or issubclass(type_info, HotBase):
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
            if issubclass(type_info, HotObject):
                # do not allow assigning
                # FIXME: if the HotObject implements a "copy constructor like"
                # function, then we can easily emulate the assigning here
                raise AttributeError("Cannot assign to %s" % name)

            # check if the value has changed
            if getattr(self, name) == val:
                return

            if val is None and not allow_none:
                raise ValueError("None not allowed for %s" % name)
            if not val is None and not isinstance(val, type_info):
                raise TypeError(
                    "Only %s allowed for %s" % (type_info.__name__, name),
                )

            ret = super(HotObject, self).__setattr__(name, val)
            self._fire("update", name)
            return ret
        # normal (not hot) properties
        return super(HotObject, self).__setattr__(name, val)


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

class TypedHotList(HotList):
    """
        TypedHotList is a HotList variant that can restrict it's items to
        the provided type.
    """
    def __init__(self, type_constraint, init_iterable=None):
        """
            Initializes the structure, sets the type all items in the list
            must be.
        """
        super(TypedHotList, self).__init__(init_iterable)

        assert type_constraint in IMMUTABLE_TYPES \
                or \
                issubclass(type_constraint, tuple) \
                or \
                issubclass(type_constraint, frozenset) \
                or \
                issubclass(type_constraint, HotObject)
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

