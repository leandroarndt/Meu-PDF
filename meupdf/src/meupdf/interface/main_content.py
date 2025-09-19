import asyncio

import toga

from toga.style import pack

from meupdf.interface.commands import create_commands
from meupdf.interface.tab import DocumentTab
from meupdf.interface.merge import MergeWindow

class MainWindow(toga.MainWindow):
    main_box:toga.Box
    tab_area:toga.OptionContainer

    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Contents
        self.main_box = toga.Box()
        self.tab_area = toga.OptionContainer(style=pack.Pack(flex=1), content=[
            toga.OptionItem(text=_('Welcome'), content=toga.Label(_('Welcome to Meu PDF'))),
        ], on_select=self.on_select_tab)
        self.main_box.add(self.tab_area)

        # Toolbar and menus
        self.app.commands.clear()
        self.toolbar.clear()
        create_commands(app, self, app.commands, self.toolbar)

        self.content = self.main_box

    def open_dialog(self, widget, **kwargs):
        dialog = toga.OpenFileDialog(_('Open PDF file'), file_types=['PDF'])
        
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file, self.app.server_dir, self.app.files_uri, self.app.host, self.app.port)
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab
        if not self.app.binded_to_port:
            dialog = toga.ErrorDialog(_('Network error!'), _('It was not possible to bind to a network port. Document contents will not be displayed.'))
            task = asyncio.create_task(self.dialog(dialog))
    
    def open_merge_window(self, widget, **kwargs):
        merge_window = MergeWindow()
        merge_window.show()
        merge_window.open_dialog(widget, first_selection=True)

    def close_tab(self, widget, **kwargs):
        if self.tab_area.current_tab.index == 0: # Do not close welcome page
            return
        try:
            tab = self.tab_area.current_tab
            i = self.tab_area.content.index(tab)
            if i == len(self.tab_area.content) - 1:
                self.tab_area.current_tab = i - 1
            else:
                self.tab_area.current_tab = i + 1
            self.tab_area.content.remove(tab)
        except Exception as e:
            print(e)

    def on_select_tab(self, widget, **kwargs):
        if self.tab_area.content.index(self.tab_area.current_tab) == 0:
            self.app.commands['close_tab'].enabled = False
        else:
            self.app.commands['close_tab'].enabled = True
