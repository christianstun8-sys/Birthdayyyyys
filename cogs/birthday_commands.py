# cogs/birthday_commands.py
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

    @app_commands.command(name="birthday-set", description="Setze deinen Geburtstag (MM TT (JJJJ) und optional deine Zeitzone.")
    @app_commands.describe(
        month="The month of your birthday.",
        day="The day of your birthday.",
        year="The year of your birthday (optional, f.e. 1990).",
        timezone="Your timezone (default: Europe/Berlin)."
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def birthday_set(self, interaction: discord.Interaction, month: int, day: int, year: int = None, timezone: str = "Europe/Berlin"):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        if timezone not in pytz.all_timezones:
            await interaction.response.send_message(_("Ungültige Zeitzone! Bitte wähle eine aus der Liste."), ephemeral=True)
            return

        try:
            if year:
                date(year, month, day)
            else:
                date(2000, month, day)
        except ValueError:
            await interaction.response.send_message(_("❌ Ungültiges Datum angegeben!"), ephemeral=True)
            return

        db_path = self.bot.get_db_path(interaction.guild_id)
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO birthdays (user_id, month, day, year, timezone) VALUES (?, ?, ?, ?, ?)",
                (interaction.user.id, month, day, year, timezone)
            )
            await db.commit()

        if year:
            await interaction.response.send_message(_("✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}.{year} ({timezone}) gesetzt!").format(day=day, month=month, year=year, timezone=timezone), ephemeral=True)
        else:
            await interaction.response.send_message(_("✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}. ({timezone}) gesetzt!").format(day=day, month=month, timezone=timezone), ephemeral=True)

    @app_commands.command(name="birthday-remove", description="Lösche deinen Geburtstag aus der Datenbank.")
    async def birthday_remove(self, interaction: discord.Interaction):
        lang = self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)

        db_path = self.bot.get_db_path(interaction.guild_id)
        async with aiosqlite.connect(db_path) as db:
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (interaction.user.id,))
            await db.commit()

        await interaction.response.send_message(_("✅ Dein Geburtstag wurde gelöscht."), ephemeral=True)

    @app_commands.command(name="birthday-show", description="Zeigt deinen gespeicherten Geburtstag an.")
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

    @app_commands.command(name="birthday-list", description="Zeigt die nächsten Geburtstage auf diesem Server an.")
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
                    member = interaction.guild.get_member(user_id)
                    if member:
                        name = member.display_name
                    else:
                        try:
                            user = await self.bot.fetch_user(user_id)
                            name = user.name
                        except:
                            name = _("Unbekannter Benutzer")

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