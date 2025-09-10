import toga, pymupdf, asyncio

from pathlib import Path
import toga.constants
from toga.style import pack

class FileRow(toga.Box):
    # Miniature | file name | up | down
    document:pymupdf.Document
    path:Path
    miniature:toga.ImageView
    up_button:toga.Button
    down_button:toga.Button

    def __init__(self, file_path:str, *args, **kwargs):
        self.path = Path(file_path)
        self.document = pymupdf.open(self.path)

        super().__init__(*args, **kwargs)

        pix = self.document[0].get_pixmap(matrix=pymupdf.Matrix(0.1, 0.1))
        img_data = pix.tobytes(output='png')
        image = toga.Image(src=img_data)
        self.miniature = toga.ImageView(image, style=pack.Pack(height=100))

        self.add(self.miniature)

class MergeWindow(toga.Window):
    documents:list[FileRow]
    add_button:toga.Button
    scroll:toga.ScrollContainer
    rows:toga.Box
    cancel_button:toga.Button
    merge_button:toga.Button

    def __init__(self, *args, **kwargs):
        self.documents = []

        super().__init__(self, on_close=self.prepare_to_close, *args, **kwargs)

        flex_column_right = pack.Pack(flex=1, direction=toga.constants.COLUMN, align_items=toga.constants.END)
        right_align = pack.Pack(flex=0, direction=toga.constants.ROW, align_items=toga.constants.END)
        self.content = toga.Box(style=flex_column_right)
        self.add_button = toga.Button(_('Add document'), enabled=False, on_press=self.open_dialog)
        self.cancel_button = toga.Button(_('Cancel'), enabled=False, on_press=self.do_close)
        self.merge_button = toga.Button(_('Merge!'), enabled=False, on_press=self.save_file_dialog)
        top_button_row = toga.Box(style=right_align)
        bottom_button_row = toga.Box(style=right_align)
        self.scroll = toga.Box(style=pack.Pack(flex=1, direction=pack.COLUMN))
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
            self.documents.append(FileRow(f))
            self.scroll.add(self.documents[-1])
        self.add_button.enabled = True
        self.cancel_button.enabled = True
        self.merge_button.enabled = True

    def save_file_dialog(self, widget):
        dialog = toga.SaveFileDialog(
            _('Chose destination file'),
            f'{self.documents[0].path.stem} - {_("merged.pdf")}',
            file_types=['PDF'],
        )
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(self.save_dialog_closed)
    
    def save_dialog_closed(self, task):
        file = task.result()
        if file:
            self.merge(file)

    def prepare_to_close(self, window, **kwargs):
        for d in self.documents:
            d.document.close()
        return True
    
    def merge(self, file:str):
        try:
            page_num = len(self.documents[0].document)
            toc = self.documents[0].document.get_toc(False)
            for doc in self.documents[1:]:
                toc2 = doc.document.get_toc(False)
                self.documents[0].document.insert_pdf(doc.document)
                for t in toc2:
                    t[2] += page_num
                page_num += len(doc.document)
                toc = toc + toc2
            self.documents[0].document.set_toc(toc)
        except IndexError:
            pass
        self.documents[0].document.save(file)
        self.do_close()

    def do_close(self, *args, **kwargs):
        self.prepare_to_close(self)
        self.close()
