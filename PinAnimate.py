import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

import os
# import imageio.v2 as imageio
from pathlib import Path
from PIL import Image, ImageDraw
from datetime import datetime
import platform
from natsort import natsorted

if platform.system() == 'Windows':
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
else:
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Downloads')

if platform.system() == 'Darwin':
    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

### START ###
### CODE FROM https://stackoverflow.com/questions/41718892/pillow-resizing-a-gif ###
def resize_gif(path, myduration, save_as=None, resize_to=None):
    """
    Resizes the GIF to a given length:

    Args:
        path: the path to the GIF file
        save_as (optional): Path of the resized gif. If not set, the original gif will be overwritten.
        resize_to (optional): new size of the gif. Format: (int, int). If not set, the original GIF will be resized to
                              half of its size.
    """

    all_frames = extract_and_resize_frames(path, resize_to)

    myduration = int(myduration)

    if not save_as:
        save_as = path

    if len(all_frames) == 1:
        print("Warning: only 1 frame found")
        all_frames[0].save(save_as, optimize=True)
    else:
        all_frames[0].save(save_as, optimize=True, save_all=True, append_images=all_frames[1:], duration=myduration, loop=0)


def analyseImage(path):
    """
    Pre-process pass over the image to determine the mode (full or additive).
    Necessary as assessing single frames isn't reliable. Need to know the mode
    before processing all frames.
    """
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def extract_and_resize_frames(path, resize_to=None):
    """
    Iterate the GIF, extracting each frame and resizing them

    Returns:
        An array of all frames
    """
    mode = analyseImage(path)['mode']

    im = Image.open(path)

    if not resize_to:
        resize_to = (im.size[0] // 2, im.size[1] // 2)

    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')

    all_frames = []
    try:
        while True:
            # print("saving %s (%s) frame %d, %s %s" % (path, mode, i, im.size, im.tile))

            '''
            If the GIF uses local colour tables, each frame will have its own palette.
            If not, we need to apply the global palette to the new frame.
            '''
            try:
                if not im.getpalette():
                    im.putpalette(p)
            except ValueError:
                pass

            new_frame = Image.new('RGBA', im.size)

            '''
            Is this file a "partial"-mode GIF where frames update a region of a different size to the entire image?
            If so, we need to construct the new frame by pasting it on top of the preceding frames.
            '''
            if mode == 'partial':
                new_frame.paste(last_frame)
            try:
                new_frame.paste(im, (0, 0), im.convert('RGBA'))
            except ValueError:
                pass

            new_frame.thumbnail(resize_to, Image.LANCZOS)
            all_frames.append(new_frame)

            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)
    except EOFError:
        pass

    return all_frames
### END ###

def compare_images(input_image, output_image):
    ### Compare Image Dimensions ###
    input_image = Image.open(input_image)
    output_image = Image.open(output_image)
    if input_image.size != output_image.size:
        return False

class PinAnimateWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PinAnimate")
        
        self.set_border_width(1)
        self.set_default_size(640, 480)

        if platform.system() == 'Darwin':
            self.pixbuf = GdkPixbuf.Pixbuf.new_from_file(resource_path('logo.png'))
            self.set_default_icon(self.pixbuf)

        if platform.system() == 'Windows':
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

        self.prev_button = Gtk.Button(label="Preview")
        self.prev_button.connect("clicked", self.preview_image)
        self.grid.add(self.prev_button)

        self.save_button = Gtk.Button(label="Export")
        self.save_button.connect("clicked", self.save_as_gif)
        self.grid.add(self.save_button)
        
        # self.export_button = Gtk.Button(label="Export as Video")
        # self.export_button.connect("clicked", self.save_as_video)
        # self.grid.add(self.export_button)

        self.help_button = Gtk.Button(label="Help/Info")
        self.help_button.connect("clicked", self.help_user)
        self.grid.add(self.help_button)

        # self.loop = Gtk.Entry()
        # self.loop.set_text("0")
        # self.loop.set_hexpand(True)
        # self.grid.attach(self.loop, 0, 1, 1, 1)

        # self.label = Gtk.Label(label="Loop")
        # self.grid.attach(self.label, 1, 1, 1, 1)
        
        self.duration = Gtk.Entry()
        self.duration.set_text("300")
        self.duration.set_hexpand(True)
        #self.duration.set_width_chars(15)
        self.grid.attach(self.duration, 0, 1, 4, 1)

        self.label = Gtk.Label(label="Duration")
        self.grid.attach(self.label, 4, 1, 1, 1) 

        # self.help_button = Gtk.Button(label="Help/Info")
        # self.help_button.connect("clicked", self.help_user)
        # self.grid.attach(self.help_button, 4, 1, 1, 1)

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

        self.hints_button = Gtk.Button(label="Helpful Hints")
        self.hints_button.connect("clicked", self.helpful_hints)
        self.grid.attach(self.hints_button, 2, 3, 1, 1)

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

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(selected, 320, 320, GdkPixbuf.InterpType.BILINEAR)
        self.img = Gtk.Image.new_from_pixbuf(pixbuf)
        
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
            self.images = list(self.image_path.glob('*.png')) + list(self.image_path.glob('*.jpg'))
            image_list = []

            self.model.clear()
            x = []
            for file_name in self.images:
                x.append(file_name)
                image = Image.open(str(file_name))
                width, height = image.size
                ImageSizes = "Width: %spx - Height: %spx" % (width, height)       
                if compare_images(x[0], str(file_name)) != False: 
                    image_list.append((str(file_name), ImageSizes))
                else:
                    pass
                
            image_list = natsorted(image_list)

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
            image_list.append(Image.open(file_name))

        #loop = int(self.loop.get_text())
        duration = int(self.duration.get_text())

        if platform.system() == 'Darwin':
            out_filename = desktop + '/PinAnimatedImage-%s.gif' % current_time    

        if platform.system() == 'Windows':
            out_filename = desktop + "\\" + 'PinAnimatedImage-%s.gif' % current_time
            
        #imageio.mimwrite(out_filename, image_list, fps=fps, duration=duration)

        image_list[0].save(out_filename,
               save_all=True,
               append_images=image_list[1:],
               duration=duration,
               loop=0)

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

    # def save_as_video(self, export_button):
    #     fmt = '%Y-%m-%d_%H.%M.%S'
    #     now = datetime.now()
    #     current_time = now.strftime(fmt)
        
    #     rows = self.treeView.get_model()
        
    #     fps = float(self.fps.get_text())
    #     if platform.system() == 'Darwin':
    #         out_filename = desktop + '/PinAnimatedMovie-%s.avi' % current_time
            
    #     if platform.system() == 'Windows':    
    #         out_filename = desktop + "\\" + 'PinAnimatedMovie-%s.avi' % current_time        

    #     writer = imageio.get_writer(out_filename, fps=fps)
    #     for row in rows:
    #         file_name = ''.join([str(elem) for elem in row[0]])
    #         im = imageio.imread(file_name)
    #         writer.append_data(im)
    #     writer.close()
     
    #     dialog = Gtk.MessageDialog(
    #         transient_for=self,
    #         flags=0,
    #         message_type=Gtk.MessageType.INFO,
    #         buttons=Gtk.ButtonsType.OK,
    #         text="Your movie has been created!",
    #     )

    #     dialog.format_secondary_text(
    #         "Your work has been saved to your Desktop folder."
    #     )
        
    #     dialog.run()
    #     dialog.destroy()
        
    def preview_image(self, prev_button):
        rows = self.treeView.get_model()

        image_list = []
        for row in rows:
            file_name = ''.join([str(elem) for elem in row[0]])
            #image_list.append(imageio.imread(file_name))
            image_list.append(Image.open(file_name))

        #loop = int(self.loop.get_text())
        duration = int(self.duration.get_text())

        if platform.system() == 'Darwin':
            out_filename = os.getcwd() + '/temp.gif'

        if platform.system() == 'Windows':
            out_filename = os.getcwd() + "\\" + 'temp.gif'
            
        #imageio.mimwrite(out_filename, image_list, fps=fps, duration=duration)

        image_list[0].save(out_filename,
               save_all=True,
               append_images=image_list[1:],
               duration=duration,
               loop=0)

        size_test = Image.open(out_filename)
        width = size_test.width
        height = size_test.height

        if width > 512 or height > 512:
            resize_gif(out_filename, duration)
        
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
        self.info = ""
        self.info += "1 - Choose a folder containing your png formatted images\n"
        self.info += "2 - Organize your images with the move up or down buttons\n"
        self.info += "3 - Set the duration and run a live preview of your animation\n"
        self.info += "4 - Finally export your animation as a gif to share with others"
        dialog.format_secondary_text(
            self.info
        )
        
        dialog.run()
        dialog.destroy()

    def helpful_hints(self, hints_button):     
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Helpful Hints!",
        )

        self.info = ""
        self.info += "1 - You can adjust the duration of your animations\n"
        self.info += "2 - Clicking an image filename will present a preview of that image\n"
        self.info += "3 - Image dimensions must be the same for each image\n"
        self.info += "4 - Animation previews will only play for up to 10 seconds\n"
        self.info += "5 - Animation and image previews are scaled down in size\n"
        self.info += "6 - Supported file types are *.png and *.jpg\n"
        self.info += "7 - Previews are optimized with your duration settings"

        dialog.format_secondary_text(
            self.info
        )
        
        dialog.run()
        dialog.destroy()
        
win = PinAnimateWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
