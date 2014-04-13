"""
    A micro wx App with a list of the things checked on the checklist.
"""
import logging

import wx

import hotlist

class MVCList(wx.ListView):
    def __init__(self, parent, id, style, columns):
        super(MVCList, self).__init__(parent, id, style=style)
        self.columns = columns
        self.column_mapping = {}
        for (idx, column_info) in enumerate(columns):
            self.InsertColumn(idx, column_info[1])
            self.column_mapping[column_info[0]] = idx

    def on_model(self, event_source, event_name, data):
        """
            An event has been "fired" in the model. It is our responsibility
            to handle only the events we care about.
        """
        handler = "handle_%s" % event_name

        if handler in dir(self):
            getattr(self, handler)(event_source, event_name, data)
        else:
            logging.warn("Unhandled in MVCList: %s", event_name)

    def handle_reset(self, event_source, event_name, data):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        for (i, data) in enumerate(self.event_source):
            self.add_item(i, data)

    def handle_insert(self, event_source, event_name, data):
        self.add_item(data, event_source[data])

    def handle_delete(self, event_source, event_name, data):
        self.DeleteItem(data)

    def add_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        item = self.InsertStringItem(index, data[0])
        for i in range(1, len(data)):
            self.SetStringItem(index, i, data[i])

class MainFrame(wx.Frame):
    def __init__(self, parent, dummy_app, title):
        """ Create the main frame. """
        wx.Frame.__init__(
            self, parent, -1,
            title,
        )

        self.list_model = hotlist.HotList()

        self.box = wx.GridBagSizer(5, 5)
        self.list_view = MVCList(self, -1, wx.LC_REPORT, [
            ("item", "Item"),
            ("date", "Date"),
        ])

        self.counter = 0
        self.list_model.add_listener(self.list_view.on_model)

        self.box.Add(self.list_view, (0, 0), (1, 3), flag=wx.EXPAND)

        rand_record = wx.Button(self, -1, "Add a record")
        clear_record = wx.Button(self, -1, "Delete selected")

        self.box.Add(rand_record, (1, 0))
        self.box.Add(clear_record, (2, 0))

        self.Bind(wx.EVT_BUTTON, self.on_random_record, rand_record)
        self.Bind(wx.EVT_BUTTON, self.on_del_record, clear_record)

        self.box.AddGrowableRow(0)
        self.box.AddGrowableCol(2)
        self.SetSizerAndFit(self.box)

    def on_random_record(self, evt):
        self.counter += 1
        self.list_model.append((str(self.counter), "hello"))
        evt.Skip()
    def on_del_record(self, evt):
        sel = self.list_view.GetFirstSelected()
        if -1 != sel:
            del self.list_model[sel]
        evt.Skip()


if "__main__" == __name__:
    APP = wx.App(redirect=False)
    FRAME = MainFrame(None, APP, "Micro wxPython Frame")
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    APP.MainLoop()
