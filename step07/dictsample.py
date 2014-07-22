"""
    A micro wx App with a list of the things checked on the checklist.
"""
import datetime
import random

import wx

import hotmodel
from hotwidgets import (
    MVCDict
)


class MyModel(hotmodel.HotContainer):
    d = hotmodel.HotTypedProperty(hotmodel.HotDict)

    def __init__(self):
        super(MyModel, self).__init__()
        self.d = {}

class DView(wx.Frame):
    def __init__(self, parent, dummy_app, title, model):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )

        self.counter = 0

        self.box = wx.GridBagSizer(5, 5)
        self.d_view = MVCDict(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("key", "Key"),
                ("v0", "V0"),
                ("v1", "V1"),
            ],
        )

        self.box.Add(self.d_view, (1, 0), flag=wx.EXPAND)

        add_btn = wx.Button(self, -1, "Add")
        del_btn = wx.Button(self, -1, "Del")

        self.box.Add(add_btn, (3, 0))
        self.box.Add(del_btn, (4, 0))

        self.box.AddGrowableRow(1)
        self.box.AddGrowableCol(0)
        self.box.AddGrowableCol(1)
        self.SetSizerAndFit(self.box)

        self.model = model
        self.mapper = hotmodel.Mapper()
        self.d_view.add_routes(self.mapper, "d")

        self.Bind(wx.EVT_BUTTON, self.on_add, add_btn)
        self.Bind(wx.EVT_BUTTON, self.on_del, del_btn)

        self.model.add_listener(self.mapper)

    def on_add(self, evt):
        key = random.randint(0, 10)
        val = ("A-%s" % key, "B-%s" % self.counter)
        self.model.d[key] = val
        self.counter += 1

    def on_del(self, evt):
        if not self.model.d:
            return
        key = random.choice(self.model.d.keys())
        del self.model.d[key]


if "__main__" == __name__:
    MODEL = MyModel()
    APP = wx.App(redirect=False)
    FRAME = DView(None, APP, "Sample Frame", MODEL)
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    FRAME.Maximize(True)
    APP.MainLoop()

