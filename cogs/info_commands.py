import time
from typing import Optional

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands
from utils.babel import translator


class InfoCommands(commands.Cog, name="InfoCommands"):
    def __init__(self, bot):
        self.bot = bot
        self.command_list = ["birthday-set", "config", "birthday-test"]

    # --- SLASH COMMAND: /info ---
    @app_commands.command(name="info", description="Zeigt Informationen über den Bot an.")
    async def info(self, interaction: discord.Interaction):
        if interaction.guild is None:
            embed_color = 0x45a6c9
            lang = "en"
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)
            lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")

        _ = translator.get_translation(lang)

        description_text = (_("""
Hey! Ich bin **Birthdayyyyys**, ein Bot, um Leuten zu ihrem **Geburtstag** zu **gratulieren**! :)

## ❔ __Infos:__
<:status_online:1390283178144698420> Ich bin <t:1751450400:R> erstellt worden
<:developer:1390293000747225098> Entwickler: _chrxstianst.
<:python:1390293453606486056> Library: discord.py-2.6.4
ℹ️ Version: v3.0
        """))

        info_embed = discord.Embed(
            title="Birthdayyyyys",
            description=description_text,
            color=embed_color
        )

        await interaction.response.send_message(embed=info_embed)

    @app_commands.command(name="help", description="Zeigt eine Liste aller Befehle an.")
    @app_commands.describe(command="Wähle einen Befehl für mehr Infos.")
    @app_commands.choices(command=[
        app_commands.Choice(name="birthday-set", value="birthday-set"),
        app_commands.Choice(name="config", value="config"),
        app_commands.Choice(name="birthday-test", value="birthday-test")
    ])
    async def help_command(self, interaction: discord.Interaction, command: Optional[str] = None):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=False)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        channel = interaction.channel
        current_config = self.bot.guild_configs.get(guild_id, {})

        permissions = channel.permissions_for(interaction.user)

        if command:
            if command == "birthday-set":
                command_embed = discord.Embed(
                    title=_("__Hilfe für den Befehl /{command}__",
                    description=f"Hiermit kannst du ganz einfach deinen Geburtstag festlegen. \n"
                                f"Dein Geburtstag kann übrigens mit `/birthday-remove` wieder entfernt werden.\n"
                                f"Falls du dich vertippt hast, nutze diesen Befehl einfach nochmal.").format(command=command),
                    color=current_config.get("config_embed_color", 0x45a6c9)
                )
                command_embed.add_field(name="`<month>`", value=_("Mit dieser Auswahl legst du deinen Geburtsmonat fest."), inline=False)
                command_embed.add_field(name="`<day>`", value=_("Mit dieser Auswahl legst du deinen Geburtstag fest."), inline=False)
                command_embed.add_field(name="`[year]`", value=_("*(optional)*: Lege hiermit das Geburtsjahr von dir fest. Dein Alter wird errechnet und offen bekannt gegeben."), inline=False)
                command_embed.add_field(name="`[timezone]`", value=_("*(optional)*: Falls du nicht in der Zeitzone **Europe/Berlin** wohnst, kannst du sie hier ändern."), inline=False)

            elif command == "config":
                if interaction.user.guild_permissions.manage_guild:
                    command_embed = discord.Embed(
                        title=_("__Hilfe für den Befehl /{command}__").format(command=command),
                        description=_("Hiermit kann man die Einstellungen für den Geburtstagsbot ändern. Dazu nutzt man die Buttons auf dem gesendeten Panel.").format(command=command),
                        color=current_config.get("config_embed_color", 0x45a6c9)
                    )
                    command_embed.add_field(name=_("`Kanal`"), value=_("Im Formular kannst du den Kanal einstellen, worin die Geburtstagsgrüße gesendet werden sollen. **WICHTIG!** Ohne diese Einstellung wird keine Nachricht gesendet."), inline=False)
                    command_embed.add_field(name=_("`Rolle`"), value=_("Im Formular kannst du eine Geburtstagsrolle festlegen, die bei einem Geburtstag für 24h vergeben wird."), inline=False)
                    command_embed.add_field(name=_("`Bilder An/Aus`"), value=_("Stelle hier ein, ob personalisierte Banner bei Geburtstagen gesendet werden sollen. Wie so ein Banner aussieht, siehst du auf **__[der Homepage](https://birthdayyyyys.christianst.xyz)__**."), inline=False)
                    command_embed.add_field(name=_("`Embed Farbe`"), value=_("Gebe in das Formular einen HEX-Code ein. Alle Nachrichten-Embeds werden nun diese Farbe nutzen. Standard: `45A6C9`."), inline=False)
                    command_embed.add_field(name=_("`News Kanal`"), value=_("Wenn du Botneuigkeiten nicht verpassen willst, kannst du in das Formular die Kanal-ID für den gewünschten Kanal eingeben. In diesen werden Changelogs und Announcements gesendet. Setze die Kanal-ID auf `0`, um keine News zu bekommen (was sehr schade wäre)."), inline=False)
                    command_embed.add_field(name=_("`Nachricht (Kein/Mit Alter)`"), value=_("Hier kannst du die Geburtstagsembeds bearbeiten. Du kannst sogar den Titel des generierten Banners auswählen. Nutze die Variablen im Titel jedes Feldes, um die Nachricht weiter zu personalisieren."), inline=False)
                else:
                    await interaction.response.send_message("⚠️ Du hast keine Berechtigung dazu.", ephemeral=True)
            elif command == "birthday-test":
                if interaction.user.guild_permissions.manage_guild:
                    command_embed = discord.Embed(
                        title=_("__Hilfe für den Befehl /{command}__").format(command=command),
                        description=_("Simuliere hier einen Geburtstag, um zu testen, ob deine Einstellungen funktionieren."),
                        color=current_config.get("config_embed_color", 0x45a6c9)
                    )
                    command_embed.add_field(name=_("`Ohne Altersangabe`"), value=_("Simuliere einen Geburtstag, wo der Benutzer kein Geburtsjahr angegeben hat."), inline=False)
                    command_embed.add_field(name=_("`Mit Altersangabe (Test-Alter: 30)`"), value=_("Simuliere einen Geburtstag, der gesendet wird, wenn der Benutzer 30 Jahre alt wird."), inline=False)
                else:
                    await interaction.response.send_message(_("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True)

            else:
                await interaction.response.send_message(_("❌ Fehler: Du hast keinen gültigen Befehl angegeben."), ephemeral=True)

            command_embed.set_thumbnail(url=self.bot.user.avatar)
            await interaction.response.send_message(embed=command_embed)


        else:

            embed = discord.Embed(
                title=_("ℹ️ Bot-Befehle"),
                description=_("Hier ist eine Liste aller verfügbaren Befehle:"),
                color=current_config.get("config_embed_color", 0x45a6c9)
            )
            if permissions.manage_guild:
                embed.add_field(name=_("__Mitglieder:__"), value='\u200b', inline=False)
                embed.add_field(name="/birthday-set <month> <day> [year] [timezone]", value=_("Setzt deinen Geburtstag."), inline=False)
                embed.add_field(name="/birthday-remove", value=_("Entfernt deinen Geburtstag."), inline=False)
                embed.add_field(name="/birthday-list", value=_("Zeigt alle gespeicherten Geburtstage an."), inline=False)
                embed.add_field(name="/info", value=_("Zeigt Informationen über den Bot an."), inline=False)
                embed.add_field(name="/ping", value=_("Misst die derzeitige Antwortlatenz des Bots"), inline=False)
                embed.add_field(name='\u200b', value='\u200b', inline=False)
                embed.add_field(name='__Team:__', value='\u200b', inline=False)
                embed.add_field(name='/config', value=_("Konfiguriert Birthdayyyyys."), inline=False)
                embed.add_field(name="/birthday-test <message_type>", value=_("Sendet eine Test-Geburtstagsnachricht an den konfigurierten Kanal."), inline=False)
            else:
                embed.add_field(name=_("__Mitglieder:__"), value='\u200b', inline=False)
                embed.add_field(name="/birthday-set <month> <day> [year] [timezone]", value=_("Setzt deinen Geburtstag."), inline=False)
                embed.add_field(name="/birthday-remove", value=_("Entfernt deinen Geburtstag."), inline=False)
                embed.add_field(name="/birthday-list", value=_("Zeigt alle gespeicherten Geburtstage an."), inline=False)
                embed.add_field(name="/info", value=_("Zeigt Informationen über den Bot an."), inline=False)
                embed.add_field(name="/ping", value=_("Misst die derzeitige Antwortlatenz von Birthdayyyyys."), inline=False)


            embed.set_footer(text=_("Nutze `/help [command]`, um über komplexere Befehle mehr zu erfahren."))
            embed.set_thumbnail(url=self.bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(name="ping", description="Zeigt die aktuelle Latenz des Bots an.")
    async def ping_command(self, interaction: discord.Interaction):
        discord_latency_ms = round(self.bot.latency * 1000)
        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True, ephemeral=True)

        if interaction.guild is None:
            embed_color = 0x45a6c9
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)

        lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        db_start_time = time.perf_counter()
        db_latency_ms = "Fehler"

        try:
            db: aiosqlite.Connection = getattr(self.bot, 'db', None)

            if db:
                await db.execute("SELECT 1")
                await db.commit()
                db_end_time = time.perf_counter()
                db_latency_ms = round((db_end_time - db_start_time) * 1000)
            else:
                db_latency_ms = "Nicht verbunden"

            if db_latency_ms != "Nicht verbunden":
                db_latency_con = _("✅ Verbunden")

            elif db_latency_ms == "Nicht verbunden":
                db_latency_con = _("❌ Nicht verbunden")

        except Exception as e:
            db_latency_ms = _("DB-Fehler: {error}").format(error=type(e).__name__)

        end_time = time.perf_counter()
        processing_latency_ms = round((end_time - start_time) * 1000)

        embed = discord.Embed(
            title=_("⏱️ Ping-Ergebnisse"),
            description=_("Latenzzeiten des Bots zu verschiedenen Komponenten:"),
            color=embed_color
        )

        embed.add_field(
            name=_("🤖 Interne Verarbeitung"),
            value=f"`{processing_latency_ms}ms`",
            inline=True
        )
        embed.add_field(
            name=_("🌐 Discord API (Heartbeat)"),
            value=f"`{discord_latency_ms}ms`",
            inline=True
        )
        embed.add_field(
            name=_("💾 Datenbank (aiosqlite)"),
            value=f"{db_latency_con}",
            inline=True
        )


        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))