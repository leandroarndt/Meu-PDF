import functools, asyncio, sys
from typing import Literal
import toga

from toga import constants
from toga.style import pack

from meupdf.documents.pdf import PDFDocument, DOCUMENT_FORMAT
from meupdf.interface.common import PageImage
from meupdf.interface.styles import row_margin_center, flex_column_right, flex_column_center_margin, flex_row_right, right_align, MARGIN, THUMBNAIL

class PageRange(toga.Box):
    document:PDFDocument
    first_miniature:toga.ImageView
    first_page:toga.TextInput
    first_value:int
    last_page:toga.TextInput
    last_miniature:toga.ImageView
    last_value:int
    delete_button:toga.Button
    add_button:toga.Button

    def __init__(self, document, first_page:int|None=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        first_page = first_page or 0
        self.first_value = first_page
        self.last_value = first_page

        self.document = document
        try:
            self.first_miniature = PageImage(self.document, first_page, style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
        except NotImplementedError:
            self.first_miniature = toga.ImageView()
        self.first_page = toga.TextInput(
            value=str(first_page + 1),
            on_confirm=functools.partial(self.validate_value, last=False),
            on_lose_focus=functools.partial(self.validate_value, last=False),
        )
        to_label = toga.Label(_('to'))
        self.last_page = toga.TextInput(
            placeholder=str(first_page + 1),
            on_confirm=functools.partial(self.validate_value, last=True),
            on_lose_focus=functools.partial(self.validate_value, last=True)
        )
        try:
            self.last_miniature = PageImage(self.document, first_page, style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
        except NotImplementedError:
            self.last_miniature = toga.ImageView()

        button_box = toga.Box(style=flex_row_right)
        self.add_button = toga.Button(_('Add'), on_press=self.on_add_pressed)
        self.delete_button = toga.Button(_('Remove'), on_press=self.on_remove_pressed)
        button_box.add(self.add_button, self.delete_button)

        self.add(self.first_miniature, self.first_page, to_label, self.last_page, self.last_miniature, button_box)

    def get_range(self) -> tuple[int, int] | tuple[int, None] | None:
        """
        Returns a range of pages according to user input.

        :return: A tuple with the first page and last page (if any). Returns None if a
        value cannot be infered from user input.
        :rtype: tuple[int, int] | tuple[int, None] | None
        """
        try:
            return int(self.first_page.value) - 1, int(self.last_page.value) - 1
        except (TypeError, ValueError):
            try:
                return int(self.first_page.value) - 1, None
            except:
                return None

    def validate_value(self, widget:toga.TextInput, last=False, **kwargs):
        # Validate values
        page_count:int
        changed_last = False
        changed_first = False

        if 'pymupdf' in sys.modules:
            page_count = self.document.page_count
        else:
            page_count = self.document.get_num_pages() # pyright: ignore[reportAttributeAccessIssue]

        if last:
            try:
                if int(widget.value) < int(self.first_page.value):
                    if int(widget.value) > 0:
                        self.first_page.value = widget.value
                        changed_first = True
                    else:
                        widget.value = self.first_page.value
                if int(widget.value) > page_count:
                    widget.value = page_count
                self.last_value = int(widget.value)
            except ValueError:
                widget.value = str(self.last_value)
            new_miniature = PageImage(self.document, page=int(int(widget.value)-1), style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
            self.replace(self.last_miniature, new_miniature)
            self.last_miniature = new_miniature
            if changed_first:
                self.validate_value(self.first_page, last=False)
        else:
            try:
                if int(widget.value) < 1:
                    widget.value = 1
                elif int(widget.value) > page_count:
                    widget.value = str(page_count)
                    self.last_page.value = widget.value
                    changed_last = True
                if not self.last_page.value:
                    self.last_page.value = widget.value
                    changed_last = True
                elif int(widget.value) > int(self.last_page.value):
                    self.last_page.value = widget.value
                    changed_last = True
                self.first_value = int(widget.value)
            except ValueError:
                widget.value = str(self.first_value)
            new_miniature = PageImage(self.document, page=int(int(widget.value)-1), style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
            self.replace(self.first_miniature, new_miniature)
            self.first_miniature = new_miniature
            if changed_last:
                self.validate_value(self.last_page, last=True)

    def on_add_pressed(self, widget, **kwargs):
        self.validate_value(self.first_page, last=False)
        self.validate_value(self.last_page, last=True)
        if 'pymupdf' in sys.modules:
            page_count = self.document.page_count
        else:
            page_count = self.document.get_num_pages() # pyright: ignore[reportAttributeAccessIssue]
        
        if self.last_value == page_count:
            page = page_count - 1
        else:
            page = self.last_value
        print(f'Add page range starting from {page + 1}')
        new_row = PageRange(self.document, first_page=page, style=row_margin_center)
        self.parent.insert(self.parent.index(self) + 1, new_row) # pyright: ignore[reportAttributeAccessIssue]

    def on_remove_pressed(self, widget, **kwargs):
        self.parent.remove(self) # pyright: ignore[reportAttributeAccessIssue]

class ExtractPagesWindow(toga.Window):
    document:PDFDocument
    content:toga.Box
    scroll:toga.ScrollContainer
    ranges:toga.Box
    add_button:toga.Button
    cancel_button:toga.Button
    extract_button:toga.Button

    def __init__(self, document, first_page=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.document = document
        first_row = PageRange(document, first_page, style=row_margin_center)

        self.content = toga.Box(style=flex_column_right) # pyright: ignore[reportIncompatibleMethodOverride]
        self.ranges = toga.Box(style=flex_column_center_margin)
        self.ranges.add(first_row)
        self.scroll = toga.ScrollContainer(vertical=True, horizontal=True, content=self.ranges, style=flex_column_center_margin)
        self.cancel_button = toga.Button(_('Cancel'), enabled=True, on_press=self.do_close)
        self.extract_button = toga.Button(_('Extract pages'), enabled=True, on_press=self.extract)
        button_row = toga.Box(style=right_align)
        button_row.add(self.cancel_button)
        button_row.add(self.extract_button)
        self.content.add(self.scroll, button_row)

    def extract(self, widget, **kwargs):
        def do_save(task):
            file_name = task.result()
            if file_name:
                first, last = self.ranges.children[0].get_range()
                new_doc = self.document.extract_pages(file_name, first=first, last=last)
                if len(self.ranges.children) > 1:
                    for range in self.ranges.children[1:]:
                        first, last = range.get_range()
                        target = new_doc
                        new_doc = self.document.extract_pages(new_path=file_name, first=first, last=last, target_doc=new_doc)
                
                new_doc.close()            
                self.do_close(None)

        dialog = toga.SaveFileDialog(
            _('Choose destination file'),
            f'{self.document.file_path.stem} - {_('selected pages')}.{DOCUMENT_FORMAT.lower()}',
            file_types=[DOCUMENT_FORMAT.lower()]
        )
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(do_save)

    def prepare_to_close(self, window, **kwargs) -> Literal[True]:
        for row in self.ranges.children:
            row.document.close()
        return True

    def do_close(self, widget, **kwargs):
        self.prepare_to_close(self)
        self.close()
