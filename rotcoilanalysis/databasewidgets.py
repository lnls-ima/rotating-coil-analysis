"""Database tables widgets."""

import os.path as _path
import sqlite3 as _sqlite3
import PyQt5.uic as _uic
from PyQt5.QtCore import Qt as _Qt
from PyQt5.QtGui import QFont as _QFont
from PyQt5.QtWidgets import (
    QTabWidget as _QTabWidget,
    QWidget as _QWidget,
    QTableWidgetItem as _QTableWidgetItem)


_basepath = _path.dirname(_path.abspath(__file__))
_fontsize = 15


class DatabaseTab(_QTabWidget):
    """Database tables widget."""

    def __init__(self, parent=None):
        """Setup the ui."""
        super(DatabaseTab, self).__init__(parent)

        # setup the ui
        uifile = _path.join(_path.join(_basepath, 'ui'), 'databasetab.ui')
        self.ui = _uic.loadUi(uifile, self)

        font = _QFont()
        font.setPixelSize(_fontsize)
        font.setBold(False)
        self.setFont(font)

        self.clear()
        self.database_filename = None
        self.tables = []

    def loadDatabase(self, database_filename):
        """Load database."""
        self.database_filename = database_filename
        con = _sqlite3.connect(self.database_filename)
        cur = con.cursor()
        res = cur.execute("SELECT name FROM sqlite_master WHERE type='table';")

        for r in res:
            table_name = r[0]
            if table_name != "sqlite_sequence" and table_name != 'failures':
                table = DatabaseTable(self)
                table.loadDatabaseTable(
                    database_filename=self.database_filename,
                    table_name=table_name)
                self.tables.append(table)
                self.addTab(table, table_name)

    def scrollDownTables(self):
        """Scroll down all tables."""
        for idx in range(len(self.tables)):
            self.setCurrentIndex(idx)
            self.tables[idx].scrollDown()

    def clearDatabase(self):
        """Clear database."""
        self.database_filename = None
        self.tables = []
        self.clear()


class DatabaseTable(_QWidget):
    """Database table widget."""

    def __init__(self, parent=None):
        """Setup the ui."""
        super(DatabaseTable, self).__init__(parent)

        # setup the ui
        uifile = _path.join(_path.join(_basepath, 'ui'), 'databasetable.ui')
        self.ui = _uic.loadUi(uifile, self)

        font = _QFont()
        font.setPixelSize(_fontsize)
        font.setBold(False)
        self.ui.database_table.setFont(font)

        self.database_filename = None
        self.table_name = None
        self.columns = []
        self.data_types = []

    def loadDatabaseTable(self, database_filename, table_name):
        """Set database filename and table name."""
        self.database_filename = database_filename
        self.table_name = table_name
        self.updateTable()

    def updateTable(self):
        """Update table."""
        if self.database_filename is None or self.table_name is None:
            return

        self.ui.database_table.blockSignals(True)
        self.ui.database_table.setColumnCount(0)
        self.ui.database_table.setRowCount(0)

        con = _sqlite3.connect(self.database_filename)
        cur = con.cursor()
        command = 'SELECT * FROM ' + self.table_name
        cur.execute(command)

        self.columns = [description[0] for description in cur.description]
        self.ui.database_table.setColumnCount(len(self.columns))
        self.ui.database_table.setHorizontalHeaderLabels(self.columns)

        command = 'SELECT * FROM ' + self.table_name
        data = cur.execute(command).fetchall()

        if len(data) > 0:
            self.data_types = [
                type(data[0][col]) for col in range(len(self.columns))]

        self.ui.database_table.setRowCount(1)
        for j in range(len(self.columns)):
            self.ui.database_table.setItem(0, j, _QTableWidgetItem(''))
        self.addRowsToTable(data)

        self.ui.database_table.blockSignals(False)
        self.ui.database_table.itemChanged.connect(self.filterColumn)

    def addRowsToTable(self, data):
        """Add rows to table."""
        if len(self.columns) == 0:
            return

        self.ui.database_table.setRowCount(len(data) + 1)
        for j in range(len(self.columns)):
            for i in range(len(data)):
                item = _QTableWidgetItem(str(data[i][j]))
                item.setFlags(_Qt.ItemIsSelectable | _Qt.ItemIsEnabled)
                self.ui.database_table.setItem(i + 1, j, item)

    def scrollDown(self):
        """Scroll down."""
        vbar = self.ui.database_table.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def filterColumn(self, item):
        """Apply column filter to data."""
        if (self.database_table.rowCount() == 0
           or self.database_table.columnCount() == 0
           or len(self.columns) == 0 or len(self.data_types) == 0
           or item.row() != 0):
            return

        con = _sqlite3.connect(self.database_filename)
        cur = con.cursor()
        command = 'SELECT * FROM ' + self.table_name

        and_flag = False
        filters = []
        for idx in range(len(self.columns)):
            filters.append(self.ui.database_table.item(0, idx).text())

        if any(filt != '' for filt in filters):
            command = command + ' WHERE '

        for idx in range(len(self.columns)):
            column = self.columns[idx]
            data_type = self.data_types[idx]
            filt = filters[idx]

            if filt != '':

                if and_flag:
                    command = command + ' AND '
                and_flag = True

                if data_type == str:
                    command = command + column + ' LIKE "%' + filt + '%"'
                else:
                    if '~' in filt:
                        fs = filt.split('~')
                        if len(fs) == 2:
                            command = command + column + ' >= ' + fs[0]
                            command = command + ' AND '
                            command = command + column + ' <= ' + fs[1]
                    else:
                        try:
                            value = data_type(filt)
                            command = command + column + ' = ' + str(value)
                        except ValueError:
                            command = command + column + ' ' + filt

        try:
            cur.execute(command)
        except Exception:
            pass

        data = cur.fetchall()
        self.addRowsToTable(data)

    def getSelectedIDs(self):
        """Get selected IDs."""
        selected = self.ui.database_table.selectedItems()
        rows = [s.row() for s in selected if s.row() != 0]

        selected_ids = []
        for row in rows:
            if 'id_0' in self.columns and 'id_f' in self.columns:
                idx_id_0 = self.columns.index('id_0')
                idx_id_f = self.columns.index('id_f')
                id_0 = int(self.ui.database_table.item(row, idx_id_0).text())
                id_f = int(self.ui.database_table.item(row, idx_id_f).text())
                for idn in range(id_0, id_f + 1):
                    selected_ids.append(idn)
            elif 'id_0' not in self.columns and 'id_f' not in self.columns:
                idn = int(self.ui.database_table.item(row, 0).text())
                selected_ids.append(idn)

        return selected_ids
