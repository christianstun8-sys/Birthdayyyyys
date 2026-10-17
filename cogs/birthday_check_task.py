from datetime import datetime
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

from utils.logger import log

BACKGROUND_IMAGE_PATH = "data/birthday_background.jpg"
FONT_PATH = "data/arial.ttf"
IMAGE_TEXT_COLOR = (0, 0, 0, 255)

DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age Birthday!"


def format_age(age: int, lang: str) -> str:
    if lang in ("de", "cs", "pl", "ru", "uk"):
        return f"{age}."

    if lang == "en":
        if 11 <= (age % 100) <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(age % 10, "th")
        return f"{age}{suffix}"

    if lang == "fr":
        suffix = "er" if age == 1 else "e"
        return f"{age}{suffix}"

    if lang == "es":
        return f"{age}º"

    if lang == "pt":
        if age == 1:
            return f"{age}º"
        return f"{age}º"

    if lang == "tr":
        return f"{age}."

    if lang == "ar":
        return f"{age}"

    if lang == "id":
        return f"{age}"

    if lang == "ja":
        return f"{age}歳"

    if lang == "ko":
        return f"{age}세"

    if lang == "zh":
        return f"{age}岁"

    return str(age)

async def setup_database_record(bot, guild_id: int, language: str):
    async with bot.db_pool.acquire() as db:
        async with db.cursor() as cursor:
            try:
                await cursor.execute(
                    """INSERT INTO guild_settings (
                        guild_id, config_embed_color, lang, message_time,
                        banner_text_position_v, banner_text_position_h,
                        banner_avatar_enabled, banner_text_enabled, banner_avatar_position_v, banner_avatar_position_h,
                        banner_text_color, banner_title_size,
                        banner_name_size, banner_avatar_size_percent, show_avatar_no_age, show_avatar_with_age
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        guild_id,
                        0x45A6C9,
                        language,
                        "08:00",
                        "center",
                        "center",
                        True,
                        True,
                        "bottom",
                        "center",
                        "000000",
                        75,
                        105,
                        45,
                        True,
                        True
                    )
                )
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
                    "banner_text_position_v": "center",
                    "banner_text_position_h": "center",
                    "banner_avatar_enabled": True,
                    "banner_text_enabled": True,
                    "banner_avatar_position_v": "bottom",
                    "banner_avatar_position_h": "center",
                    "banner_text_color": "000000",
                    "banner_title_size": 75,
                    "banner_name_size": 105,
                    "banner_avatar_size_percent": 45,
                    "banner_name_text_no_age": None,
                    "banner_name_text_with_age": None,
                    "show_avatar_no_age": True,
                    "show_avatar_with_age": True
                }
                await cursor.execute(
                    """
                    INSERT INTO guild_settings (
                        guild_id, birthday_channel_id, config_embed_color, birthday_role_id,
                        birthday_image_enabled, lang,
                        title_no_age, message_no_age, footer_no_age, image_title_no_age,
                        title_with_age, message_with_age, footer_with_age, image_title_with_age, message_time,
                        banner_text_position_v, banner_text_position_h, banner_avatar_enabled, banner_text_enabled, banner_avatar_position_v, banner_avatar_position_h,
                        banner_text_color, banner_title_size, banner_name_size, banner_avatar_size_percent,
                        banner_name_text_no_age, banner_name_text_with_age, show_avatar_no_age, show_avatar_with_age 
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        "center",
                        "center",
                        True,
                        True,
                        "bottom",
                        "center",
                        "000000",
                        75,
                        105,
                        45,
                        None,
                        None,
                        True,
                        True
                    ),
                )


async def load_all_guild_configs(bot):
    for guild in bot.guilds:
        try:
            await load_bot_config(bot, guild.id)
        except Exception as e:
            log(f"Error loading configuration for guild {guild.id}: {e}", 'ERROR')


async def generate_birthday_image(
        user: discord.Member,
        title_text: str,
        name_text: str,
        background_path: str = None,
        bot: commands.Bot = None,
        guild_id: int = None,
        banner_config: dict = None,
        with_age: bool = False,
        age_str: str = None,
) -> discord.File:
    try:
        bg_path = (
            background_path
            if background_path and os.path.exists(background_path)
            else BACKGROUND_IMAGE_PATH
        )
        if not os.path.exists(bg_path):
            return None

        if banner_config is None:
            banner_config = {}
            if bot and guild_id:
                await bot.load_bot_config(bot, guild_id)
                config = bot.guild_configs.get(guild_id, {})
                banner_config = {
                    "text_position_v": config.get("banner_text_position_v", "center"),
                    "text_position_h": config.get("banner_text_position_h", "center"),
                    "avatar_activated": config.get("banner_avatar_enabled", True),
                    "text_activated": config.get("banner_text_enabled", True),
                    "avatar_position_v": config.get("banner_avatar_position_v", "bottom"),
                    "avatar_position_h": config.get("banner_avatar_position_h", "center"),
                    "text_color": config.get("banner_text_color", "000000"),
                    "title_size": config.get("banner_title_size", 75),
                    "name_size": config.get("banner_name_size", 105),
                    "avatar_size_percent": config.get("banner_avatar_size_percent", 45),
                    "image_title_no_age": config.get("image_title_no_age", "Happy Birthday!"),
                    "image_title_with_age": config.get("image_title_with_age", "Happy Birthday!"),
                    "banner_name_text_no_age": config.get("banner_name_text_no_age", "%username"),
                    "banner_name_text_with_age": config.get("banner_name_text_with_age", "%username"),
                }
            else:
                banner_config = {
                    "text_position_v": "center",
                    "text_position_h": "center",
                    "avatar_activated": True,
                    "text_activated": True,
                    "avatar_position_v": "bottom",
                    "avatar_position_h": "center",
                    "text_color": "000000",
                    "title_size": 75,
                    "name_size": 105,
                    "avatar_size_percent": 45,
                    "image_title_no_age": "Happy Birthday!",
                    "image_title_with_age": "Happy Birthday!",
                    "banner_name_text_no_age": "%username",
                    "banner_name_text_with_age": "%username",
                }

        with Image.open(bg_path) as img:
            draw = ImageDraw.Draw(img)

            title_size = banner_config.get("title_size") or 75
            name_size = banner_config.get("name_size") or 105

            try:
                font_title = ImageFont.truetype(FONT_PATH, title_size)
                font_name = ImageFont.truetype(FONT_PATH, name_size)
            except Exception:
                font_title = ImageFont.load_default()
                font_name = ImageFont.load_default()

            text_color_hex = banner_config.get("text_color") or "000000"
            if not isinstance(text_color_hex, str) or len(text_color_hex) < 6:
                text_color_hex = "000000"

            text_color = (
                int(text_color_hex[0:2], 16),
                int(text_color_hex[2:4], 16),
                int(text_color_hex[4:6], 16),
                255
            )

            text_y_map = {"top": img.height * 0.2, "center": img.height * 0.4, "bottom": img.height * 0.7}
            text_x_map = {"left": img.width * 0.15, "center": img.width * 0.5, "right": img.width * 0.85}

            v_pos = banner_config.get("text_position_v") or "center"
            h_pos = banner_config.get("text_position_h") or "center"

            y_title = text_y_map.get(v_pos, img.height * 0.4) - 100
            y_name = text_y_map.get(v_pos, img.height * 0.4) + 15
            x_text = text_x_map.get(h_pos, img.width * 0.5)

            if banner_config.get("text_activated", True):
                image_title_key = "image_title_with_age" if with_age else "image_title_no_age"
                image_title_text = banner_config.get(image_title_key) or title_text or "Happy Birthday!"

                if isinstance(image_title_text, str):
                    image_title_text = image_title_text.replace("%username", user.display_name or "")
                    if with_age and age_str:
                        image_title_text = image_title_text.replace("%age", age_str)

                draw.text(
                    (x_text, y_title),
                    str(image_title_text),
                    font=font_title,
                    fill=text_color,
                    anchor="mm",
                )

                banner_name_text_key = "banner_name_text_with_age" if with_age else "banner_name_text_no_age"
                banner_name_text = banner_config.get(banner_name_text_key) or name_text or user.display_name or ""

                if isinstance(banner_name_text, str):
                    banner_name_text = banner_name_text.replace("%username", user.display_name or "")
                    if with_age and age_str:
                        banner_name_text = banner_name_text.replace("%age", age_str)

                draw.text(
                    (x_text, y_name),
                    str(banner_name_text),
                    font=font_name,
                    fill=text_color,
                    anchor="mm",
                )

            if banner_config.get("avatar_activated", True):
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(user.display_avatar.url)) as resp:
                        if resp.status == 200:
                            avatar_data = io.BytesIO(await resp.read())
                            with Image.open(avatar_data) as avatar:
                                avatar_size = int(img.height * (banner_config.get("avatar_size_percent", 45) / 100))
                                avatar = avatar.convert("RGBA").resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

                                mask = Image.new("L", (avatar_size, avatar_size), 0)
                                draw_mask = ImageDraw.Draw(mask)
                                draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)

                                avatar_alpha = avatar.getchannel("A")
                                final_mask = Image.composite(avatar_alpha, Image.new("L", (avatar_size, avatar_size), 0), mask)

                                avatar_y_map = {"top": img.height * 0.1, "center": img.height * 0.5, "bottom": img.height * 0.85}
                                avatar_x_map = {"left": img.width * 0.1, "center": img.width * 0.5, "right": img.width * 0.9}

                                avatar_v = banner_config.get("avatar_position_v") or "bottom"
                                avatar_h = banner_config.get("avatar_position_h") or "center"

                                x_pos = avatar_x_map.get(avatar_h, img.width * 0.5) - (avatar_size // 2)
                                y_pos = avatar_y_map.get(avatar_v, img.height * 0.85) - (avatar_size // 2)

                                img.paste(avatar, (int(x_pos), int(y_pos)), final_mask)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format="PNG")
            img_byte_arr.seek(0)
            return discord.File(img_byte_arr, filename="birthday_card.png")
    except Exception as e:
        log(f"Error during image generation: {e}", 'ERROR')
        return None

async def get_first_writable_channel(guild: discord.Guild):
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            return channel
    return None


class BirthdayCheckTask(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
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
                            if not (now_tz.month == month and now_tz.day == day):
                                birthdays_to_remove_role.append(user_id)
                        except Exception as e:
                            log(f"Error in timezone calculation for {user_id}: {e}", 'ERROR')

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
                        age_str = format_age(age, lang)
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
                    thumbnail_enabled = current_config.get(f'show_avatar_{message_type}')
                    if thumbnail_enabled:
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
                            self.bot,
                            guild.id,
                            with_age=(message_type == "with_age"),
                            age_str=age_str if message_type == "with_age" else None,
                        )

                    if target_channel:
                        try:
                            await target_channel.send(embed=embed)
                            if generated_image_file:
                                await target_channel.send(file=generated_image_file)
                        except Exception as e:
                            log(
                                f"Error sending birthday message in {guild.name}: {e}",
                                'ERROR'
                            )

                    if birthday_role and birthday_role not in member.roles:
                        try:
                            if guild.me.top_role <= birthday_role:
                                continue
                            await member.add_roles(
                                birthday_role, reason=_("Geburtstagsrolle zugewiesen")
                            )
                        except Exception as e:
                            pass

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
                            pass

    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()

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