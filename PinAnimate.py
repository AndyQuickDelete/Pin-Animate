import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

import os, time
import imageio.v2 as imageio
from pathlib import Path
from PIL import Image
from datetime import datetime
#import cv2
#import numpy as np

desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

class PinAnimateWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pin Animate")
        self.set_border_width(1)
        self.set_default_size(640, 480)
        
        self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(os.getcwd() + '\\logo.png')
        self.set_default_icon(self.pixbuf)

        self.grid = Gtk.Grid()
        
        self.entry = Gtk.Entry()
        self.entry.set_text(desktop)
        self.entry.set_hexpand(True)
        self.grid.add(self.entry)

        self.open_button = Gtk.Button(label="Choose Images")
        self.open_button.connect("clicked", self.open_location)
        self.grid.add(self.open_button)

        self.save_button = Gtk.Button(label="Export as Gif")
        self.save_button.connect("clicked", self.save_as_gif)
        self.grid.add(self.save_button)
        
        self.export_button = Gtk.Button(label="Export as Video")
        self.export_button.connect("clicked", self.save_as_video)
        self.grid.add(self.export_button)
        
        self.prev_button = Gtk.Button(label="Preview")
        self.prev_button.connect("clicked", self.preview_image)
        self.grid.add(self.prev_button)

        self.fps = Gtk.Entry()
        self.fps.set_text("24")
        self.fps.set_hexpand(True)
        self.grid.attach(self.fps, 0, 1, 1, 1)

        self.label = Gtk.Label(label="FPS")
        self.grid.attach(self.label, 1, 1, 1, 1)
        
        self.duration = Gtk.Entry()
        self.duration.set_text("0.2")
        self.duration.set_width_chars(15)
        self.grid.attach(self.duration, 2, 1, 1, 1)

        self.label = Gtk.Label(label="Duration")
        self.grid.attach(self.label, 3, 1, 1, 1) 

        self.help_button = Gtk.Button(label="Help/Info")
        self.help_button.connect("clicked", self.help_user)
        self.grid.attach(self.help_button, 4, 1, 1, 1)

        self.model = Gtk.ListStore(str, str)    
        self.treeView = Gtk.TreeView()

        for i, column_title in enumerate(["Image Filenames", "Image Sizes"]):
            self.renderer = Gtk.CellRendererText()
            self.column = Gtk.TreeViewColumn(column_title, self.renderer, text=i)
            self.treeView.append_column(self.column)
        
        self.treeView.set_model(self.model)
        self.treeView.set_hexpand(True)
        
        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)        
        self.grid.attach(self.scrollable_treelist, 0, 2, 5, 1)
        self.scrollable_treelist.add(self.treeView)

        self.move_up = Gtk.Button(label="Move Up")
        self.move_up.connect("clicked", self.move_selected_items_up)
        self.grid.attach(self.move_up, 3, 3, 1, 1)
        
        self.move_down = Gtk.Button(label="Move Down")
        self.move_down.connect("clicked", self.move_selected_items_down)
        self.grid.attach(self.move_down, 4, 3, 1, 1)

        ### TREEVIEW SELECT ##
        self.treeselect = self.treeView.get_selection()
        self.treeselect.connect("changed", self.show_image)

        self.add(self.grid)
        self.show_all()

    def move_selected_items_up(self, treeView):
        selection = self.treeView.get_selection()
        model, selected_paths = selection.get_selected_rows()
        for path in selected_paths:
            index_above = path[0]-1
            if index_above < 0:
                return
            model.move_before(model.get_iter(path), model.get_iter((index_above,)))
   
    def move_selected_items_down(self, treeView):            
        selection = self.treeView.get_selection()
        model, selected_paths = selection.get_selected_rows()
        for path in reversed(selected_paths):
            index_below = path[0]+1
            if index_below >= len(model):
                return
            model.move_after(model.get_iter(path), model.get_iter((index_below,)))

    def show_image(self, treeView):
        selection = self.treeView.get_selection()
        model, row = selection.get_selected()
        selected = model[row][0]

        self.img = Gtk.Image()
        self.img.set_from_file(selected)
        self.grid.attach(self.img, 5, 0, 4, 4)
        self.img.show()

        GLib.timeout_add(1000, self.img.hide)

    def open_location(self, open_button):
        dialog = Gtk.FileChooserDialog(
            title="Please choose a folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Select", Gtk.ResponseType.OK
        )
        dialog.set_default_size(360, 180)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.directory = dialog.get_filename()

            self.entry.set_text("")
            self.entry.set_text(dialog.get_filename())

            self.image_path = Path(self.directory)
            self.images = list(self.image_path.glob('*.png'))
            image_list = []

            self.model.clear()
       
            for file_name in self.images:
                image = Image.open(str(file_name))
                width, height = image.size
                ImageSizes = "Width: %spx - Height: %spx" % (width, height)
                    
                image_list.append((str(file_name), ImageSizes))
            for image_ref in image_list:
                self.model.append(list(image_ref))
        elif response == Gtk.ResponseType.CANCEL:
            pass

        dialog.destroy()

    def save_as_gif(self, save_button):   
        fmt = '%Y-%m-%d_%H.%M.%S'
        now = datetime.now()
        current_time = now.strftime(fmt)

        rows = self.treeView.get_model()
            
        image_list = []
        for row in rows:
            #print(''.join([str(elem) for elem in row[0]]))
            file_name = ''.join([str(elem) for elem in row[0]])
            image_list.append(imageio.imread(file_name))

        fps = float(self.fps.get_text())
        duration = float(self.duration.get_text())

        out_filename = desktop + "\\" + 'PinAnimatedImages-%s.gif' % current_time    
        imageio.mimwrite(out_filename, image_list, fps=fps, duration=duration)

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Your animated gif has been created!",
        )

        dialog.format_secondary_text(
            "Your work has been saved to your Desktop folder."
        )
        
        dialog.run()
        dialog.destroy()

    def save_as_video(self, export_button):   
        fmt = '%Y-%m-%d_%H.%M.%S'
        now = datetime.now()
        current_time = now.strftime(fmt)
        
        rows = self.treeView.get_model()
        
        fps = float(self.fps.get_text())
        out_filename = desktop + "\\" + 'PinAnimatedImages-%s.avi' % current_time
        
        writer = imageio.get_writer(out_filename, fps=fps)
        #image_array = []
        for row in rows:
            file_name = ''.join([str(elem) for elem in row[0]])
            im = imageio.imread(file_name)
            writer.append_data(im)
        writer.close()

##            img = cv2.imread(file_name)
##            height, width, layers = img.shape
##            size = (width,height)
##            image_array.append(img)
##
##        out = cv2.VideoWriter(out_filename, cv2.VideoWriter_fourcc(*'DIVX'), 15, size)
##
##        for i in range(len(image_array)):
##            out.write(image_array[i])
##        out.release()
            
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Your movie has been created!",
        )

        dialog.format_secondary_text(
            "Your work has been saved to your Desktop folder."
        )
        
        dialog.run()
        dialog.destroy()

    def preview_image(self, prev_button):
        rows = self.treeView.get_model()

        image_list = []
        for row in rows:
            file_name = ''.join([str(elem) for elem in row[0]])
            image_list.append(imageio.imread(file_name))

        fps = float(self.fps.get_text())
        duration = float(self.duration.get_text())

        out_filename = os.getcwd() + "\\" + 'temp.gif'    
        imageio.mimwrite(out_filename, image_list, fps=fps, duration=duration)

        self.pixbufanim = GdkPixbuf.PixbufAnimation.new_from_file(out_filename)
        self.img = Gtk.Image()
        self.img.set_from_animation(self.pixbufanim)

        self.grid.attach(self.img, 5, 0, 4, 4)
        self.img.show()

        GLib.timeout_add(10000, self.img.hide)
        
    def help_user(self, help_button):     
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Your simple guide to PinAnimate!",
        )

        dialog.format_secondary_text(
            "1 - Choose a folder containing your png formatted images\n2 - Organize your images with the move up or down buttons\n3 - Set the duration and frames per second for the animated gif\n4 - Run a live preview of your animation\n5 - Finally export your animation as a gif to share with others"
        )
        
        dialog.run()
        dialog.destroy()
        
win = PinAnimateWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
