import Tkinter as Tk
import Tkconstants
import tkFileDialog
import glob
import os
import json


class ImageSelector(object):

    def __init__(self, root, polygons):

        # options for buttons
        button_opt = {'fill': Tkconstants.BOTH, 'padx': 5, 'pady': 5}

        self.polys = polygons
        # define buttons
        Tk.Button(root, text='askdirectory', command=self.askdirectory).pack(
            **button_opt)
        button = Tk.Button(master=root, text='->', command=self.next_image)
        button.pack(side=Tk.RIGHT)
        button = Tk.Button(master=root, text='<-', command=self.prev_image)
        button.pack(side=Tk.LEFT)
        self.filelist = []
        self.selectedfile = None
        self.dirname = None

    def askdirectory(self):
        """Returns a selected directoryname."""

        self.dirname = tkFileDialog.askdirectory()
        self.update_file_list(self.dirname)
        self.update_image()

    def update_file_list(self, dirname):
        self.filelist = []
        filetypes = ["*.png", "*.jpg"]
        for filetype in filetypes:
            self.filelist.extend(glob.glob(os.path.join(dirname, filetype)))

        self.filelist = sorted(self.filelist)
        self.selectedfile = 0

    def update_image(self):
        print "load", self.filelist[self.selectedfile]
        x1, y1, x2, y2 = self.get_json_coordinates()
        self.polys.load_new_image(
            self.filelist[self.selectedfile], x1=x1, y1=y1, x2=x2, y2=y2)

    def get_current_json_fname(self):
        current_fname = self.filelist[self.selectedfile]
        path, fname = os.path.split(current_fname)
        fname, ext = os.path.splitext(fname)
        return os.path.join(path, fname + ".json")

    def get_json_coordinates(self):
        """
        load json coordinates from file if a .json file with the same
        name as the image exists.
        """

        if os.path.exists(self.get_current_json_fname()):
            x1, y1, x2, y2 = self.load_current_json_coord()
        else:
            x1, y1, x2, y2 = None, None, None, None

        return x1, y1, x2, y2

    def load_current_json_coord(self):

        fid = open(self.get_current_json_fname(), mode='r')
        data = json.load(fid)
        return data['x1'], data['y1'], data['x2'], data['y2']

    def save_current_json_coord(self):

        x1 = list(self.polys.p1.poly.get_xy()[:, 0])
        y1 = list(self.polys.p1.poly.get_xy()[:, 1])
        x2 = list(self.polys.p2.poly.get_xy()[:, 0])
        y2 = list(self.polys.p2.poly.get_xy()[:, 1])
        area_torso = self.polys.p1.area
        area_total = self.polys.p2.area
        fid = open(self.get_current_json_fname(), mode='w')
        json.dump({'x1': x1, 'y1': y1,
                   'x2': x2, 'y2': y2,
                   'area_torso': area_torso,
                   'area_total': area_total}, fid)

    def next_image(self):
        self.save_current_json_coord()
        self.selectedfile += 1
        if self.selectedfile >= len(self.filelist):
            print "Last File"
            self.selectedfile -= 1
        else:
            self.update_image()

    def prev_image(self):
        self.save_current_json_coord()
        self.selectedfile -= 1
        if self.selectedfile < 0:
            print "First File"
            self.selectedfile += 1
        else:
            self.update_image()
