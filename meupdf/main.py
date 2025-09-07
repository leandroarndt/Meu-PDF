import kivy
kivy.require('2.3.1')  # Ensure the correct Kivy version is used

from kivy.app import App
from kivy.config import Config
from kivy.logger import Logger

from pathlib import Path

from interface.root import MeuPDFRoot

class MeuPDFApp(App):
    config:Config

    def build_config(self, config):
        config.setdefaults(
            'permanent', {
                'last_filepath': str(Path.home()),
                'last_files': '{}',
            }
        )
        config.setdefaults(
            'interface', {
                'last_files_length': 50,
            }
        )
        Logger.info("MeuPDFApp: set defaults.")
        config.write()
        Logger.info("MeuPDFApp: file written.")
        Logger.info("MeuPDFApp: default path is %s" % config.get('permanent', 'last_filepath'))
        self.config = config

    def build(self):

        self.title = "MeuPDF"
        app = self
        root = MeuPDFRoot(self.config)

        return root

    def save_pages(self):
        for tab in self.root.contents.tab_list:
            try:
                tab.content.save_page()
            except AttributeError: # Not a document tab
                pass
    
    def close_docs(self):
        for tab in self.root.contents.tab_list:
            try:
                tab.content.close()
            except AttributeError: # Not a document tab
                pass

    def on_pause(self):
        self.save_pages()
        return super().on_pause()
    
    def on_resume(self):
        return super().on_resume()
    
    def on_stop(self):
        self.save_pages()
        self.close_docs()
        return super().on_stop()

if __name__ == '__main__':
    MeuPDFApp().run()
