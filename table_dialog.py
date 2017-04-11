# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'table_dialog.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_FormTable(object):
    def setupUi(self, FormTable):
        FormTable.setObjectName(_fromUtf8("FormTable"))
        FormTable.resize(957, 523)
        self.gridLayout = QtGui.QGridLayout(FormTable)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tb_general = QtGui.QTableWidget(FormTable)
        self.tb_general.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tb_general.setObjectName(_fromUtf8("tb_general"))
        self.tb_general.setColumnCount(0)
        self.tb_general.setRowCount(0)
        self.gridLayout.addWidget(self.tb_general, 1, 0, 1, 1)
        self.pb_copy_to_clipboard = QtGui.QPushButton(FormTable)
        self.pb_copy_to_clipboard.setObjectName(_fromUtf8("pb_copy_to_clipboard"))
        self.gridLayout.addWidget(self.pb_copy_to_clipboard, 0, 0, 1, 1)

        self.retranslateUi(FormTable)
        QtCore.QMetaObject.connectSlotsByName(FormTable)

    def retranslateUi(self, FormTable):
        FormTable.setWindowTitle(_translate("FormTable", "Table", None))
        self.pb_copy_to_clipboard.setText(_translate("FormTable", "Copiar para área de transferência", None))

