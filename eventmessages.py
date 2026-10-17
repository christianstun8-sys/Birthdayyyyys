import discord
import main
from utils.babel import translator
from utils.logger import log

async def unknown_error(guild: discord.Guild, bot: main.BirthdayBot, interaction, error: str = None):
    guild_id = guild.id
    guild_name = guild.name if guild else "Unknown Guild"
    user = interaction.user if interaction else None
    user_name = user.name if user else "Unknown User"

    if guild_id:
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
    else:
        lang = "en"

    _ = translator.get_translation(lang)

    error_msg = f"Error in guild '{guild_name}' (ID: {guild_id}) by user '{user_name}' (ID: {user.id if user else 'N/A'})"
    if error:
        error_msg += f": {error}"
    log(error_msg, 'ERROR')

    embed = discord.Embed(
        title=_("⚠️ Unbekannter Fehler"),
        description=_("Ein unbekannter Fehler ist aufgetreten. Bitte melde dich beim Support-Server."),
        color=discord.Color.yellow()
    )
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            pass

async def permission_error(guild: discord.Guild, bot: main.BirthdayBot, interaction, permission: str):
    guild_id = guild.id
    guild_name = guild.name if guild else "Unknown Guild"
    user = interaction.user if interaction else None
    user_name = user.name if user else "Unknown User"

    if guild_id:
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
    else:
        lang = "en"

    _ = translator.get_translation(lang)

    log(f"Permission denied in guild '{guild_name}' (ID: {guild_id}) for user '{user_name}' (ID: {user.id if user else 'N/A'}): Missing {permission}", 'WARNING')

    embed = discord.Embed(
        title=_("⚠️ Fehlende Berechtigung"),
        description=_("Du hast nicht die erforderliche Berechtigung für diese Aktion."),
        color=discord.Color.orange()
    )

    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            pass

async def bot_permission_error(guild: discord.Guild, bot: main.BirthdayBot, interaction, permission: str):
    guild_id = guild.id
    guild_name = guild.name if guild else "Unknown Guild"

    if guild_id:
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
    else:
        lang = "en"

    _ = translator.get_translation(lang)

    log(f"Bot permission denied in guild '{guild_name}' (ID: {guild_id}): Missing {permission}", 'ERROR')

    embed = discord.Embed(
        title=_("⚠️ Bot fehlt Berechtigung"),
        description=_("Der Bot hat nicht die erforderliche Berechtigung für diese Aktion. Bitte überprüfe die Bot-Rolle."),
        color=discord.Color.red()
    )

    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            pass

async def not_found_error(guild: discord.Guild, bot: main.BirthdayBot, interaction, item: str):
    guild_id = guild.id
    guild_name = guild.name if guild else "Unknown Guild"
    user = interaction.user if interaction else None
    user_name = user.name if user else "Unknown User"

    if guild_id:
        lang = bot.guild_configs.get(guild_id, {}).get("lang", "en")
    else:
        lang = "en"

    _ = translator.get_translation(lang)

    log(f"Item not found in guild '{guild_name}' (ID: {guild_id}) by user '{user_name}' (ID: {user.id if user else 'N/A'}): {item}", 'WARNING')

    embed = discord.Embed(
        title=_("⚠️ Nicht gefunden"),
        description=_(f"Das angeforderte Element wurde nicht gefunden: {item}"),
        color=discord.Color.orange()
    )

    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception:
        try:
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            pass