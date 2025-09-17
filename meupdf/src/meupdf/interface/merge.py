import toga, asyncio

from pathlib import Path
import toga.constants
from toga.style import pack

from meupdf.interface.document_organizer import FileRow
            
class MergeWindow(toga.Window):
    # documents:list[FileRow]
    add_button:toga.Button
    scroll:toga.ScrollContainer
    document_organizer:toga.Box
    rows:toga.Box
    cancel_button:toga.Button
    merge_button:toga.Button

    def __init__(self, *args, **kwargs):
        super().__init__(self, on_close=self.prepare_to_close, *args, **kwargs)

        flex_column_right = pack.Pack(flex=1, direction=toga.constants.COLUMN, align_items=toga.constants.END)
        right_align = pack.Pack(flex=0, direction=toga.constants.ROW, align_items=toga.constants.END)
        self.content = toga.Box(style=flex_column_right)
        self.add_button = toga.Button(_('Add document'), enabled=False, on_press=self.open_dialog)
        self.cancel_button = toga.Button(_('Cancel'), enabled=False, on_press=self.do_close)
        self.merge_button = toga.Button(_('Merge'), enabled=False, on_press=self.save_file_dialog)
        top_button_row = toga.Box(style=right_align)
        bottom_button_row = toga.Box(style=right_align)
        self.document_organizer = toga.Box(style=pack.Pack(flex=1, direction=pack.COLUMN, margin=5))
        self.scroll = toga.ScrollContainer(vertical=True, horizontal=True, content=self.document_organizer, style=pack.Pack(flex=1))
        top_button_row.add(self.add_button)
        bottom_button_row.add(self.cancel_button, self.merge_button)
        self.content.add(top_button_row, self.scroll, bottom_button_row)

    def open_dialog(self, widget, first_selection=False):
        dialog = toga.OpenFileDialog(_('Select PDF files to merge'), file_types=['PDF'], multiple_select=True)
        
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        files = task.result()
        if not isinstance(files, list):
            self.do_close()
        if not files:
            self.do_close()
        for f in files:
            try:
                self.document_organizer.add(FileRow(f, self.document_organizer, style=pack.Pack(margin=5)))
            except NotImplementedError:
                dialog = toga.ErrorDialog(_('File format error!'), f'{_("file format").capitalize()} "{Path(f).suffix}" {_("is not supported")}.')
                asyncio.create_task(self.dialog(dialog))
        self.add_button.enabled = True
        self.cancel_button.enabled = True
        self.merge_button.enabled = True
        self.document_organizer.children[0].inhibit_buttons()
        self.document_organizer.children[-1].inhibit_buttons()

    def save_file_dialog(self, widget):
        dialog = toga.SaveFileDialog(
            _('Chose destination file'),
            f'{self.document_organizer.children[0].document.file_path.stem} - {_("merged.pdf")}',
            file_types=['PDF'],
        )
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(self.save_dialog_closed)
    
    def save_dialog_closed(self, task):
        file = task.result()
        if file:
            self.merge(file)

    def prepare_to_close(self, window, **kwargs):
        for row in self.document_organizer.children:
            row.document.close()
        return True
    
    def merge(self, file:str):
        for r in range(1, len(self.document_organizer.children)):
            self.document_organizer.children[0].document.merge(self.document_organizer.children[r].document)
        self.document_organizer.children[0].document.save(file)
        self.do_close()

    def do_close(self, *args, **kwargs):
        self.prepare_to_close(self)
        self.close()
