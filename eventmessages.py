import discord
from discord.ext import commands
import main
from utils.babel import translator

async def unknown_error(guild: discord.Guild, bot: main.BirthdayBot, interaction: discord.Interaction):
    guild_id = guild.id

    if guild_id:
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
    else:
        lang = "en"

    _ = translator.get_translation(lang)

    embed = discord.Embed(
        title=_("⚠️ Unbekannter Fehler"),
        description=_("Ein unbekannter Fehler ist aufgetreten. Bitte melde dich beim Support-Server."),
        color=discord.Color.yellow()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)