"""Utils."""

import numpy as _np


class DraggableText(object):
    """Draggable text annotation."""

    def __init__(self, canvas, ax, x, y, string, tol=50, **kwargs):
        """Initialize variables and set callbacks."""
        self.canvas = canvas
        self.ax = ax
        self.tol = tol
        self.text = self.ax.text(x, y, string, **kwargs)
        self.change_position = False
        self._set_callbacks()

    def _get_distance_from_point(self, x, y):
        bb = self.text.get_window_extent(renderer=self.canvas.renderer)
        xm = (bb.x1 + bb.x0)/2
        ym = (bb.y1 + bb.y0)/2
        return _np.sqrt((xm - x)**2 + (ym - y)**2)

    def _set_center_position(self, x, y):
        bb = self.text.get_window_extent(renderer=self.canvas.renderer)
        bb = bb.transformed(self.ax.transData.inverted())
        dx = bb.x1 - bb.x0
        dy = bb.y1 - bb.y0
        self.text.set_position((x - dx/2, y - dy/2))

    def _set_callbacks(self):
        def button_press_callback(event):
            if event.x is not None and event.y is not None:
                dist = self._get_distance_from_point(event.x, event.y)
                if dist < self.tol:
                    self.change_position = True

        def button_release_callback(event):
            self.change_position = False

        def motion_notify_callback(event):
            if not self.change_position:
                return
            if event.xdata is None and event.ydata is None:
                return
            self._set_center_position(event.xdata, event.ydata)
            self.canvas.draw()

        self.canvas.mpl_connect(
            'button_press_event', button_press_callback)
        self.canvas.mpl_connect(
            'button_release_event', button_release_callback)
        self.canvas.mpl_connect(
            'motion_notify_event', motion_notify_callback)


class DraggableLegend(object):
    """Draggable legend."""

    def __init__(self, canvas, ax, tol=50, **kwargs):
        """Initialize variables and set callbacks."""
        self.canvas = canvas
        self.ax = ax
        self.tol = tol
        self.legend = self.ax.legend(**kwargs)
        self.change_position = False
        self._set_callbacks()

    def _get_distance_from_point(self, x, y):
        bb = self.legend.get_window_extent(renderer=self.canvas.renderer)
        xm = (bb.x1 + bb.x0)/2
        ym = (bb.y1 + bb.y0)/2
        return _np.sqrt((xm - x)**2 + (ym - y)**2)

    def _set_center_position(self, x, y):
        bb = self.legend.get_window_extent(renderer=self.canvas.renderer)
        bb = bb.transformed(self.ax.transData.inverted())
        dx = bb.x1 - bb.x0
        dy = bb.y1 - bb.y0
        bb.x0 = x - dx/2
        bb.y0 = y - dy/2
        bb.x1 = bb.x0 + dx
        bb.y1 = bb.y0 + dy
        self.legend.set_bbox_to_anchor(bb, transform=self.ax.transData)

    def _set_callbacks(self):
        def button_press_callback(event):
            if event.x is not None and event.y is not None:
                dist = self._get_distance_from_point(event.x, event.y)
                if dist < self.tol:
                    self.change_position = True

        def button_release_callback(event):
            self.change_position = False

        def motion_notify_callback(event):
            if not self.change_position:
                return
            if event.xdata is None and event.ydata is None:
                return
            self._set_center_position(event.xdata, event.ydata)
            self.canvas.draw()

        self.canvas.mpl_connect(
            'button_press_event', button_press_callback)
        self.canvas.mpl_connect(
            'button_release_event', button_release_callback)
        self.canvas.mpl_connect(
            'motion_notify_event', motion_notify_callback)


def scientific_notation(value, error):
    """Return a string with value and error in scientific notation."""
    if value is None or error is None:
        return ''

    exponent = int('{:e}'.format(value).split('e')[-1])
    exponent_str = ' x E'+str(exponent)

    if exponent > 0:
        exponent = 0
    if exponent == 0:
        exponent_str = ''

    nr_digits = abs(int('{:e}'.format(error/10**exponent).split('e')[-1]))

    value_str = ('{:.'+str(nr_digits)+'f}').format(value/10**exponent)
    error_str = ('{:.'+str(nr_digits)+'f}').format(error/10**exponent)

    scientific_notation = ('(' + value_str + " " + chr(177) + " " +
                           error_str + ')' + exponent_str)

    return scientific_notation
