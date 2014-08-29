"""
hotmodel sample: A database viewer.
If you supply the SQLAlchemy database uri as the first argument
the database will be reflected and it's contents displayed. If
started without an argument, the local file db.sqlite3 will be
used.
"""
import sys

from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import Table
import wx
import wx.lib.mixins.listctrl as listmix

import hotmodel, hotwidgets

hotmodel.IMMUTABLE_TYPES.add(Table)


class DBModel(hotmodel.HotContainer):
    """
        Maintains the list of database tables (reflected using sqlalchemy),
        keeps track of a selected table, and any extra parameters used for
        filtering. Can run simple queries.
    """
    table_names = hotmodel.HotTypedProperty(hotmodel.HotList)
    current_table = hotmodel.HotProperty()
    query_params = hotmodel.HotTypedProperty(hotmodel.HotDict)
    row_set = hotmodel.HotTypedProperty(hotmodel.HotList)

    def __init__(self):
        super(DBModel, self).__init__()
        self.table_names = []
        self._tables = {}
        self.query_params = {}
        self.row_set = []

    def set_tables(self, tables):
        """
            Resets the state by setting the list of tables and clearing the
            currently selected table, query parameters and current query
            results.
        """
        self._tables = tables
        self.table_names = sorted(tables.keys())
        self.current_table = None
        self.query_params = {}
        self.row_set = []

    def select_table(self, sel):
        """
            Called from the UI to select a table. Clears the query parameters.
        """
        if sel >= len(self.table_names):
            sel = -1
        if -1 == sel:
            current_table = None
        else:
            current_table = self._tables[self.table_names[sel]]
        if self.current_table != current_table:
            self.current_table = current_table
            self.query_params = {}
            self.row_set = []
            self.run_query()
        return

    def run_query(self):
        """
            Run a simple query on the selected tables using the current
            query parameters.
        """
        if self.current_table is None:
            return
        res = []
        q = self.current_table.select().limit(1000)
        for (k, v) in self.query_params.items():
            if k in self.current_table.c and v:
                q = q.where(self.current_table.c[k]==v)
        for i in q.execute():
            res.append(tuple(i))
        self.row_set = res

    def initialize(self, uri):
        """
            Reflect the tables from the database and set initialize self.
        """
        if not uri:
            uri = "sqlite:///db.sqlite3"
        engine = create_engine(uri)
        meta = MetaData(bind=engine)
        meta.reflect()
        self.set_tables(meta.tables)


class TableView(hotwidgets.MVCList, listmix.TextEditMixin):
    """
        A view for a database table. The second column can be edited.
    """
    def __init__(self, parent, id, model):
        hotwidgets.MVCList.__init__(
            self, parent, id,
            style=wx.LC_REPORT,
            columns=[
                ("name", "Name"),
                ("filter", "Filter"),
                ("tp", "Type"),
                ("extra", ""),
            ],
        )
        listmix.TextEditMixin.__init__(self)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        self.model = model

    def OnBeginLabelEdit(self, event):
        """
            Allow editing the second column only.
        """
        if event.m_col != 1:
            event.Veto()
        else:
            event.Skip()

    def add_routes(self, mapper, fqname):
        """
            We do not expect the table to be altered during the UI lifetime,
            therefore we point all events to reset.
        Params:
            mapper      The Mapper object the routes are added to.
            fqname      The routes are added under this fqname.
        """
        mapper.add_route(fqname, "", self.handle_reset,)

    def update_item(self, index, data):
        """
            Inserts an item at the desired position.
        """
        self.SetStringItem(index, 0, str(data.name))
        tp_name = ""
        try:
            tp_name = str(data.type)
        except:
            pass
        self.SetStringItem(index, 2, tp_name)
        extra = ""
        if data.primary_key:
            extra += "PK"
        self.SetStringItem(index, 3, extra)

    def handle_reset(self, model, fqname, event_name, key):
        """
            Rebuild the list's contents.
        """
        self.DeleteAllItems()
        if model is None:
            return
        for (i, data) in enumerate(model.columns):
            self.add_item(i, data)


class DBView(wx.Frame):
    """
        A view of a list of the tables, the selected table, and a sample of
        the data of the selected table.
    """
    def __init__(self, parent, dummy_app, title, model):
        """ Create the main frame. """
        super(DBView, self).__init__(
            parent, -1,
            title,
        )
        self.model = model

        self.box = wx.GridBagSizer(5, 5)
        self.tables_view = hotwidgets.MVCPlainList(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("name", "Name"),
            ],
        )
        self.table_view = TableView(self, -1, self.model)
        self.row_view = hotwidgets.MVCList(
            self, -1, style=wx.LC_REPORT,
            columns=[
                ("n", "N"),
            ],
        )

        self.box.Add(self.tables_view, (0, 0), flag=wx.EXPAND)
        self.box.Add(self.table_view, (1, 0), flag=wx.EXPAND)
        self.box.Add(self.row_view, (0, 1), (2, 2), flag=wx.EXPAND)

        self.mapper = hotmodel.Mapper()
        self.tables_view.add_routes(self.mapper, "table_names")
        self.table_view.add_routes(self.mapper, "current_table")
        self.mapper.add_route("row_set", "", self.on_row_set)

        self.model.add_listener(self.mapper)

        self.tables_view.Bind(
            wx.EVT_LIST_ITEM_SELECTED,
            self.on_table_selection,
        )
        self.table_view.Bind(
            wx.EVT_LIST_END_LABEL_EDIT,
            self.on_filter_update,
        )
        self.box.AddGrowableCol(0)
        self.box.AddGrowableCol(1)
        self.box.AddGrowableCol(2)
        self.box.AddGrowableRow(0)
        self.box.AddGrowableRow(1)
        self.SetSizerAndFit(self.box)

    def on_filter_update(self, evt):
        """
            When a new filter value has been entered, update query params
            within the model, and run the query.
        """
        evt.Skip()
        row = evt.m_itemIndex
        column_name = self.table_view.GetItem(row, 0).GetText()
        filter_value = evt.m_item.GetText()
        self.model.query_params[column_name] = filter_value
        self.model.run_query()

    def on_table_selection(self, evt):
        """
            A new table has been selected in the UI.
        """
        evt.Skip()
        self.model.select_table(self.tables_view.GetFirstSelected())

    def on_row_set(self, model, fqname, event_name, key):
        """
            A new rowset has arrived from the model.
        """
        if self.model.current_table is None: # the first call with no data
            return
        self.row_view.set_columns(
            [ (i.name, i.name) for i in self.model.current_table.columns],
        )
        self.row_view.handle_reset(model, fqname, event_name, key)

if "__main__" == __name__:
    URI = None

    if len(sys.argv) > 1:
        URI = sys.argv[1]

    MODEL = DBModel()
    APP = wx.App(redirect=False)
    FRAME = DBView(None, APP, "SQLAlchemy database viewer", MODEL)
    APP.SetTopWindow(FRAME)
    FRAME.Show(True)
    FRAME.Maximize(True)

    wx.CallAfter(MODEL.initialize, URI)

    APP.MainLoop()
