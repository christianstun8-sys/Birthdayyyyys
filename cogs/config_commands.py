# cogs/config_commands.py
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import os
import asyncio

# --- Standardwerte (Unverändert) ---
DEFAULT_NO_AGE_TITLE = "🎉 Herzlichen Glückwunsch zum Geburtstag, %username!"
DEFAULT_NO_AGE_MESSAGE = "Bitte sende deine besten Wünsche an %mention!"
DEFAULT_IMAGE_NO_AGE_TITLE = "Happy Birthday!"

DEFAULT_WITH_AGE_TITLE = "🎂 Alles Gute zum %age. Geburtstag, %username!"
DEFAULT_WITH_AGE_MESSAGE = "Lasst uns %mention zu seinem %age. Geburtstag gratulieren!"
DEFAULT_WITH_AGE_FOOTER = "Feiere schön!"
DEFAULT_IMAGE_WITH_AGE_TITLE = "Happy %age. Birthday!"

# --- Hilfsfunktionen für Embed-Einstellungen (Unverändert) ---

async def get_embed_settings(bot: commands.Bot, guild_id: int, message_type: str):
    """Ruft aktuelle Embed-Einstellungen für eine spezifische Guild und einen Nachrichtentyp ab."""
    # Stellt sicher, dass die aktuelle Konfiguration geladen ist
    await bot.load_bot_config(bot, guild_id)
    config = bot.guild_configs.get(guild_id, {})

    # Ruft die 5 benötigten Felder ab: title, message, footer, color, image_title
    # Die Reihenfolge muss zu den Argumenten in den Modals passen
    return (
        config.get(f"title_{message_type}"),
        config.get(f"message_{message_type}"),
        config.get(f"footer_{message_type}"),
        config.get("config_embed_color"),
        config.get(f"image_title_{message_type}")
    )

async def update_embed_settings(bot: commands.Bot, guild_id: int, title: str, message: str, footer: str, color: int, image_title: str, message_type: str):
    """Aktualisiert oder fügt Embed-Einstellungen für einen bestimmten Nachrichtentyp für eine spezifische Guild hinzu."""
    await bot.setup_database(guild_id)

    # Stelle sicher, dass die aktuelle Konfiguration in der Instanz geladen ist, um alle Werte zu erhalten
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

    config_to_save = bot.guild_configs[guild_id] # Die aktuelle, aktualisierte Konfiguration

    async with aiosqlite.connect(bot.get_db_path(guild_id)) as db:
        await bot.ensure_tables(db)

        # Komplettes INSERT OR REPLACE, um alle Spalten zu aktualisieren (jetzt 14 Spalten)
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


# --- Modals (Unverändert) ---

# ... NoAgeMessageModal (unverändert) ...
class NoAgeMessageModal(discord.ui.Modal, title="Nachricht ohne Altersangabe anpassen"):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        super().__init__()
        self.bot = bot
        self.current_settings = current_settings
        self.guild_id = guild_id
        # Eingegebene Werte aus DB laden
        title_default = current_settings[0] if current_settings and current_settings[0] else DEFAULT_NO_AGE_TITLE
        message_default = current_settings[1] if current_settings and current_settings[1] else DEFAULT_NO_AGE_MESSAGE
        footer_default = current_settings[2] if current_settings and current_settings[2] else None
        image_title_default = current_settings[4] if current_settings and current_settings[4] else DEFAULT_IMAGE_NO_AGE_TITLE

        self.title_input = discord.ui.TextInput(
            label="Titel des Embeds (%username)",
            placeholder=DEFAULT_NO_AGE_TITLE,
            default=title_default,
            required=False,
            max_length=256,
        )
        self.add_item(self.title_input)

        self.message_input = discord.ui.TextInput(
            label="Nachricht im Embed (%mention, %username)",
            placeholder=DEFAULT_NO_AGE_MESSAGE,
            default=message_default,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
        )
        self.add_item(self.message_input)

        self.footer_input = discord.ui.TextInput(
            label="Footer im Embed (optional, %username)",
            placeholder="Kein Footer",
            default=footer_default,
            required=False,
            max_length=2048,
        )
        self.add_item(self.footer_input)

        self.image_title_input = discord.ui.TextInput(
            label="Titel auf Geburtstagsbild (%username)",
            placeholder=DEFAULT_IMAGE_NO_AGE_TITLE,
            default=image_title_default,
            required=False,
            max_length=256,
        )
        self.add_item(self.image_title_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        new_title = self.title_input.value or DEFAULT_NO_AGE_TITLE
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or DEFAULT_NO_AGE_MESSAGE
        new_image_title = self.image_title_input.value or DEFAULT_IMAGE_NO_AGE_TITLE
        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)

        # Nutze die aktualisierte Funktion
        await update_embed_settings(self.bot, self.guild_id, new_title, new_message, new_footer, current_color, new_image_title, 'no_age')

        await interaction.followup.send(f"Die Geburtstagsnachricht (ohne Alter) und Bildtext wurde erfolgreich aktualisiert! ✅", ephemeral=True)


# ... WithAgeMessageModal (unverändert) ...
class WithAgeMessageModal(discord.ui.Modal, title="Nachricht mit Altersangabe anpassen"):
    def __init__(self, bot: commands.Bot, current_settings, guild_id: int):
        super().__init__()
        self.bot = bot
        self.current_settings = current_settings
        self.guild_id = guild_id

        # Eingegebene Werte aus DB laden
        title_default = current_settings[0] if current_settings and current_settings[0] else DEFAULT_WITH_AGE_TITLE
        message_default = current_settings[1] if current_settings and current_settings[1] else DEFAULT_WITH_AGE_MESSAGE
        footer_default = current_settings[2] if current_settings and current_settings[2] else DEFAULT_WITH_AGE_FOOTER
        image_title_default = current_settings[4] if current_settings and current_settings[4] else DEFAULT_IMAGE_WITH_AGE_TITLE

        self.title_input = discord.ui.TextInput(
            label="Titel (%age)",
            placeholder=DEFAULT_WITH_AGE_TITLE,
            default=title_default,
            required=False,
            max_length=256,
        )
        self.add_item(self.title_input)
        self.message_input = discord.ui.TextInput(
            label="Beschr. (%mention, %username, %age)",
            placeholder=DEFAULT_WITH_AGE_MESSAGE,
            default=message_default,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
        )
        self.add_item(self.message_input)

        self.footer_input = discord.ui.TextInput(
            label="Footer (optional, %username)",
            placeholder="Standard: Feiere schön!",
            default=footer_default,
            required=False,
            max_length=2048,
        )
        self.add_item(self.footer_input)
        self.image_title_input = discord.ui.TextInput(
            label="Bildtitel (%age, %username)",
            placeholder=DEFAULT_IMAGE_WITH_AGE_TITLE,
            default=image_title_default,
            required=False,
            max_length=256,
        )
        self.add_item(self.image_title_input)


    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        new_title = self.title_input.value or DEFAULT_WITH_AGE_TITLE
        new_footer = self.footer_input.value if self.footer_input.value else None
        new_message = self.message_input.value or DEFAULT_WITH_AGE_MESSAGE
        new_image_title = self.image_title_input.value or DEFAULT_IMAGE_WITH_AGE_TITLE

        current_color = self.bot.guild_configs.get(self.guild_id, {}).get("config_embed_color", 0x45a6c9)
        # Nutze die aktualisierte Funktion
        await update_embed_settings(self.bot, self.guild_id, new_title, new_message, new_footer, current_color, new_image_title, 'with_age')

        await interaction.followup.send(f"Die Geburtstagsnachricht (mit Alter) und Bildtext wurde erfolgreich aktualisiert! ✅", ephemeral=True)


class ConfigColorModal(discord.ui.Modal, title="Embed-Farbe anpassen"):
    def __init__(self, bot: commands.Bot, current_color: int, guild_id: int):
        super().__init__()
        self.bot = bot
        self.guild_id = guild_id

        self.color_input = discord.ui.TextInput(
            label="Farbe des Embeds (Hex-Code, z.B. FF00FF)",
            placeholder=f"Aktuell: {current_color:06X}",
            default=f"{current_color:06X}",
            required=True,
            max_length=6,
            min_length=6
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.bot.load_bot_config(self.bot, self.guild_id)

        new_color_str = self.color_input.value.strip().replace("#", "")

        if not (len(new_color_str) == 6 and all(c in "0123456789abcdefABCDEF" for c in new_color_str.lower())):
            await interaction.followup.send(
                "Ungültiger Hex-Code für die Farbe. Bitte gib einen gültigen 6-stelligen Hex-Code an (z.B. FF00FF).",
                ephemeral=True
            )
            return

        try:
            new_color = int(new_color_str, 16)
        except ValueError:
            await interaction.followup.send(
                "Ungültiger Hex-Code für die Farbe. Bitte gib einen gültigen 6-stelligen Hex-Code an (z.B. FF00FF).",
                ephemeral=True
            )
            return

        await self.bot.setup_database(self.guild_id)
        current_config = self.bot.guild_configs.get(self.guild_id, {})

        async with aiosqlite.connect(self.bot.get_db_path(self.guild_id)) as db:
            await self.bot.ensure_tables(db)
            # Nutze die gespeicherte Konfiguration und aktualisiere nur die Farbe (14 Spalten)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (self.guild_id, new_color, current_config.get("birthday_channel_id"), current_config.get("birthday_image_enabled"), current_config.get("birthday_image_background"),
                 current_config.get("message_no_age"), current_config.get("title_no_age"), current_config.get("footer_no_age"),
                 current_config.get("message_with_age"), current_config.get("title_with_age"), current_config.get("footer_with_age"),
                 current_config.get("image_title_no_age"), current_config.get("image_title_with_age"), current_config.get("birthday_role_id"))
            )
            await db.commit()

        if self.guild_id in self.bot.guild_configs:
            self.bot.guild_configs[self.guild_id]["config_embed_color"] = new_color
        print(f"Guild {self.guild_id}: Embed-Farbe aktualisiert auf: {hex(new_color)}")
        await interaction.followup.send(f"Die Farbe für Embeds wurde auf`#{new_color_str.upper()}` aktualisiert.", ephemeral=True)


# ... MessageAdjusterView (Unverändert) ...
class MessageAdjusterView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild_id: int):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id

    @discord.ui.button(label="Nachricht ohne Alter", style=discord.ButtonStyle.primary)
    async def no_age_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await get_embed_settings(self.bot, self.guild_id, 'no_age')
        await interaction.response.send_modal(NoAgeMessageModal(self.bot, settings, self.guild_id))

    @discord.ui.button(label="Nachricht mit Alter", style=discord.ButtonStyle.primary)
    async def with_age_message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        settings = await get_embed_settings(self.bot, self.guild_id, 'with_age')
        await interaction.response.send_modal(WithAgeMessageModal(self.bot, settings, self.guild_id))


# --- Cog-Klasse ---

class ConfigCommands(commands.Cog, name="ConfigCommands"):
    def __init__(self, bot):
        self.bot = bot

    # NEUES FEHLERHANDLING: Fängt Permission-Fehler ab und sendet eine ephemere Nachricht
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            # Sendet die gewünschte Fehlermeldung
            try:
                # Prüfen, ob bereits geantwortet/defered wurde
                if interaction.response.is_done():
                    await interaction.followup.send("⚠️ Du hast keine Berechtigung dazu.", ephemeral=True)
                else:
                    await interaction.response.send_message("⚠️ Du hast keine Berechtigung dazu.", ephemeral=True)
            except discord.HTTPException:
                pass # Ignoriere, falls die Interaktion komplett fehlschlägt
            return

        # Für alle anderen Fehler, lasse sie durchlaufen (oder raise error um global zu loggen)
        raise error

    # --- SLASH COMMAND: /config-role ---
    @app_commands.command(name="config-role", description="Setzt die Rolle, die Mitgliedern an ihrem Geburtstag zugewiesen wird.")
    # Permission geändert: manage_guild wird zu manage_messages
    @app_commands.default_permissions(manage_messages=True)
    async def config_role(self, interaction: discord.Interaction, role: discord.Role = None):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        # ... Rest der Logik unverändert
        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)

        # Prüfe, ob die Rolle überhaupt gesetzt werden soll (z.B. wenn 'role' None ist, soll sie entfernt werden)
        role_id_to_set = role.id if role else None
        role_name_display = role.name if role else "keine"

        if role:
            # Zusätzliche Prüfung der Rollenhierarchie (Bot muss Rolle zuweisen können)
            if interaction.guild.me.top_role <= role:
                await interaction.response.send_message(
                    f"⚠️ Ich kann die Rolle **{role.name}** nicht zuweisen. "
                    "Bitte stelle sicher, dass meine Rolle höher ist als die Geburtstagsrolle in der Rollenliste des Servers.",
                    ephemeral=True
                )
                return

        await self.bot.setup_database(guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})

        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await self.bot.ensure_tables(db)
            # Nutze die gespeicherte Konfiguration und aktualisiere nur die role_id (14 Spalten)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, current_config.get("config_embed_color"), current_config.get("birthday_channel_id"), current_config.get("birthday_image_enabled"), current_config.get("birthday_image_background"),
                 current_config.get("message_no_age"), current_config.get("title_no_age"), current_config.get("footer_no_age"),
                 current_config.get("message_with_age"), current_config.get("title_with_age"), current_config.get("footer_with_age"),
                 current_config.get("image_title_no_age"), current_config.get("image_title_with_age"), role_id_to_set)
            )
            await db.commit()

        if guild_id in self.bot.guild_configs:
            self.bot.guild_configs[guild_id]["birthday_role_id"] = role_id_to_set

        print(f"Guild {guild_id}: Geburtstagsrolle auf {role_name_display} gesetzt.")

        if role:
            await interaction.response.send_message(f"✅ Die Geburtstagsrolle wurde auf **{role.mention}** gesetzt.", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Die Geburtstagsrolle wurde entfernt.", ephemeral=True)


    # --- SLASH COMMAND: /config-channel ---
    @app_commands.command(name="config-channel", description="Setzt den Kanal, in den Geburtstagsnachrichten gesendet werden.")
    # Permission geändert: manage_guild wird zu manage_messages
    @app_commands.default_permissions(manage_messages=True)
    async def config_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        # ... Rest der Logik unverändert
        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)

        await self.bot.setup_database(guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})

        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await self.bot.ensure_tables(db)
            # Nutze die gespeicherte Konfiguration und aktualisiere nur die Channel-ID (14 Spalten)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, current_config.get("config_embed_color"), channel.id, current_config.get("birthday_image_enabled"), current_config.get("birthday_image_background"),
                 current_config.get("message_no_age"), current_config.get("title_no_age"), current_config.get("footer_no_age"),
                 current_config.get("message_with_age"), current_config.get("title_with_age"), current_config.get("footer_with_age"),
                 current_config.get("image_title_no_age"), current_config.get("image_title_with_age"), current_config.get("birthday_role_id"))
            )
            await db.commit()

        if guild_id in self.bot.guild_configs:
            self.bot.guild_configs[guild_id]["birthday_channel_id"] = channel.id
        print(f"Guild {guild_id}: Geburtstagskanal auf {channel.name} ({channel.id}) gesetzt.")
        await interaction.response.send_message(f"Geburtstagsnachrichten werden nun in {channel.mention} gesendet. ✅", ephemeral=True)


    # --- SLASH COMMAND: /config-image ---
    @app_commands.command(name="config-image", description="Aktiviert/Deaktiviert die Geburtstagsbild-Generierung.")
    @app_commands.default_permissions(manage_messages=True)
    async def config_image(self, interaction: discord.Interaction, enable: bool):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)

        current_config = self.bot.guild_configs.get(guild_id, {})
        final_background_path = current_config.get("birthday_image_background", 'data/birthday_background.jpg')

        if enable and final_background_path and not os.path.exists(final_background_path):
            await interaction.response.send_message(
                "⚠️ Hintergrundbild nicht gefunden. Bitte stelle sicher, dass 'data/birthday_background.jpg' existiert.",
                ephemeral=True
            )
            return

        await self.bot.setup_database(guild_id)

        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await self.bot.ensure_tables(db)
            await db.execute(
                "INSERT OR REPLACE INTO guild_settings (guild_id, config_embed_color, birthday_channel_id, birthday_image_enabled, birthday_image_background, message_no_age, title_no_age, footer_no_age, message_with_age, title_with_age, footer_with_age, image_title_no_age, image_title_with_age, birthday_role_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guild_id, current_config.get("config_embed_color"), current_config.get("birthday_channel_id"), enable, final_background_path,
                 current_config.get("message_no_age"), current_config.get("title_no_age"), current_config.get("footer_no_age"),
                 current_config.get("message_with_age"), current_config.get("title_with_age"), current_config.get("footer_with_age"),
                 current_config.get("image_title_no_age"), current_config.get("image_title_with_age"), current_config.get("birthday_role_id"))
            )
            await db.commit()

        if guild_id in self.bot.guild_configs:
            self.bot.guild_configs[guild_id]["birthday_image_enabled"] = enable
            self.bot.guild_configs[guild_id]["birthday_image_background"] = final_background_path

        status = "aktiviert" if enable else "deaktiviert"
        print(f"Guild {guild_id}: Geburtstagsbild-Generierung {status}.")
        await interaction.response.send_message(f"Geburtstagsbild-Generierung wurde {status}", ephemeral=True)


    # --- SLASH COMMAND: /config-color ---
    @app_commands.command(name="config-color", description="Passt die Farbe der Bot-Embeds an")
    @app_commands.default_permissions(manage_messages=True)
    async def config_color(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        current_color = self.bot.guild_configs.get(guild_id, {}).get("config_embed_color", 0x45a6c9)
        await interaction.response.send_modal(ConfigColorModal(self.bot, current_color, guild_id))


    # --- SLASH COMMAND: /set-birthday-message ---
    @app_commands.command(name="set-birthday-message", description="Passe die Geburtstagsnachrichten des Bots an.")
    # Permission geändert: manage_guild wird zu manage_messages
    @app_commands.default_permissions(manage_messages=True)
    async def set_birthday_message(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        # ... Rest der Logik unverändert
        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)

        await interaction.response.send_message(
            "Wähle aus, welche Art von Geburtstagsnachricht du anpassen möchtest:",
            view=MessageAdjusterView(self.bot, guild_id),
            ephemeral=True
        )

    # --- SLASH COMMAND: /birthday-test ---
    @app_commands.command(name="birthday-test", description="Sende eine Test-Geburtstagsnachricht in den konfigurierten Kanal.")
    @app_commands.describe(
        message_type="Art der Testnachricht (ohne/mit Altersangabe).",
        user_to_test="Der Benutzer, für den die Testnachricht gesendet werden soll (Standard: du selbst)."
    )
    @app_commands.choices(message_type=[
        app_commands.Choice(name="Ohne Altersangabe", value="no_age"),
        app_commands.Choice(name="Mit Altersangabe (Test-Alter: 30)", value="with_age")
    ])
    # Permission geändert: manage_channels wird zu manage_messages
    @app_commands.default_permissions(manage_messages=True)
    async def test_birthday_message(self, interaction: discord.Interaction, message_type: app_commands.Choice[str], user_to_test: discord.User = None):

        # ... Rest der Logik unverändert
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur auf einem Server verwendet werden.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id) # Lade aktuelle Konfiguration für diesen Server
        current_config = self.bot.guild_configs.get(guild_id, {})

        user = user_to_test if user_to_test else interaction.user

        configured_channel_id = current_config.get("birthday_channel_id")

        if not configured_channel_id:
            await interaction.followup.send(
                "Es wurde kein Geburtstagskanal konfiguriert. Bitte konfiguriere ihn zuerst mit `/config-channel`.",
                ephemeral=True
            )
            return

        target_channel = self.bot.get_channel(configured_channel_id)
        if not target_channel:
            try:
                target_channel = await self.bot.fetch_channel(configured_channel_id)
            except (discord.NotFound, discord.Forbidden) as e:
                await interaction.followup.send(
                    f"Ich habe keinen Zugriff auf den konfigurierten Geburtstagskanal (ID: `{configured_channel_id}`). Bitte überprüfe meine Berechtigungen.`",
                    ephemeral=True
                )
                return
            except Exception as e:
                await interaction.followup.send(
                    f"Ein Fehler ist beim Abrufen des konfigurierten Kanals aufgetreten: `{e}`",
                    ephemeral=True
                )
                return

        # Hole die aktuellen Embed-Einstellungen aus der Konfiguration
        embed_title = current_config.get(f"title_{message_type.value}")
        embed_message = current_config.get(f"message_{message_type.value}")
        embed_footer = current_config.get(f"footer_{message_type.value}")
        image_title = current_config.get(f"image_title_{message_type.value}")

        age_str = ""
        if message_type.value == "with_age":
            age_str = "30" # Test-Alter

        # Ersetze Platzhalter
        final_embed_title = embed_title.replace("%username", user.display_name).replace("%age", age_str)
        final_embed_message = embed_message.replace("%username", user.display_name).replace("%age", age_str).replace("%mention", user.mention)
        final_embed_footer = embed_footer.replace("%username", user.display_name).replace("%age", age_str) if embed_footer else None
        final_image_title = image_title.replace("%username", user.display_name).replace("%age", age_str)


        embed_color = current_config.get("config_embed_color", 0x3aaa06)
        embed = discord.Embed(
            title=final_embed_title,
            description=final_embed_message,
            color=embed_color
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        if final_embed_footer:
            embed.set_footer(text=final_embed_footer)

        generated_image_file = None
        if current_config.get("birthday_image_enabled", False):
            background_path = current_config.get("birthday_image_background")
            try:
                generated_image_file = await self.bot.generate_birthday_image(user, final_image_title, user.display_name, background_path)
                if generated_image_file:
                    embed.set_image(url="attachment://birthday_card.png")
            except Exception as e:
                await interaction.followup.send(f"⚠️ Fehler bei der Bildgenerierung: `{e}`", ephemeral=True)
                generated_image_file = None # Im Fehlerfall kein Bild senden

        try:
            if generated_image_file:
                await target_channel.send(embed=embed, file=generated_image_file)
            else:
                await target_channel.send(embed=embed)

            await interaction.followup.send(
                f"Test-Geburtstagsnachricht ({message_type.name}) erfolgreich in **`#{target_channel.name}`** gesendet! ✅",
                ephemeral=True
            )
            print(f"Test-Geburtstagsnachricht für {user.name} ({message_type.name}) gesendet.")
        except discord.Forbidden:
            await interaction.followup.send(
                f"Fehler: Ich habe keine Berechtigung, Nachrichten in Kanal **`#{target_channel.name}`** zu senden. "
                "Bitte überprüfe meine Kanalberechtigungen.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"⚠️ Ein globaler Fehler ist beim Senden der Nachricht aufgetreten. Error: `{e}`",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ConfigCommands(bot))