# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'graph_dialog.ui'
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

class Ui_FormGraph(object):
    def setupUi(self, FormGraph):
        FormGraph.setObjectName(_fromUtf8("FormGraph"))
        FormGraph.resize(875, 489)
        self.gridLayout = QtGui.QGridLayout(FormGraph)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.wt_multipoles = matplotlibWidget(FormGraph)
        self.wt_multipoles.setObjectName(_fromUtf8("wt_multipoles"))
        self.gridLayout.addWidget(self.wt_multipoles, 0, 0, 1, 1)

        self.retranslateUi(FormGraph)
        QtCore.QMetaObject.connectSlotsByName(FormGraph)

    def retranslateUi(self, FormGraph):
        FormGraph.setWindowTitle(_translate("FormGraph", "Graph", None))

from PlotGUI import matplotlibWidget
