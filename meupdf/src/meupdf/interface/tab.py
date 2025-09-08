import toga
import pymupdf, io, json, logging

from collections import OrderedDict
from pathlib import Path
from toga import Image, ImageView
from toga.style.pack import Pack

logger = logging.getLogger(__name__)

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

class Page(toga.Box):
    #TODO: load and unload pages dynamically to save memory
    document:pymupdf.Document
    page:pymupdf.Page
    page_number:int
    size:tuple[int, int]
    original_size:tuple[int, int]
    loaded:bool = False
    image:Image
    
    def __init__(self, document:pymupdf.Document, page:int, **kwargs):
        self.document = document
        self.page_number = page
        self.page = self.document[self.page_number]
        self.size = (int(self.page.bound()[2]), int(self.page.bound()[3]))
        self.original_size = (self.size[0], self.size[1])
        self.loaded = False
        super().__init__(**kwargs)
        self.load_page()
    
    def load_page(self, view_options:ViewOptions=ViewOptions()):
        logger.debug(f'Page: Current view options: zoom={view_options.zoom}, rotation={view_options.rotation}')
        pix = self.page.get_pixmap(matrix=view_options.get_matrix_view())
        img_data = pix.tobytes(output='png')
        # image_view = toga.ImageView(img_data)
        self.image = toga.Image(src=img_data)
        image_view = toga.ImageView(self.image)
        try:
            self.add(image_view)
        except:
            print('Cannot add children')
        # self.size = (temp_img.width, temp_img.height)
        # self.src = temp_img
        self.loaded = True
        logger.debug(f'Page: Loaded page {self.page_number}.')

    def unload_page(self):
        self.image_view = None
        # self.remove_from_cache()
        self.loaded = False
        logger.debug(f'Page: unloaded page {self.page_number}.')
    
    def resize(self, view_options:ViewOptions=ViewOptions()):
        if view_options.rotation % 180 == 0:
            self.size = (int(self.original_size[0] * view_options.zoom), int(self.original_size[1] * view_options.zoom))
        else:
            self.size = (int(self.original_size[1] * view_options.zoom), int(self.original_size[0] * view_options.zoom))
        self.width, self.height = self.size
        if self.loaded:
            self.load_page(view_options=view_options)
        else:
            logger.debug(f'Page: What size is page {self.page_number} now? {self.size}')

class DocumentTab(toga.OptionItem):
    pages:list
    current_page:int
    document:pymupdf.Document
    page_container:toga.Box
    file_path:str
    width:int
    height:int
    spacer_height:int = 20
    page_cache:int
    view_options:ViewOptions

    def __init__(self, file_path:str, *args, **kwargs):
        super().__init__(text=Path(file_path).name, content=toga.Box(), *args, **kwargs)
        self.pages = []
        self.current_page = 0
        self.document = pymupdf.open(file_path)
        self.file_path = file_path
        # self.parent_widget = parent
        self.page_cache = 5
        self.view_options = ViewOptions()
        self.load_pages()
        # self.page_container = toga.Box()
        
        # self.add(self.page_container)

        for p in self.pages:
            self.content.add(p)
        self.display_pages()

    def load_pages(self):

        for p in range(self.document.page_count):
            page = Page(self.document, p)
            page.load_page(view_options=self.view_options)
            self.pages.append(page)

        logger.debug(f"PDFTab: Loaded {p+1} pages from the document.")

        self.place_pages()

    def place_pages(self):
        pass
    
    def display_pages(self):
        pass

    # def __init__(self, file_path:Path, *args, **kwargs):
    #     content = toga.Box()
    #     label = toga.Label(text=f'File name is {Path(file_path).name}.')
    #     content.add(label)
    #     text = Path(file_path).name
    #     super().__init__(text, content)