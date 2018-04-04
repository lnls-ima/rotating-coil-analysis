"""Matplotlib Widget."""

from PyQt5.QtWidgets import (
    QWidget as _QWidget,
    QVBoxLayout as _QVBoxLayout,
    QSizePolicy as _QSizePolicy)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as _FigCanvas,
    NavigationToolbar2QT as _Toolbar)
from matplotlib.figure import Figure as _Figure


class MplCanvas(_FigCanvas):
    """Matplotlib Widget Canvas."""

    def __init__(self):
        """Initialize figure canvas."""
        self.fig = _Figure()
        self.fig.patch.set_facecolor('1')
        self.ax = self.fig.add_subplot(111, adjustable='datalim')
        _FigCanvas.__init__(self, self.fig)
        _FigCanvas.setSizePolicy(
            self, _QSizePolicy.Expanding, _QSizePolicy.Expanding)
        _FigCanvas.updateGeometry(self)
        self.ax.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
        self.fig.tight_layout()
        self.fig.canvas.draw()


class MplWidget(_QWidget):
    """Matplotlib Widget."""

    def __init__(self, parent=None):
        """Initialize widget and add figure canvas."""
        super(MplWidget, self).__init__(parent)
        self.canvas = MplCanvas()
        self.vbl = _QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.toolbar = _Toolbar(self.canvas, self)
        self.vbl.addWidget(self.toolbar)
        self.setLayout(self.vbl)
