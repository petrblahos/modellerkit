"""
Widgets handling events from hotmodel objects.
"""

import wx


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
        item = self.InsertStringItem(index, str(data[0]))
        for i in range(1, len(data)):
            self.SetStringItem(index, i, str(data[i]))

    def update_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        for i in range(0, len(data)):
            self.SetStringItem(index, i, str(data[i]))
