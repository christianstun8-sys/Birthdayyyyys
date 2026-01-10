import discord
from discord.ext import commands
from discord import app_commands
from datetime import time
import aiosqlite

class InfoCommands(commands.Cog, name="InfoCommands"):
    def __init__(self, bot):
        self.bot = bot

    # --- SLASH COMMAND: /info ---
    @app_commands.command(name="info", description="Zeigt Informationen über den Bot an.")
    async def info(self, interaction: discord.Interaction):
        if interaction.guild is None:
            embed_color = 0x45a6c9
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)

        description_text = """
Hey! Ich bin **Birthdayyyyys**, ein Bot, um Leuten zu ihrem **Geburtstag** zu **gratulieren**! :)

*❔ __Infos:__*
<:status_online:1390283178144698420> Ich bin <t:1751450400:R> erstellt worden
<:developer:1390293000747225098> Entwickler: _chrxstianst.
<:python:1390293453606486056> Library: discord.py-2.5.2
ℹ️ Bot-Version: 2.0
        """

        info_embed = discord.Embed(
            title="Birthdayyyyys",
            description=description_text,
            color=embed_color
        )

        await interaction.response.send_message(embed=info_embed)

    @app_commands.command(name="help", description="Zeigt eine Liste aller Befehle an.")
    async def help_command(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=False)
            return

        guild_id = interaction.guild.id
        channel = interaction.channel
        await self.bot.load_bot_config(self.bot, guild_id)
        current_config = self.bot.guild_configs.get(guild_id, {})

        permissions = channel.permissions_for(interaction.user)

        embed = discord.Embed(
            title="Bot-Befehle",
            description="Hier ist eine Liste aller verfügbaren Befehle:",
            color=current_config.get("config_embed_color", 0x45a6c9)
        )
        if permissions.manage_messages:
            embed.add_field(name="__Mitglieder:__", value='\u200b', inline=False)
            embed.add_field(name="/birthday-set <month> <day> [year]", value="Setzt deinen Geburtstag.", inline=False)
            embed.add_field(name="/birthday-remove", value="Entfernt deinen Geburtstag.", inline=False)
            embed.add_field(name="/birthday-list", value="Zeigt alle gespeicherten Geburtstage an.", inline=False)
            embed.add_field(name="/info", value="Zeigt Informationen über den Bot an.", inline=False)
            embed.add_field(name="/ping", value="Misst die derzeitige Antwortlatenz des Bots", inline=False)
            embed.add_field(name='_Team:_', value='\u200b', inline=False)
            embed.add_field(name="/set-birthday-message", value="Passt die Nachricht für Geburtstags-Embeds *und Bildtexte* an.", inline=False)
            embed.add_field(name="/config-channel <channel>", value="Setzt den Kanal, in den Geburtstagsnachrichten gesendet werden.", inline=False)
            embed.add_field(name="/config-image <enable|disable>", value="Aktiviert/Deaktiviert Geburtstagsbilder.", inline=False)
            embed.add_field(name="/config-color", value="Passt die Farbe der Bot-Embeds an (Info, Hilfe, Liste).", inline=False)
            embed.add_field(name="/config-role", value="Setzt eine Geburtstagsrolle, die an Geburtstagen vergeben wird.", inline=False)
            embed.add_field(name="/birthday-test", value="Sendet eine Test-Geburtstagsnachricht an den konfigurierten Kanal.", inline=False)
        else:
            embed.add_field(name="__Mitglieder:__", value='\u200b', inline=False)
            embed.add_field(name="/birthday-set <month> <day> [year]", value="Setzt deinen Geburtstag.", inline=False)
            embed.add_field(name="/birthday-remove", value="Entfernt deinen Geburtstag.", inline=False)
            embed.add_field(name="/birthday-list", value="Zeigt alle gespeicherten Geburtstage an.", inline=False)
            embed.add_field(name="/info", value="Zeigt Informationen über den Bot an.", inline=False)
            embed.add_field(name="/ping", value="Misst die derzeitige Antwortlatenz des Bots", inline=False)


        embed.set_footer(text="Birthdayyyyys")
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

        except Exception as e:
            db_latency_ms = f"DB-Fehler: {type(e).__name__}"

        end_time = time.perf_counter()
        processing_latency_ms = round((end_time - start_time) * 1000)

        embed = discord.Embed(
            title="⏱️ Ping-Ergebnisse",
            description="Latenzzeiten des Bots zu verschiedenen Komponenten:",
            color=embed_color
        )

        embed.add_field(
            name="🤖 Interne Verarbeitung",
            value=f"`{processing_latency_ms}ms`",
            inline=True
        )
        embed.add_field(
            name="🌐 Discord API (Heartbeat)",
            value=f"`{discord_latency_ms}ms`",
            inline=True
        )
        embed.add_field(
            name="💾 Datenbank (aiosqlite)",
            value=f"`{db_latency_ms}ms`",
            inline=True
        )


        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))