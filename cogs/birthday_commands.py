import discord
from discord.ext import commands
from discord import app_commands
from utils.babel import translator
import aiosqlite
from datetime import datetime, date
import os
import pytz
import eventmessages

class BirthdayCommands(commands.Cog, name="BirthdayCommands"):
    def __init__(self, bot):
        self.bot = bot

    async def timezone_autocomplete(self, interaction: discord.Interaction, current: str):
        all_tzs = pytz.common_timezones
        return [
                   app_commands.Choice(name=tz, value=tz)
                   for tz in all_tzs if current.lower() in tz.lower()
               ][:25]

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_set_name"),
        description=app_commands.locale_str("cmd_birthday_set_desc")
    )
    @app_commands.describe(
        month=app_commands.locale_str("param_birthday_set_month"),
        day=app_commands.locale_str("param_birthday_set_day"),
        year=app_commands.locale_str("param_birthday_set_year"),
        timezone=app_commands.locale_str("param_birthday_set_timezone"),
        user=app_commands.locale_str("param_birthday_set_user")
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def birthday_set(self, interaction: discord.Interaction, month: int, day: int, year: int = None, timezone: str = "Europe/Berlin", user: discord.User = None):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if user is not None:
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(_("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True)

        if timezone not in pytz.all_timezones:
            return await interaction.response.send_message(_("Ungültige Zeitzone! Bitte wähle eine aus der Liste."), ephemeral=True)

        try:
            if year:
                date(year, month, day)
            else:
                date(2000, month, day)
        except ValueError:
            return await interaction.response.send_message(_("❌ Ungültiges Datum angegeben!"), ephemeral=True)

        db_path = self.bot.get_db_path(interaction.guild_id)
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO birthdays (user_id, month, day, year, timezone) VALUES (?, ?, ?, ?, ?)",
                (user.id if user else interaction.user.id, month, day, year, timezone)
            )
            await db.commit()

        if user:
            if year:
                return await interaction.response.send_message(_("✅ Der Geburtstag von {mention} wurde auf den {day:02d}.{month:02d}.{year} ({timezone}) gesetzt!").format(mention=user.mention, day=day, month=month, year=year, timezone=timezone), ephemeral=True)
            else:
                return await interaction.response.send_message(_("✅ Der Geburtstag von {mention} wurde auf den {day:02d}.{month:02d} ({timezone}) gesetzt!").format(mention=user.mention, day=day, month=month, timezone=timezone), ephemeral=True)

        if year:
            await interaction.response.send_message(_("✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}.{year} ({timezone}) gesetzt!").format(day=day, month=month, year=year, timezone=timezone), ephemeral=True)
        else:
            await interaction.response.send_message(_("✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}. ({timezone}) gesetzt!").format(day=day, month=month, timezone=timezone), ephemeral=True)


    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_remove_name"),
        description=app_commands.locale_str("cmd_birthday_remove_desc")
    )
    @app_commands.describe(
        user=app_commands.locale_str("param_birthday_remove_user"),
    )
    async def birthday_remove(self, interaction: discord.Interaction, user: discord.User = None):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if user is not None:
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(_("⚠️ Du hast keine Berechtigung dazu."))

        db_path = self.bot.get_db_path(interaction.guild_id)
        async with aiosqlite.connect(db_path) as db:
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user.id if user else interaction.user.id,))
            await db.commit()

        if user:
            return await interaction.response.send_message(_("✅ Der Geburtstag von {mention} wurde gelöscht.").format(mention=user.mention), ephemeral=True)
        await interaction.response.send_message(_("✅ Dein Geburtstag wurde gelöscht."), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_show_name"),
        description=app_commands.locale_str("cmd_birthday_show_desc")
    )
    async def birthday_show(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        db_path = self.bot.get_db_path(interaction.guild_id)
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT month, day, year, timezone FROM birthdays WHERE user_id = ?", (interaction.user.id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    month, day, year, tz = row
                    if year:
                        await interaction.response.send_message(_("Dein Geburtstag ist am {day:02d}.{month:02d}.{year} ({tz}).").format(day=day, month=month, year=year, tz=tz), ephemeral=True)
                    else:
                        await interaction.response.send_message(_("Dein Geburtstag ist am {day:02d}.{month:02d}. ({tz}).").format(day=day, month=month, tz=tz), ephemeral=True)
                else:
                    await interaction.response.send_message(_("❌ Du hast noch keinen Geburtstag registriert."), ephemeral=True)


    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_list_name"),
        description=app_commands.locale_str("cmd_birthday_list_desc")
    )
    async def birthday_list(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        db_path = self.bot.get_db_path(interaction.guild_id)
        if not os.path.exists(db_path):
            await interaction.response.send_message(_("⚠️ Es sind noch keine Geburtstage registriert."), ephemeral=True)
            return

        await interaction.response.defer()
        embed_color = self.bot.guild_configs.get(interaction.guild_id, {}).get("config_embed_color", 0x3aaa06)

        try:
            async with aiosqlite.connect(db_path) as db:
                async with db.execute("SELECT user_id, month, day, year, timezone FROM birthdays ORDER BY month, day") as cursor:
                    rows = await cursor.fetchall()

                if not rows:
                    await interaction.followup.send(_("⚠️ Es sind noch keine Geburtstage registriert."), ephemeral=True)
                    return

                response_message = ""
                for user_id, month, day, birth_year, tz_name in rows:
                    name = f"<@{user_id}>"

                    age_info = ""
                    if birth_year and birth_year > 0:
                        try:
                            tz = pytz.timezone(tz_name or 'Europe/Berlin')
                            today_tz = datetime.now(tz)
                            age = today_tz.year - birth_year
                            age_info = f" ({age} " + _("Jahre") + ")"
                        except:
                            pass

                    tz_display = f" [{tz_name}]" if tz_name and tz_name != 'Europe/Berlin' else ""
                    year_display = f".{birth_year}" if birth_year else ""

                    response_message += f"- **{name}**: {day:02d}.{month:02d}{year_display}{age_info}{tz_display}\n"

                embed = discord.Embed(
                    title=_("Geburtstagskalender"),
                    description=response_message,
                    color=embed_color
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in birthday-list: {e}")
            await eventmessages.unknown_error(interaction.guild, self.bot, interaction)

async def setup(bot):
    await bot.add_cog(BirthdayCommands(bot))