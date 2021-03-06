# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os
import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler


from matplotlib.figure import Figure

from polygon_interactor import TwoPolys, PolygonInteractor
from filedialog import ImageSelector

import sys
if sys.version_info[0] < 3:
    import Tkinter as Tk
else:
    import tkinter as Tk

import tkFileDialog

root = Tk.Tk()
root.wm_title("Bilderbuchvermessung")


f = Figure()
a = f.add_subplot(111)


# a tk.DrawingArea
canvas = FigureCanvasTkAgg(f, master=root)
polys = TwoPolys(f, a)
canvas.show()
canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)


def on_key_event(event):
    print('you pressed %s' % event.key)
    if event.key == 'enter':
        dirdialog.next_image()
    if event.key == 'right':
        dirdialog.next_image()
    if event.key == 'left':
        dirdialog.prev_image()

keypress_cbid = canvas.mpl_connect('key_press_event', on_key_event)


def global_draw_callback(event):
    PolygonInteractor.background = canvas.copy_from_bbox(a.bbox)
    canvas.blit(a.bbox)


draw_cbid = canvas.mpl_connect('draw_event', global_draw_callback)


def _quit():
    dirdialog.save_current_json_coord()
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate

button = Tk.Button(master=root, text='Quit', command=_quit)
button.pack(side=Tk.BOTTOM)


dirdialog = ImageSelector(root, polys)

dirdialog.askdirectory()

Tk.mainloop()
# If you put root.destroy() here, it will cause an error if
# the window is closed with the window manager.
