modellerkit
===========

An attempt to make a toolset for interaction between a model and view the pythonic way.

step01
------
The most basic list model, demonstrated on a wxPython's ListView and a tk's Treeview.

step02
------
Added the info about the selected item into the model.

step03
------
A TypedHotList can check that items are of the declared type.

step04
------
A new approach: HotObject checks the type for it's properties. Can hold
primitive types or hot values.

step05
------
Adding hierarchy to the hot objects and "event sources" to the events.
Implemented a simple mapper to route events.

step06
------
A full wxPython example based on step05's production.

sidestep01
----------
An example, similar to step06/view01.py, implemented using setters and getters
(and other special methods) on a wx.Frame.

step07
------
A different approach when the model class members are declared by decriptor
classes.
