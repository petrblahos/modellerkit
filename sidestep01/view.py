"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import random

import wx

import production

class MVCList(wx.ListView):
    """
        A list (wx.ListView subclass) that mimics python list behaviour, i.e.
        implementes assignment and retrieval of items using a[x], and methods
        insert, append, and len.

        FIXME: this has not been written with much care, I would not be
        surprised if there are memory leaks.
        FIXME: Does not support slice operations.
    """
    def __init__(self, parent, id, style, columns,):
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
        self.client_objects = {}
    def __len__(self):
        return self.GetItemCount()
    def __getitem__(self, key):
        return self.client_objects[self.GetItemData(key)]
    def __delitem__(self, key):
        del self.client_objects[self.GetItemData(key)]
        self.DeleteItem(key)
    def __setitem__(self, key, value):
        del self.client_objects[self.GetItemData(key)]
        self.client_objects[id(value)] = value
        self.SetItemData(key, id(value))
        self.set_item(key, value)
    def insert(self, key, value):
        self.InsertStringItem(key, str(value))
        self.client_objects[id(value)] = value
        self.SetItemData(key, id(value))
        self.set_item(key, value)
    def append(self, value):
        self.insert(self.GetItemCount(), value)
    def set_item(self, key, value):
        for (i, val) in enumerate(value):
            self.SetStringItem(key, i, str(val))
    def DeleteAllItems(self):
        super(MVCList, self).DeleteAllItems()
        self.client_objects.clear()

class ProductionView(wx.Frame):
    """
        A window with 2 list (a process list and a operations list), a counter
        under each list, and some buttons.
    """
    def __init__(self, parent, dummy_app, title, server):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )
        self.server = server

        self.box = wx.GridBagSizer(5, 5)
        self._article = wx.StaticText(self, -1, "")
        self._sn = wx.StaticText(self, -1, "")
        self.proc_view = MVCList(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("operation", "Op."),
                ("act", "Act"),
            ],
        )
        self.ops_view = MVCList(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("operation", "Operation"),
                ("tm", "Time"),
                ("workplace", "Workplace"),
            ],
        )
        self.proc_count = wx.StaticText(self, -1, "")
        self.ops_count = wx.StaticText(self, -1, "")
        self.box.Add(self._article, (0, 0), (1, 1), flag=wx.EXPAND)
        self.box.Add(self._sn, (0, 1), (1, 1), flag=wx.EXPAND)
        self.box.Add(self.proc_view, (1, 0), flag=wx.EXPAND)
        self.box.Add(self.ops_view, (1, 1), flag=wx.EXPAND)
        self.box.Add(self.proc_count, (2, 0), flag=wx.EXPAND)
        self.box.Add(self.ops_count, (2, 1), flag=wx.EXPAND)

        next = wx.Button(self, -1, "Next Record")
        add_op = wx.Button(self, -1, "Add Operation")
        del_selected_op = wx.Button(self, -1, "Delete Operation")

        self.box.Add(next, (3, 0))
        self.box.Add(add_op, (3, 1))
        self.box.Add(del_selected_op, (4, 1))

        self.box.AddGrowableRow(1)
        self.box.AddGrowableCol(0)
        self.box.AddGrowableCol(1)
        self.SetSizerAndFit(self.box)

        self.Bind(wx.EVT_BUTTON, self.on_next, next)
        self.Bind(wx.EVT_BUTTON, self.on_add_op, add_op)
        self.Bind(wx.EVT_BUTTON, self.on_del_op, del_selected_op)

        wx.CallAfter(self.set_random_product)

    @property
    def article(self):
        return self._article.GetLabel()
    @article.setter
    def article(self, val):
        self._article.SetLabel(str(val))

    @property
    def sn(self):
        return int(self._sn.GetLabel())
    @sn.setter
    def sn(self, val):
        self._sn.SetLabel(str(val))

    def update_count(self, model, view):
        """
            Set the view's label to number of items in model. Typically used
            to indicate a number of items in a list_view.
        """
        view.SetLabel(str(len(model)))

    def on_product(self, model, fqname, event_name, key):
        """
            An article or sn change handler.
        """
        self.product.SetLabel("%s %s" % (model.article, model.sn))

    def on_next(self, evt):
        """
            Display the next product.
        """
        evt.Skip()
        self.set_random_product()

    @property
    def process(self):
        return self.proc_view
    @process.setter
    def process(self, val):
        self.proc_view.DeleteAllItems()
        for i in val:
            self.proc_view.append(i)

    @property
    def operations(self):
        return self.ops_view
    @operations.setter
    def operations(self, val):
        self.ops_view.DeleteAllItems()
        for i in val:
            self.ops_view.append(i)


    def set_random_product(self):
        self.article = "AAAQA%s" % random.randint(0, 9)
        self.sn = random.randint(1, 1000)

        self.process = self.server.get_process(self.article, self.sn)
        self.operations = self.server.get_product_ops(self.article, self.sn)

    def on_add_op(self, evt):
        """
            Add a random operation to the operation list.
        """
        evt.Skip()
        proc_op = random.choice(self.process)
        self.operations.append(production.ProductOperation(
            operation=proc_op.operation,
            tm=datetime.datetime.now(),
            workplace=100,
        ))

    def on_del_op(self, evt):
        """
            Delete selected operation.
        """
        evt.Skip()
        sel = self.ops_view.GetFirstSelected()
        if -1 != sel:
            del self.operations[sel]


if "__main__" == __name__:
    APP = wx.App(redirect=False)
    FRAME = ProductionView(None, APP, "Sample Frame", production.Server())
    APP.SetTopWindow(FRAME)
    FRAME.Maximize(True)
    FRAME.Show(True)
    APP.MainLoop()
