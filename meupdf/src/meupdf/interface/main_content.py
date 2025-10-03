import asyncio, functools
from pathlib import Path

import toga

from toga.style import pack

from meupdf.interface.commands import create_commands, FileMenuItems
from meupdf.interface.tab import DocumentTab
from meupdf.interface.extract_pages import ExtractPagesWindow
from meupdf.interface.merge import MergeWindow
from meupdf.interface.viewserver import ViewServer
from meupdf.documents import pdf

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

    async def get_page(self, tab):
            result = await tab.view.evaluate_javascript('document.getElementById("pageNumber").value;')
            return result
    
    def extract_current_page(self, widget, **kwargs):
        current_tab = self.tab_area.current_tab
        
        def do_save(task, page):
            file_name = task.result()
            if file_name:
                current_tab.document.extract_pages(file_name, page-1)

        def ask_save(task):
            page = int(task.result())
            dialog = toga.SaveFileDialog(
                _('Choose destination file'),
                f'{current_tab.document.file_path.stem} p {page}.{pdf.DOCUMENT_FORMAT.lower()}',
                file_types=[pdf.DOCUMENT_FORMAT.lower()],
            )
            task = asyncio.create_task(self.dialog(dialog))
            task.add_done_callback(functools.partial(do_save, page=page))

        task = asyncio.create_task(self.get_page(tab=current_tab))
        task.add_done_callback(functools.partial(ask_save))
    
    def open_dialog(self, widget, **kwargs):
        dialog = toga.OpenFileDialog(_('Open PDF file'), file_types=[pdf.DOCUMENT_FORMAT.lower()])
        
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(self.open_dialog_closed)

    def open_dialog_closed(self, task):
        file = task.result()
        if file:
            new_tab = DocumentTab(file, self.app.server_dir, self.app.files_uri, self.app.host, self.app.port) # type: ignore
            self.tab_area.content.append(new_tab)
            self.tab_area.current_tab = new_tab
        if not self.app.binded_to_port: # type: ignore
            dialog = toga.ErrorDialog(_('Network error!'), _('It was not possible to bind to a network port. Document contents will not be displayed.'))
            task = asyncio.create_task(self.dialog(dialog))
    
    def open_extract_pages_window(self, widget, **kwargs):
        def open_window(task, tab):
            page = None
            try:
                page = int(task.result()) - 1
            except ValueError:
                pass
            extract_window = ExtractPagesWindow(tab.document, first_page=page)
            extract_window.show()

        current_tab = self.tab_area.current_tab
        task = asyncio.create_task(self.get_page(tab=current_tab))
        task.add_done_callback(functools.partial(open_window, tab=current_tab))

    def open_merge_window(self, widget, **kwargs):
        merge_window = MergeWindow()
        merge_window.show()
        merge_window.open_dialog(widget, first_selection=True)

    async def save(self, callback, tab:DocumentTab, path:str|Path|None=''):
        path = path or tab.document.file_path
        key = ViewServer.create_expectation(path, int(tab.document.hashed_path()), tab.view.url, callback)
        script =   'var save = async function() {'
        script +=  '  var xhr = new XMLHttpRequest();'
        script += f'  xhr.open("POST", "http://{self.app.host}:{self.app.port}");' # pyright: ignore[reportAttributeAccessIssue]
        script +=  '  xhr.setRequestHeader("Content-Type", "application/pdf");'
        script += f'  xhr.setRequestHeader("path", "{str(tab.file_path).replace('\\', '\\\\')}");'
        script += f'  xhr.setRequestHeader("hash", "{tab.document.hashed_path()}");'
        script += f'  xhr.setRequestHeader("key", "{key}");'
        script +=  '  var doc = await PDFViewerApplication.pdfDocument.saveDocument();'
        script +=  '  xhr.send(doc);'
        script +=  '};'
        script +=  'save();'
        return await tab.view.evaluate_javascript(script)

    def _save_callback(self, path:Path, e:Exception|None, loop, tab:DocumentTab):
        if e:
            dialog = toga.ErrorDialog(_('Error saving file'), f'{_("File")} "{path.name}" {_("could not be saved:")}\n{e}')
            asyncio.run_coroutine_threadsafe(self.dialog(dialog), loop)
            return
        if path != tab.document.file_path:
            tab.text = path.name
            tab.document.file_path = path

    async def save_tab(self, widget, **kwargs):
        if self.tab_area.current_tab.index == 0: # Welcome page
            return

        await self.save(
            functools.partial(
                self._save_callback,
                path=self.tab_area.current_tab.document.file_path,
                loop=asyncio.get_event_loop(),
                tab=self.tab_area.current_tab,
            ),
            tab=self.tab_area.current_tab,
            ) # pyright: ignore[reportArgumentType]

    def save_as(self, widget, **kwargs):
        if self.tab_area.current_tab.index == 0: # Welcome page
            return
        
        tab:DocumentTab = self.tab_area.current_tab

        def do_save(task):
            new_path = task.result()
            if new_path:
                save_task = asyncio.create_task(
                    self.save(
                        functools.partial(
                            self._save_callback,
                            path=new_path,
                            loop=asyncio.get_event_loop(),
                            tab=self.tab_area.current_tab,
                        ),
                        tab=tab,
                        path=new_path,
                    )
                )

        dialog = toga.SaveFileDialog(
            title=_('Choose destination file'),
            suggested_filename=f'{tab.file_path.name}',
            file_types=[pdf.DOCUMENT_FORMAT.lower()],
        )
        task = asyncio.create_task(self.dialog(dialog))
        task.add_done_callback(do_save)


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
        command_list = [
            'close_tab',
            'extract_current_page',
            'extract_pages',
            'save_file',
            'save_as',
        ]
        for command in command_list:
            self.app.commands[command].enabled = \
                self.tab_area.content.index(self.tab_area.current_tab) != 0
