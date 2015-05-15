# -*- coding: utf-8 -*-
"""
This is an example to show how to build cross-GUI applications using
matplotlib event handling to interact with objects on the canvas

"""
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.text import Text
from matplotlib.patches import Polygon
from matplotlib.artist import Artist
from matplotlib.mlab import dist_point_to_segment
import matplotlib.pyplot as plt
from shapely.geometry import Polygon as SPolygon
import matplotlib.image as mpimg
import os


class PolygonInteractor(object):

    """
    An polygon editor.

    Key-bindings

      't' toggle vertex markers on and off.  When vertex markers are on,
          you can move them, delete them

      'd' delete the vertex under point

      'i' insert a vertex at point.  You must be within epsilon of the
          line connecting two existing vertices

    """

    showverts = True
    epsilon = 20  # max pixel distance to count as a vertex hit
    background = None

    def __init__(self, ax, poly, markerfacecolor='r', marker='o', label="inside",
                 mbutton=1):
        if poly.figure is None:
            raise RuntimeError(
                'You must first add the polygon to a figure or canvas before defining the interactor')
        self.ax = ax
        canvas = poly.figure.canvas
        self.poly = poly
        self.spoly = SPolygon(poly.get_xy())
        self.mbutton = mbutton
        coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
        x, y = zip(*coords)
        self.line = Line2D(
            x, y, marker=marker, color='w', markerfacecolor=markerfacecolor, animated=True)
        self.text = Text(
            self.spoly.centroid.x, self.spoly.centroid.y, text=label, animated=True,
            color='w', backgroundcolor='k')
        self.ax.add_artist(self.text)
        self.ax.add_line(self.line)
        # self._update_line(poly)
        self.control_pressed = False

        cid = self.poly.add_callback(self.poly_changed)
        self._ind = None  # the active vert

        self.connections = []
        self.connections.append(
            canvas.mpl_connect('draw_event', self.draw_callback))
        self.connections.append(
            canvas.mpl_connect('button_press_event', self.button_press_callback))
        self.connections.append(
            canvas.mpl_connect('key_press_event', self.key_press_callback))
        self.connections.append(
            canvas.mpl_connect('key_release_event', self.key_release_callback))
        # self.connections.append(
        #     canvas.mpl_connect('pick_event', self.pick_event_callback))
        self.connections.append(canvas.mpl_connect(
            'button_release_event', self.button_release_callback))
        self.connections.append(
            canvas.mpl_connect('motion_notify_event', self.motion_notify_callback))
        self.canvas = canvas

    @property
    def area(self):
        return self.spoly.area

    def draw_callback(self, event):
        self.ax.draw_artist(self.poly)
        self.ax.draw_artist(self.line)
        # update shapely polygon
        self.spoly = SPolygon(self.poly.get_xy())
        # update text coordinates
        self.text.set_x(self.spoly.centroid.x)
        self.text.set_y(self.spoly.centroid.y)
        self.ax.draw_artist(self.text)

    def poly_changed(self, poly):
        'this method is called whenever the polygon object is called'
        # only copy the artist props to the line (except visibility)
        vis = self.line.get_visible()
        Artist.update_from(self.line, poly)
        self.line.set_visible(vis)  # don't use the poly visibility state

    def get_ind_under_point(self, event, check_epsilon=True):
        'get the index of the vertex under point if within epsilon tolerance'

        # display coords
        xy = np.asarray(self.poly.xy)
        xyt = self.poly.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        indseq = np.nonzero(np.equal(d, np.amin(d)))[0]
        ind = indseq[0]

        if d[ind] >= self.epsilon and check_epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):
        'whenever a mouse button is pressed'
        if not self.showverts:
            return
        if event.inaxes == None:
            return
        if event.button not in [self.mbutton]:
            return
        if self.control_pressed:
            self.start_x = event.xdata
            self.start_y = event.ydata
            self.start_x0, self.start_y0 = self.poly.xy[
                :, 0], self.poly.xy[:, 1]
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        'whenever a mouse button is released'
        if not self.showverts:
            return
        if event.button not in [self.mbutton, 2]:
            return
        if event.button == 2:
            ind = self.get_ind_under_point(event)
            if ind is None:
                self.insert_point(event.x, event.y, event.xdata, event.ydata)
            else:
                self.poly.xy = [
                    tup for i, tup in enumerate(self.poly.xy) if i != ind]
                coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
                self.line.set_data(zip(*coords))
        self._ind = None
        self.canvas.draw()

    def key_press_callback(self, event):
        'whenever a key is pressed'
        if not event.inaxes:
            return
        if event.key == 't':
            self.showverts = not self.showverts
            self.line.set_visible(self.showverts)
            if not self.showverts:
                self._ind = None
        elif event.key == 'a':
            print self.area
        elif event.key == 'd':
            ind = self.get_ind_under_point(event)
            if ind is not None:
                self.poly.xy = [
                    tup for i, tup in enumerate(self.poly.xy) if i != ind]
                coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
                self.line.set_data(zip(*coords))
        elif event.key == 'i':
            # display coords
            self.insert_point(event.x, event.y, event.xdata, event.ydata)

        if event.key == 'control':
            self.control_pressed = True

        self.canvas.draw()

    def key_release_callback(self, event):
        if event.key == 'control':
            self.control_pressed = False
        self.canvas.draw()
        return

    def insert_point(self, x, y, xdata, ydata):
        coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
        xys = self.poly.get_transform().transform(coords)
        p = x, y  # display coords
        for i in range(len(xys) - 1):
            s0 = xys[i]
            s1 = xys[i + 1]
            d = dist_point_to_segment(p, s0, s1)
            if d <= self.epsilon:
                self.poly.xy = np.array(
                    list(coords[:i + 1]) +
                    [(xdata, ydata)] +
                    list(coords[i + 1:]))
                coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
                self.line.set_data(zip(*coords))
                break

    def motion_notify_callback(self, event):
        'on mouse movement'
        if not self.showverts:
            return
        if event.button not in [self.mbutton]:
            return
        if event.inaxes is None:
            return
        if self.control_pressed is False:
            if self._ind is None:
                x, y = event.xdata, event.ydata
                ind = self.get_ind_under_point(event, check_epsilon=False)

                self.poly.xy[ind] = x, y
                coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
                self.line.set_data(zip(*coords))
                # update shapely polygon
                self.spoly = SPolygon(self.poly.get_xy())
                # update text coordinates
                self.text.set_x(self.spoly.centroid.x)
                self.text.set_y(self.spoly.centroid.y)

                self.canvas.restore_region(self.background)
                self.ax.draw_artist(self.poly)
                self.ax.draw_artist(self.line)
                # self.ax.draw_artist(self.text)
                self.canvas.blit(self.ax.bbox)
                return
            x, y = event.xdata, event.ydata

            self.poly.xy[self._ind] = x, y
            coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
            self.line.set_data(zip(*coords))
            # update shapely polygon
            self.spoly = SPolygon(self.poly.get_xy())
            # update text coordinates
            self.text.set_x(self.spoly.centroid.x)
            self.text.set_y(self.spoly.centroid.y)

            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.poly)
            self.ax.draw_artist(self.line)
            # self.ax.draw_artist(self.text)
            self.canvas.blit(self.ax.bbox)
        else:
            if self.poly.contains_point((event.x, event.y)):
                offsetx = event.xdata - self.start_x
                offsety = event.ydata - self.start_y
                new_coords = np.vstack([self.start_x0 + offsetx,
                                        self.start_y0 + offsety])
                self.poly.xy = new_coords.T
                coords = np.vstack([self.poly.xy, self.poly.xy[0, :]])
                self.line.set_data(zip(*coords))
                self.canvas.restore_region(self.background)
                self.ax.draw_artist(self.poly)
                self.ax.draw_artist(self.line)
                self.ax.draw_artist(self.text)
                self.canvas.blit(self.ax.bbox)

    def remove(self):
        for connection in self.connections:
            self.canvas.mpl_disconnect(connection)

        self.poly.remove()
        self.line.remove()
        self.text.remove()


def show_image(ax, imgpath):
    im = mpimg.imread(imgpath)
    ax.clear()
    ax.imshow(im)


def sane_rect_coord(ax, xperc=[0.1, 0.4], yperc=[0.1, 0.9]):
    """
    calculate sane rectangular coordinates inside the axis limits

    Parameters
    ----------
    ax: matplotlib axis
        description
    xperc: list
        percentage of total axis x size to place the rectangle at
    yperc: list
        percentage of total axis y size to place the rectangle at

    Returns
    -------
    xs: list
        x coordinates
    ys: list
        y coordinates
    """
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xdist = xlim[1] - xlim[0]
    ydist = ylim[1] - ylim[0]

    xs = [xlim[0] + xperc[0] * xdist, xlim[0] + xperc[0] * xdist,
          xlim[0] + xperc[1] * xdist, xlim[0] + xperc[1] * xdist]
    ys = [ylim[0] + yperc[0] * ydist, ylim[0] + yperc[1] * ydist,
          ylim[0] + yperc[1] * ydist, ylim[0] + yperc[0] * ydist]

    return xs, ys


class TwoPolys(object):

    def __init__(self, fig, ax):

        self.ax = ax
        self.fig = fig

        xs, ys = sane_rect_coord(self.ax)
        poly = Polygon(
            list(zip(xs, ys)), color='r', closed=False, alpha=0.5, animated=True)
        self.ax.add_patch(poly)
        self.p1 = PolygonInteractor(self.ax, poly, label="Torso")

        xs1, ys1 = sane_rect_coord(self.ax, xperc=[0.6, 0.9])
        poly1 = Polygon(
            list(zip(xs1, ys1)), closed=False, color='b', alpha=0.5, animated=True)
        self.ax.add_patch(poly1)
        self.p2 = PolygonInteractor(self.ax, poly1, label="Gesamt", mbutton=3,
                                    markerfacecolor='b')
        # ax.add_line(p.line)

    def load_new_image(self, impath, x1=None, y1=None, x2=None, y2=None):
        self.p1.remove()
        self.p2.remove()
        show_image(self.ax, impath)

        xs, ys = sane_rect_coord(self.ax)
        if x1 is not None:
            xs = x1
        if y1 is not None:
            ys = y1
        poly = Polygon(
            list(zip(xs, ys)), color='r', closed=False, alpha=0.5, animated=True)
        self.ax.add_patch(poly)
        self.p1 = PolygonInteractor(self.ax, poly, label="Torso")

        xs1, ys1 = sane_rect_coord(self.ax, xperc=[0.6, 0.9])
        if x2 is not None:
            xs1 = x2
        if y2 is not None:
            ys1 = y2
        poly1 = Polygon(
            list(zip(xs1, ys1)), closed=False, color='b', alpha=0.5, animated=True)
        self.ax.add_patch(poly1)
        self.p2 = PolygonInteractor(self.ax, poly1, label="Gesamt", mbutton=3,
                                    markerfacecolor='b')
        self.ax.set_title(os.path.split(impath)[1])
        self.fig.canvas.draw()


if __name__ == '__main__':
    pass
