import kivy

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.config import Config
from kivy.logger import Logger

from collections import OrderedDict
from pathlib import Path
import json

from . import tab

class ButtonedLabel(ButtonBehavior, Label):
    pass

class MeuPDFRoot(BoxLayout):
    pdf_path = StringProperty("")
    page_number = NumericProperty(0)
    config:Config
    contents:TabbedPanel

    def __init__(self, config:Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        last_files:OrderedDict = OrderedDict()
        self.config = config
        self.contents = self.ids['contents']
        self.welcome = self.contents.get_def_tab_content()
        last_files_json = self.config.get('permanent', 'last_files')
        try:
            last_files = json.loads(last_files_json, object_hook=OrderedDict)
        except json.JSONDecodeError:
            pass
        for f, p in last_files.items():
            if Path(f).is_file():
                self.ids['recent_files_box'].add_widget(
                    ButtonedLabel(
                        text=Path(f).name,
                        on_release=lambda instance, file_path=f, *args, **kwargs: self.load_pdf([file_path], None)
                    )
                )

    def show_file_chooser(self, instance):
        content = FileChooserIconView()
        content.path = self.config.get('permanent', 'last_filepath')
        popup = Popup(title="Choose a PDF file", content=content, size_hint=(0.9, 0.9), )
        content.bind(on_submit=lambda chooser, selection, touch: self.load_pdf(selection, popup))
        popup.open()

    def load_pdf(self, selection, popup):
        last_files:OrderedDict = OrderedDict()
        page:int = 0
        if selection:
            self.config.set('permanent', 'last_filepath', str(Path(selection[0]).parent))
            last_files_json = self.config.get('permanent', 'last_files')
            try:
                last_files = json.loads(last_files_json, object_hook=OrderedDict)
            except json.JSONDecodeError:
                pass
            try:
                page = last_files[selection[0]]
                last_files.move_to_end(selection[0], last=False)
            except KeyError:
                last_files[selection[0]] = 0
            self.config.set('permanent', 'last_files', json.dumps(last_files))
            self.config.write()
            for f in selection:
                new_tab_item = TabbedPanelItem(text=Path(f).name)
                new_tab = tab.PDFTab(new_tab_item, f, size_hint=(1, 1))
                new_tab_item.content = new_tab
                self.contents.add_widget(new_tab_item)
                self.contents.switch_to(new_tab_item)
                if page: new_tab.go_to_page(page)
        try:
            popup.dismiss()
        except AttributeError: # Did not come from a file dialogue
            pass
