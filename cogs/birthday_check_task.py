from datetime import datetime, timedelta
import aiohttp
import discord
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont
import pytz
import aiomysql
import glob
import io
import os
import random


from utils.babel import translator

BACKGROUND_IMAGE_PATH = "data/birthday_background.jpg"
FONT_PATH = "data/arial.ttf"
IMAGE_TEXT_COLOR = (0, 0, 0, 255)

DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age Birthday!"


def format_age(age: int, lang: str) -> str:
    if lang == "de":
        return f"{age}."

    if lang == "en":
        if 11 <= (age % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(age % 10, "th")
        return f"{age}{suffix}"

    return str(age)

async def setup_database_record(bot, guild_id: int, language: str):
    async with bot.db_pool.acquire() as db:
        async with db.cursor() as cursor:
            try:
                await cursor.execute("""INSERT INTO guild_settings (guild_id, config_embed_color, lang, message_time) VALUES (%s, %s, %s, %s)""", (guild_id, 0x45A6C9, language, "08:00"))
                await db.commit()
            except aiomysql.IntegrityError:
                pass

async def remove_database_record(bot, guild_id: int):
    async with bot.db_pool.acquire() as db:
        async with db.cursor() as cursor:
            await cursor.execute("""DELETE FROM guild_settings WHERE guild_id = %s""", (guild_id,))
            await cursor.execute("""DELETE FROM birthdays WHERE guild_id = %s""", (guild_id,))
            await db.commit()

async def load_bot_config(bot, guild_id: int):
    async with bot.db_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM guild_settings WHERE guild_id = %s", (guild_id,)
            )
            row = await cursor.fetchone()

            if row:
                columns = [column[0] for column in cursor.description]
                bot.guild_configs[guild_id] = dict(zip(columns, row))
            else:
                bot.guild_configs[guild_id] = {
                    "guild_id": guild_id,
                    "birthday_channel_id": None,
                    "config_embed_color": 0x45A6C9,
                    "birthday_role_id": None,
                    "birthday_image_enabled": False,
                    "lang": "en",
                    "title_no_age": None,
                    "message_no_age": None,
                    "footer_no_age": None,
                    "image_title_no_age": None,
                    "title_with_age": None,
                    "message_with_age": None,
                    "footer_with_age": None,
                    "image_title_with_age": None,
                    "message_time": "08:00",
                }
                await cursor.execute(
                    """
                    INSERT INTO guild_settings (
                        guild_id, birthday_channel_id, config_embed_color, birthday_role_id,
                        birthday_image_enabled, lang,
                        title_no_age, message_no_age, footer_no_age, image_title_no_age,
                        title_with_age, message_with_age, footer_with_age, image_title_with_age, message_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        guild_id,
                        None,
                        0x45A6C9,
                        None,
                        False,
                        "en",
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        "08:00",
                    ),
                )


async def load_all_guild_configs(bot):
    for guild in bot.guilds:
        try:
            await load_bot_config(bot, guild.id)
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration für Guild {guild.id}: {e}")


async def generate_birthday_image(
        user: discord.Member,
        title_text: str,
        name_text: str,
        background_path: str = None,
):
    try:
        bg_path = (
            background_path
            if background_path and os.path.exists(background_path)
            else BACKGROUND_IMAGE_PATH
        )
        if not os.path.exists(bg_path):
            return None

        with Image.open(bg_path) as img:
            draw = ImageDraw.Draw(img)

            try:
                font_title = ImageFont.truetype(FONT_PATH, 75)
                font_name = ImageFont.truetype(FONT_PATH, 105)
            except Exception:
                font_title = ImageFont.load_default()
                font_name = ImageFont.load_default()

            center_x = img.width // 2
            center_y = img.height // 3

            y_title = center_y - 100
            y_name = center_y + 15

            draw.text(
                (center_x, y_title),
                title_text,
                font=font_title,
                fill=IMAGE_TEXT_COLOR,
                anchor="mm",
            )
            draw.text(
                (center_x, y_name),
                name_text,
                font=font_name,
                fill=IMAGE_TEXT_COLOR,
                anchor="mm",
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(str(user.display_avatar.url)) as resp:
                    if resp.status == 200:
                        avatar_data = io.BytesIO(await resp.read())
                        with Image.open(avatar_data) as avatar:
                            avatar_size = int(img.height * 0.45)
                            avatar = avatar.resize((avatar_size, avatar_size)).convert("RGBA")

                            mask = Image.new("L", (avatar_size, avatar_size), 0)
                            draw_mask = ImageDraw.Draw(mask)
                            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

                            avatar_alpha = avatar.split()[3]

                            final_mask = Image.new("L", (avatar_size, avatar_size), 0)
                            final_mask.paste(mask, (0, 0), mask=avatar_alpha)

                            x_pos = center_x - (avatar_size // 2)
                            y_pos = img.height - avatar_size

                            img.paste(avatar, (x_pos, y_pos), final_mask)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
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
        for guild in self.bot.guilds:
            await self.bot.load_bot_config(self.bot, guild.id)
            current_config = self.bot.guild_configs.get(guild.id, {})
            lang = current_config.get("lang", "en")
            _ = translator.get_translation(lang)

            config_time_str = current_config.get("message_time") or "00:00"
            try:
                target_time = datetime.strptime(config_time_str, "%H:%M").time()
            except ValueError:
                try:
                    parts = config_time_str.split(":")
                    target_time = datetime.strptime(
                        f"{parts[0]}:{parts[1]}", "%H:%M"
                    ).time()
                except Exception:
                    target_time = datetime.strptime("00:00", "%H:%M").time()

            birthdays_today = []
            birthdays_to_remove_role = []

            async with self.bot.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "SELECT user_id, month, day, timezone FROM birthdays WHERE"
                        " guild_id = %s",
                        (guild.id,),
                    )
                    rows = await cursor.fetchall()
                    for user_id, month, day, tz_name in rows:
                        try:
                            tz = pytz.timezone(tz_name or "Europe/Berlin")
                            now_tz = datetime.now(tz)

                            if (
                                    now_tz.month == month
                                    and now_tz.day == day
                                    and now_tz.hour == target_time.hour
                                    and now_tz.minute == target_time.minute
                            ):
                                birthdays_today.append(user_id)

                            if now_tz.hour == 0 and now_tz.minute == 0:
                                yesterday = now_tz - timedelta(days=1)
                                if yesterday.month == month and yesterday.day == day:
                                    birthdays_to_remove_role.append(user_id)
                        except Exception as e:
                            print(f"Fehler bei Zeitzonenberechnung für {user_id}: {e}")

            birthday_channel_id = current_config.get("birthday_channel_id")
            birthday_role_id = current_config.get("birthday_role_id")
            birthday_role = (
                guild.get_role(birthday_role_id) if birthday_role_id else None
            )

            if birthdays_today:
                target_channel = (
                    guild.get_channel(birthday_channel_id)
                    if birthday_channel_id
                    else await self.bot.get_first_writable_channel(guild)
                )

                for user_id in birthdays_today:
                    member = guild.get_member(user_id)
                    if not member:
                        continue

                    birth_year = 0
                    user_tz_name = "Europe/Berlin"

                    async with self.bot.db_pool.acquire() as conn:
                        async with conn.cursor() as cursor:
                            await cursor.execute(
                                "SELECT year, timezone FROM birthdays WHERE guild_id = %s"
                                " AND user_id = %s",
                                (guild.id, user_id),
                            )
                            row = await cursor.fetchone()
                            if row:
                                if row[0]:
                                    birth_year = row[0]
                                if row[1]:
                                    user_tz_name = row[1]

                    age_str = ""
                    message_type = "no_age"
                    if birth_year > 0:
                        tz = pytz.timezone(user_tz_name)
                        age = datetime.now(tz).year - birth_year
                        print(f"[BIRTHDAY DEBUG] guild={guild.name!r} lang={lang!r} age={age}")
                        age_str = format_age(age, lang)
                        print(f"[BIRTHDAY DEBUG] age_str={age_str!r}")
                        message_type = "with_age"

                    embed_title = current_config.get(f"title_{message_type}") or (
                        _("🎉 Herzlichen Glückwunsch zum Geburtstag, %username!")
                        if message_type == "no_age"
                        else _("🎂 Alles Gute zum %age Geburtstag, %username!")
                    )
                    embed_message = current_config.get(f"message_{message_type}") or (
                        _("Bitte sende deine besten Wünsche an %mention!")
                        if message_type == "no_age"
                        else _(
                            "Lasst uns %mention zu seinem %age Geburtstag gratulieren!"
                        )
                    )
                    embed_footer = current_config.get(f"footer_{message_type}") or (
                        None if message_type == "no_age" else _("Feiere schön!")
                    )
                    image_title = current_config.get(f"image_title_{message_type}") or (
                        DEFAULT_IMAGE_NO_AGE_TITLE
                        if message_type == "no_age"
                        else DEFAULT_IMAGE_WITH_AGE_TITLE
                    )

                    final_embed_title = embed_title.replace(
                        "%username", member.display_name
                    ).replace("%age", age_str)
                    final_embed_message = (
                        embed_message.replace("%username", member.display_name)
                        .replace("%age", age_str)
                        .replace("%mention", member.mention)
                    )
                    final_embed_footer = (
                        embed_footer.replace("%username", member.display_name).replace(
                            "%age", age_str
                        )
                        if embed_footer
                        else None
                    )
                    final_image_title = image_title.replace(
                        "%username", member.display_name
                    ).replace("%age", age_str)

                    embed = discord.Embed(
                        title=final_embed_title,
                        description=final_embed_message,
                        color=current_config.get("config_embed_color", 0x3AAA06),
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    if final_embed_footer:
                        embed.set_footer(text=final_embed_footer)

                    generated_image_file = None
                    if current_config.get("birthday_image_enabled", True):
                        IMAGE_DIR = "data/custom_images"

                        custom_files = glob.glob(os.path.join(IMAGE_DIR, f"{guild.id}_*.*"))

                        selected_background = None
                        if custom_files:
                            selected_background = random.choice(custom_files)

                        generated_image_file = await self.bot.generate_birthday_image(
                            member,
                            final_image_title,
                            member.display_name,
                            selected_background,
                        )

                    if target_channel:
                        try:
                            await target_channel.send(embed=embed)
                            if generated_image_file:
                                await target_channel.send(file=generated_image_file)
                        except Exception as e:
                            print(
                                f"Fehler beim Senden der Geburstagsnachricht in"
                                f" {guild.name}: {e}"
                            )

                    if birthday_role and birthday_role not in member.roles:
                        try:
                            if guild.me.top_role <= birthday_role:
                                continue
                            await member.add_roles(
                                birthday_role, reason=_("Geburtstagsrolle zugewiesen")
                            )
                        except Exception as e:
                            print(
                                f"Unerwarteter Fehler beim Zuweisen der Rolle an"
                                f" {member.name}: {e}"
                            )

            if birthday_role and birthdays_to_remove_role:
                for user_id in birthdays_to_remove_role:
                    member = guild.get_member(user_id)
                    if member and birthday_role in member.roles:
                        try:
                            await member.remove_roles(
                                birthday_role,
                                reason=_(
                                    "Geburtstagsrolle entfernt (Geburtstag vorbei)"
                                ),
                            )
                        except Exception as e:
                            print(
                                f"Unerwarteter Fehler beim Entfernen der Rolle von"
                                f" {member.name}: {e}"
                            )
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = member.guild.id
        member_id = member.id

        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""SELECT * FROM birthdays WHERE guild_id = %s AND user_id = %s""", (guild_id, member_id))
                row = await cursor.fetchone()
                if row:
                    await cursor.execute("""DELETE FROM birthdays WHERE guild_id = %s AND user_id = %s""", (guild_id, member_id))



async def setup(bot):
    bot.load_bot_config = load_bot_config
    bot.generate_birthday_image = generate_birthday_image
    bot.get_first_writable_channel = get_first_writable_channel
    bot.load_all_guild_configs = load_all_guild_configs

    await bot.add_cog(BirthdayCheckTask(bot))