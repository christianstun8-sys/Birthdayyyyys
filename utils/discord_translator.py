import discord
from discord import app_commands
import os
import json
from utils.logger import log

class DiscordSlashTranslator(app_commands.Translator):
    def __init__(self):
        self.json_path = os.path.join(os.path.dirname(__file__), "translations.json")
        self.translations = {}

    async def load(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            log(f"Native slash translations loaded ({len(self.translations)} languages).")
        else:
            log(f"WARNING: Translation file '{self.json_path}' not found!", 'WARNING')

    async def unload(self):
        pass

    async def translate(self, string: app_commands.locale_str, locale: discord.Locale, context: app_commands.TranslationContext) -> str | None:
        lang_key = locale.value

        if lang_key in ("en-US", "en-GB"):
            lang_key = "en-US"
        elif lang_key in ("de-DE", "de-AT", "de-CH", "de"):
            lang_key = "de"
        elif lang_key in ("es-ES", "es-419"):
            lang_key = "es-ES"
        elif lang_key in ("pt-BR", "pt-PT", "pt"):
            lang_key = "pt-BR"
        elif lang_key in ("zh-CN", "zh-TW", "zh"):
            lang_key = "zh-CN"

        lang_dict = self.translations.get(lang_key)

        if not lang_dict:
            lang_dict = self.translations.get("en-US")

        if lang_dict:
            return lang_dict.get(string.message)

        return None