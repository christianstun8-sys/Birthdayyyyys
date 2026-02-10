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
from utils.babel import translator

BACKGROUND_IMAGE_PATH = 'data/birthday_background.jpg'
FONT_PATH = 'data/arial.ttf'
IMAGE_TEXT_COLOR = (0, 0, 0, 255)

DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age. Birthday!"

def get_db_path(guild_id: int) -> str:
    return f'databases/guild_{guild_id}.db'

async def ensure_tables(db: aiosqlite.Connection):
    await db.execute('''
                     CREATE TABLE IF NOT EXISTS guild_settings (
                                                                   guild_id INTEGER PRIMARY KEY,
                                                                   birthday_channel_id INTEGER,
                                                                   config_embed_color INTEGER DEFAULT 0x3aaa06,
                                                                   birthday_role_id INTEGER,
                                                                   birthday_image_enabled INTEGER DEFAULT 1,
                                                                   birthday_image_background TEXT,
                                                                   lang TEXT DEFAULT 'en',
                                                                   title_no_age TEXT,
                                                                   message_no_age TEXT,
                                                                   footer_no_age TEXT,
                                                                   image_title_no_age TEXT,
                                                                   title_with_age TEXT,
                                                                   message_with_age TEXT,
                                                                   footer_with_age TEXT,
                                                                   image_title_with_age TEXT
                     )
                     ''')
    await db.execute('''
                     CREATE TABLE IF NOT EXISTS birthdays (
                                                              user_id INTEGER PRIMARY KEY,
                                                              month INTEGER,
                                                              day INTEGER,
                                                              year INTEGER,
                                                              timezone TEXT DEFAULT 'Europe/Berlin'
                     )
                     ''')
    await db.commit()

async def setup_database(guild_id: int):
    db_path = get_db_path(guild_id)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await ensure_tables(db)

def format_age(age: int, lang: str) -> str:
    if lang == "de":
        return f"{age}."

    if 11 <= (age % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(age % 10, 'th')

    return f"{age}{suffix}"

async def load_bot_config(bot, guild_id: int):
    await setup_database(guild_id)
    db_path = get_db_path(guild_id)
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                bot.guild_configs[guild_id] = dict(zip(columns, row))
            else:
                bot.guild_configs[guild_id] = {"lang": "de"}

async def load_all_guild_configs(bot):
    for guild in bot.guilds:
        try:
            await load_bot_config(bot, guild.id)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration für Guild {guild.id}: {e}")

async def generate_birthday_image(user: discord.Member, title_text: str, name_text: str, background_path: str = None):
    try:
        bg_path = background_path if background_path and os.path.exists(background_path) else BACKGROUND_IMAGE_PATH
        if not os.path.exists(bg_path):
            return None

        with Image.open(bg_path) as img:
            draw = ImageDraw.Draw(img)
            try:
                font_title = ImageFont.truetype(FONT_PATH, 60)
                font_name = ImageFont.truetype(FONT_PATH, 80)
            except:
                font_title = ImageFont.load_default()
                font_name = ImageFont.load_default()

            draw.text((img.width // 2, 150), title_text, font=font_title, fill=IMAGE_TEXT_COLOR, anchor="mm")
            draw.text((img.width // 2, 300), name_text, font=font_name, fill=IMAGE_TEXT_COLOR, anchor="mm")

            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.display_avatar.url)) as resp:
                    if resp.status == 200:
                        avatar_data = io.BytesIO(await resp.read())
                        with Image.open(avatar_data) as avatar:
                            avatar = avatar.resize((200, 200)).convert("RGBA")
                            mask = Image.new("L", (200, 200), 0)
                            draw_mask = ImageDraw.Draw(mask)
                            draw_mask.ellipse((0, 0, 200, 200), fill=255)
                            img.paste(avatar, (img.width // 2 - 100, 450), mask)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            return discord.File(img_byte_arr, filename="birthday_card.png")
    except Exception as e:
        print(f"Fehler bei der Bildgenerierung: {e}")
        return None

async def get_first_writable_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel
    return None

class BirthdayCheckTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    @tasks.loop(minutes=1)
    async def check_birthdays(self):
        now_utc = datetime.now(pytz.utc)
        if now_utc.minute != 0:
            return

        for guild in self.bot.guilds:
            await self.bot.load_bot_config(self.bot, guild.id)
            current_config = self.bot.guild_configs.get(guild.id, {})
            lang = current_config.get("lang", "en")
            _ = translator.get_translation(lang)

            db_path = get_db_path(guild.id)
            if not os.path.exists(db_path):
                continue

            birthdays_today = []
            birthdays_to_remove_role = []

            async with aiosqlite.connect(db_path) as db:
                async with db.execute("SELECT user_id, month, day, timezone FROM birthdays") as cursor:
                    async for user_id, month, day, tz_name in cursor:
                        try:
                            tz = pytz.timezone(tz_name or 'Europe/Berlin')
                            now_tz = datetime.now(tz)

                            if now_tz.month == month and now_tz.day == day and now_tz.hour == 0:
                                birthdays_today.append(user_id)

                            yesterday = now_tz - timedelta(days=1)
                            if yesterday.month == month and yesterday.day == day and now_tz.hour == 0:
                                birthdays_to_remove_role.append(user_id)
                        except Exception as e:
                            print(f"Fehler bei Zeitzonenberechnung für {user_id}: {e}")

            birthday_channel_id = current_config.get("birthday_channel_id")
            birthday_role_id = current_config.get("birthday_role_id")
            birthday_role = guild.get_role(birthday_role_id) if birthday_role_id else None

            if birthdays_today:
                target_channel = guild.get_channel(birthday_channel_id) if birthday_channel_id else await self.bot.get_first_writable_channel(guild)

                for user_id in birthdays_today:
                    member = guild.get_member(user_id)
                    if not member:
                        continue

                    birth_year = 0
                    async with aiosqlite.connect(db_path) as db:
                        async with db.execute("SELECT year FROM birthdays WHERE user_id = ?", (user_id,)) as cursor:
                            row = await cursor.fetchone()
                            if row and row[0]:
                                birth_year = row[0]

                    age_str = ""
                    message_type = "no_age"
                    if birth_year > 0:
                        tz = pytz.timezone(current_config.get("timezone", "Europe/Berlin"))
                        age = datetime.now(tz).year - birth_year
                        age_str = format_age(age, lang)
                        message_type = "with_age"

                    embed_title = current_config.get(f"title_{message_type}") or (_("🎉 Herzlichen Glückwunsch zum Geburtstag, %username!") if message_type == "no_age" else _("🎂 Alles Gute zum %age. Geburtstag, %username!"))
                    embed_message = current_config.get(f"message_{message_type}") or (_("Bitte sende deine besten Wünsche an %mention!") if message_type == "no_age" else _("Lasst uns %mention zu seinem %age. Geburtstag gratulieren!"))
                    embed_footer = current_config.get(f"footer_{message_type}") or (None if message_type == "no_age" else _("Feiere schön!"))
                    image_title = current_config.get(f"image_title_{message_type}") or (DEFAULT_IMAGE_NO_AGE_TITLE if message_type == "no_age" else DEFAULT_IMAGE_WITH_AGE_TITLE)

                    final_embed_title = embed_title.replace("%username", member.display_name).replace("%age", age_str)
                    final_embed_message = embed_message.replace("%username", member.display_name).replace("%age", age_str).replace("%mention", member.mention)
                    final_embed_footer = embed_footer.replace("%username", member.display_name).replace("%age", age_str) if embed_footer else None
                    final_image_title = image_title.replace("%username", member.display_name).replace("%age", age_str)

                    embed = discord.Embed(title=final_embed_title, description=final_embed_message, color=current_config.get("config_embed_color", 0x3aaa06))
                    embed.set_thumbnail(url=member.display_avatar.url)
                    if final_embed_footer:
                        embed.set_footer(text=final_embed_footer)

                    generated_image_file = None
                    if current_config.get("birthday_image_enabled", 1):
                        generated_image_file = await self.bot.generate_birthday_image(member, final_image_title, member.display_name, current_config.get("birthday_image_background"))
                        if generated_image_file:
                            embed.set_image(url="attachment://birthday_card.png")

                    if target_channel:
                        try:
                            await target_channel.send(embed=embed, file=generated_image_file)
                        except Exception as e:
                            print(f"Fehler beim Senden der Geburstagsnachricht in {guild.name}: {e}")

                    if birthday_role and birthday_role not in member.roles:
                        try:
                            if guild.me.top_role <= birthday_role:
                                continue
                            await member.add_roles(birthday_role, reason=_("Geburtstagsrolle zugewiesen"))
                        except Exception as e:
                            print(f"Unerwarteter Fehler beim Zuweisen der Rolle an {member.name}: {e}")

            if birthday_role and birthdays_to_remove_role:
                for user_id in birthdays_to_remove_role:
                    member = guild.get_member(user_id)
                    if member and birthday_role in member.roles:
                        try:
                            await member.remove_roles(birthday_role, reason=_("Geburtstagsrolle entfernt (Geburtstag vorbei)"))
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
    bot.load_all_guild_configs = load_all_guild_configs

    await bot.add_cog(BirthdayCheckTask(bot))