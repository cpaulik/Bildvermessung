import Tkinter as Tk
import Tkconstants
import tkFileDialog
import glob
import os


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
        self.polys.load_new_image(self.filelist[self.selectedfile])

    def next_image(self):
        self.selectedfile += 1
        if self.selectedfile >= len(self.filelist):
            print "Last File"
            self.selectedfile -= 1
        else:
            self.update_image()

    def prev_image(self):
        self.selectedfile -= 1
        if self.selectedfile < 0:
            print "First File"
            self.selectedfile += 1
        else:
            self.update_image()
