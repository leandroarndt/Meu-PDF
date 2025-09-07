import kivy, pymupdf, io, json
from collections import OrderedDict

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image, CoreImage
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.config import Config

class ViewOptions(object):
    zoom_list:list[float] = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 5.0]
    zoom_index:int = 3
    zoom:float = 1.0
    rotation:int = 0

    def __init__(self, zoom:float=1.0, rotation:int=0):
        self.zoom = zoom

        self.set_zoom(zoom)

        self.rotation = rotation

    def rotate_right(self):
        self.rotation += 90
        if self.rotation == 360:
            self.rotation = 0
    
    def rotate_left(self):
        self.rotation -= 90
        if self.rotation == -360:
            self.rotation = 0
    
    def zoom_in(self):
        self.zoom_index += 1
        if self.zoom_index >= len(self.zoom_list):
            self.zoom_index = len(self.zoom_list) - 1
        self.zoom = self.zoom_list[self.zoom_index]

    def zoom_out(self):
        self.zoom_index -= 1
        if self.zoom_index < 0:
            self.zoom_index = 0
        self.zoom = self.zoom_list[self.zoom_index]
    
    def set_zoom(self, zoom:float):
        if zoom in self.zoom_list:
            self.zoom_index = self.zoom_list.index(zoom)
        else:
            for z in zoom_list:
                if z > zoom:
                    self.zoom_index = self.zoom_list.index(z) - 1
                    break

    def get_matrix_view(self):
        return pymupdf.Matrix(self.zoom, self.zoom).prerotate(self.rotation)

class Page(Image):
    #TODO: load and unload pages dynamically to save memory
    document:pymupdf.Document
    page:pymupdf.Page
    page_number:int
    size:tuple[int, int]
    original_size:tuple[int, int]
    loaded:bool = False
    
    def __init__(self, document:pymupdf.Document, page:int, **kwargs):
        self.document = document
        self.page_number = page
        self.page = self.document[self.page_number]
        self.size = (int(self.page.bound()[2]), int(self.page.bound()[3]))
        self.original_size = (self.size[0], self.size[1])
        self.loaded = False
        super().__init__(**kwargs)
    
    def load_page(self, view_options:ViewOptions=ViewOptions()):
        Logger.debug(f'Page: Current view options: zoom={view_options.zoom}, rotation={view_options.rotation}')
        pix = self.page.get_pixmap(matrix=view_options.get_matrix_view())
        img_data = io.BytesIO(pix.tobytes())
        temp_img = CoreImage(img_data, ext="png").texture
        self.size = (temp_img.width, temp_img.height)
        self.texture = temp_img
        self.loaded = True
        Logger.debug(f'Page: Loaded page {self.page_number}.')

    def unload_page(self):
        self.texture = None
        self.remove_from_cache()
        self.loaded = False
        Logger.debug(f'Page: unloaded page {self.page_number}.')
    
    def resize(self, view_options:ViewOptions=ViewOptions()):
        if view_options.rotation % 180 == 0:
            self.size = (int(self.original_size[0] * view_options.zoom), int(self.original_size[1] * view_options.zoom))
        else:
            self.size = (int(self.original_size[1] * view_options.zoom), int(self.original_size[0] * view_options.zoom))
        self.width, self.height = self.size
        if self.loaded:
            self.load_page(view_options=view_options)
        else:
            Logger.debug(f'Page: What size is page {self.page_number} now? {self.size}')

class PDFTab(ScrollView):
    pages:list
    current_page:int
    document:pymupdf.Document
    parent_widget:Widget
    file_path:str
    content:BoxLayout
    width:int
    height:int
    spacer_height:int = 20
    page_cache:int
    view_options:ViewOptions
    config:Config

    def __init__(self, parent:Widget, file_path:str, **kwargs):
        self.pages = []
        self.current_page = 0
        self.document = pymupdf.open(file_path)
        self.file_path = file_path
        self.parent_widget = parent
        self.page_cache = 5
        self.view_options = ViewOptions()
        self.load_pages()
        super().__init__(**kwargs)
        self.config = App.get_running_app().config
        self.scroll_type = ['bars', 'content']

        self.content = BoxLayout(size_hint=(None, None), size=(self.width, self.height), orientation='vertical', spacing=self.spacer_height)
        self.add_widget(self.content)

        for p in self.pages:
            self.content.add_widget(p)
        self.display_pages()

        # Bind events
        self.bind(on_scroll_move=lambda *args, **kwargs: self.display_pages())
        self.bind(on_scroll_stop=lambda *args, **kwargs: self.display_pages())
    
    def load_pages(self):

        for p in range(self.document.page_count):
            page = Page(self.document, p, size_hint=(1, None))
            page.load_page(view_options=self.view_options)
            self.pages.append(page)

        Logger.debug(f"PDFTab: Loaded {p+1} pages from the document.")

        self.place_pages()

    def place_pages(self):
        self.width = 0
        self.height = 0
        
        for p in range(len(self.pages)):
            if self.pages[p].width > self.width:
                self.width = self.pages[p].width
            self.height += self.pages[p].height
            if p < self.document.page_count:
                self.height += self.spacer_height
            if hasattr(self, 'content'):
                self.content.add_widget(self.pages[p])
                self.content.width = self.width
                self.content.height = self.height

    def display_pages(self):
        page_top:int = 0
        page_bottom:int = 0
        first:int = -1
        last:int = -1
        visible:bool = False

        # Calculate the visible area in the ScrollView
        center = (1 - self.scroll_y) * (self.viewport_size[1] - Window.height) + Window.height / 2
        top = center - Window.height / 2
        bottom = top + Window.height

        # Search for pages in the visible area
        for p in range(self.document.page_count):
            page_top = sum(self.pages[i].height + self.spacer_height for i in range(p))
            page_bottom = page_top + self.pages[p].height
            if page_bottom >= top and page_top <= bottom:
                if first == -1:
                    first = p
                visible = True
                if page_top <= center <= page_bottom:
                    self.current_page = p
                    Logger.debug(f"PDFTab: Current page is {self.current_page}.")
            elif visible:
                last = p
                break

        Logger.info(f"PDFTab: Last page was calculated as {last}.")
        if last == -1:
            last = self.document.page_count - 1
        first -= self.page_cache
        last += self.page_cache
        Logger.info(f"PDFTab: Last page was calculated as {last} after cache.")
        if first < 0:
            first = 0
        if last >= self.document.page_count:
            last = self.document.page_count - 1
        Logger.info(f"PDFTab: Last page was corrected to {last}.")
        Logger.info(f"PDFTab: Visible pages are from {first} to {last}. Current page is {self.current_page}.")
        for p in range(self.document.page_count):
            current_pages = range(first, last + 1)
            if p in current_pages:
                if not self.pages[p].loaded:
                    self.pages[p].load_page(view_options=self.view_options)
                    Logger.debug(f"PDFTab: Displaying page {p}.")
            if p not in current_pages and self.pages[p].loaded:
                self.pages[p].unload_page()
        Logger.debug(f"PDFTab: Displaying pages {first} to {last}.")
    
    def go_to_page(self, page:int):
        if 0 < page < self.document.page_count:
            self.current_page = page - 1
        elif page >= self.document.page_count:
            self.current_page = self.document.page_count - 1
        else:
            self.current_page = 0
        try:
            self.scroll_to(self.pages[self.current_page])
            Clock.schedule_once(lambda dt: self.display_pages(), 1) # Needs a delay to work properly
            self.display_pages()
        except Exception as e:
            Logger.error(f"PDFTab: Could not go to page {page}: {e}")    
    
    def rotate_right(self):
        self.view_options.rotate_right()
        self.resize()

    def rotate_left(self):
        self.view_options.rotate_left()
        self.resize()
    
    def zoom_in(self):
        self.view_options.zoom_in()
        self.resize()

    def zoom_out(self):
        self.view_options.zoom_out()
        self.resize()
    
    def set_zoom(self, zoom:float):
        self.resize()

    def resize(self):
        scroll_x = self.scroll_x
        scroll_y = self.scroll_y
        Logger.debug(f"PDFTab: Resizing document with zoom={self.view_options.zoom} and rotation={self.view_options.rotation}.")
        self.content.clear_widgets()
        for p in self.pages:
            p.resize(view_options=self.view_options)
        self.place_pages()
        self.scroll_x, self.scroll_y = scroll_x, scroll_y

    def save_page(self):
        last_files:OrderedDict = json.loads(self.config.get('permanent', 'last_files'), object_hook=OrderedDict)
        last_files[self.file_path] = self.current_page
        last_files.move_to_end(self.file_path, last=False)
        self.config.set('permanent', 'last_files', json.dumps(last_files))
        self.config.write()

    def close(self):
        self.save_page()
        self.document.close()

    def __del__(self):
        self.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()