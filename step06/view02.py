"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import random

import wx

import hotmodel
import production
import hotwidgets

class ProductionView(wx.Frame):
    def __init__(self, parent, dummy_app, title, model):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )

        self.box = wx.GridBagSizer(5, 5)
        self.product = wx.StaticText(self, -1, "")
        self.proc_view = hotwidgets.MVCList(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("operation", "Op."),
                ("act", "Act"),
            ],
        )
        self.ops_view = hotwidgets.MVCList(
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
        self.proc_view.add_routes(self.mapper, "/process")
        self.ops_view.add_routes(self.mapper, "/operations")

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
            Button "Next" handler: Display the next product.
        """
        evt.Skip()
        self.model.set_product("AAAQA%s" % random.randint(0, 9), 1)

    def on_add_op(self, evt):
        """
            Button "add op" handler: Add a random operation to the operation
            list.
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
            Button "delete" handler: Delete selected operation.
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
    FRAME.Maximize(True)
    APP.MainLoop()

