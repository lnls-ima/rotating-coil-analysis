"""Database tables widgets."""

import os.path as _path
import sqlite3 as _sqlite3
import numpy as _np
from PyQt5.QtCore import Qt as _Qt
from PyQt5.QtGui import QFont as _QFont
from PyQt5.QtWidgets import (
    QWidget as _QWidget,
    QLabel as _QLabel,
    QTabWidget as _QTabWidget,
    QTableWidget as _QTableWidget,
    QTableWidgetItem as _QTableWidgetItem,
    QVBoxLayout as _QVBoxLayout,
    QHBoxLayout as _QHBoxLayout,
    QSpinBox as _QSpinBox,
    QAbstractItemView as _QAbstractItemView,
    )

_basepath = _path.dirname(_path.abspath(__file__))
_fontsize = 15
_max_number_rows = 1000
_max_str_size = 1000


class DatabaseTab(_QTabWidget):
    """Tab with database table widgets."""

    def __init__(self, parent=None):
        """Setup the ui."""
        super().__init__(parent)

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
                tab = _QWidget()
                vlayout = _QVBoxLayout()
                hlayout = _QHBoxLayout()

                initial_id_la = _QLabel("Initial ID:")
                initial_id_sb = _QSpinBox()
                initial_id_sb.setMinimumWidth(100)
                initial_id_sb.setButtonSymbols(2)
                hlayout.addStretch(0)
                hlayout.addWidget(initial_id_la)
                hlayout.addWidget(initial_id_sb)
                hlayout.addSpacing(30)

                number_rows_la = _QLabel("Number of rows:")
                number_rows_sb = _QSpinBox()
                number_rows_sb.setMinimumWidth(100)
                number_rows_sb.setButtonSymbols(2)
                number_rows_sb.setReadOnly(True)
                hlayout.addWidget(number_rows_la)
                hlayout.addWidget(number_rows_sb)
                hlayout.addSpacing(30)

                max_number_rows_la = _QLabel("Maximum number of rows:")
                max_number_rows_sb = _QSpinBox()
                max_number_rows_sb.setMinimumWidth(100)
                max_number_rows_sb.setButtonSymbols(2)
                max_number_rows_sb.setReadOnly(True)
                hlayout.addWidget(max_number_rows_la)
                hlayout.addWidget(max_number_rows_sb)

                table.loadDatabaseTable(
                    self.database_filename,
                    table_name,
                    initial_id_sb,
                    number_rows_sb,
                    max_number_rows_sb)

                vlayout.addWidget(table)
                vlayout.addLayout(hlayout)
                tab.setLayout(vlayout)

                self.tables.append(table)
                self.addTab(tab, table_name)

    def scrollDownTables(self):
        """Scroll down all tables."""
        for idx in range(len(self.tables)):
            self.setCurrentIndex(idx)
            self.tables[idx].scrollDown()

    def clearDatabase(self):
        """Clear database."""
        ntabs = self.count()
        for idx in range(ntabs):
            self.removeTab(idx)
            self.tables[idx].deleteLater()
        self.database_filename = None
        self.tables = []
        self.clear()


class DatabaseTable(_QTableWidget):
    """Database table widget."""

    _datatype_dict = {
        'INTEGER': int,
        'REAL': float,
        'TEXT': str,
        }

    _hidden_columns = [
        'read_data',
        'raw_curve',
        ]

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setDefaultSectionSize(120)

        self.database = None
        self.table_name = None
        self.column_names = []
        self.data_types = []
        self.data = []
        self.initial_table_id = None
        self.initial_id_sb = None
        self.number_rows_sb = None
        self.max_number_rows_sb = None

    def changeInitialID(self):
        """Change initial ID."""
        initial_id = self.initial_id_sb.value()
        self.filterColumn(initial_id=initial_id)

    def loadDatabaseTable(
            self, database, table_name,
            initial_id_sb, number_rows_sb, max_number_rows_sb):
        """Set database filename and table name."""
        self.database = database
        self.table_name = table_name

        self.initial_id_sb = initial_id_sb
        self.initial_id_sb.editingFinished.connect(self.changeInitialID)

        self.number_rows_sb = number_rows_sb
        self.number_rows_sb.setMaximum(_max_number_rows)

        self.max_number_rows_sb = max_number_rows_sb
        self.max_number_rows_sb.setMaximum(_max_number_rows)

        self.updateTable()

    def updateTable(self):
        """Update table."""
        if self.database is None or self.table_name is None:
            return
        
        self.blockSignals(True)
        self.clearContents()
        self.setColumnCount(0)
        self.setRowCount(0)

        con = _sqlite3.connect(self.database)
        cur = con.cursor()

        cmd = "PRAGMA TABLE_INFO({0})".format(self.table_name)
        cur.execute(cmd)
        table_info = cur.fetchall()
        
        self.column_names = []
        self.data_types = []
        for ti in table_info:
            column_name = ti[1]
            column_type = ti[2]
            if column_name not in self._hidden_columns:
                self.column_names.append(column_name)
                self.data_types.append(self._datatype_dict[column_type])
               
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)

        self.setRowCount(1)
        for j in range(len(self.column_names)):
            self.setItem(0, j, _QTableWidgetItem(''))
  
        column_names_str = ''
        for col_name in self.column_names:
            column_names_str = column_names_str + '"{0:s}", '.format(col_name)
        column_names_str = column_names_str[:-2]

        cmd = 'SELECT * FROM (SELECT {0:s} FROM {1:s} ORDER BY id DESC LIMIT {2:d}) ORDER BY id ASC'.format(
             column_names_str, self.table_name, _max_number_rows)
        data = cur.execute(cmd).fetchall()

        if len(data) > 0:
            cmd = 'SELECT MIN(id) FROM {0}'.format(self.table_name)
            min_idn = cur.execute(cmd).fetchone()[0]
            self.initial_id_sb.setMinimum(min_idn)

            cmd = 'SELECT MAX(id) FROM {0}'.format(self.table_name)
            max_idn = cur.execute(cmd).fetchone()[0]               
            self.initial_id_sb.setMaximum(max_idn)
            
            self.max_number_rows_sb.setValue(len(data))
            self.data = data[:]
            self.addRowsToTable(data)
        else:
            self.initial_id_sb.setMinimum(0)
            self.initial_id_sb.setMaximum(0)
            self.max_number_rows_sb.setValue(0)
        
        self.setSelectionBehavior(_QAbstractItemView.SelectRows)
        self.blockSignals(False)
        self.itemChanged.connect(self.filterChanged)
        self.itemSelectionChanged.connect(self.selectLine)

    def addRowsToTable(self, data):
        """Add rows to table."""
        if len(self.column_names) == 0:
            return

        self.setRowCount(1)

        if len(data) > self.max_number_rows_sb.value():
            tabledata = data[-self.max_number_rows_sb.value()::]
        else:
            tabledata = data

        if len(tabledata) == 0:
            return

        self.initial_id_sb.setValue(int(tabledata[0][0]))
        self.setRowCount(len(tabledata) + 1)
        self.number_rows_sb.setValue(len(tabledata))
        self.initial_table_id = tabledata[0][0]

        for j in range(len(self.column_names)):
            for i in range(len(tabledata)):
                item_str = str(tabledata[i][j])
                if len(item_str) > _max_str_size:
                    item_str = item_str[:10] + '...'
                item = _QTableWidgetItem(item_str)
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
            self.setSelectionBehavior(_QAbstractItemView.SelectItems)
        else:
            self.setSelectionBehavior(_QAbstractItemView.SelectRows)

    def filterChanged(self, item):
        """Apply column filter to data."""
        if item.row() == 0:
            self.filterColumn()

    def filterColumn(self, initial_id=None):
        """Apply column filter to data."""
        if (self.rowCount() == 0
           or self.columnCount() == 0
           or len(self.column_names) == 0 or len(self.data_types) == 0):
            return
        
        try:
            con = _sqlite3.connect(self.database)
            cur = con.cursor()
            column_names_str = ''
            for col_name in self.column_names:
                column_names_str = column_names_str + '"{0:s}", '.format(col_name)
            column_names_str = column_names_str[:-2]
            cmd = 'SELECT {0:s} FROM {1:s}'.format(
                column_names_str, self.table_name)

            and_flag = False
            filters = []
            for idx in range(len(self.column_names)):
                filters.append(self.item(0, idx).text())
    
            if any(filt != '' for filt in filters):
                cmd = cmd + ' WHERE '
    
            for idx in range(len(self.column_names)):
                column = self.column_names[idx]
                data_type = self.data_types[idx]
                filt = filters[idx]
    
                if filt != '':
    
                    if and_flag:
                        cmd = cmd + ' AND '
                    and_flag = True
    
                    if data_type == str:
                        cmd = cmd + column + ' LIKE "%' + filt + '%"'
                    else:
                        if '~' in filt:
                            fs = filt.split('~')
                            if len(fs) == 2:
                                cmd = cmd + column + ' >= ' + fs[0]
                                cmd = cmd + ' AND '
                                cmd = cmd + column + ' <= ' + fs[1]
                        elif filt.lower() == 'none' or filt.lower() == 'null':
                            cmd = cmd + column + ' IS NULL'
                        else:
                            try:
                                value = data_type(filt)
                                cmd = cmd + column + ' = ' + str(value)
                            except ValueError:
                                cmd = cmd + column + ' ' + filt
    
            if initial_id is not None:
                if 'WHERE' in cmd:
                    cmd = 'SELECT * FROM (' + cmd + ' AND id >= {0:d} LIMIT {1:d})'.format(
                        initial_id, _max_number_rows)
                else:
                    cmd = 'SELECT * FROM (' + cmd + ' WHERE id >= {0:d} LIMIT {1:d})'.format(
                        initial_id, _max_number_rows)
    
            else:
                cmd = 'SELECT * FROM (' + cmd + ' ORDER BY id DESC LIMIT {0:d}) ORDER BY id ASC'.format(
                    _max_number_rows)
        
            cur.execute(cmd)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            pass

        data = cur.fetchall()
        self.data = data[:]
        self.addRowsToTable(data)

    def getSelectedIDs(self):
        """Get selected IDs."""
        selected = self.selectedItems()
        rows = [s.row() for s in selected if s.row() != 0]
        rows = _np.unique(rows)

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
