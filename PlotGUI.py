from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure()
        self.fig.patch.set_facecolor('1')
        self.ax = self.fig.add_subplot(111, adjustable='datalim')
##        self.bx = self.fig.add_subplot(111, adjustable='datalim')
#         self.bx = self.ax.twinx()
#         self.ay = self.fig.add_subplot(312)
#         self.by = self.ay.twinx()
#         self.az = self.fig.add_subplot(313)
#         self.bz = self.az.twinx()
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.ax.ticklabel_format(style='sci',scilimits=(0,0),axis='y')

        self.fig.tight_layout()
        self.fig.canvas.draw()

class matplotlibWidget(QtGui.QWidget):
    def __init__(self, parent = None):
        QtGui.QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        self.vbl = QtGui.QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vbl.addWidget(self.toolbar)        
        self.setLayout(self.vbl)
