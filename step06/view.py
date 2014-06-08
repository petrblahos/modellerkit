"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import random

import wx

import hotmodel
import production

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

    def handle_reset(self, model, fqname, dummy_event_name, key):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        for (i, data) in enumerate(model):
            self.add_item(i, data)

    def add_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        item = self.InsertStringItem(index, str(data[0]))
        for i in range(1, len(data)):
            self.SetStringItem(index, i, str(data[i]))

class ProductionView(wx.Frame):
    def __init__(self, parent, dummy_app, title, model):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )

        self.box = wx.GridBagSizer(5, 5)
        self.product = wx.StaticText(self, -1, "")
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
        self.box.Add(self.product, (0, 0), (1, 2), flag=wx.EXPAND)
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

        self.model = model
        self.mapper = hotmodel.Mapper()
        self.mapper.add_route("/process", "", self.proc_view.handle_reset,)
        self.mapper.add_route("/operations", "", self.ops_view.handle_reset,)

        self.mapper.add_route(
            "/process",
            "",
            lambda m, fqn, event, key: self.update_count(m, self.proc_count),
        )
        self.mapper.add_route(
            "/operations",
            "",
            lambda m, fqn, event, key: self.update_count(m, self.ops_count),
        )

        self.mapper.add_route("/", "", self.on_product,)
        self.model.add_listener(self.mapper)

        wx.CallAfter(lambda: self.model.set_product("FIRST8", 1))

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
        self.model.set_product("AAAQA%s" % random.randint(0, 9), 1)

    def on_add_op(self, evt):
        """
            Add a random operation to the operation list.
        """
        evt.Skip()
        proc_op = random.choice(self.model.process)
        self.model.operations.append(production.ProductOperation(
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
            del self.model.operations[sel]


if "__main__" == __name__:
    MODEL = production.ProductModel(production.Server())
    APP = wx.App(redirect=False)
    FRAME = ProductionView(None, APP, "Sample Frame", MODEL)
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    APP.MainLoop()


