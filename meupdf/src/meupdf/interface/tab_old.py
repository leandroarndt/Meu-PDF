import toga
import io, json, logging, asyncio

from collections import OrderedDict
from pathlib import Path
from toga import Image, ImageView
import toga.constants
from toga.style import pack
import toga.style
import toga.widgets

from meupdf.documents.generic import GenericDocument, GenericPage
from meupdf.documents.pdf import PDFDocument, PDFPage

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
        pass
        # TODO
        # return pymupdf.Matrix(self.zoom, self.zoom).prerotate(self.rotation)

class Page(object):
    #TODO: load and unload pages dynamically to save memory
    document:PDFDocument
    page:PDFPage
    page_number:int
    page_size:tuple[int, int]
    original_size:tuple[int, int]
    loaded:bool = False
    image:Image
    image_view:ImageView
    parent:toga.Box
    
    def __init__(self, document:PDFDocument, page:int, parent:toga.Box, **kwargs):
        self.document = document
        self.page_number = page
        self.page = self.document.pages[self.page_number]
        self.page_size = (int(self.page.bound()[2]), int(self.page.bound()[3]))
        self.original_size = (self.page.rect[2]-self.page.rect[0], self.page.rect[3]-self.page.rect[1])#(self.page_size[0], self.page_size[1])
        self.loaded = False
        self.parent = parent
        # self.load_page()
    
    def load_page(self, view_options:ViewOptions=ViewOptions()):
        logger.debug(f'Page: Current view options: zoom={view_options.zoom}, rotation={view_options.rotation}')
        pix = self.page.get_pixmap(matrix=view_options.get_matrix_view())
        img_data = pix.tobytes(output='png')
        self.image = toga.Image(src=img_data)
        self.image_view = toga.ImageView(self.image, style=pack.Pack(width=self.page_size[0], height=self.page_size[1]))
        # print(f'Page {self.page_number} size: {self.page_size}')
        # try:
        #     if not self.parent.children:
        #         self.parent.add(self.image_view)
        #     else:
        #         self.parent.replace(0, self.image_view)
        # except:
        #     pass
        self.parent.add(self.image_view)
        self.loaded = True
        logger.debug(f'Page: Loaded page {self.page_number}.')

    def unload_page(self):
        self.image_view = None
        self.loaded = False
        logger.debug(f'Page: unloaded page {self.page_number}.')
    
    def resize(self, view_options:ViewOptions=ViewOptions()):
        if view_options.rotation % 180 == 0:
            self.page_size = (int(self.original_size[0] * view_options.zoom), int(self.original_size[1] * view_options.zoom))
        else:
            self.page_size = (int(self.original_size[1] * view_options.zoom), int(self.original_size[0] * view_options.zoom))
        self.width, self.height = self.page_size
        if self.loaded:
            self.load_page(view_options=view_options)
        else:
            logger.debug(f'Page: What size is page {self.page_number} now? {self.page_size}')

class DocumentTab(toga.OptionItem):
    pages:list
    current_page:int
    page_indicator:toga.TextInput
    document:GenericDocument
    file_path:str
    width:int
    height:int
    margin:int = 30
    page_cache:int
    view_options:ViewOptions
    scroll:toga.ScrollContainer
    scroll_content:toga.Box
    scroll_pos:float
    toolbox:toga.Box
    page_loaders = []
    async_task:asyncio.Task
    redrawing:bool = False
    changing_pos:bool = False

    def __init__(self, file_path:str, *args, **kwargs):
        super().__init__(text=Path(file_path).name, content=toga.Box(style=pack.Pack(direction=toga.constants.COLUMN)), *args, **kwargs)
        self.pages = []
        self.current_page = 0
        self.file_path = file_path
        self.page_cache = 5
        self.view_options = ViewOptions()
        self.redrawing:bool = False
        self.changing_pos:bool = False

        # Load document
        self.document = PDFDocument(self.file_path)

        # Content area (scroll)
        self.scroll_content = toga.Box(style=pack.Pack(align_items=pack.CENTER, direction=pack.COLUMN, gap=DocumentTab.margin))
        self.scroll = toga.ScrollContainer(content=self.scroll_content, style=pack.Pack(flex=1))
        self.current_scroll = (self.scroll.horizontal_position, self.scroll.vertical_position)
        # self.scroll.on_scroll = lambda widget, *kwargs: asyncio.create_task(self.display_pages())

        # Toolbox
        self.toolbox = toga.Box(style=pack.Pack(direction=toga.constants.ROW))
        self.toolbox.add(toga.Label(_('Page')))
        self.page_indicator = toga.TextInput(value='1')
        self.toolbox.add(self.page_indicator)
        self.total_pages = toga.Label(f'{_('of')} {self.document.page_count}')
        self.toolbox.add(self.total_pages)

        # Add to content box
        self.content.add(self.toolbox)
        self.content.add(self.scroll)

        # Display document
        self.place_pages()
        self.task = asyncio.create_task(self.display_pages())
        # self.task.add_done_callback(lambda *args, **kwargs: print(f"Done displaying pages from {self.file_path.name}"))

        # Add binding
        self.scroll.on_scroll = self.update_current_page
        self.page_indicator.on_confirm = self.go_to_page

    def place_pages(self):
        for p in range(self.document.page_count):
            page = PDFPage(self.document, p)
            style = pack.Pack(
                width=int(page.width),
                height=int(page.height),
                margin=self.margin,
            )
            box = toga.Box(style=style)
            self.scroll_content.add(box)
            self.pages.append(Page(self.document, p, box))
    
    async def display_pages(self):
        # Works but blockingly:
        if len(self.pages) > 10000: # aleviates task overload
            # print(f'Load in {self.document.page_count // 10 + 1} groups of 10 pages.')
            for group in range(self.document.page_count // 10 + 1):
                # print(f'Loading group {group}.')
                for n in range(10):
                    if group * 10 + n >= self.focument.page_count: 
                        # print(f'Don\'t load page {group * 10 + n}')
                        break
                    else:
                        # print(f'Load page {group * 10 + n}')
                        await asyncio.to_thread(self.pages[group * 10 + n].load_page())
                # await asyncio.sleep(0)
        else:
            for p in self.pages:
                p.load_page()

        # TODO: discover some way that would not reset the scroll container position:
        # # Calculate the visible area of the scroll container
        # if self.current_scroll == (self.scroll.horizontal_position, self.scroll.vertical_position):
        #     return
        # self.current_scroll = (self.scroll.horizontal_position, self.scroll.vertical_position)
        # center:int = int(self.scroll.vertical_position + (0.5 - self.scroll.vertical_position / self.scroll.max_vertical_position) * self.scroll.layout.height)
        # top:int = int(center - self.scroll.layout.height / 2)
        # bottom:int = int(top + self.scroll.layout.height)

        # # print(f'Top: {top}; center: {center}; bottom: {bottom}.')
        # # print(f'Scroll contents height: {self.scroll_content.layout.height}. Maximum scroll: {self.scroll.max_vertical_position}')

        # for p in self.pages:
        #     # print(f'Displaying page {p.page_number}…')
        #     # print(f'Box top: {p.box.layout.content_top}; box bottom: {p.box.layout.content_top + p.box.layout.content_height}')
        #     if  p.box.layout.content_top <= bottom and p.box.layout.content_top + p.box.layout.content_height >= top:
        #         # print(f'Page {p.page_number} from "{p.document}" loaded.')
        #         p.load_page()
        #     # else:
        #         # print(f'Page {p.page_number} from "{p.document}" not loaded.')
        #     await asyncio.sleep(0)
        
        # self.scroll.horizontal_position = self.current_scroll[0]
        # self.scroll.vertical_position = self.current_scroll[1]

    def center_page(self):
        percent_position:float = self.scroll.vertical_position / self.scroll.max_vertical_position
        center:float = self.scroll.vertical_position + (0.5 - percent_position) * self.scroll.layout.height
        print(f'center: {center}; maximum: {self.scroll.max_vertical_position}, height: {self.scroll.layout.height}')
        
        top = 0
        for p in range(self.document.page_count):
            print(f'page {p} top: {top}; height: {self.pages[p].image_view.layout.height}')
            if top >= center:
                return p - 1
            top += self.pages[p].image_view.layout.height
        return self.document.page_count - 1
    
    def update_current_page(self, widget, **kwars):
        if self.changing_pos:
            self.changing_pos = False
            return
        
        n:int = self.center_page()
        self.page_indicator.value = n + 1
    
    def go_to_page(self, widget, **kwargs):
        try:
            page_number = int(widget.value)
            if page_number > len(self.document): page_number = len(self.document)
        except (AttributeError, ValueError):
            page_number = len(self.document)
            page_number = str(len(self.document))
        
        self.changing_pos = True

        print(f'page {page_number}')
        
        top = 0
        for p in range(page_number - 1):
            top += self.pages[p].image_view.layout.height + 2 * self.margin
        if page_number > 1:
            top += self.margin

        print(f'top: {top}; percent: {top / self.scroll_content.layout.height}; layout height: {self.scroll_content.layout.height}; position: {top / self.scroll.layout.height * self.scroll.max_vertical_position}; max position: {self.scroll.max_vertical_position}')

        self.scroll.vertical_position = top / (self.scroll_content.layout.height - self.scroll.layout.height) * self.scroll.max_vertical_position
