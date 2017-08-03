"""Matplotlib Widget."""

from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as _FigCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as _Toolbar
from matplotlib.figure import Figure


class MplCanvas(_FigCanvas):
    """Matplotlib Widget Canvas."""

    def __init__(self):
        """Initialize figure canvas."""
        self.fig = Figure()
        self.fig.patch.set_facecolor('1')
        self.ax = self.fig.add_subplot(111, adjustable='datalim')
        _FigCanvas.__init__(self, self.fig)
        _FigCanvas.setSizePolicy(
            self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        _FigCanvas.updateGeometry(self)

        self.ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')

        self.fig.tight_layout()
        self.fig.canvas.draw()


class matplotlibWidget(QtGui.QWidget):
    """Matplotlib Widget."""

    def __init__(self, parent=None):
        """Initialize widget and add figure canvas."""
        QtGui.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.toolbar = _Toolbar(self.canvas, self)
        self.vbl.addWidget(self.toolbar)
        self.setLayout(self.vbl)
