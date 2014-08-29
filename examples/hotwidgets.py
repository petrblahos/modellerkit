"""
Widgets handling events from hotmodel objects.
"""
import logging

import wx

LOGGER = logging.getLogger("hotwidgets")
LOGGER.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('[%(name)s]%(levelname)s: %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
LOGGER.addHandler(ch)

class MVCList(wx.ListView):
    """
        A list that takes a list of column names as a parameter. The value
        updates are not set directly, instead the view responds to event
        fired by a HotList object (probably TypedHotList with tuples as the
        items).
    """
    def __init__(self, parent, id, style, columns,):
        """
            Set up the list in a single selection mode with a list of
            columns.
        Params:
            parent  The parent window
            id      The window id
            style   LC_SINGLE_SEL is added to the style. As this is a "report"
                    style view, you should probably specify at least LC_REPORT
            columns A list of column names.
        """
        super(MVCList, self).__init__(
            parent,
            id,
            style=style | wx.LC_SINGLE_SEL,
        )
        self.set_columns(columns)

    def set_columns(self, columns):
        """
            Set the new column set.
        """
        while self.GetColumnCount():
            self.DeleteColumn(0)
        self.columns = columns
        self.column_mapping = {}
        for (idx, column_info) in enumerate(columns):
            self.InsertColumn(idx, column_info[1])
            self.column_mapping[column_info[0]] = idx

    def add_routes(self, mapper, fqname):
        """
            Map the events to this view.
        Params:
            mapper      The Mapper object the routes are added to.
            fqname      The routes are added under this fqname.
        """
        mapper.add_route(fqname, "reset", self.handle_reset,)
        mapper.add_route(fqname, "update", self.handle_update,)
        mapper.add_route(fqname, "insert", self.handle_insert,)
        mapper.add_route(fqname, "delete", self.handle_delete,)

    def handle_reset(self, model, fqname, event_name, key):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        for (i, data) in enumerate(model):
            self.add_item(i, data)

    def handle_update(self, model, fqname, event_name, key):
        """
            Update the item model[key] on position key.
        """
        self.update_item(key, model[key])

    def handle_insert(self, model, fqname, event_name, key):
        """
            Insert the item model[key] to position key.
        """
        self.add_item(key, model[key])

    def handle_delete(self, model, fqname, event_name, key):
        """
            Delete the item on the position key.
        """
        self.DeleteItem(key)

    def add_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        item = self.InsertStringItem(index, "X")
        self.update_item(index, data)

    def update_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        for i in range(0, len(data)):
            val = "???"
            try:
                val = str(data[i])
            except:
                try:
                    val = repr(data[i])
                except:
                    LOGGER.exception(
                        "Error displaying %s/%s" % (repr(val), type(val)),
                    )

            self.SetStringItem(index, i, val)


class MVCPlainList(MVCList):
    """
        A simple list, that only puts the value into the first column.
    """
    def update_item(self, index, data):
        """
            Converts the data to string and puts them into the first column.
        """
        self.SetStringItem(index, 0, str(data))


class MVCDict(wx.ListView):
    """
        A table view that shows content of an underlying HotDict. The value
        updates are not set directly, instead the view responds to event
        fired by a HotDict object (probably TypedHotDict with tuples as the
        items).
    """
    def __init__(self, parent, id, style, columns,):
        """
            Set up the list in a single selection mode with a list of
            columns.
        Params:
            parent  The parent window
            id      The window id
            style   LC_SINGLE_SEL is added to the style. As this is a "report"
                    style view, you should probably specify at least LC_REPORT
            columns A list of column names.
        """
        super(MVCDict, self).__init__(
            parent,
            id,
            style=style | wx.LC_SINGLE_SEL,
        )
        self.columns = columns
        self.column_mapping = {}
        for (idx, column_info) in enumerate(columns):
            self.InsertColumn(idx, column_info[1])
            self.column_mapping[column_info[0]] = idx
        self.data_mapping = []

    def add_routes(self, mapper, fqname):
        """
            Map the events to this view.
        Params:
            mapper      The Mapper object the routes are added to.
            fqname      The routes are added under this fqname.
        """
        mapper.add_route(fqname, "reset", self.handle_reset,)
        mapper.add_route(fqname, "update", self.handle_update,)
        mapper.add_route(fqname, "insert", self.handle_insert,)
        mapper.add_route(fqname, "delete", self.handle_delete,)

    def handle_reset(self, model, fqname, event_name, key):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        for (k, v) in model.items():
            self.add_item(k, v)

    def handle_update(self, model, fqname, event_name, key):
        """
            Update the item model[key] on position key.
        """
        self.update_item(key, model[key])

    def handle_insert(self, model, fqname, event_name, key):
        """
            Insert the item model[key] to position key.
        """
        self.add_item(key, model[key])

    def handle_delete(self, model, fqname, event_name, key):
        """
            Delete the item on the position key.
        """
        index = self.data_mapping.index(key)
        del self.data_mapping[index]
        self.DeleteItem(index)

    def add_item(self, key, data):
        """
            Inserts an item at the desired position.
        """
        index = len(self.data_mapping)
        item = self.InsertStringItem(index, str(key))
        self.data_mapping.append(key)
        for i in range(0, len(data)):
            self.SetStringItem(index, i + 1, str(data[i]))

    def update_item(self, key, data):
        """
            Inserts an item at the desired position.
        """
        index = self.data_mapping.index(key)
        self.SetStringItem(index, 0, str(key))
        for i in range(0, len(data)):
            self.SetStringItem(index, i + 1, str(data[i]))

    def DeleteAllItems(self):
        super(MVCDict, self).DeleteAllItems()
        self.data_mapping[:] = []
