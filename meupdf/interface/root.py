import kivy

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.config import Config
from kivy.logger import Logger

from pathlib import Path

from . import tab

class MeuPDFRoot(BoxLayout):
    pdf_path = StringProperty("")
    page_number = NumericProperty(0)
    config:Config
    contents:TabbedPanel

    def __init__(self, config:Config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.contents = self.ids['contents']

    def show_file_chooser(self, instance):
        content = FileChooserIconView()
        content.path = self.config.get('permanent', 'last_filepath')
        popup = Popup(title="Choose a PDF file", content=content, size_hint=(0.9, 0.9), )
        content.bind(on_submit=lambda chooser, selection, touch: self.load_pdf(selection, popup))
        popup.open()

    def load_pdf(self, selection, popup):
        if selection:
            self.config.set('permanent', 'last_filepath', str(Path(selection[0]).parent))
            self.config.write()
            for f in selection:
                new_tab_item = TabbedPanelItem(text=Path(f).name)
                new_tab = tab.PDFTab(new_tab_item, f, size_hint=(1, 1))
                new_tab_item.content = new_tab
                self.contents.add_widget(new_tab_item)
                self.contents.switch_to(new_tab_item)
        popup.dismiss()

