import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from utils.babel import translator
from cogs.birthday_check_task import format_age
import os
import glob
import pathlib
import io
from PIL import Image, ImageOps
import random
from cogs.birthday_check_task import generate_birthday_image


def default_title(_, age: bool):
    if not age:
        return _("🎉 Herzlichen Glückwunsch zum Geburtstag, %username!")
    else:
        return _("🎂 Alles Gute zum %age Geburtstag, %username!")

def default_description(_, age: bool):
    if not age:
        return _("Bitte sende deine besten Wünsche an %mention!")
    else:
        return _("Lasst uns %mention zu seinem %age Geburtstag gratulieren!")

def default_image_title(_, age: bool):
    if not age:
        return _("Happy Birthday!")
    else:
        return _("Happy %age Birthday!")

def with_age_footer(_):
    return _("Feiere schön!")

def build_config_embed(bot: commands.Bot, guild_id: int, l: str = None):
    config = bot.guild_configs.get(guild_id, {})
    lang = l if l else config.get("lang", "en")
    _ = translator.get_translation(lang)
    guild = bot.get_guild(guild_id)

    color_int = config.get("config_embed_color", 0x45a6c9)
    color_hex = f"#{color_int:06X}"

    lang_names = {
        "de": "Deutsch <:de:1470890238871339202>",
        "en": "English <:gb:1470890201449758763>",
        "fr": "Français <:fr:1517917845550534666>",
        "es": "Español <:sp:1517919374046920774>",
        "pl": "Polski <:pl:1517920067256324108>",
        "ru": "Русский <:ru:1517920710889050122>",
        "uk": "Українська <:ua:1518274492156215366>"
    }
    lang_display = lang_names.get(lang, lang.upper())

    alerts_id = config.get("alerts")
    if alerts_id == "" or alerts_id is None:
        alerts_val = f"<#{guild.system_channel.id}>"
    elif alerts_id == 0:
        alerts_val = _("Deaktiviert")
    else:
        alerts_val = f"<#{alerts_id}>"

    channel_id = config.get("birthday_channel_id")
    role_id = config.get("birthday_role_id")

    channel_val = f"<#{channel_id}>" if channel_id else _("Nicht gesetzt")
    role_val = f"<@&{role_id}>" if role_id else _("Keine")
    image_val = _("✅ Aktiviert") if config.get("birthday_image_enabled", False) else _("❌ Deaktiviert")
    time_val = config.get("message_time", "08:00")

    embed = discord.Embed(
        title=_("⚙️ Server-Konfiguration"),
        description=_("Hier kannst du alle Einstellungen für das Geburtstagssystem verwalten.\nNutze das Menü unten zum Konfigurieren."),
        color=color_int
    )

    embed.add_field(name=_("🪛 Kanal"), value=channel_val, inline=True)
    embed.add_field(name=_("⚙️ Rolle"), value=role_val, inline=True)
    embed.add_field(name=_("🖼️ Bilder"), value=image_val, inline=True)
    embed.add_field(name=_("🎨 Farbe"), value=f"`{color_hex}`", inline=True)
    embed.add_field(name=_("🗣️ Sprache"), value=lang_display, inline=True)
    embed.add_field(name=_("⏰ Uhrzeit"), value=f"`{time_val}`", inline=True)
    embed.add_field(name=_("📣 Ankündigungen"), value=alerts_val, inline=True)

    return embed

def is_valid_banner_resolution(width: int, height: int, tolerance: float = 0.15) -> bool:
    if not width or not height or width <= 0 or height <= 0:
        return False

    target_ratio = 1920 / 540
    actual_ratio = width / height

    min_ratio = target_ratio * (1 - tolerance)
    max_ratio = target_ratio * (1 + tolerance)

    is_correct_ratio = min_ratio <= actual_ratio <= max_ratio

    is_big_enough = width >= 800

    return is_correct_ratio and is_big_enough

async def validate_and_read_image(attachment: discord.Attachment) -> tuple[bool, str, Image.Image | None]:
    ALLOWED_FORMATS = {"PNG", "JPEG", "WEBP"}
    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
    if not attachment.filename.lower().endswith(valid_extensions):
        return False, "Ungültige Dateiendung. Erlaubt sind: .png, .jpg, .jpeg, .webp", None

    if attachment.content_type and not attachment.content_type.startswith("image/"):
        return False, "Der Dateityp ist kein gültiges Bild.", None

    try:
        image_bytes = await attachment.read()
        image = Image.open(io.BytesIO(image_bytes))

        if image.format not in ALLOWED_FORMATS:
            return False, f"Das Format '{image.format}' wird nicht unterstützt.", None

        image.verify()

        image = Image.open(io.BytesIO(image_bytes))

        return True, "", image

    except Exception as e:
        return False, "Die Datei ist beschädigt oder kein gültiges Bild.", None

async def process_image(attachment: discord.Attachment):
    image_bytes = await attachment.read()
    image = Image.open(io.BytesIO(image_bytes))

    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    target_size = (1920, 540)
    resized_image = ImageOps.fit(image, target_size, Image.Resampling.LANCZOS)

    return resized_image

async def get_embed_settings(bot, guild_id: int, message_type: str):
    await bot.load_bot_config(bot, guild_id)
    config = bot.guild_configs.get(guild_id, {})
    return (
        config.get(f"title_{message_type}"),
        config.get(f"message_{message_type}"),
        config.get(f"footer_{message_type}"),
        config.get("config_embed_color"),
        config.get(f"image_title_{message_type}")
    )

async def update_embed_settings(bot: commands, guild_id: int, title: str, message: str, footer: str, color: int, image_title: str, message_type: str):
    await bot.load_bot_config(bot, guild_id)

    if message_type == 'no_age':
        bot.guild_configs[guild_id]["title_no_age"] = title
        bot.guild_configs[guild_id]["message_no_age"] = message
        bot.guild_configs[guild_id]["footer_no_age"] = footer
        bot.guild_configs[guild_id]["image_title_no_age"] = image_title
    elif message_type == 'with_age':
        bot.guild_configs[guild_id]["title_with_age"] = title
        bot.guild_configs[guild_id]["message_with_age"] = message
        bot.guild_configs[guild_id]["footer_with_age"] = footer
        bot.guild_configs[guild_id]["image_title_with_age"] = image_title

    config_to_save = bot.guild_configs[guild_id]

    async with bot.db_pool.acquire() as db:
        async with db.cursor() as cur:
            await cur.execute(
                "UPDATE guild_settings SET guild_id = %s, config_embed_color = %s, birthday_channel_id = %s, birthday_image_enabled = %s,"
                "message_no_age = %s, title_no_age = %s, footer_no_age = %s, message_with_age = %s, title_with_age = %s, footer_with_age = %s,"
                "image_title_no_age = %s, image_title_with_age = %s, birthday_role_id = %s WHERE guild_id = %s",
                (
                    guild_id,
                    config_to_save["config_embed_color"],
                    config_to_save["birthday_channel_id"],
                    config_to_save["birthday_image_enabled"],
                    config_to_save["message_no_age"],
                    config_to_save["title_no_age"],
                    config_to_save["footer_no_age"],
                    config_to_save["message_with_age"],
                    config_to_save["title_with_age"],
                    config_to_save["footer_with_age"],
                    config_to_save["image_title_no_age"],
                    config_to_save["image_title_with_age"],
                    config_to_save["birthday_role_id"],
                    guild_id
                )
            )
        await db.commit()


async def update_alerts_settings(bot: commands.Bot, guild_id: int, channel_id: int):
    async with bot.db_pool.acquire() as db:
        async with db.cursor() as cur:
            await cur.execute("UPDATE guild_settings SET alerts = %s WHERE guild_id = %s", (channel_id, guild_id))
        await db.commit()

    if guild_id not in bot.guild_configs:
        await bot.load_bot_config(bot, guild_id)
    bot.guild_configs[guild_id]["alerts"] = channel_id

async def save_uploaded_image(guild_id: int, image_or_attachment) -> str:
    IMAGE_DIR = "data/custom_images"
    os.makedirs(IMAGE_DIR, exist_ok=True)

    if isinstance(image_or_attachment, discord.Attachment):
        filename_source = image_or_attachment.filename
        ext = pathlib.Path(filename_source).suffix.lower()
    else:
        ext = ".png"

    if not ext:
        ext = ".png"

    existing_files = glob.glob(os.path.join(IMAGE_DIR, f"{guild_id}_*.*"))

    max_count = 0
    for file_path in existing_files:
        filename = os.path.basename(file_path)
        try:
            parts = filename.split("_", 1)
            if len(parts) > 1:
                count_part = parts[1].split(".")[0]
                count = int(count_part)
                if count > max_count:
                    max_count = count
        except ValueError:
            continue

    next_count = max_count + 1
    new_filename = f"{guild_id}_{next_count}{ext}"
    full_path = os.path.join(IMAGE_DIR, new_filename)

    if isinstance(image_or_attachment, discord.Attachment):
        await image_or_attachment.save(full_path)
    elif isinstance(image_or_attachment, Image.Image):
        image_or_attachment.save(full_path)
    elif hasattr(image_or_attachment, "save"):
        image_or_attachment.save(full_path)
    else:
        raise TypeError(f"Nicht unterstützter Bildtyp: {type(image_or_attachment)}")

    return full_path

class ResizeButtonView(discord.ui.View):
    def __init__(self, bot: commands.Bot, attachment: discord.Attachment):
        super().__init__(timeout=None)
        self.attachment = attachment

    @discord.ui.button(label="🔧 Größe anpassen", style=discord.ButtonStyle.success)
    async def callback_change_size_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_image = await process_image(self.attachment)
        await save_uploaded_image(interaction.guild.id, new_image)
        return await interaction.response.edit_message(embed=None, content="✅ Bild wurde erfolgreich zugeschnitten und gespeichert!", view=None)

    @discord.ui.button(label="👍 Überspringen", style=discord.ButtonStyle.danger)
    async def callback_change_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await save_uploaded_image(interaction.guild.id, self.attachment)
        await interaction.response.edit_message(embed=None, content="✅ Bild wurde ohne Zuschneiden gespeichert!", view=None)

class ImageUploadModal(discord.ui.Modal):
    def __init__(self, bot, guild_id: int):
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        super().__init__(title="Bilddatei hochladen", timeout=None)
        self.fileupload = discord.ui.FileUpload(
            custom_id="file_upload_input",
            min_values=1,
            max_values=5,
            required=True
        )
        self.add_item(discord.ui.Label(text=_("Bilder hochladen:"), component=self.fileupload))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        attachment = self.fileupload.values[0]
        valid_file_type, err_msg, _ = await validate_and_read_image(attachment)
        if not valid_file_type:
            return await interaction.followup.send(f"❌ {err_msg}", ephemeral=True)

        valid_size = is_valid_banner_resolution(attachment.width, attachment.height)
        if not valid_size:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Falsches Bildformat!",
                    description=f"Das Standard-Bildformat lautet `1920x540`. Das Format deines Bildes ist `{attachment.width}x{attachment.height}`. "
                                f"Texte und Bilder können dadurch verrutschen. Willst du das Bild automatisch zuschneiden lassen, oder dennoch fortfahren?",
                    color=discord.Color.red()
                ),
                view=ResizeButtonView(interaction.client, attachment),
                ephemeral=True
            )

        await save_uploaded_image(interaction.guild.id, attachment)
        return await interaction.followup.send("✅ Datei wurde erfolgreich hochgeladen!", ephemeral=True)


class MessageTimeModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, current_time: str, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        super().__init__(title=_("Sendezeit der Geburtstagsnachricht setzen"))
        self.time_input = discord.ui.TextInput(
            label=_("Neue Zeit (Format: HH:MM)"),
            placeholder="z.B. 08:00",
            default=current_time,
            max_length=5,
            min_length=5
        )
        self.add_item(self.time_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        guild_id = interaction.guild.id
        try:
            time_obj = datetime.strptime(self.time_input.value, "%H:%M").time()
            formatted_time_str = time_obj.strftime("%H:%M")

        except ValueError:
            return await interaction.response.send_message(
                _("❌ Die Eingabe {input} ist keine gültige Zeit.").format(input=self.time_input.value), ephemeral=True
            )

        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET message_time = %s WHERE guild_id = %s",
                    (formatted_time_str, guild_id)
                )
            await db.commit()

        self.bot.guild_configs[guild_id]["message_time"] = formatted_time_str
        embed = build_config_embed(interaction.client, interaction.guild.id)
        return await interaction.response.edit_message(embed=embed, view=MainConfigView(interaction.client, guild_id))

class NoAgeMessageModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, current_settings: list, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("Nachricht ohne Altersangabe anpassen"), timeout=None)

        title_default = current_settings[0] if current_settings and current_settings[0] else default_title(_, False)
        message_default = current_settings[1] if current_settings and current_settings[1] else default_description(_, False)
        footer_default = current_settings[2] if current_settings and current_settings[2] else None
        image_title_default = current_settings[4] if current_settings and current_settings[4] else default_image_title(_, False)

        self.title_input = discord.ui.TextInput(
            label=_("Titel des Embeds (%username)"),
            placeholder=default_title(_, False),
            default=title_default,
            required=False,
            max_length=256
        )
        self.add_item(self.title_input)

        self.message_input = discord.ui.TextInput(
            label=_("Nachricht im Embed (%mention, %username)"),
            placeholder=default_description(_, False),
            default=message_default,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.message_input)

        self.footer_input = discord.ui.TextInput(
            label=_("Footer im Embed (optional, %username)"),
            placeholder=_("Kein Footer"),
            default=footer_default,
            required=False,
            max_length=2048
        )
        self.add_item(self.footer_input)

        self.image_title_input = discord.ui.TextInput(
            label=_("Titel auf Geburtstagsbild (%username)"),
            placeholder=default_image_title(_, False),
            default=image_title_default,
            required=False,
            max_length=256
        )
        self.add_item(self.image_title_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        await interaction.response.defer(ephemeral=True)

        new_title = self.title_input.value or default_title(_, False)
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or default_description(_, False)
        new_image_title = self.image_title_input.value or default_image_title(_, False)
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)

        await update_embed_settings(
            self.bot,
            self.guild_id,
            new_title,
            new_message,
            new_footer,
            current_color,
            new_image_title,
            'no_age'
        )

        await interaction.followup.send(
            _("Die Geburtstagsnachricht (ohne Alter) wurde erfolgreich aktualisiert! ✅"),
            ephemeral=True
        )


class WithAgeMessageModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("Nachricht mit Altersangabe anpassen"), timeout=None)

        title_default = current_settings[0] if current_settings and current_settings[0] else default_title(_, True)
        message_default = current_settings[1] if current_settings and current_settings[1] else default_description(_, True)
        footer_default = current_settings[2] if current_settings and current_settings[2] else with_age_footer(_)
        image_title_default = current_settings[4] if current_settings and current_settings[4] else default_image_title(_, True)

        self.title_input = discord.ui.TextInput(
            label=_("Titel (%age)"),
            placeholder=default_title(_, True),
            default=title_default,
            required=False,
            max_length=256
        )
        self.add_item(self.title_input)

        self.message_input = discord.ui.TextInput(
            label=_("Beschr. (%mention, %username, %age)"),
            placeholder=default_description(_, True),
            default=message_default,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.message_input)

        self.footer_input = discord.ui.TextInput(
            label=_("Footer (optional, %username)"),
            placeholder=_("Standard: Feiere schön!"),
            default=footer_default,
            required=False,
            max_length=2048
        )
        self.add_item(self.footer_input)

        self.image_title_input = discord.ui.TextInput(
            label=_("Bildtitel (%age, %username)"),
            placeholder=default_image_title(_, True),
            default=image_title_default,
            required=False,
            max_length=256
        )
        self.add_item(self.image_title_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        await interaction.response.defer(ephemeral=True)

        new_title = self.title_input.value or default_title(_, True)
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or default_description(_, True)
        new_image_title = self.image_title_input.value or default_image_title(_, True)
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)

        await update_embed_settings(
            self.bot,
            self.guild_id,
            new_title,
            new_message,
            new_footer,
            current_color,
            new_image_title,
            'with_age'
        )

        await interaction.followup.send(
            _("Die Geburtstagsnachricht (mit Alter) wurde erfolgreich aktualisiert! ✅"),
            ephemeral=True
        )


class ConfigColorModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, current_color: int, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("Embed-Farbe anpassen"))

        color_int = current_color if current_color is not None else 0xFFFFFF
        color_hex = f"{color_int:06X}"

        self.color_input = discord.ui.TextInput(
            label=_("Farbe des Embeds (Hex-Code, z.B. FF00FF)"),
            placeholder=_("Aktuell: {color}").format(color=color_hex),
            default=color_hex,
            required=True,
            max_length=6,
            min_length=6
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        await self.bot.load_bot_config(self.bot, self.guild_id)

        new_color_str = self.color_input.value.strip().replace("#", "")
        if not (len(new_color_str) == 6 and all(c in "0123456789abcdefABCDEF" for c in new_color_str)):
            return await interaction.response.send_message(_("Ungültiger Hex-Code."), ephemeral=True)

        new_color = int(new_color_str, 16)

        current_config = self.bot.guild_configs.get(self.guild_id, {})
        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET guild_id = %s, config_embed_color = %s, birthday_channel_id = %s, birthday_image_enabled = %s,"
                    "message_no_age = %s, title_no_age = %s, footer_no_age = %s, message_with_age = %s, title_with_age = %s, footer_with_age = %s,"
                    "image_title_no_age = %s, image_title_with_age = %s, birthday_role_id = %s WHERE guild_id = %s",
                    (
                        self.guild_id,
                        new_color,
                        current_config.get("birthday_channel_id"),
                        current_config.get("birthday_image_enabled"),
                        current_config.get("message_no_age"),
                        current_config.get("title_no_age"),
                        current_config.get("footer_no_age"),
                        current_config.get("message_with_age"),
                        current_config.get("title_with_age"),
                        current_config.get("footer_with_age"),
                        current_config.get("image_title_no_age"),
                        current_config.get("image_title_with_age"),
                        current_config.get("birthday_role_id"),
                        self.guild_id
                    )
                )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["config_embed_color"] = new_color
        await interaction.response.edit_message(embed=build_config_embed(interaction.client, interaction.guild.id), view=MainConfigView(interaction.client, interaction.guild.id))

class ChannelConfigModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("Geburtstagskanal festlegen"))

        self.channel_select = discord.ui.ChannelSelect(
            placeholder=_("Kanal auswählen..."),
            max_values=1,
            min_values=1,
            channel_types=[discord.ChannelType.text],
            required=True
        )
        self.channel_wrapper = discord.ui.Label(
            text=_("Ziel-Kanal für Geburtstage:"),
            component=self.channel_select
        )

        self.add_item(self.channel_wrapper)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        try:
            channel = await interaction.guild.fetch_channel(self.channel_select.values[0].id)
        except discord.Forbidden:
            return await interaction.response.send_message(_("❌ Ich habe keine Berechtigung, auf den konfigurierten Kanal zuzugreifen."), ephemeral=True)
        guild_id = interaction.guild.id
        perms = channel.permissions_for(interaction.guild.me).send_messages

        if not perms:
            return await interaction.response.send_message(_("❌ Ich kann keine Nachrichten in dem ausgewählten Kanal schreiben."), ephemeral=True)

        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET birthday_channel_id = %s WHERE guild_id = %s",
                    (channel.id, guild_id)
                )
            await db.commit()
        self.bot.guild_configs[guild_id]["birthday_channel_id"] = channel.id
        new_embed = build_config_embed(interaction.client, interaction.guild.id)
        await interaction.response.edit_message(
            embed=new_embed,
            view=MainConfigView(self.bot, self.guild_id)
        )

class AlertsConfigModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("News-Kanal festlegen"))

        self.channel_select = discord.ui.ChannelSelect(
            placeholder=_("Kanal auswählen, leer lassen zum Deaktivieren..."),
            max_values=1,
            min_values=0,
            channel_types=[discord.ChannelType.text]
        )
        self.channel_wrapper = discord.ui.Label(
            text=_("Ziel-Kanal für News:"),
            component=self.channel_select
        )

        self.add_item(self.channel_wrapper)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if not self.channel_select.values:
            await update_alerts_settings(self.bot, self.guild_id, 0)
            return await interaction.response.edit_message(embed=build_config_embed(self.bot, self.guild_id), view=MainConfigView(self.bot, self.guild_id))
        try:
            channel = await interaction.guild.fetch_channel(self.channel_select.values[0].id)
        except discord.Forbidden:
            return await interaction.response.send_message(_("❌ Ich habe keine Berechtigung, auf den konfigurierten Kanal zuzugreifen."), ephemeral=True)
        perms = channel.permissions_for(interaction.guild.me).send_messages

        if not perms:
            return await interaction.response.send_message(_("❌ Ich kann keine Nachrichten in dem ausgewählten Kanal schreiben."), ephemeral=True)

        await update_alerts_settings(self.bot, self.guild_id, channel.id)
        await interaction.response.edit_message(
            embed=build_config_embed(self.bot, self.guild_id),
            view=MainConfigView(self.bot, self.guild_id))

class RoleConfigModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        super().__init__(title=_("Geburtstagsrolle festlegen"))

        self.role_select = discord.ui.RoleSelect(
            placeholder=_("Rolle auswählen, leer lassen zum Deaktivieren..."),
            min_values=0,
            max_values=1,
            required=False
        )

        self.role_wrapper = discord.ui.Label(
            text=_("Geburtstagsrolle wählen"),
            component=self.role_select
        )

        self.add_item(self.role_wrapper)

    async def on_submit(self, interaction: discord.Interaction):
        guild_id = self.guild_id
        lang = self.bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if not self.role_select.values:
            async with self.bot.db_pool.acquire() as db:
                async with db.cursor() as cur:
                    await cur.execute(
                        "UPDATE guild_settings SET birthday_role_id = %s WHERE guild_id = %s",
                        (0, guild_id)
                    )
                await db.commit()

            if guild_id in self.bot.guild_configs:
                self.bot.guild_configs[guild_id]["birthday_role_id"] = 0
            embed=build_config_embed(interaction.client, interaction.guild.id)
            return await interaction.response.edit_message(embed=embed, view=MainConfigView(interaction.client, interaction.guild.id))

        selection = self.role_select.values[0]

        role = interaction.guild.get_role(selection.id) or await interaction.guild.fetch_role(selection.id)

        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                _("⚠️ Ich kann die Rolle {role} nicht vergeben, da sie höher oder gleichrangig mit meiner eigenen Rolle ist.").format(role=role.mention),
                ephemeral=True
            )

        if role.is_default():
            return await interaction.response.send_message(
                _("❌ Du kannst nicht die @everyone Rolle als Geburtstagsrolle setzen."),
                ephemeral=True
            )

        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET birthday_role_id = %s WHERE guild_id = %s",
                    (role.id, guild_id)
                )
            await db.commit()

        self.bot.guild_configs[guild_id]["birthday_role_id"] = role.id
        current_config = self.bot.guild_configs[self.guild_id]
        new_status = current_config.get("birthday_image_enabled", False)

        new_embed = build_config_embed(interaction.client, interaction.guild.id)

        await interaction.response.edit_message(
            embed=new_embed,
            view=MainConfigView(self.bot, self.guild_id)
        )

class LanguageConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=60)
        self.bot = bot
        self.guild_id = guild_id

        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        self.add_item(
            discord.ui.Button(
                label=_("Deutsch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_de",
                emoji="<:de:1470890238871339202>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("English"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_en",
                emoji="<:gb:1470890201449758763>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("Französisch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_fr",
                emoji="<:fr:1517917845550534666>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("Spanisch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_es",
                emoji="<:sp:1517919374046920774>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("Polnisch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_pl",
                emoji="<:pl:1517920067256324108>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("Russisch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_ru",
                emoji="<:ru:1517920710889050122>"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("Ukrainisch"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_uk",
                emoji="<:ua:1518274492156215366>"
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id")

        if custom_id == "lang_de":
            await self.set_language(interaction, "de")
        elif custom_id == "lang_en":
            await self.set_language(interaction, "en")
        elif custom_id == "lang_fr":
            await self.set_language(interaction, "fr")
        elif custom_id == "lang_es":
            await self.set_language(interaction, "es")
        elif custom_id == "lang_pl":
            await self.set_language(interaction, "pl")
        elif custom_id == "lang_ru":
            await self.set_language(interaction, "ru")
        elif custom_id == "lang_uk":
            await self.set_language(interaction, "uk")

        return False

    async def set_language(self, interaction: discord.Interaction, lang_code: str):
        current_lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")

        if current_lang == lang_code:
            _ = translator.get_translation(lang_code)
            await interaction.response.send_message(
                _("❌ Diese Sprache ist bereits eingestellt."),
                ephemeral=True
            )
            return

        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET lang = %s WHERE guild_id = %s",
                    (lang_code, self.guild_id)
                )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["lang"] = lang_code
        await self.bot.load_bot_config(self.bot, self.guild_id)

        _ = translator.get_translation(lang_code)

        embed = build_config_embed(interaction.client, interaction.guild.id, lang_code)

        await interaction.response.edit_message(
            embed=embed,
            view=MainConfigView(self.bot, self.guild_id)
        )

class DeleteImageSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, guild_id: int, images: dict):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        options = []
        for filename in images.keys():
            parts = filename.split("_", 1)
            count_str = parts[1].split(".")[0] if len(parts) > 1 else filename
            options.append(
                discord.SelectOption(
                    label=_("Bild {count}").format(count=count_str),
                    value=filename,
                    description=filename,
                    emoji="🗑️"
                )
            )

        super().__init__(
            placeholder=_("Wähle ein Bild zum Löschen..."),
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_file = self.values[0]
        IMAGE_DIR = "data/custom_images"
        file_path = os.path.join(IMAGE_DIR, selected_file)

        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                await interaction.response.send_message(
                    _("✅ Bild `{file}` wurde erfolgreich gelöscht!").format(file=selected_file),
                    ephemeral=True
                )
            except Exception:
                await interaction.response.send_message(
                    _("❌ Fehler beim Löschen der Datei."),
                    ephemeral=True
                )
        else:
            await interaction.response.send_message(
                _("❌ Das Bild existiert nicht mehr."),
                ephemeral=True
            )

class AddImageButton(discord.ui.Button):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        super().__init__(style=discord.ButtonStyle.success, label="➕ Bild hinzufügen")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ImageUploadModal(self.bot, self.guild_id))

class PictureListLayout(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, images: dict, colour: int, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.images = images
        self.files = []

        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        self.container = discord.ui.Container(accent_color=discord.Color(colour))
        self.container.add_item(discord.ui.TextDisplay(_("## Hintergrundbilder verwalten")))
        self.container.add_item(discord.ui.Separator())
        self.container.add_item(
            discord.ui.TextDisplay(
                _("Du findest hier eine Liste aller Bilder, die du hinzugefügt hast. "
                  "Solltest du derzeit keine Bilder hinzugefügt haben, wird das Standardbild genutzt.\n**HINWEIS:** Die Funktion ist derzeit in der Beta-Phase. Bugs oder Benutzerunfreundlichkeiten können auftreten. Bitte melde jegliche auf dem Support Server!")
            )
        )
        self.container.add_item(discord.ui.Separator())

        if self.images:
            gallery = discord.ui.MediaGallery()
            for filename, image_data in self.images.items():
                if isinstance(image_data, bytes):
                    file = discord.File(io.BytesIO(image_data), filename=filename)
                elif isinstance(image_data, str):
                    file = discord.File(image_data, filename=filename)
                else:
                    continue

                self.files.append(file)

                parts = filename.split("_", 1)
                img_num = parts[1].split(".")[0] if len(parts) > 1 else filename
                gallery.add_item(media=file, description=_("Bild {count}").format(count=img_num))

            self.container.add_item(gallery)
            self.container.add_item(discord.ui.Separator())

            arow1 = discord.ui.ActionRow()
            arow1.add_item(DeleteImageSelect(bot, guild_id, images))
            self.container.add_item(arow1)

        if len(self.images) < 10:
            arow2 = discord.ui.ActionRow()
            arow2.add_item(AddImageButton(bot, guild_id))
            self.container.add_item(arow2)

        self.add_item(self.container)

class ConfigSelect(discord.ui.Select):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        options = [
            discord.SelectOption(label=_("Kanal"), value="set_channel", emoji="🪛", description=_("Geburtstagskanal festlegen")),
            discord.SelectOption(label=_("Rolle"), value="set_role", emoji="⚙️", description=_("Geburtstagsrolle zuweisen")),
            discord.SelectOption(label=_("Bilder An/Aus"), value="toggle_image", emoji="🪟", description=_("Geburtstagskarten aktivieren/deaktivieren")),
            discord.SelectOption(label=_("Farbe"), value="color", emoji="🎨", description=_("Farbe der Embeds ändern")),
            discord.SelectOption(label=_("Ankündigungen"), value="alerts", emoji="📣", description=_("News-Kanal verwalten")),
            discord.SelectOption(label=_("Sprache"), value="language", emoji="🗣️", description=_("Sprache des Bots ändern")),
            discord.SelectOption(label=_("Nachricht (ohne Alter)"), value="msg_no_age", emoji="🗨️", description=_("Embed-Text für Modus ohne Alter")),
            discord.SelectOption(label=_("Nachricht (mit Alter)"), value="msg_with_age", emoji="ℹ️", description=_("Embed-Text für Modus mit Alter")),
            discord.SelectOption(label=_("Uhrzeit"), value="set_time", emoji="⏰", description=_("Sendezeit der Nachrichten anpassen")),
            discord.SelectOption(label=_("BETA: Bilder-Verwaltung"), value="image", emoji="🖼️", description=_("Öffne das Verwaltungsfenster für Hintergrundbilder"))
        ]

        super().__init__(
            placeholder=_("Wähle eine Einstellung zum Bearbeiten..."),
            min_values=1,
            max_values=1,
            options=options,
            custom_id="config_select_dropdown"
        )

    async def callback(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        selected = self.values[0]

        if selected == "set_channel":
            await interaction.response.send_modal(ChannelConfigModal(self.bot, self.guild_id))
        elif selected == "set_role":
            await interaction.response.send_modal(RoleConfigModal(self.bot, self.guild_id))
        elif selected == "toggle_image":
            await self.view.toggle_image(interaction)
        elif selected == "color":
            current_color = self.bot.guild_configs[self.guild_id].get("config_embed_color", 0x45a6c9)
            await interaction.response.send_modal(ConfigColorModal(self.bot, current_color, self.guild_id))
        elif selected == "msg_no_age":
            settings = await get_embed_settings(self.bot, self.guild_id, 'no_age')
            await interaction.response.send_modal(NoAgeMessageModal(self.bot, settings, self.guild_id))
        elif selected == "msg_with_age":
            settings = await get_embed_settings(self.bot, self.guild_id, 'with_age')
            await interaction.response.send_modal(WithAgeMessageModal(self.bot, settings, self.guild_id))
        elif selected == "alerts":
            await interaction.response.send_modal(AlertsConfigModal(self.bot, self.guild_id))
        elif selected == "language":
            await self.view.send_language_panel(interaction)
        elif selected == "set_time":
            current_time = self.bot.guild_configs[self.guild_id].get("message_time", "08:00")
            await interaction.response.send_modal(MessageTimeModal(self.bot, current_time, self.guild_id))
        elif selected == "image":
            await self.view.manage_custom_images(interaction)

class MainConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.add_item(ConfigSelect(bot, guild_id))

    async def toggle_image(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})
        new_status = not current_config.get("birthday_image_enabled", False)

        async with self.bot.db_pool.acquire() as db:
            async with db.cursor() as cur:
                await cur.execute(
                    "UPDATE guild_settings SET birthday_image_enabled = %s WHERE guild_id = %s",
                    (new_status, self.guild_id)
                )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["birthday_image_enabled"] = new_status

        new_embed = build_config_embed(self.bot, self.guild_id)

        await interaction.response.edit_message(
            embed=new_embed,
            view=MainConfigView(self.bot, self.guild_id)
        )

    async def color_button(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_color = self.bot.guild_configs[self.guild_id].get("config_embed_color", 0x45a6c9)
        await interaction.response.send_modal(
            ConfigColorModal(self.bot, current_color, self.guild_id)
        )

    async def msg_no_age(self, interaction: discord.Interaction):
        settings = await get_embed_settings(self.bot, self.guild_id, 'no_age')
        await interaction.response.send_modal(NoAgeMessageModal(self.bot, settings, self.guild_id))

    async def msg_with_age(self, interaction: discord.Interaction):
        settings = await get_embed_settings(self.bot, self.guild_id, 'with_age')
        await interaction.response.send_modal(WithAgeMessageModal(self.bot, settings, self.guild_id))

    async def set_alerts(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        await interaction.response.send_modal(AlertsConfigModal(self.bot, self.guild_id))

    async def send_language_panel(self, interaction: discord.Interaction):
        _ = translator.get_translation(self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en"))
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})
        langembed = discord.Embed(
            title=_("🌍 Sprache"),
            description=_("Hier kannst du die Sprache der Antworten des Bots anpassen.\n"
                          "**HINWEIS:** Übersetzungen können fehlerhaft sein."),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        await interaction.response.send_message(embed=langembed, view=LanguageConfigView(self.bot, self.guild_id), ephemeral=True)

    async def set_time(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_time = self.bot.guild_configs[self.guild_id].get("message_time", "08:00")
        await interaction.response.send_modal(MessageTimeModal(self.bot, current_time, self.guild_id))

    async def manage_custom_images(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        IMAGE_DIR = "data/custom_images"
        os.makedirs(IMAGE_DIR, exist_ok=True)
        files = glob.glob(os.path.join(IMAGE_DIR, f"{self.guild_id}_*.*"))

        images = {}
        for file_path in files:
            filename = os.path.basename(file_path)
            images[filename] = file_path

        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)
        view = PictureListLayout(self.bot, images, current_color, self.guild_id)

        await interaction.followup.send(
            embed=None,
            view=view,
            files=view.files,
            ephemeral=True
        )

class ConfigCommands(commands.Cog, name="ConfigCommands"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if isinstance(error, app_commands.MissingPermissions):
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(_("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True)
                else:
                    await interaction.response.send_message(_("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True)
            except discord.HTTPException:
                pass
            return
        raise error

    @app_commands.command(
        name=app_commands.locale_str("cmd_config_name"),
        description=app_commands.locale_str("cmd_config_desc")
    )
    @app_commands.default_permissions(manage_guild=True)
    async def config_main(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if interaction.guild is None:
            await interaction.response.send_message(_("Nur in Servern möglich."), ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)

        embed = build_config_embed(interaction.client, interaction.guild.id)

        await interaction.response.send_message(
            embed=embed,
            view=MainConfigView(self.bot, guild_id),
            ephemeral=True
        )

    @app_commands.command(
        name=app_commands.locale_str("cmd_config_test_name"),
        description=app_commands.locale_str("cmd_config_test_desc")
    )
    @app_commands.describe(
        message_type=app_commands.locale_str("param_config_test_type"),
        user_to_test=app_commands.locale_str("param_config_test_user")
    )
    @app_commands.choices(message_type=[
        app_commands.Choice(name=app_commands.locale_str("choice_test_no_age"), value="no_age"),
        app_commands.Choice(name=app_commands.locale_str("choice_test_with_age"), value="with_age")
    ])
    @app_commands.default_permissions(manage_guild=True)
    async def test_birthday_message(self, interaction: discord.Interaction, message_type: app_commands.Choice[str], user_to_test: discord.User = None):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if interaction.guild is None:
            await interaction.response.send_message(_("Nur auf einem Server möglich."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})
        user = user_to_test if user_to_test else interaction.user
        configured_channel_id = current_config.get("birthday_channel_id")

        if not configured_channel_id:
            await interaction.followup.send(_("Kein Kanal konfiguriert."), ephemeral=True)
            return

        target_channel = self.bot.get_channel(configured_channel_id)
        if target_channel is None:
            try:
                target_channel = await self.bot.fetch_channel(configured_channel_id)
            except discord.NotFound:
                await interaction.followup.send(_("❌ Der konfigurierte Kanal wurde nicht gefunden (gelöscht?). Bitte setze ihn in der Config neu."), ephemeral=True)
                return
            except discord.Forbidden:
                await interaction.followup.send(_("❌ Ich habe keine Berechtigung, auf den konfigurierten Kanal zuzugreifen."), ephemeral=True)
                return

        embed_title = current_config.get(f"title_{message_type.value}") or default_title(_, message_type.value == "with_age")
        embed_message = current_config.get(f"message_{message_type.value}") or default_description(_, message_type.value == "with_age")
        embed_footer = current_config.get(f"footer_{message_type.value}")
        image_title = current_config.get(f"image_title_{message_type.value}") or default_image_title(_, message_type.value == "with_age")

        age_str = ""
        if message_type.value == "with_age":
            age_str = format_age(30, lang)

        final_embed_title = embed_title.replace("%username", user.display_name).replace("%age", age_str)
        final_embed_message = embed_message.replace("%username", user.display_name).replace("%age", age_str).replace("%mention", user.mention)
        final_image_title = image_title.replace("%username", user.display_name).replace("%age", age_str)

        final_embed_footer = None
        if embed_footer:
            final_embed_footer = embed_footer.replace("%username", user.display_name).replace("%age", age_str)
        elif message_type.value == "with_age":
            final_embed_footer = with_age_footer(_)

        embed = discord.Embed(
            title=final_embed_title,
            description=final_embed_message,
            color=current_config.get("config_embed_color", 0x3aaa06)
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        if final_embed_footer:
            embed.set_footer(text=final_embed_footer)

        generated_image_file = None
        if current_config.get("birthday_image_enabled", True):
            try:
                # Zufälliges Hintergrundbild aus dem Ordner custom_images wählen
                IMAGE_DIR = "data/custom_images"
                custom_files = glob.glob(os.path.join(IMAGE_DIR, f"{guild_id}_*.*"))

                selected_background = None
                if custom_files:
                    selected_background = random.choice(custom_files)

                generated_image_file = await generate_birthday_image(
                    user,
                    final_image_title,
                    user.display_name,
                    selected_background
                )
            except Exception as e:
                print(f"Fehler bei der Test-Bildgenerierung: {e}")

        try:
            if generated_image_file:
                await target_channel.send(embed=embed, file=generated_image_file)
            else:
                await target_channel.send(embed=embed)

        except discord.Forbidden:
            return await interaction.followup.send(_("❌ Ich habe keine Berechtigung, in den konfigurierten Kanal zu schreiben."), ephemeral=True)

        await interaction.followup.send(_("Test gesendet! ✅"), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))