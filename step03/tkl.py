"""
    A micro tk app with a list driven by the model.
"""
from collections import namedtuple
import logging

from Tkinter import *
from ttk import Treeview

import hotlist

Item = namedtuple("Item", ["item", "date",])

class MVCList(Treeview):
    def __init__(self, parent, model):
        Treeview.__init__(
            self,
            parent,
            columns=["COL0", "COL1"],
            selectmode="browse",
        )
        self.heading(0, text="Number")
        self.heading(1, text="Text")
        self["show"] = "headings"
        self.counter = 0
        self.bind("<<TreeviewSelect>>", self.on_select)
        self.model = model
        self.model.add_listener(self.on_model)

    def on_select(self, event):
        sel = self.selection()
        if not sel:
            self.model.select(None)
        else:
            self.model.select(self.index(sel[0]))

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
        self.delete(self.get_children())
        for (i, data) in enumerate(self.event_source):
            self.add_item(i, data)

    def handle_insert(self, event_source, event_name, data):
        """
            A handler for the item insertion.
        """
        self.add_item(data, event_source[data])

    def handle_select(self, event_source, event_name, data):
        """
            A handler for the selection.
        """
        self.selection_set(self.get_children()[data])

    def handle_delete(self, event_source, event_name, data):
        """
            A handler for the item deletion.
        """
        kids = self.get_children()
        self.delete(kids[data])

    def add_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        item = self.insert("", index, text="")
        self.counter += 1
        for (index, value) in enumerate(data):
            self.set(item, index, value)

class Application(Frame):
    def add_item(self):
        """
            The handler for the add button.
        """
        self.counter += 1
        self.list_model.append(Item(str(self.counter), "hello"))

    def del_item(self):
        """
            The handler for the delete button.
        """
        sel = self.list_view.selection()
        if not sel:
            return
        sel_index = self.list_view.index(sel[0])
        del self.list_model[sel_index]

    def createWidgets(self):
        """
            Layout the window.
        """
        self.QUIT = Button(self)
        self.QUIT["text"] = "Quit"
        self.QUIT["command"] =  self.quit

        self.add_btn = Button(self)
        self.add_btn["text"] = "Add an item"
        self.add_btn["command"] = self.add_item

        self.del_btn = Button(self)
        self.del_btn["text"] = "Delete selected"
        self.del_btn["command"] = self.del_item

        self.QUIT.pack({"side": "bottom"})
        self.del_btn.pack({"side": "bottom"})
        self.add_btn.pack({"side": "bottom"})

        self.list_model = hotlist.TypedHotList(type_constraint=Item)
        self.list_view = MVCList(self, self.list_model)
        self.list_view.pack({"side": "top"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.counter = 0
        self.pack()
        self.createWidgets()

ROOT = Tk()
APP = Application(master=ROOT)
APP.mainloop()
ROOT.destroy()

