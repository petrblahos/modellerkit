"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import logging
import random

import wx

import hotmodel
import production

class MVCList(wx.ListView):
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
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_selection_changed)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_selection_changed)

    def on_selection_changed(self, evt):
        evt.Skip()

    def handle_reset(self, model, fqname, event_name, key):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        for (i, data) in enumerate(model):
            self.add_item(i, data)

    def handle_select(self, event_source, event_name, data):
        selected = self.GetFirstSelected()
        if data == selected:
            return
        if data > -1:
            self.Select(data)
        elif -1 == selected:
            pass
        else:
            self.Select(selected, False)

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
        self.mapper.add_route("/process", "", self.update_proc_count,)
        self.mapper.add_route("/operations", "", self.update_ops_count,)
        self.mapper.add_route("/", "", self.on_product,)
        self.model.add_listener(self.mapper)

        self.article_counter = 0

    def update_proc_count(self, model, fqname, event_name, key):
        self.proc_count.SetLabel(str(len(model)))
    def update_ops_count(self, model, fqname, event_name, key):
        self.ops_count.SetLabel(str(len(model)))

    def on_product(self, model, fqname, event_name, key):
        self.product.SetLabel("%s %s" % (model.article, model.sn))

    def on_next(self, evt):
        evt.Skip()
        self.model.set_product("AAAQA%s" % self.article_counter, 1)
        self.article_counter += 1

    def on_add_op(self, evt):
        evt.Skip()
        proc_op = random.choice(self.model.process)
        self.model.operations.append(production.ProductOperation(
            operation=proc_op.operation,
            tm=datetime.datetime.now(),
            workplace=100,
        ))

    def on_del_op(self, evt):
        evt.Skip()
        sel = self.ops_view.GetFirstSelected()
        if -1 != sel:
            del self.model.operations[sel]


if "__main__" == __name__:
    MODEL = production.ProductModel(production.Server())
    APP = wx.App(redirect=False)
    FRAME = ProductionView(None, APP, "Micro wxPython Frame", MODEL)
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    APP.MainLoop()


