import functools
from typing import Literal
import toga

from toga import constants
from toga.style import pack

from meupdf.documents.pdf import PDFDocument
from meupdf.interface.common import PageImage
from meupdf.interface.styles import row_margin_center, flex_column_right, flex_column_center_margin, right_align, MARGIN, THUMBNAIL

class PageRange(toga.Box):
    document:PDFDocument
    first_miniature:toga.ImageView
    first_page:toga.TextInput
    first_value:int
    last_page:toga.TextInput
    last_miniature:toga.ImageView
    last_value:int
    delete_button:toga.Button

    def __init__(self, document, first_page:int|None=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        first_page = first_page or 0
        self.document = document
        try:
            self.first_miniature = PageImage(self.document, first_page, style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
        except NotImplementedError:
            self.first_miniature = toga.ImageView()
        self.first_page = toga.TextInput(value=str(first_page + 1), on_confirm=functools.partial(self.validate_value, last=False))
        to_label = toga.Label(_('to'))
        self.last_page = toga.TextInput(placeholder=str(first_page + 1), on_confirm=functools.partial(self.validate_value, last=True))
        try:
            self.last_miniature = PageImage(self.document, first_page, style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
        except NotImplementedError:
            self.last_miniature = toga.ImageView()
        self.add(self.first_miniature, self.first_page, to_label, self.last_page, self.last_miniature)

    def get_range(self) -> tuple[int, int] | tuple[int, None] | None:
        """
        Returns a range of pages according to user input.

        :return: A tuple with the first page and last page (if any). Returns None if a
        value cannot be infered from user input.
        :rtype: tuple[int, int] | tuple[int, None] | None
        """
        try:
            return int(self.first_page.value) - 1, int(self.last_page.value) - 1
        except TypeError:
            try:
                return int(self.first_page.value) - 1, None
            except:
                return None

    def validate_value(self, widget:toga.TextInput, last=False, **kwargs):
        # Validate values
        changed_last = False

        if last:
            if int(widget.value) < int(self.first_page.value):
                widget.value = self.first_page.value
            if int(widget.value) > self.document.page_count:
                widget.value = self.document.page_count
            try:
                self.last_value = int(widget.value)
            except ValueError:
                widget.value = str(self.last_value)
            new_miniature = PageImage(self.document, page=int(int(widget.value)-1), style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
            self.replace(self.last_miniature, new_miniature)
            self.last_miniature = new_miniature
        else:
            if int(widget.value) < 1:
                widget.value = 1
            elif int(widget.value) > self.document.page_count:
                widget.value = str(self.document.page_count)
                self.last_page.value = widget.value
                changed_last = True
            if not self.last_page.value:
                self.last_page.value = widget.value
                changed_last = True
            elif int(widget.value) > int(self.last_page.value):
                self.last_page.value = widget.value
                changed_last = True
            try:
                self.first_value = int(widget.value)
            except ValueError:
                widget.value = str(self.first_value)
            new_miniature = PageImage(self.document, page=int(int(widget.value)-1), style=pack.Pack(margin=MARGIN, height=THUMBNAIL))
            self.replace(self.first_miniature, new_miniature)
            self.first_miniature = new_miniature
            if changed_last:
                self.validate_value(self.last_page, last=True)

class ExtractPagesWindow(toga.Window):
    document:PDFDocument
    content:toga.Box
    scroll:toga.ScrollContainer
    ranges:toga.Box
    add_button:toga.Button
    cancel_button:toga.Button
    extact_button:toga.Button

    def __init__(self, document, first_page=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.document = document
        first_row = PageRange(document, first_page, style=row_margin_center)

        self.content = toga.Box(style=flex_column_right) # pyright: ignore[reportIncompatibleMethodOverride]
        self.ranges = toga.Box(style=flex_column_center_margin)
        self.ranges.add(first_row)
        self.scroll = toga.ScrollContainer(vertical=True, horizontal=True, content=self.ranges, style=flex_column_center_margin)
        self.cancel_button = toga.Button(_('Cancel'), enabled=True, on_press=self.do_close)
        button_row = toga.Box(style=right_align)
        button_row.add(self.cancel_button)
        self.content.add(self.scroll, button_row)
    
    def prepare_to_close(self, window, **kwargs) -> Literal[True]:
        for row in self.ranges.children:
            row.document.close()
        return True

    def do_close(self, widget, **kwargs):
        self.prepare_to_close(self)
        self.close()
