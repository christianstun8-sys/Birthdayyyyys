# cogs/info_commands.py
import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio

class InfoCommands(commands.Cog, name="InfoCommands"):
    def __init__(self, bot):
        self.bot = bot

    # --- SLASH COMMAND: /info ---
    @app_commands.command(name="info", description="Zeigt Informationen über den Bot an.")
    async def info(self, interaction: discord.Interaction):
        if interaction.guild is None:
            # Für DMs die Standardfarbe verwenden
            embed_color = 0x45a6c9
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)

        description_text = """
Hey! Ich bin **Birthdayyyyys**, ein Bot, um Leuten zu ihrem **Geburtstag** zu **gratulieren**! :)

*❔ __Infos:__*
<:status_online:1390283178144698420> Ich bin <t:1751450400:R> erstellt worden
<:developer:1390293000747225098> Entwickler: _chrxstianstun
<:python:1390293453606486056> Library: discord.py-2.5.2
ℹ️ Bot-Version: 1.24

*<:adorable:1396798143835799642> __Bot-Tester:__*
-dergamer1.0

Danke an alle Bot-Tester, die sich freiwillig bereit erklärt haben, den Bot zu testen <3.
        """

        info_embed = discord.Embed(
            title="Birthdayyyyys",
            description=description_text,
            color=embed_color
        )

        await interaction.response.send_message(embed=info_embed)

    # --- SLASH COMMAND: /help ---
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

    # --- SLASH COMMAND: /ping ---
    @app_commands.command(name="ping", description="Misst die Antwortzeit (Latenz) des Bots.")
    async def ping(self, interaction: discord.Interaction):
        if interaction.guild is None:
            # Für DMs die Standardfarbe verwenden
            embed_color = 0x45a6c9
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)

        latency_ms = round(self.bot.latency * 1000)
        ping_embed = discord.Embed(
            title="Pong! 🏓",
            description=f"Ich brauchte {latency_ms}ms um dir zu antworten!",
            color=embed_color
        )

        await interaction.response.send_message(embed=ping_embed)

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))