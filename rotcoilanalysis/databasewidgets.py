"""Database tables widgets."""

import os.path as _path
import sqlite3 as _sqlite3
from PyQt5.QtCore import Qt as _Qt
from PyQt5.QtGui import QFont as _QFont
from PyQt5.QtWidgets import (
    QTabWidget as _QTabWidget,
    QTableWidget as _QTableWidget,
    QTableWidgetItem as _QTableWidgetItem)

_basepath = _path.dirname(_path.abspath(__file__))
_fontsize = 15


class DatabaseTab(_QTabWidget):
    """Tab with database table widgets."""

    def __init__(self, parent=None):
        """Setup the ui."""
        super(DatabaseTab, self).__init__(parent)

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


class DatabaseTable(_QTableWidget):
    """Database table widget."""

    def __init__(self, parent=None):
        """Setup the ui."""
        super(DatabaseTable, self).__init__(parent)

        font = _QFont()
        font.setPixelSize(_fontsize)
        font.setBold(False)
        self.setFont(font)
        self.setAlternatingRowColors(True)  # Added by Vitor
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(120)

        self.database_filename = None
        self.table_name = None
        self.column_names = []
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

        self.blockSignals(True)
        self.setColumnCount(0)
        self.setRowCount(0)

        con = _sqlite3.connect(self.database_filename)
        cur = con.cursor()
        command = 'SELECT * FROM ' + self.table_name
        cur.execute(command)

        self.column_names = [description[0] for description in cur.description]
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)

        command = 'SELECT * FROM ' + self.table_name
        data = cur.execute(command).fetchall()

        if len(data) > 0:
            self.data_types = [
                type(data[0][col]) for col in range(len(self.column_names))]
            # Added by Vitor:
            if self.table_name == 'measurements':
                self.data_types[35] = str
            elif self.table_name == 'sets_of_measurements':
                self.data_types[2] = str

        self.setRowCount(1)
        for j in range(len(self.column_names)):
            self.setItem(0, j, _QTableWidgetItem(''))
        self.addRowsToTable(data)

        self.blockSignals(False)
        self.itemChanged.connect(self.filterColumn)
        self.itemSelectionChanged.connect(self.selectLine)

    def addRowsToTable(self, data):
        """Add rows to table."""
        if len(self.column_names) == 0:
            return

        self.setRowCount(len(data) + 1)
        for j in range(len(self.column_names)):
            for i in range(len(data)):
                item = _QTableWidgetItem(str(data[i][j]))
                item.setFlags(_Qt.ItemIsSelectable | _Qt.ItemIsEnabled)
                self.setItem(i + 1, j, item)

    def scrollDown(self):
        """Scroll down."""
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def selectLine(self):
        """Select the entire line."""
        if (self.rowCount() == 0
           or self.columnCount() == 0
           or len(self.column_names) == 0 or len(self.data_types) == 0):
            return

        selected = self.selectedItems()
        rows = [s.row() for s in selected]

        if 0 in rows:
            return

        self.blockSignals(True)
        for row in rows:
            for col in range(len(self.column_names)):
                item = self.item(row, col)
                if item and not item.isSelected():
                    item.setSelected(True)
        self.blockSignals(False)

    def filterColumn(self, item):
        """Apply column filter to data."""
        if (self.rowCount() == 0
           or self.columnCount() == 0
           or len(self.column_names) == 0 or len(self.data_types) == 0
           or item.row() != 0):
            return

        con = _sqlite3.connect(self.database_filename)
        cur = con.cursor()
        command = 'SELECT * FROM ' + self.table_name

        and_flag = False
        filters = []
        for idx in range(len(self.column_names)):
            filters.append(self.item(0, idx).text())

        if any(filt != '' for filt in filters):
            command = command + ' WHERE '

        for idx in range(len(self.column_names)):
            column = self.column_names[idx]
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
        selected = self.selectedItems()
        rows = [s.row() for s in selected if s.row() != 0]

        selected_ids = []
        for row in rows:
            if 'id_0' in self.column_names and 'id_f' in self.column_names:
                idx_id_0 = self.column_names.index('id_0')
                idx_id_f = self.column_names.index('id_f')
                id_0 = int(self.item(row, idx_id_0).text())
                id_f = int(self.item(row, idx_id_f).text())
                for idn in range(id_0, id_f + 1):
                    selected_ids.append(idn)
            elif ('id_0' not in self.column_names
                  and 'id_f' not in self.column_names):
                idn = int(self.item(row, 0).text())
                selected_ids.append(idn)

        return selected_ids
