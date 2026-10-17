import time
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from utils.babel import translator
from utils.logger import log


class InfoCommands(commands.Cog, name="InfoCommands"):
    def __init__(self, bot):
        self.bot = bot
        self.command_list = ["birthday-set", "config", "birthday-test"]

    @app_commands.command(
        name=app_commands.locale_str("cmd_info_name"),
        description=app_commands.locale_str("cmd_info_desc")
    )
    async def info(self, interaction: discord.Interaction):
        if interaction.guild is None:
            embed_color = 0x45a6c9
            lang = "en"
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)
            lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")

        _ = translator.get_translation(lang)

        description_text = _(
            "Hey! Ich bin **Birthdayyyyys**, ein Bot, um Leuten zu ihrem **Geburtstag** zu **gratulieren**! :)\n"
            "\n"
            "## ❔ __Infos:__\n"
            "<:status_online:1390283178144698420> Ich bin <t:1751450400:R> erstellt worden\n"
            "<:developer:1390293000747225098> Entwickler: **__[_chrxstianst.](https://discordid.netlify.app/?id=1235134572157603841)__**\n"
            "<:python:1390293453606486056> Library: discord.py-{version}\n"
            "ℹ️ Version: v{bot_version}\n"
            "🌐 Website: https://birthdayyyyys.christianst.xyz"
        ).format(version=discord.__version__, bot_version=interaction.client.version)

        info_embed = discord.Embed(
            title="Birthdayyyyys",
            description=description_text,
            color=embed_color
        )

        await interaction.response.send_message(embed=info_embed)

    @app_commands.command(
        name=app_commands.locale_str("cmd_help_name"),
        description=app_commands.locale_str("cmd_help_desc")
    )
    async def help_command(self, interaction: discord.Interaction):

        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=False)
            return

        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        channel = interaction.channel
        current_config = self.bot.guild_configs.get(guild_id, {})

        permissions = channel.permissions_for(interaction.user)

        embed = discord.Embed(
            title=_("🎉 Birthdayyyyys - Hilfe"),
            description=_("Willkommen! Hier findest du alle verfügbaren Befehle."),
            color=current_config.get("config_embed_color", 0x45a6c9)
        )

        embed.add_field(
            name=_("📅 Geburtstagsbefehle"),
            value=(
                "`/birthday-set` - " + _("Deinen Geburtstag festlegen") + "\n"
                "`/birthday-remove` - " + _("Deinen Geburtstag entfernen") + "\n"
                "`/birthday-show` - " + _("Geburtstag anzeigen") + "\n"
                "`/birthday-list` - " + _("Geburtstagskalender anzeigen")
            ),
            inline=False
        )

        embed.add_field(
            name=_("⚙️ Konfiguration"),
            value=(
                "`/config` - " + _("Bot-Einstellungen öffnen") + "\n"
                "`/config-test` - " + _("Geburtstagsnachricht testen")
            ),
            inline=False
        )

        embed.add_field(
            name=_("ℹ️ Information"),
            value=(
                "`/info` - " + _("Bot-Informationen anzeigen") + "\n"
                "`/ping` - " + _("Bot-Latenz prüfen") + "\n"
                "`/help` - " + _("Diese Hilfe anzeigen")
            ),
            inline=False
        )

        embed.add_field(
            name=_("📚 Dokumentation"),
            value=_("Für ausführliche Anleitungen und weitere Informationen besuche unsere [Dokumentation](https://birthdayyyyys.christianst.xyz/docs)."),
            inline=False
        )

        if permissions.manage_guild:
            embed.add_field(
                name=_("🔧 Admin-Hinweis"),
                value=_("Als Server-Administrator kannst du `/config` nutzen, um alle Bot-Einstellungen anzupassen."),
                inline=False
            )

        embed.set_thumbnail(url=self.bot.user.avatar)
        embed.set_footer(text=_("Bei Fragen oder Problemen: https://birthdayyyyys.christianst.xyz/docs"))
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @app_commands.command(
        name=app_commands.locale_str("cmd_ping_name"),
        description=app_commands.locale_str("cmd_ping_desc")
    )
    async def ping_command(self, interaction: discord.Interaction):
        discord_latency_ms = round(self.bot.latency * 1000)
        start_time = time.perf_counter()
        await interaction.response.defer(thinking=True, ephemeral=True)

        if interaction.guild is None:
            embed_color = 0x45a6c9
            lang = "en"
        else:
            await self.bot.load_bot_config(self.bot, interaction.guild.id)
            embed_color = self.bot.guild_configs.get(interaction.guild.id, {}).get("config_embed_color", 0x45a6c9)
            lang = self.bot.guild_configs.get(interaction.guild.id, {}).get("lang", "en")

        _ = translator.get_translation(lang)

        db_start_time = time.perf_counter()

        try:
            async with self.bot.db_pool.acquire() as db:
                async with db.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                db_end_time = time.perf_counter()
                db_latency_str = f"`{round((db_end_time - db_start_time) * 1000)}ms`"

        except Exception as e:
            log(f"Database error: {e}", 'ERROR')
            db_latency_str = _("❌ Datenbankfehler")

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
            name=_("💾 Datenbank"),
            value=db_latency_str,
            inline=True
        )

        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(InfoCommands(bot))