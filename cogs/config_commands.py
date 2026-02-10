import discord
from discord._types import ClientT
from discord.ext import commands
from discord import app_commands, Interaction
import aiosqlite

from utils.babel import translator


def default_title(_, age: bool):
    if not age:
        return _("🎉 Herzlichen Glückwunsch zum Geburtstag, %username!")
    else:
        return _("🎂 Alles Gute zum %age. Geburtstag, %username!")
    
def default_description(_, age: bool):
    if not age:
        return _("Bitte sende deine besten Wünsche an %mention!")
    else:
        return _("Lasst uns %mention zu seinem %age. Geburtstag gratulieren!")

def default_image_title(_, age: bool):
    if not age:
        return _("Happy Birthday!")
    else:
        return _("Happy %age. Birthday!")
    
def with_age_footer(_):
    return _("Feiere schön!")


async def get_embed_settings(bot: commands.Bot, guild_id: int, message_type: str):
    await bot.load_bot_config(bot, guild_id)
    config = bot.guild_configs.get(guild_id, {})
    return (
        config.get(f"title_{message_type}"),
        config.get(f"message_{message_type}"),
        config.get(f"footer_{message_type}"),
        config.get("config_embed_color"),
        config.get(f"image_title_{message_type}")
    )


async def update_embed_settings(bot: commands.Bot, guild_id: int, title: str, message: str, footer: str, color: int, image_title: str, message_type: str):
    await bot.setup_database(guild_id)
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

    async with aiosqlite.connect(bot.get_db_path(guild_id)) as db:
        await bot.ensure_tables(db)
        await db.execute(
            "INSERT OR REPLACE INTO guild_settings "
            "(guild_id, birthday_channel_id, config_embed_color, birthday_image_enabled, birthday_image_background, "
            "message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, "
            "image_title_no_age, image_title_with_age, birthday_role_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                guild_id,
                config_to_save["birthday_channel_id"],
                config_to_save["config_embed_color"],
                config_to_save["birthday_image_enabled"],
                config_to_save["birthday_image_background"],
                config_to_save["message_no_age"],
                config_to_save["title_no_age"],
                config_to_save["footer_no_age"],
                config_to_save["message_with_age"],
                config_to_save["title_with_age"],
                config_to_save["footer_with_age"],
                config_to_save["image_title_no_age"],
                config_to_save["image_title_with_age"],
                config_to_save["birthday_role_id"]
            )
        )
        await db.commit()


async def update_alerts_settings(bot: commands.Bot, guild_id: int, channel_id: int):
    await bot.setup_database(guild_id)

    async with aiosqlite.connect(bot.get_db_path(guild_id)) as db:
        await db.execute("UPDATE guild_settings SET alerts = ? WHERE guild_id = ?", (channel_id, guild_id))
        await db.commit()

    if guild_id not in bot.guild_configs:
        await bot.load_bot_config(bot, guild_id)
    bot.guild_configs[guild_id]["alerts"] = channel_id

def config_legend(_):
    return _(
        "Hier kannst du alle Einstellungen für das Geburtstagssystem verwalten.\n"
        "Nutze die Buttons unten zum Konfigurieren.\n\n"
        "🪛 = Kanal\n"
        "⚙️ = Rolle\n"
        "🖼️ = Bilder An/Aus\n"
        "🎨 = Farbe\n"
        "📣 = Ankündigungen\n"
        "🗣️ = Sprache\n"
        "🗨️ℹ️ = Nachricht (Mit Alter)\n"
        "🗨️ = Nachricht (Ohne Alter)"
    )


class NoAgeMessageModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        super().__init__(title=_("Nachricht ohne Altersangabe anpassen"))

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

        super().__init__(title=_("Nachricht mit Altersangabe anpassen"))

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

        self.color_input = discord.ui.TextInput(
            label=_("Farbe des Embeds (Hex-Code, z.B. FF00FF)"),
            placeholder=_("Aktuell: {color}").format(color=f"{current_color:06X}"),
            default=f"{current_color:06X}",
            required=True,
            max_length=6,
            min_length=6
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        await interaction.response.defer(ephemeral=True)
        await self.bot.load_bot_config(self.bot, self.guild_id)

        new_color_str = self.color_input.value.strip().replace("#", "")
        if not (len(new_color_str) == 6 and all(c in "0123456789abcdefABCDEF" for c in new_color_str)):
            await interaction.followup.send(_("Ungültiger Hex-Code."), ephemeral=True)
            return

        new_color = int(new_color_str, 16)
        await self.bot.setup_database(self.guild_id)

        current_config = self.bot.guild_configs.get(self.guild_id, {})
        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await self.bot.ensure_tables(db)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings "
                "(guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, "
                "message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, "
                "image_title_no_age, image_title_with_age, birthday_role_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self.guild_id,
                    new_color,
                    current_config.get("birthday_channel_id"),
                    current_config.get("birthday_image_enabled"),
                    current_config.get("birthday_image_background"),
                    current_config.get("message_no_age"),
                    current_config.get("title_no_age"),
                    current_config.get("footer_no_age"),
                    current_config.get("message_with_age"),
                    current_config.get("title_with_age"),
                    current_config.get("footer_with_age"),
                    current_config.get("image_title_no_age"),
                    current_config.get("image_title_with_age"),
                    current_config.get("birthday_role_id")
                )
            )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["config_embed_color"] = new_color
        await interaction.followup.send(
            _("Farbe auf `#{color}` aktualisiert.").format(color=new_color_str.upper()),
            ephemeral=True
        )

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

        channel = await interaction.guild.fetch_channel(self.channel_select.values[0].id)
        guild_id = interaction.guild.id
        perms = channel.permissions_for(interaction.guild.me).send_messages

        if not perms:
            return await interaction.response.send_message("❌ Ich kann keine Nachrichten in dem ausgewählten Kanal schreiben.", ephemeral=True)

        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await db.execute(
                "UPDATE guild_settings SET birthday_channel_id = ? WHERE guild_id = ?",
                (channel.id, guild_id)
            )
            await db.commit()
        self.bot.guild_configs[guild_id]["birthday_channel_id"] = channel.id
        current_config = self.bot.guild_configs[self.guild_id]
        new_status = not current_config.get("birthday_image_enabled", False)
        new_embed = discord.Embed(
            title=_("⚙️ Server-Konfiguration"),
            description=config_legend(_),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        new_embed.add_field(
            name=_("Kanal"),
            value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else _("Nicht gesetzt")
        )
        new_embed.add_field(
            name=_("Rolle"),
            value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else _("Keine")
        )
        new_embed.add_field(
            name=_("Bilder"),
            value=_("✅ Aktiviert") if new_status else _("❌ Deaktiviert")
        )
        await interaction.response.edit_message(
            embed=new_embed,
            view=MainConfigView(self.bot, self.guild_id)
        )

class AlertsConfigModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild_id: int, current_val: str = ""):
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
            await interaction.response.send_message(_("✅ Bot-News wurden deaktiviert."), ephemeral=True)
            return

        channel = await interaction.guild.fetch_channel(self.channel_select.values[0].id)
        perms = channel.permissions_for(interaction.guild.me).send_messages

        if not perms:
            return await interaction.response.send_message(_("❌ Ich kann keine Nachrichten in dem ausgewählten Kanal schreiben."), ephemeral=True)

        await update_alerts_settings(self.bot, self.guild_id, channel.id)
        await interaction.response.send_message(
            _("✅ News-Kanal wurde auf {channel} gesetzt.").format(channel=channel.mention),
            ephemeral=True
        )

class RoleConfigModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id

        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        super().__init__(title="Geburtstagsrolle festlegen")

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
            async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
                await db.execute(
                    "UPDATE guild_settings SET birthday_role_id = ? WHERE guild_id = ?",
                    (0, guild_id)
                )
                await db.commit()

            if guild_id in self.bot.guild_configs:
                self.bot.guild_configs[guild_id]["birthday_role_id"] = 0

            await interaction.response.send_message(_("✅ Geburtstagsrolle deaktiviert."), ephemeral=True)
            return

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

        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await db.execute(
                "UPDATE guild_settings SET birthday_role_id = ? WHERE guild_id = ?",
                (role.id, guild_id)
            )
            await db.commit()

        self.bot.guild_configs[guild_id]["birthday_role_id"] = role.id
        current_config = self.bot.guild_configs[self.guild_id]
        new_status = not current_config.get("birthday_image_enabled", False)

        new_embed = discord.Embed(
            title=_("⚙️ Server-Konfiguration"),
            description=config_legend(_),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        new_embed.add_field(
            name=_("Kanal"),
            value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else _("Nicht gesetzt")
        )
        new_embed.add_field(
            name=_("Rolle"),
            value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else _("Keine")
        )
        new_embed.add_field(
            name=_("Bilder"),
            value=_("✅ Aktiviert") if new_status else _("❌ Deaktiviert")
        )
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
                label=_("Deutsch 🇩🇪"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_de"
            )
        )
        self.add_item(
            discord.ui.Button(
                label=_("English 🇬🇧"),
                style=discord.ButtonStyle.grey,
                custom_id="lang_en"
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = interaction.data.get("custom_id")

        if custom_id == "lang_de":
            await self.set_language(interaction, "de")
        elif custom_id == "lang_en":
            await self.set_language(interaction, "en")

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

        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await db.execute(
                "UPDATE guild_settings SET lang = ? WHERE guild_id = ?",
                (lang_code, self.guild_id)
            )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["lang"] = lang_code
        await self.bot.load_bot_config(self.bot, self.guild_id)

        current_config = self.bot.guild_configs[self.guild_id]
        _ = translator.get_translation(lang_code)

        embed = discord.Embed(
            title=_("⚙️ Server-Konfiguration"),
            description=config_legend(_),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )

        embed.add_field(
            name=_("Kanal"),
            value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get("birthday_channel_id") else _("Nicht gesetzt")
        )
        embed.add_field(
            name=_("Rolle"),
            value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get("birthday_role_id") else _("Keine")
        )
        embed.add_field(
            name=_("Bilder"),
            value=_("✅ Aktiviert") if current_config.get("birthday_image_enabled") else _("❌ Deaktiviert")
        )

        await interaction.response.edit_message(
            embed=embed,
            view=MainConfigView(self.bot, self.guild_id)
        )


class MainConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        self.add_item(discord.ui.Button(label="🪛", style=discord.ButtonStyle.secondary, row=0, custom_id="set_channel"))
        self.add_item(discord.ui.Button(label="⚙️", style=discord.ButtonStyle.secondary, row=0, custom_id="set_role"))
        self.add_item(discord.ui.Button(label="🖼️", style=discord.ButtonStyle.secondary, row=0, custom_id="toggle_image"))
        self.add_item(discord.ui.Button(label="🎨", style=discord.ButtonStyle.secondary, row=1, custom_id="color"))
        self.add_item(discord.ui.Button(label="📣", style=discord.ButtonStyle.secondary, row=1, custom_id="alerts"))
        self.add_item(discord.ui.Button(label="🗣️", style=discord.ButtonStyle.secondary, row=1, custom_id="language"))
        self.add_item(discord.ui.Button(label="🗨️ℹ️", style=discord.ButtonStyle.primary, row=2, custom_id="msg_no_age"))
        self.add_item(discord.ui.Button(label="🗨️", style=discord.ButtonStyle.primary, row=2, custom_id="msg_with_age"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await self.bot.load_bot_config(self.bot, self.guild_id)
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        custom_id = interaction.data.get("custom_id")

        if custom_id == "set_channel":
            await interaction.response.send_modal(ChannelConfigModal(self.bot, self.guild_id))
        elif custom_id == "set_role":
            await interaction.response.send_modal(RoleConfigModal(self.bot, self.guild_id))
        elif custom_id == "toggle_image":
            await self.toggle_image(interaction)
        elif custom_id == "color":
            await self.color_button(interaction)
        elif custom_id == "msg_no_age":
            await self.msg_no_age(interaction)
        elif custom_id == "msg_with_age":
            await self.msg_with_age(interaction)
        elif custom_id == "alerts":
            await self.set_alerts(interaction)
        elif custom_id == "language":
            await self.send_language_panel(interaction)
        return False  # verhindert, dass Discord automatisch "Button nicht erkannt" meldet

    # --- die alten Callback-Methoden einfach anpassen ---
    async def toggle_image(self, interaction: discord.Interaction):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})
        new_status = not current_config.get("birthday_image_enabled", False)

        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await db.execute(
                "UPDATE guild_settings SET birthday_image_enabled = ? WHERE guild_id = ?",
                (new_status, self.guild_id)
            )
            await db.commit()

        self.bot.guild_configs[self.guild_id]["birthday_image_enabled"] = new_status

        _ = translator.get_translation(self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en"))

        new_embed = discord.Embed(
            title=_("⚙️ Server-Konfiguration"),
            description=config_legend(_),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        new_embed.add_field(
            name=_("Kanal"),
            value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else _("Nicht gesetzt")
        )
        new_embed.add_field(
            name=_("Rolle"),
            value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else _("Keine")
        )
        new_embed.add_field(
            name=_("Bilder"),
            value=_("✅ Aktiviert") if new_status else _("❌ Deaktiviert")
        )
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
        current_alerts = self.bot.guild_configs.get(self.guild_id, {}).get("alerts")
        await interaction.response.send_modal(AlertsConfigModal(self.bot, self.guild_id, current_alerts))

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

    @app_commands.command(name="config", description="Zentrales Menü für alle Bot-Einstellungen.")
    @app_commands.default_permissions(manage_guild=True)
    async def config_main(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if interaction.guild is None:
            await interaction.response.send_message(_("Nur in Servern möglich."), ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        await self.bot.setup_database(guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})

        embed = discord.Embed(
            title=_("⚙️ Server-Konfiguration"),
            description=config_legend(_),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )

        embed.add_field(
            name=_("Kanal"),
            value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else _("Nicht gesetzt")
        )
        embed.add_field(
            name=_("Rolle"),
            value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else _("Keine")
        )
        embed.add_field(
            name=_("Bilder"),
            value=_("✅ Aktiviert") if current_config.get('birthday_image_enabled') else _("❌ Deaktiviert")
        )

        await interaction.response.send_message(
            embed=embed,
            view=MainConfigView(self.bot, guild_id),
            ephemeral=True
        )

    @app_commands.command(name="config-test", description="Sende eine Test-Geburtstagsnachricht.")
    @app_commands.describe(message_type="Art der Testnachricht", user_to_test="Benutzer für den Test")
    @app_commands.choices(message_type=[
        app_commands.Choice(name="Ohne Altersangabe", value="no_age"),
        app_commands.Choice(name="Mit Altersangabe (Test-Alter: 30)", value="with_age")
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

        target_channel = self.bot.get_channel(configured_channel_id) or await self.bot.fetch_channel(configured_channel_id)

        embed_title = current_config.get(f"title_{message_type.value}")
        embed_message = current_config.get(f"message_{message_type.value}")
        embed_footer = current_config.get(f"footer_{message_type.value}")
        image_title = current_config.get(f"image_title_{message_type.value}")

        age_str = "30" if message_type.value == "with_age" else ""
        final_embed_title = embed_title.replace("%username", user.display_name).replace("%age", age_str)
        final_embed_message = embed_message.replace("%username", user.display_name).replace("%age", age_str).replace("%mention", user.mention)
        final_embed_footer = embed_footer.replace("%username", user.display_name).replace("%age", age_str) if embed_footer else None
        final_image_title = image_title.replace("%username", user.display_name).replace("%age", age_str)

        embed = discord.Embed(
            title=final_embed_title,
            description=final_embed_message,
            color=current_config.get("config_embed_color", 0x3aaa06)
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        if final_embed_footer:
            embed.set_footer(text=final_embed_footer)

        generated_image_file = None
        if current_config.get("birthday_image_enabled", False):
            try:
                generated_image_file = await self.bot.generate_birthday_image(
                    user,
                    final_image_title,
                    user.display_name,
                    current_config.get("birthday_image_background")
                )
                if generated_image_file:
                    embed.set_image(url="attachment://birthday_card.png")
            except:
                pass

        if generated_image_file:
            await target_channel.send(embed=embed, file=generated_image_file)
        else:
            await target_channel.send(embed=embed)

        await interaction.followup.send(_("Test gesendet! ✅"), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))
