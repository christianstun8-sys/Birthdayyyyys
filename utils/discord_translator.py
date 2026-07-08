import discord
from discord import app_commands
from discord.ext import commands
import os
import json

class DiscordSlashTranslator(app_commands.Translator):
    def __init__(self):
        self.json_path = os.path.join(os.path.dirname(__file__), "translations.json")
        self.translator = {}

    async def load(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
            print(f"Native Slash-Übersetzungen geladen ({len(self.translations)} Sprachen).")
        else:
            print(f"WARNUNG: Übersetzungsdatei '{self.json_path}' wurde nicht gefunden!")


    async def unload(self):
        pass

    async def translate(self, string: app_commands.locale_str, locale: discord.Locale, context: app_commands.TranslationContext) -> str | None:
        lang_key = locale.value

        if lang_key in ("en-US", "en-GB"):
            lang_key = "en-US"
        elif lang_key == "es-ES":
            lang_key = "es-ES"

        lang_dict = self.translations.get(lang_key)

        if not lang_dict:
            lang_dict = self.translations.get("en-US")

        if lang_dict:
            return lang_dict.get(string.message)

        return None