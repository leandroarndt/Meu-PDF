from pathlib import Path

import toga
from toga.style import pack

from meupdf.documents.generic import GenericDocument, document_formats, FormatInfos, get_document_class
from meupdf.interface.styles import flex_margin, THUMBNAIL

class PageImage(toga.ImageView):

    def __init__(self, document:GenericDocument, page:int=0, *args, **kwargs):
        pix = document.pages[page].to_image()
        img_data = pix.tobytes(output='png')
        image = toga.Image(src=img_data)
        super().__init__(image=image, *args, **kwargs)

class FileRow(toga.Box):
    # Miniature | file name | up | down
    document:GenericDocument
    path:Path
    miniature:toga.ImageView
    up_button:toga.Button
    down_button:toga.Button
    parent_container:toga.Box # parent might not have been set

    def __init__(self, file_path:str, parent:toga.Box, *args, **kwargs):
        self.path = Path(file_path)
        self.document = get_document_class(file_path)(file_path)
        self.parent_container = parent

        super().__init__(*args, **kwargs)

        # First page miniature
        try:
            self.miniature = PageImage(self.document, page=0, style=pack.Pack(height=THUMBNAIL))
            self.add(self.miniature)
        except NotImplementedError:
            pass

        # File info
        label = toga.Label(text=str(self.document.file_path.stem) + \
                f' ({document_formats[self.document.format][FormatInfos.SHORT_NAME]})\n' + _\
                ('At ') + str(self.document.file_path.parent), style=flex_margin)
        self.add(label)

        # Move buttons
        self.up_button = toga.Button(_('Up'), on_press=self.move_up)
        self.down_button = toga.Button(_('Down'), on_press=self.move_down)
        self.add(self.up_button)
        self.add(self.down_button)

    def inhibit_buttons(self):
        position = self.parent_container.index(self)
        self.up_button.enabled = position != 0
        self.down_button.enabled = position != len(self.parent.children) - 1 # type: ignore

    def move_up(self, widget, **kwargs):
        position = self.parent_container.index(self) - 1
        self.parent_container.remove(self)
        self.parent_container.insert(position, self)
        self.inhibit_buttons()
        self.parent_container.children[1].inhibit_buttons()
        self.parent_container.children[-1].inhibit_buttons()

    def move_down(self, widget, **kwargs):
        position = self.parent_container.index(self) + 1
        self.parent_container.remove(self)
        self.parent_container.insert(position, self)
        self.inhibit_buttons()
        self.parent_container.children[-2].inhibit_buttons()
        self.parent_container.children[0].inhibit_buttons()
