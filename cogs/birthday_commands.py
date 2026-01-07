# cogs/birthday_commands.py
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from datetime import datetime, date
import os
import asyncio
import pytz

class BirthdayCommands(commands.Cog, name="BirthdayCommands"):
    def __init__(self, bot):
        self.bot = bot

    # Autocomplete für Zeitzonen
    async def timezone_autocomplete(self, interaction: discord.Interaction, current: str):
        all_tzs = pytz.common_timezones
        return [
                   app_commands.Choice(name=tz, value=tz)
                   for tz in all_tzs if current.lower() in tz.lower()
               ][:25]

    # --- SLASH COMMAND: /birthday-set ---
    @app_commands.command(name="birthday-set", description="Setze deinen Geburtstag (MM TT (JJJJ) und optional deine Zeitzone.")
    @app_commands.describe(
        month="Der Monat deines Geburtstags (1-12).",
        day="Der Tag deines Geburtstags (z.B. 15).",
        year="Das Geburtsjahr (optional, z.B. 1990).",
        timezone="Deine Zeitzone (Standard: Europe/Berlin)."
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def birthday_set(self, interaction: discord.Interaction, month: int, day: int, year: int = None, timezone: str = "Europe/Berlin"):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur auf einem Server verwendet werden.", ephemeral=True)
            return

        # Validierung Zeitzone
        if timezone not in pytz.all_timezones:
            await interaction.response.send_message("Ungültige Zeitzone. Bitte wähle eine aus der Liste.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.setup_database(guild_id)

        if year is not None and (year < 1900 or year > datetime.now().year):
            await interaction.response.send_message(
                "Das angegebene Jahr ist ungültig. Bitte gib ein Jahr zwischen 1900 und dem aktuellen Jahr an.",
                ephemeral=True
            )
            return

        try:
            date(year if year is not None else 2000, month, day)
        except ValueError:
            await interaction.response.send_message(
                "Ungültiges Datum.",
                ephemeral=True
            )
            return

        user_id = interaction.user.id
        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await self.bot.ensure_tables(db)
            await db.execute(
                "INSERT OR REPLACE INTO birthdays (user_id, guild_id, month, day, year, timezone) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, guild_id, month, day, year, timezone)
            )
            await db.commit()

        year_str = f".{year}" if year is not None else ""
        await interaction.response.send_message(
            f"Dein Geburtstag wurde als {day:02d}.{month:02d}{year_str} ({timezone}) gespeichert! ✅",
            ephemeral=True
        )

    # --- SLASH COMMAND: /birthday-remove ---
    @app_commands.command(name="birthday-remove", description="Entferne deinen Geburtstag.")
    async def birthday_remove(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Dieser Befehl kann nur in einem Server verwendet werden.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        await self.bot.setup_database(guild_id)

        user_id = interaction.user.id
        async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
            await self.bot.ensure_tables(db)
            await db.execute("DELETE FROM birthdays WHERE user_id = ?", (user_id,))
            await db.commit()
        await interaction.response.send_message("Dein Geburtstag wurde erfolgreich entfernt.", ephemeral=True)

    # --- SLASH COMMAND: /birthday-list ---
    @app_commands.command(name="birthday-list", description="Zeigt alle registrierten Geburtstage für diesen Server an.")
    @app_commands.guild_only()
    async def birthday_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        guild_id = interaction.guild_id

        if guild_id is None:
            await interaction.followup.send("Dieser Befehl kann nur in einem Server ausgeführt werden.", ephemeral=True)
            return

        try:
            async with aiosqlite.connect(self.bot.get_db_path(guild_id)) as db:
                await self.bot.ensure_tables(db)

                cursor = await db.execute("SELECT user_id, day, month, year, timezone FROM birthdays WHERE guild_id = ?", (guild_id,))
                birthdays = await cursor.fetchall()

                current_config = self.bot.guild_configs.get(guild_id, {})
                embed_color = current_config.get("config_embed_color", 0x45a6c9)

                if not birthdays:
                    await interaction.followup.send("Es sind noch keine Geburtstage für diesen Server registriert.", ephemeral=True)
                    return

                response_message = ""
                birthdays.sort(key=lambda b: (b[2], b[1]))

                month_names = {
                    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
                    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
                }

                current_month = None
                for user_id, day, month, birth_year, tz_name in birthdays:
                    if month != current_month:
                        response_message += f"\n**__{month_names.get(month, str(month))}__**\n"
                        current_month = month

                    try:
                        user = await self.bot.fetch_user(user_id)
                    except discord.NotFound:
                        user = None

                    # Altersberechnung basierend auf lokaler Zeitzone des Nutzers
                    age_info = ""
                    if birth_year is not None and birth_year > 0:
                        tz = pytz.timezone(tz_name or 'Europe/Berlin')
                        today_tz = datetime.now(tz)
                        age = today_tz.year - birth_year
                        age_info = f" ({age} Jahre)"

                    tz_display = f" [{tz_name}]" if tz_name and tz_name != 'Europe/Berlin' else ""

                    if user:
                        response_message += f"- **{user.display_name}**: {day:02d}.{month:02d}.{f'{birth_year}' if birth_year else ''}{age_info}{tz_display}\n"
                    else:
                        response_message += f"- Unbekannter Benutzer (ID: {user_id}): {day:02d}.{month:02d}.{f'{birth_year}' if birth_year else ''}{age_info}{tz_display}\n"

                embed = discord.Embed(
                    title="Geburtstagskalender",
                    description=response_message,
                    color=embed_color
                )
                await interaction.followup.send(embed=embed, ephemeral=False)

        except Exception as e:
            await interaction.followup.send(f"⚠️ Fehler: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(BirthdayCommands(bot))