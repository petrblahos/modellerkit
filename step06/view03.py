"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import random

import wx

import hotmodel
import production
import hotwidgets


class ProcView(hotwidgets.MVCList):
    """
        A specialized version of MVCList that sets columns for the process
        operations and adds another column that indicates, whether the
        operation has been done.
    """
    def __init__(self, parent, id, model):
        super(ProcView, self).__init__(
            parent, id, style=wx.LC_REPORT,
            columns=[
                ("operation", "Op."),
                ("act", "Act"),
                ("done", "Done"),
            ],
        )
        self.model = model

    def indicate_operation_status(self, row, status):
        self.SetStringItem(row, 2, "YES" if status else "NO",)

    def update_indication(self, model, fqname, event_name, key):
        """
            Marks those operations that have been done as done and those that
            have not been done as not done.
        """
        done_ops = set([i.operation for i in self.model.operations])
        for (i, op) in enumerate(self.model.process):
            self.indicate_operation_status(
                i,
                op.operation in done_ops,
            )


class ProductionView(wx.Frame):
    def __init__(self, parent, dummy_app, title, model):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )

        self.box = wx.GridBagSizer(5, 5)
        self.product = wx.StaticText(self, -1, "")
        self.proc_view = ProcView(self, -1, model)

        self.box.Add(self.product, (0, 0), (1, 2), flag=wx.EXPAND)
        self.box.Add(self.proc_view, (1, 0), (1, 2), flag=wx.EXPAND)

        next = wx.Button(self, -1, "Next Record")
        add_op = wx.Button(self, -1, "Add Operation")

        self.box.Add(next, (3, 0))
        self.box.Add(add_op, (3, 1))

        self.box.AddGrowableRow(1)
        self.box.AddGrowableCol(0)
        self.box.AddGrowableCol(1)
        self.SetSizerAndFit(self.box)

        self.Bind(wx.EVT_BUTTON, self.on_next, next)
        self.Bind(wx.EVT_BUTTON, self.on_add_op, add_op)

        self.model = model
        self.mapper = hotmodel.Mapper()
        self.proc_view.add_routes(self.mapper, "/process")
        self.mapper.add_route(
            "/process",
            "",
            self.proc_view.update_indication,
        )
        self.mapper.add_route(
            "/operations",
            "",
            self.proc_view.update_indication,
        )

        self.mapper.add_route("/", "", self.on_product,)
        self.model.add_listener(self.mapper)

        wx.CallAfter(lambda: self.model.set_product("FIRST8", 1))

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


if "__main__" == __name__:
    MODEL = production.ProductModel(production.Server(op_done_rate=10))
    APP = wx.App(redirect=False)
    FRAME = ProductionView(None, APP, "Sample Frame", MODEL)
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    FRAME.Maximize(True)
    APP.MainLoop()
