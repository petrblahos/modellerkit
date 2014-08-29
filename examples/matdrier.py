"""
This sample demonstrates a system for drying material. Various pieces
of material must be dried on defined or higher temperature for defined
period of time, uninterrupted. This system keeps track on the temperature
in the oven, as well as the material in the oven and how long it has been
drying.
"""
from collections import namedtuple
import datetime
import time

import wx
try:
    import wx.gizmos

    LedCtrl = wx.gizmos.LEDNumberCtrl
except:
    LedCtrl = lambda x, y: wx.TextCtrl(x, y, style=wx.TE_READONLY)

import hotmodel, hotwidgets


class Material(namedtuple(
    "_Material",
    [
        "name",
        "status",   # "DRYING", "DRIED", "IDLE"
        "req_temp", # degrees centigrate
        "req_time", # seconds
        "start_tm", # datetime if currently "DRYING" or undefined
    ],
    ),
):
    """
        A material status. Can be IDLE, DRYING, DRIED. Keeps track
        on requested drying temperature, and time, and if DRYING also
        time when drying started.

        Material is a collections.namedtuple, which is a tuple, therefore
        immutable.
    """
    def update(self, temperature, tm=None):
        """
            Should be called when the temperature has changed. If the
            change causes status change, then make the change and return
            an updated object. If there is no change, return self.

            Never modifies self.
        """
        if "DRIED" == self.status:
            return self
        if "IDLE" == self.status and temperature < self.req_temp:
            return self
        if tm is None:
            tm = datetime.datetime.now()
        if "DRYING" == self.status and temperature >= self.req_temp:
            # maybe dry?
            secs = (tm - self.start_tm).total_seconds()
            if secs >= self.req_time:
                return Material(
                    self.name,
                    "DRIED",
                    self.req_temp,
                    self.req_time,
                    tm,
                )
            return self

        return Material(
            self.name,
            "DRYING" if temperature >= self.req_temp else "IDLE",
            self.req_temp,
            self.req_time,
            tm,
        )


class MaterialList(hotmodel.TypedHotList):
    """
        A HotList that accepts only Material instances as items.
    """
    def __init__(self, init_iterable=None, name=None, container=None):
        super(MaterialList, self).__init__(
            Material, init_iterable, name, container,
        )

class Model(hotmodel.HotContainer):
    """
        Keeps track on the material and the temperature in the oven.
    """
    material = hotmodel.HotTypedProperty(MaterialList)
    temperature = hotmodel.HotProperty()

    def __init__(self):
        super(Model, self).__init__()
        self.material = []
        self.temperature = 20

    def set_temperature(self, temp):
        """
            Set the temperature in the oven. Check the material with regard
            to this new temperature.
        """
        if temp == self.temperature:
            return

        self.temperature = temp
        self.update_mat()

    def update_mat(self):
        """
            Should be called periodically to manipulate states of the material.
        """
        tm = datetime.datetime.now()
        for (index, mat) in enumerate(self.material):
            new_mat = mat.update(self.temperature, tm)
            if new_mat != mat:
                self.material[index] = new_mat

    def add_material(self, mat):
        """
            Adds the material mat to the model.
        """
        mat = mat.update(self.temperature)
        self.material.append(mat)


class MaterialView(hotwidgets.MVCList):
    """
        A table displaying one Material on each row.
    """
    def __init__(self, parent):
        super(MaterialView, self).__init__(
            parent, -1, style=wx.LC_REPORT,
            columns=[
                ("label", "Material"),
                ("status", ""),
                ("req_temp", "Dries at"),
                ("req_time", "How long (seconds)"),
                ("start_tm", "Until"),
            ],
        )

    def update_item(self, index, data):
        """
            The "Until" column requires some computation. Also setting
            the background color of the item.
        """
        super(MaterialView, self).update_item(index, data)
        dry_at = ""
        color = "LIGHT GREY"
        if "DRYING" == data.status:
            tm = data.start_tm + datetime.timedelta(0, data.req_time)
            tm = datetime.time(tm.hour, tm.minute, tm.second)
            dry_at = str(tm)
            color = "PINK"
        elif "DRIED" == data.status:
            color = "PALE GREEN"
        self.SetStringItem(index, 4, dry_at)
        self.SetItemBackgroundColour(index, wx.TheColourDatabase.Find(color))

class MatDrierView(wx.Dialog):
    """
        The viewer for the whole Material Drying model.
    """
    def __init__(
        self, parent, dummy_app, title, model,
    ):
        super(MatDrierView, self).__init__(
            parent, -1,
            title,
        )
        self.model = model
        box = wx.GridBagSizer(5, 5)

        self.mat_view = MaterialView(self)
        self.mat_view.SetMinSize((500, 300))
        self.temperature = LedCtrl(self, -1)

        # material input
        self.mat_name = wx.TextCtrl(self, -1, "")
        self.req_time = wx.TextCtrl(self, -1, "")
        self.req_temp = wx.TextCtrl(self, -1, "")
        add_mat = wx.Button(self, -1, "Add material")
        self.temp_goal = wx.TextCtrl(self, -1, "75")

        box.Add(self.mat_view, (0, 0), (1, 7), flag=wx.EXPAND)
        box.Add(self.temperature, (1, 0))
        box.Add(
            wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL),
            (2, 0), (1, 7), flag=wx.EXPAND,
        )
        box.Add(
            wx.StaticText(self, -1, "Material:"),
            (3, 0), flag=wx.ALIGN_CENTER_VERTICAL,
        )
        box.Add(self.mat_name, (3, 1))
        box.Add(
            wx.StaticText(self, -1, "Dry time:"),
            (3, 2), flag=wx.ALIGN_CENTER_VERTICAL,
        )
        box.Add(self.req_time, (3, 3))
        box.Add(
            wx.StaticText(self, -1, "Dry temperature:"),
            (3, 4), flag=wx.ALIGN_CENTER_VERTICAL,
        )
        box.Add(self.req_temp, (3, 5))
        box.Add(add_mat, (3, 6))
        box.Add((10, 10), (4, 0))
        box.Add(
            wx.StaticText(self, -1, "Set oven temperature to:"),
            (5, 0), flag=wx.ALIGN_CENTER_VERTICAL,
        )
        box.Add(self.temp_goal, (5, 1))
        box.Add((10, 10), (6, 0))

        self.mapper = hotmodel.Mapper()
        self.mat_view.add_routes(self.mapper, "material")
        self.mapper.add_route("temperature", "", self.on_temperature)
        self.model.add_listener(self.mapper)

        self.Bind(wx.EVT_BUTTON, self.on_add_mat, add_mat)
        box.AddGrowableCol(6)
        box.AddGrowableRow(0)
        self.SetSizerAndFit(box)

        self.timer = wx.Timer(self, -1)
        self.timer.Start(1000)
        self.Bind(wx.EVT_TIMER, self.on_timer)


    def on_timer(self, evt):
        evt.Skip()
        goal = int(self.temp_goal.GetValue())
        temp = self.model.temperature
        if goal > self.model.temperature:
            temp += 1
        elif goal < self.model.temperature:
            temp -= 1
        self.model.set_temperature(temp)
        self.model.update_mat()

    def on_add_mat(self, evt):
        evt.Skip()
        mat = self.mat_name.GetValue()
        tm = int(self.req_time.GetValue())
        temp = int(self.req_temp.GetValue())
        if mat:
            self.model.add_material(Material(
                    mat, "IDLE", temp, tm, None
            ))

    def on_temperature(self, model, fqname, event_name, key):
        """
            The temperature has changed in the model.
        """
        self.temperature.SetValue(str(model))


if "__main__" == __name__:
    MODEL = Model()
    APP = wx.App(redirect=False)
    FRAME = MatDrierView(None, APP, "Material Drier", MODEL)

    # throw in some values to have more than just an empty dialog box
    MODEL.add_material(Material("MAT-001", "IDLE", 60, 100, None))
    MODEL.add_material(Material("MAT-002", "IDLE", 60, 30, None))
    MODEL.add_material(Material("MAT-003", "IDLE", 70, 30, None))
    MODEL.add_material(Material("MAT-004", "IDLE", 80, 100, None))
    MODEL.set_temperature(55)

    FRAME.ShowModal()
    FRAME.Destroy()

    APP.MainLoop()
