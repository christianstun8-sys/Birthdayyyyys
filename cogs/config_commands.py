import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import os
import asyncio

DEFAULT_NO_AGE_TITLE = "🎉 Herzlichen Glückwunsch zum Geburtstag, %username!"
DEFAULT_NO_AGE_MESSAGE = "Bitte sende deine besten Wünsche an %mention!"
DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"

DEFAULT_WITH_AGE_TITLE = "🎂 Alles Gute zum %age. Geburtstag, %username!"
DEFAULT_WITH_AGE_MESSAGE = "Lasst uns %mention zu seinem %age. Geburtstag gratulieren!"
DEFAULT_WITH_AGE_FOOTER = "Feiere schön!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age. Birthday!"

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
            "INSERT OR REPLACE INTO guild_settings (guild_id, birthday_channel_id, config_embed_color, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                guild_id, config_to_save["birthday_channel_id"], config_to_save["config_embed_color"], config_to_save["birthday_image_enabled"],
                config_to_save["birthday_image_background"], config_to_save["message_no_age"], config_to_save["title_no_age"], config_to_save["footer_no_age"],
                config_to_save["message_with_age"], config_to_save["title_with_age"], config_to_save["footer_with_age"],
                config_to_save["image_title_no_age"], config_to_save["image_title_with_age"], config_to_save["birthday_role_id"]
            )
        )
        await db.commit()

class NoAgeMessageModal(discord.ui.Modal, title="Nachricht ohne Altersangabe anpassen"):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        super().__init__()
        self.bot = bot
        self.current_settings = current_settings
        self.guild_id = guild_id
        title_default = current_settings[0] if current_settings and current_settings[0] else DEFAULT_NO_AGE_TITLE
        message_default = current_settings[1] if current_settings and current_settings[1] else DEFAULT_NO_AGE_MESSAGE
        footer_default = current_settings[2] if current_settings and current_settings[2] else None
        image_title_default = current_settings[4] if current_settings and current_settings[4] else DEFAULT_IMAGE_NO_AGE_TITLE

        self.title_input = discord.ui.TextInput(label="Titel des Embeds (%username)", placeholder=DEFAULT_NO_AGE_TITLE, default=title_default, required=False, max_length=256)
        self.add_item(self.title_input)
        self.message_input = discord.ui.TextInput(label="Nachricht im Embed (%mention, %username)", placeholder=DEFAULT_NO_AGE_MESSAGE, default=message_default, style=discord.TextStyle.paragraph, required=False, max_length=1000)
        self.add_item(self.message_input)
        self.footer_input = discord.ui.TextInput(label="Footer im Embed (optional, %username)", placeholder="Kein Footer", default=footer_default, required=False, max_length=2048)
        self.add_item(self.footer_input)
        self.image_title_input = discord.ui.TextInput(label="Titel auf Geburtstagsbild (%username)", placeholder=DEFAULT_IMAGE_NO_AGE_TITLE, default=image_title_default, required=False, max_length=256)
        self.add_item(self.image_title_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_title = self.title_input.value or DEFAULT_NO_AGE_TITLE
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or DEFAULT_NO_AGE_MESSAGE
        new_image_title = self.image_title_input.value or DEFAULT_IMAGE_NO_AGE_TITLE
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)
        await update_embed_settings(self.bot, self.guild_id, new_title, new_message, new_footer, current_color, new_image_title, 'no_age')
        await interaction.followup.send(f"Die Geburtstagsnachricht (ohne Alter) wurde erfolgreich aktualisiert! ✅", ephemeral=True)

class WithAgeMessageModal(discord.ui.Modal, title="Nachricht mit Altersangabe anpassen"):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        super().__init__()
        self.bot = bot
        self.current_settings = current_settings
        self.guild_id = guild_id
        title_default = current_settings[0] if current_settings and current_settings[0] else DEFAULT_WITH_AGE_TITLE
        message_default = current_settings[1] if current_settings and current_settings[1] else DEFAULT_WITH_AGE_MESSAGE
        footer_default = current_settings[2] if current_settings and current_settings[2] else DEFAULT_WITH_AGE_FOOTER
        image_title_default = current_settings[4] if current_settings and current_settings[4] else DEFAULT_IMAGE_WITH_AGE_TITLE

        self.title_input = discord.ui.TextInput(label="Titel (%age)", placeholder=DEFAULT_WITH_AGE_TITLE, default=title_default, required=False, max_length=256)
        self.add_item(self.title_input)
        self.message_input = discord.ui.TextInput(label="Beschr. (%mention, %username, %age)", placeholder=DEFAULT_WITH_AGE_MESSAGE, default=message_default, style=discord.TextStyle.paragraph, required=False, max_length=1000)
        self.add_item(self.message_input)
        self.footer_input = discord.ui.TextInput(label="Footer (optional, %username)", placeholder="Standard: Feiere schön!", default=footer_default, required=False, max_length=2048)
        self.add_item(self.footer_input)
        self.image_title_input = discord.ui.TextInput(label="Bildtitel (%age, %username)", placeholder=DEFAULT_IMAGE_WITH_AGE_TITLE, default=image_title_default, required=False, max_length=256)
        self.add_item(self.image_title_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_title = self.title_input.value or DEFAULT_WITH_AGE_TITLE
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or DEFAULT_WITH_AGE_MESSAGE
        new_image_title = self.image_title_input.value or DEFAULT_IMAGE_WITH_AGE_TITLE
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)
        await update_embed_settings(self.bot, self.guild_id, new_title, new_message, new_footer, current_color, new_image_title, 'with_age')
        await interaction.followup.send(f"Die Geburtstagsnachricht (mit Alter) wurde erfolgreich aktualisiert! ✅", ephemeral=True)

class ConfigColorModal(discord.ui.Modal, title="Embed-Farbe anpassen"):
    def __init__(self, bot: commands.Bot, current_color: int, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id
        self.color_input = discord.ui.TextInput(label="Farbe des Embeds (Hex-Code, z.B. FF00FF)", placeholder=f"Aktuell: {current_color:06X}", default=f"{current_color:06X}", required=True, max_length=6, min_length=6)
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.load_bot_config(self.bot, self.guild_id)
        new_color_str = self.color_input.value.strip().replace("#", "")
        if not (len(new_color_str) == 6 and all(c in "0123456789abcdefABCDEF" for c in new_color_str.lower())):
            await interaction.followup.send("Ungültiger Hex-Code.", ephemeral=True)
            return
        new_color = int(new_color_str, 16)
        await self.bot.setup_database(self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})
        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await self.bot.ensure_tables(db)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.guild_id, new_color, current_config.get("birthday_channel_id"), current_config.get("birthday_image_enabled"), current_config.get("birthday_image_background"), current_config.get("message_no_age"), current_config.get("title_no_age"), current_config.get("footer_no_age"), current_config.get("message_with_age"), current_config.get("title_with_age"), current_config.get("footer_with_age"), current_config.get("image_title_no_age"), current_config.get("image_title_with_age"), current_config.get("birthday_role_id"))
            )
            await db.commit()
        self.bot.guild_configs[self.guild_id]["config_embed_color"] = new_color
        await interaction.followup.send(f"Farbe auf `#{new_color_str.upper()}` aktualisiert.", ephemeral=True)

class MainConfigView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Kanal", style=discord.ButtonStyle.secondary, row=0)
    async def set_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bitte nutze `/config` mit dem Parameter `channel`, um den Kanal direkt zu setzen, oder wähle hier eine andere Option.", ephemeral=True)

    @discord.ui.button(label="Rolle", style=discord.ButtonStyle.secondary, row=0)
    async def set_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Bitte nutze `/config` mit dem Parameter `role`, um die Rolle direkt zu setzen.", ephemeral=True)

    @discord.ui.button(label="Bilder An/Aus", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_image_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})

        new_status = not current_config.get("birthday_image_enabled", False)

        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await db.execute("UPDATE guild_settings SET birthday_image_enabled = ? WHERE guild_id = ?", (new_status, self.guild_id))
            await db.commit()

        self.bot.guild_configs[self.guild_id]["birthday_image_enabled"] = new_status

        new_embed = discord.Embed(
            title="⚙️ Server-Konfiguration",
            description="Hier kannst du alle Einstellungen für das Geburtstagssystem verwalten. Nutze die Buttons unten für Nachrichten und Farben.",
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        new_embed.add_field(name="Kanal", value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else "Nicht gesetzt")
        new_embed.add_field(name="Rolle", value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else "Keine")
        new_embed.add_field(name="Bilder", value="✅ Aktiviert" if new_status else "❌ Deaktiviert")
        await interaction.response.edit_message(embed=new_embed, view=self)

    @discord.ui.button(label="Embed Farbe", style=discord.ButtonStyle.secondary, row=1)
    async def color_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.load_bot_config(self.bot, self.guild_id)
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)
        await interaction.response.send_modal(ConfigColorModal(self.bot, current_color, self.guild_id))

    @discord.ui.button(label="Nachricht (Kein Alter)", style=discord.ButtonStyle.primary, row=2)
    async def msg_no_age_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await get_embed_settings(self.bot, self.guild_id, 'no_age')
        await interaction.response.send_modal(NoAgeMessageModal(self.bot, settings, self.guild_id))

    @discord.ui.button(label="Nachricht (Mit Alter)", style=discord.ButtonStyle.primary, row=2)
    async def msg_with_age_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await get_embed_settings(self.bot, self.guild_id, 'with_age')
        await interaction.response.send_modal(WithAgeMessageModal(self.bot, settings, self.guild_id))

class ConfigCommands(commands.Cog, name="ConfigCommands"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("⚠️ Du hast keine Berechtigung dazu.", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ Du hast keine Berechtigung dazu.", ephemeral=True)
            except discord.HTTPException:
                pass
            return
        raise error

    @app_commands.command(name="config", description="Zentrales Menü für alle Bot-Einstellungen.")
    @app_commands.describe(channel="Setze den Kanal für Nachrichten", role="Setze die Geburtstagsrolle")
    @app_commands.default_permissions(manage_messages=True)
    async def config_main(self, interaction: discord.Interaction, channel: discord.TextChannel = None, role: discord.Role = None):
        if interaction.guild is None:
            await interaction.response.send_message("Nur in Servern möglich.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        await self.bot.setup_database(guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})

        if channel:
            async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
                await db.execute("UPDATE guild_settings SET birthday_channel_id = ? WHERE guild_id = ?", (channel.id, guild_id))
                await db.commit()
            self.bot.guild_configs[guild_id]["birthday_channel_id"] = channel.id
            await interaction.response.send_message(f"Kanal auf {channel.mention} gesetzt. ✅", ephemeral=True)
            return

        if role:
            if interaction.guild.me.top_role <= role:
                await interaction.response.send_message(f"⚠️ Rolle **{role.name}** ist zu hoch.", ephemeral=True)
                return
            async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
                await db.execute("UPDATE guild_settings SET birthday_role_id = ? WHERE guild_id = ?", (role.id, guild_id))
                await db.commit()
            self.bot.guild_configs[guild_id]["birthday_role_id"] = role.id
            await interaction.response.send_message(f"Rolle auf **{role.name}** gesetzt. ✅", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚙️ Server-Konfiguration",
            description="Hier kannst du alle Einstellungen für das Geburtstagssystem verwalten. Nutze die Buttons unten für Nachrichten und Farben.",
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        embed.add_field(name="Kanal", value=f"<#{current_config.get('birthday_channel_id')}>" if current_config.get('birthday_channel_id') else "Nicht gesetzt")
        embed.add_field(name="Rolle", value=f"<@&{current_config.get('birthday_role_id')}>" if current_config.get('birthday_role_id') else "Keine")
        embed.add_field(name="Bilder", value="✅ Aktiviert" if current_config.get('birthday_image_enabled') else "❌ Deaktiviert")

        await interaction.response.send_message(embed=embed, view=MainConfigView(self.bot, guild_id), ephemeral=True)

    @app_commands.command(name="birthday-test", description="Sende eine Test-Geburtstagsnachricht.")
    @app_commands.describe(message_type="Art der Testnachricht", user_to_test="Benutzer für den Test")
    @app_commands.choices(message_type=[
        app_commands.Choice(name="Ohne Altersangabe", value="no_age"),
        app_commands.Choice(name="Mit Altersangabe (Test-Alter: 30)", value="with_age")
    ])
    @app_commands.default_permissions(manage_messages=True)
    async def test_birthday_message(self, interaction: discord.Interaction, message_type: app_commands.Choice[str], user_to_test: discord.User = None):
        if interaction.guild is None:
            await interaction.response.send_message("Nur im Server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})
        user = user_to_test if user_to_test else interaction.user
        configured_channel_id = current_config.get("birthday_channel_id")

        if not configured_channel_id:
            await interaction.followup.send("Kein Kanal konfiguriert.", ephemeral=True)
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

        embed = discord.Embed(title=final_embed_title, description=final_embed_message, color=current_config.get("config_embed_color", 0x3aaa06))
        embed.set_thumbnail(url=user.display_avatar.url)
        if final_embed_footer: embed.set_footer(text=final_embed_footer)

        generated_image_file = None
        if current_config.get("birthday_image_enabled", False):
            try:
                generated_image_file = await self.bot.generate_birthday_image(user, final_image_title, user.display_name, current_config.get("birthday_image_background"))
                if generated_image_file: embed.set_image(url="attachment://birthday_card.png")
            except: pass

        await target_channel.send(embed=embed, file=generated_image_file) if generated_image_file else await target_channel.send(embed=embed)
        await interaction.followup.send("Test gesendet! ✅", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))