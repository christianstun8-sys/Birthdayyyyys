import collections.abc

import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, date, timedelta
from collections import defaultdict
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io
import os
import asyncio
import pytz

# --- Konstanten für Pfade (angepasst an das neue data-Verzeichnis) ---
BACKGROUND_IMAGE_PATH = 'data/birthday_background.jpg'
FONT_PATH = 'data/arial.ttf'
IMAGE_TEXT_COLOR = (0, 0, 0, 255)

# --- Standardwerte (aus dem Original-Skript übernommen) ---
DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age. Birthday!"

# --- Hilfsfunktionen für die Datenbank und Konfiguration ---

def get_db_path(guild_id: int) -> str:
    """Gibt den Pfad zur SQLite-Datenbank für eine spezifische Guild zurück."""
    return f'databases/guild_{guild_id}.db' # Pfad angepasst auf "databases"

async def ensure_tables(db: aiosqlite.Connection):
    """Stellt sicher, dass die notwendigen Datenbanktabellen existieren und führt Migrationen durch."""
    await db.execute('''
                     CREATE TABLE IF NOT EXISTS guild_settings (
                                                                   guild_id INTEGER PRIMARY KEY,
                                                                   birthday_channel_id INTEGER,
                                                                   config_embed_color INTEGER,
                                                                   birthday_image_enabled BOOLEAN,
                                                                   birthday_image_background TEXT,
                                                                   message_no_age TEXT,
                                                                   title_no_age TEXT,
                                                                   footer_no_age TEXT,
                                                                   message_with_age TEXT,
                                                                   title_with_age TEXT,
                                                                   footer_with_age TEXT,
                                                                   image_title_no_age TEXT,
                                                                   image_title_with_age TEXT,
                                                                   birthday_role_id INTEGER,
                                                                   alerts INTEGER
                     )
                     ''')
    await db.execute('''
                     CREATE TABLE IF NOT EXISTS birthdays (
                                                              user_id INTEGER PRIMARY KEY,
                                                              guild_id INTEGER,
                                                              day INTEGER,
                                                              month INTEGER,
                                                              year INTEGER,
                                                              timezone TEXT DEFAULT 'Europe/Berlin',
                                                              FOREIGN KEY (guild_id) REFERENCES guild_settings (guild_id) ON DELETE CASCADE
                     )
                     ''')
    # Migrationen: Prüfe und füge neue Spalten hinzu
    async def run_migration(column_name):
        try:
            # Überprüfe, ob die Spalte existiert
            await db.execute(f"SELECT {column_name} FROM guild_settings LIMIT 1")
        except aiosqlite.OperationalError:
            print(f"Füge '{column_name}' Spalte zu 'guild_settings' Tabelle hinzu...")
            # Füge die Spalte hinzu (standardmäßig NULL)
            await db.execute(f"ALTER TABLE guild_settings ADD COLUMN {column_name} INTEGER" if column_name == "birthday_role_id" else f"ALTER TABLE guild_settings ADD COLUMN {column_name} TEXT")

    await run_migration("image_title_no_age")
    await run_migration("image_title_with_age")
    await run_migration("birthday_role_id") # NEUE SPALTE HINZUFÜGEN

    await db.commit()

async def setup_database(guild_id: int):
    """Initialisiert die SQLite-Datenbank für eine spezifische Guild und führt Migrationen durch."""
    async with aiosqlite.connect(get_db_path(guild_id)) as db:
        await ensure_tables(db)

async def load_bot_config(bot: commands.Bot, guild_id: int):
    """Lädt die Konfiguration einer Gilde aus der DB oder setzt Standardwerte."""
    # Definiere Standardwerte, falls die Konfiguration fehlt
    default_config = {
        "config_embed_color": 0x45a6c9,
        "birthday_channel_id": None,
        "birthday_image_enabled": False,
        "birthday_image_background": BACKGROUND_IMAGE_PATH,
        "message_no_age": "Alles Gute zum Geburtstag, %username!",
        "title_no_age": "Herzlichen Glückwunsch!",
        "footer_no_age": "Feiere schön!",
        "message_with_age": "Alles Gute zum %age. Geburtstag, %username!",
        "title_with_age": "Happy %age. Birthday!",
        "footer_with_age": "Lass dich feiern!",
        "image_title_no_age": DEFAULT_IMAGE_NO_AGE_TITLE,
        "image_title_with_age": DEFAULT_IMAGE_WITH_AGE_TITLE,
        "birthday_role_id": None,
        "alerts": None
    }

    config = default_config.copy() # Beginne mit Standardwerten

    await setup_database(guild_id)

    async with aiosqlite.connect(get_db_path(guild_id)) as db:
        cursor = await db.execute("""
                                  SELECT
                                      birthday_channel_id, config_embed_color, birthday_image_enabled, birthday_image_background,
                                      message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age,
                                      image_title_no_age, image_title_with_age, birthday_role_id, alerts
                                  FROM guild_settings WHERE guild_id = ?
                                  """, (guild_id,))
        row = await cursor.fetchone()

        if row:
            # Werte aus der DB laden (Index 0 bis 12, da 13 Spalten nach guild_id)
            config["birthday_channel_id"] = row[0]
            config["config_embed_color"] = row[1]
            config["birthday_image_enabled"] = bool(row[2])
            config["birthday_image_background"] = row[3]
            config["message_no_age"] = row[4]
            config["title_no_age"] = row[5]
            config["footer_no_age"] = row[6]
            config["message_with_age"] = row[7]
            config["title_with_age"] = row[8]
            config["footer_with_age"] = row[9]
            config["image_title_no_age"] = row[10] if row[10] is not None else DEFAULT_IMAGE_NO_AGE_TITLE
            config["image_title_with_age"] = row[11] if row[11] is not None else DEFAULT_IMAGE_WITH_AGE_TITLE
            config["birthday_role_id"] = row[12] # NEUER WERT
            config["alerts"] = row[13]
        else:
            # Standardwerte in die DB speichern, falls kein Eintrag existiert
            await db.execute("""
                INSERT OR REPLACE INTO guild_settings (
                    guild_id, birthday_channel_id, config_embed_color, birthday_image_enabled,
                    birthday_image_background, message_no_age, title_no_age, footer_no_age,
                    message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id, alerts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guild_id, config["birthday_channel_id"], config["config_embed_color"], config["birthday_image_enabled"],
                config["birthday_image_background"], config["message_no_age"], config["title_no_age"], config["footer_no_age"],
                config["message_with_age"], config["title_with_age"], config["footer_with_age"],
                config["image_title_no_age"], config["image_title_with_age"], config["birthday_role_id"], config["alerts"]
            ))
            await db.commit()

    bot.guild_configs[guild_id] = config # Speichere die Konfiguration in der Bot-Instanz
    return config

async def load_all_guild_configs(bot: commands.Bot):
    """Lädt die Konfiguration für alle verbundenen Guilds beim Bot-Start."""
    bot.guild_configs = {}
    await bot.wait_until_ready()

    print("Lade Konfigurationen für alle verbundenen Gilden...")
    for guild in bot.guilds:
        await load_bot_config(bot, guild.id)
    print("Alle Gilden-Konfigurationen geladen.")

    cog = bot.get_cog("BirthdayCheckTask")
    if cog and not cog.check_birthdays.is_running():
        cog.check_birthdays.start()
        print("Geburtstags-Check-Task gestartet.")

async def get_first_writable_channel(guild: discord.Guild) -> discord.TextChannel | None:

    for channel in guild.text_channels:

        bot_permissions = channel.permissions_for(guild.me)

        if bot_permissions.send_messages:
            return channel

    return None

# --- Bildgenerierungsfunktion (Unverändert) ---
async def generate_birthday_image(user: discord.User, main_text: str, username_text: str, background_path: str):
    # ... [Die gesamte generate_birthday_image Funktion bleibt unverändert] ...
    """Generiert ein Geburtstagsbild mit Avatar und Text."""
    try:
        # Lade Hintergrundbild
        final_background_path = background_path
        if not os.path.exists(final_background_path):
            print(f"Hintergrundbild nicht gefunden unter: {final_background_path}. Verwende Standardpfad.")
            final_background_path = BACKGROUND_IMAGE_PATH

        if not os.path.exists(final_background_path):
            print(f"Kritischer Fehler: Standardhintergrundbild {BACKGROUND_IMAGE_PATH} nicht gefunden.")
            return None


        with Image.open(final_background_path).convert("RGBA") as img:
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size

            # Lade Schriftart
            try:
                font_main = ImageFont.truetype(FONT_PATH, 60)
                font_name = ImageFont.truetype(FONT_PATH, 50)
            except IOError:
                font_main = ImageFont.load_default()
                font_name = ImageFont.load_default()

            # Avatar-Position und Größe
            avatar_size = 200
            x_avatar = (img_width // 2) - (avatar_size // 2)
            y_avatar = 50

            # Textpositionen
            x_center = img_width // 2
            y_name = y_avatar + avatar_size + 20 # Unter dem Avatar
            y_main = y_name + 60 # Unter dem Namen

            # --- TEXTE AUF DAS BILD ZEICHNEN ---
            draw.text((x_center, y_name), username_text, font=font_name, fill=IMAGE_TEXT_COLOR, anchor="mm")
            draw.text((x_center, y_main), main_text, font=font_main, fill=IMAGE_TEXT_COLOR, anchor="mm")

            # Avatar hinzufügen
            try:
                avatar_url = user.display_avatar.url
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(avatar_url)) as resp:
                        if resp.status == 200:
                            avatar_data = io.BytesIO(await resp.read())
                            avatar_img = Image.open(avatar_data).convert("RGBA")

                            avatar_img = avatar_img.resize((avatar_size, avatar_size))

                            mask = Image.new('L', (avatar_size, avatar_size), 0)
                            draw_mask = ImageDraw.Draw(mask)
                            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

                            img.paste(avatar_img, (x_avatar, y_avatar), mask)
            except Exception as e:
                print(f"Fehler beim Hinzufügen des Avatars zum Bild: {e}")

            # Speichere das Bild in einem BytesIO-Objekt
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return discord.File(img_byte_arr, filename='birthday_card.png')
    except Exception as e:
        print(f"Fehler beim Generieren des Geburtstagsbildes: {e}")
        return None


# --- Cog-Klasse ---
class BirthdayCheckTask(commands.Cog, name="BirthdayCheckTask"):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=1.0)
    async def check_birthdays(self):

        # Iteriere über alle Gilden
        for guild_id, current_config in list(self.bot.guild_configs.items()):

            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            # Konfigurationswerte für diese Gilde
            birthday_channel_id = current_config.get("birthday_channel_id")
            birthday_role_id = current_config.get("birthday_role_id")
            birthday_role = guild.get_role(birthday_role_id) if birthday_role_id else None

            target_channel = None
            if birthday_channel_id:
                target_channel = guild.get_channel(birthday_channel_id)

            if not target_channel:
                target_channel = await self.bot.get_first_writable_channel(guild)

            # --- 1. GEBURTSTAG HEUTE: Nachricht senden und Rolle zuweisen ---

            birthdays_to_announce = []
            birthdays_to_remove_role = []

            try:
                async with aiosqlite.connect(get_db_path(guild_id)) as db:
                    await ensure_tables(db)
                    cursor = await db.execute(
                        "SELECT user_id, day, month, year, timezone FROM birthdays WHERE guild_id = ?",
                        (guild_id,)
                    )
                    all_birthdays = await cursor.fetchall()

                    for user_id, b_day, b_month, b_year, tz_name in all_birthdays:
                        try:
                            tz = pytz.timezone(tz_name or 'Europe/Berlin')
                            now_tz = datetime.now(tz)

                            # Check ob HEUTE Geburtstag in dieser Zeitzone ist
                            if now_tz.day == b_day and now_tz.month == b_month and now_tz.hour == 0:
                                birthdays_to_announce.append((user_id, b_day, b_month, b_year, now_tz))

                            # Check ob GESTERN Geburtstag war (zum Rollenentfernen)
                            yesterday_tz = now_tz - timedelta(days=1)
                            if yesterday_tz.day == b_day and yesterday_tz.month == b_month and now_tz.hour == 0:
                                birthdays_to_remove_role.append(user_id)

                        except Exception as tz_err:
                            print(f"Zeitzonenfehler für User {user_id}: {tz_err}")

            except Exception as e:
                print(f"Fehler beim Abrufen der Geburtstage in Gilde {guild.name}: {e}")

            # Nachricht senden
            if target_channel and birthdays_to_announce:
                for user_id, day, month, birth_year, now_tz in birthdays_to_announce:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    if not user: continue

                    age_str = ""
                    message_type_key = "no_age"
                    if birth_year is not None and birth_year > 0:
                        age = now_tz.year - birth_year
                        age_str = str(age)
                        message_type_key = "with_age"

                    embed_title = current_config.get(f"title_{message_type_key}")
                    embed_message = current_config.get(f"message_{message_type_key}")
                    embed_footer = current_config.get(f"footer_{message_type_key}")
                    image_title = current_config.get(f"image_title_{message_type_key}")

                    final_embed_title = embed_title.replace("%username", user.display_name).replace("%age", age_str)
                    final_embed_message = embed_message.replace("%username", user.display_name).replace("%age", age_str).replace("%mention", user.mention)
                    final_embed_footer = embed_footer.replace("%username", user.display_name).replace("%age", age_str) if embed_footer else None
                    final_image_title = image_title.replace("%username", user.display_name).replace("%age", age_str)

                    embed_color = current_config.get("config_embed_color", 0x45a6c9)
                    embed = discord.Embed(title=final_embed_title, description=final_embed_message, color=embed_color)
                    embed.set_thumbnail(url=user.display_avatar.url)
                    if final_embed_footer: embed.set_footer(text=final_embed_footer)

                    generated_image_file = None
                    if current_config.get("birthday_image_enabled", False):
                        background_path = current_config.get("birthday_image_background", BACKGROUND_IMAGE_PATH)
                        generated_image_file = await generate_birthday_image(user, final_image_title, user.display_name, background_path)
                        if generated_image_file: embed.set_image(url="attachment://birthday_card.png")

                    try:
                        if generated_image_file:
                            await target_channel.send(embed=embed, file=generated_image_file)
                        else:
                            await target_channel.send(embed=embed)
                        print(f"Geburtstagsnachricht für {user.name} in Gilde {guild.name} gesendet.")
                    except Exception as e:
                        print(f"Unerwarteter Fehler beim Senden der Nachricht für {user.name} in Gilde {guild.name}: {e}")

            # ROLLE ZUWEISEN
            if birthday_role:
                for user_id, _, _, _, _ in birthdays_to_announce:
                    member = guild.get_member(user_id)
                    if member and birthday_role not in member.roles:
                        try:
                            if guild.me.top_role <= birthday_role:
                                continue
                            await member.add_roles(birthday_role, reason="Geburtstagsrolle zugewiesen")
                        except Exception as e:
                            print(f"Unerwarteter Fehler beim Zuweisen der Rolle an {member.name}: {e}")

            # --- 2. GEBURTSTAG GESTERN: Rolle entfernen ---
            if birthday_role and birthdays_to_remove_role:
                for user_id in birthdays_to_remove_role:
                    member = guild.get_member(user_id)
                    if member and birthday_role in member.roles:
                        try:
                            await member.remove_roles(birthday_role, reason="Geburtstagsrolle entfernt (Geburtstag vorbei)")
                            print(f"Rolle {birthday_role.name} von {member.name} entfernt.")
                        except Exception as e:
                            print(f"Unerwarteter Fehler beim Entfernen der Rolle von {member.name}: {e}")


async def setup(bot):
    bot.get_db_path = get_db_path
    bot.ensure_tables = ensure_tables
    bot.setup_database = setup_database
    bot.load_bot_config = load_bot_config
    bot.generate_birthday_image = generate_birthday_image
    bot.get_first_writable_channel = get_first_writable_channel

    await bot.add_cog(BirthdayCheckTask(bot))