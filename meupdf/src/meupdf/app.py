"""
Free Open Source PDF viewer and editor
"""

import toga, asyncio
from toga.style.pack import COLUMN, ROW, Pack

from meupdf.interface.tab import DocumentTab
from meupdf.interface.merge import MergeWindow

# toga.Widget.DEBUG_LAYOUT_ENABLED = True

class MeuPDF(toga.App):
    main_box:toga.Box
    tab_area:toga.OptionContainer

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """

        # toga.Button('Open', on_press=self.open_dialog)# tab_area.content.append(DocumentTab(toga.OpenFileDialog('Open PDF file', file_types='*.pdf'))))


        self.main_box = toga.Box()
        self.tab_area = toga.OptionContainer(style=Pack(flex=1), content=[
            toga.OptionItem(text=_('Welcome'), content=toga.Label(_('Welcome to Meu PDF'))),
        ])

        self.main_box.add(self.tab_area)

        self.main_window = toga.MainWindow(title=self.formal_name)

        self.main_window.toolbar.clear()
        self.main_window.toolbar.add(
            toga.Command(
                self.open_dialog,
                text='Open',
                tooltip='Open a PDF file',
                order=0,
                group=toga.Group.FILE
            ),
            toga.Command(
                self.open_merge_window,
                text='Merge documents',
                tooltip='Merge two or more PDF documents',
                order=1,
                group=toga.Group.FILE
            ),
        )

        self.main_window.content = self.main_box
        self.main_window.show()

    def open_dialog(self, widget):
        dialog = toga.OpenFileDialog('Open PDF file', file_types=['PDF'])
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file)
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab
    
    def open_merge_window(self, widget):
        merge_window = MergeWindow()
        merge_window.show()
        merge_window.open_dialog(widget, first_selection=True)

def main():
    return MeuPDF()
