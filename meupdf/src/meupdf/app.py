"""
Free Open Source PDF viewer and editor
"""

import toga, asyncio
from toga.style.pack import COLUMN, ROW, Pack

from meupdf.interface.tab import DocumentTab

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
        self.main_box = toga.Box()
        open_button = toga.Button('Open', on_press=self.open_dialog)# tab_area.content.append(DocumentTab(toga.OpenFileDialog('Open PDF file', file_types='*.pdf'))))

        self.tab_area = toga.OptionContainer(style=Pack(flex=1), content=[
            toga.OptionItem(text='Welcome', content=toga.Label('Welcome to Meu PDF')),
        ])

        self.main_box.add(open_button)
        self.main_box.add(self.tab_area)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    def open_dialog(self, widget):
        dialog = toga.OpenFileDialog('Open PDF file', file_types=['pdf'])
        
        task = asyncio.create_task(self.main_window.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file)
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab

def main():
    return MeuPDF()
