import gettext
from pathlib import Path

locale_path = Path(__file__).parent.resolve() / 'resources/locale/'
language = gettext.translation ('meupdf',
    localedir=locale_path,
    languages=['pt'],
    fallback=True,
)
language.install()