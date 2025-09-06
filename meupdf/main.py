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

if __name__ == '__main__':
    MeuPDFApp().run()
