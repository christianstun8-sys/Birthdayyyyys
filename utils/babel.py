import gettext
from pathlib import Path
import os

class Translator:
    def __init__(self, default_lang="de"):
        self.default_lang = default_lang
        self.localedir = Path.joinpath(Path(__file__).parent.parent, "locales")
        self.translations = {}

    def get_translation(self, lang):
        if lang not in self.translations:
            self.translations[lang] = gettext.translation(
                'messages', localedir=self.localedir, languages=[lang], fallback=True
            )
        return self.translations[lang].gettext

translator = Translator()