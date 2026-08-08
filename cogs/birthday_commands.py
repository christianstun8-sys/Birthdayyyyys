from datetime import date, datetime
import discord
from discord import app_commands
from discord.ext import commands
import pytz

import eventmessages
from utils.babel import translator


class BirthdayCommands(commands.Cog, name="BirthdayCommands"):

    def __init__(self, bot):
        self.bot = bot

    async def timezone_autocomplete(
            self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        all_tzs = pytz.common_timezones
        choices = []
        current_lower = current.lower()

        for tz in all_tzs:
            if current_lower in tz.lower():
                choices.append(app_commands.Choice(name=tz, value=tz))
            if len(choices) == 25:
                break

        return choices

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_set_name"),
        description=app_commands.locale_str("cmd_birthday_set_desc"),
    )
    @app_commands.describe(
        month=app_commands.locale_str("param_birthday_set_month"),
        day=app_commands.locale_str("param_birthday_set_day"),
        year=app_commands.locale_str("param_birthday_set_year"),
        timezone=app_commands.locale_str("param_birthday_set_timezone"),
        user=app_commands.locale_str("param_birthday_set_user"),
    )
    @app_commands.autocomplete(timezone=timezone_autocomplete)
    async def birthday_set(
            self,
            interaction: discord.Interaction,
            month: int,
            day: int,
            year: int = None,
            timezone: str = "Europe/Berlin",
            user: discord.User = None,
    ):
        lang = (
            self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        )
        _ = translator.get_translation(lang)

        if user is not None and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                _("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True
            )

        if timezone not in pytz.all_timezones:
            return await interaction.response.send_message(
                _("Ungültige Zeitzone! Bitte wähle eine aus der Liste."),
                ephemeral=True,
            )

        try:
            date(year if year else 2000, month, day)
        except ValueError:
            return await interaction.response.send_message(
                _("❌ Ungültiges Datum angegeben!"), ephemeral=True
            )

        target_user_id = user.id if user else interaction.user.id

        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    INSERT INTO birthdays (guild_id, user_id, month, day, year, timezone)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        month = VALUES(month),
                        day = VALUES(day),
                        year = VALUES(year),
                        timezone = VALUES(timezone)
                """,
                (interaction.guild_id, target_user_id, month, day, year, timezone),
                )
                await conn.commit()

        if user:
            if year:
                return await interaction.response.send_message(
                    _(
                        "✅ Der Geburtstag von {mention} wurde auf den"
                        " {day:02d}.{month:02d}.{year} ({timezone}) gesetzt!"
                    ).format(
                        mention=user.mention,
                        day=day,
                        month=month,
                        year=year,
                        timezone=timezone,
                    ),
                    ephemeral=True,
                )
            else:
                return await interaction.response.send_message(
                    _(
                        "✅ Der Geburtstag von {mention} wurde auf den"
                        " {day:02d}.{month:02d} ({timezone}) gesetzt!"
                    ).format(
                        mention=user.mention,
                        day=day,
                        month=month,
                        timezone=timezone,
                    ),
                    ephemeral=True,
                )

        if year:
            await interaction.response.send_message(
                _(
                    "✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}.{year}"
                    " ({timezone}) gesetzt!"
                ).format(day=day, month=month, year=year, timezone=timezone),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                _(
                    "✅ Dein Geburtstag wurde auf den {day:02d}.{month:02d}."
                    " ({timezone}) gesetzt!"
                ).format(day=day, month=month, timezone=timezone),
                ephemeral=True,
            )

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_remove_name"),
        description=app_commands.locale_str("cmd_birthday_remove_desc"),
    )
    @app_commands.describe(
        user=app_commands.locale_str("param_birthday_remove_user"),
    )
    async def birthday_remove(
            self, interaction: discord.Interaction, user: discord.User = None
    ):
        lang = (
            self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        )
        _ = translator.get_translation(lang)

        if user is not None and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(
                _("⚠️ Du hast keine Berechtigung dazu."), ephemeral=True
            )

        target_user_id = user.id if user else interaction.user.id

        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM birthdays WHERE guild_id = %s AND user_id = %s",
                    (interaction.guild_id, target_user_id),
                )
                await conn.commit()

        if user:
            return await interaction.response.send_message(
                _("✅ Der Geburtstag von {mention} wurde gelöscht.").format(
                    mention=user.mention
                ),
                ephemeral=True,
            )
        await interaction.response.send_message(
            _("✅ Dein Geburtstag wurde gelöscht."), ephemeral=True
        )

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_show_name"),
        description=app_commands.locale_str("cmd_birthday_show_desc"),
    )
    @app_commands.describe(
        user=app_commands.locale_str("param_birthday_show_user")
    )
    async def birthday_show(
            self, interaction: discord.Interaction, user: discord.User = None
    ):
        lang = (
            self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        )
        _ = translator.get_translation(lang)

        target_user_id = user.id if user else interaction.user.id

        async with self.bot.db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT month, day, year, timezone
                       FROM birthdays
                       WHERE guild_id = %s AND user_id = %s""",
                    (interaction.guild_id, target_user_id),
                )
                row = await cursor.fetchone()

                if row:
                    month, day, year, tz = row
                    if user:
                        if year:
                            return await interaction.response.send_message(
                                _(
                                    "Der Geburtstag von {mention} ist am"
                                    " {day:02d}.{month:02d}.{year} ({tz})."
                                ).format(
                                    day=day,
                                    month=month,
                                    year=year,
                                    tz=tz,
                                    mention=user.mention,
                                ),
                                ephemeral=True,
                            )
                        else:
                            return await interaction.response.send_message(
                                _(
                                    "Der Geburtstag von {mention} ist am"
                                    " {day:02d}.{month:02d} ({tz})."
                                ).format(day=day, month=month, tz=tz, mention=user.mention),
                                ephemeral=True,
                            )
                    else:
                        if year:
                            return await interaction.response.send_message(
                                _(
                                    "Dein Geburtstag ist am {day:02d}.{month:02d}.{year}"
                                    " ({tz})."
                                ).format(day=day, month=month, year=year, tz=tz),
                                ephemeral=True,
                            )
                        else:
                            return await interaction.response.send_message(
                                _("Dein Geburtstag ist am {day:02d}.{month:02d}. ({tz}).").format(
                                    day=day, month=month, tz=tz
                                ),
                                ephemeral=True,
                            )
                else:
                    if user:
                        return await interaction.response.send_message(
                            _(
                                "❌ Der Benutzer {mention} hat noch keinen Geburtstag"
                                " registriert."
                            ).format(mention=user.mention),
                            ephemeral=True,
                        )
                    else:
                        return await interaction.response.send_message(
                            _("❌ Du hast noch keinen Geburtstag registriert."),
                            ephemeral=True,
                        )

    @app_commands.command(
        name=app_commands.locale_str("cmd_birthday_list_name"),
        description=app_commands.locale_str("cmd_birthday_list_desc"),
    )
    async def birthday_list(self, interaction: discord.Interaction):
        lang = (
            self.bot.guild_configs.get(interaction.guild_id, {}).get("lang", "en")
        )
        _ = translator.get_translation(lang)

        await interaction.response.defer()
        embed_color = self.bot.guild_configs.get(interaction.guild_id, {}).get(
            "config_embed_color", 0x3AAA06
        )

        month_names = {
            1: _("Januar"),
            2: _("Februar"),
            3: _("März"),
            4: _("April"),
            5: _("Mai"),
            6: _("Juni"),
            7: _("Juli"),
            8: _("August"),
            9: _("September"),
            10: _("Oktober"),
            11: _("November"),
            12: _("Dezember"),
        }

        try:
            async with self.bot.db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        """SELECT user_id, month, day, year, timezone
                           FROM birthdays
                           WHERE guild_id = %s
                           ORDER BY month, day""",
                        (interaction.guild_id,),
                    )
                    rows = await cursor.fetchall()

            if not rows:
                await interaction.followup.send(
                    _("⚠️ Es sind noch keine Geburtstage registriert."), ephemeral=True
                )
                return

            months_dict = {}

            for user_id, month, day, birth_year, tz_name in rows:
                name = f"<@{user_id}>"

                age_info = ""
                if birth_year and birth_year > 0:
                    try:
                        tz = pytz.timezone(tz_name or "Europe/Berlin")
                        today_tz = datetime.now(tz)
                        age = today_tz.year - birth_year
                        age_info = f" ({age} " + _("Jahre") + ")"
                    except Exception:
                        pass

                tz_display = (
                    f" `[{tz_name}]`" if tz_name and tz_name != "Europe/Berlin" else ""
                )
                year_display = f".{birth_year}" if birth_year else ""

                entry = (
                    f"• **{day:02d}.{month:02d}{year_display}** -"
                    f" {name}{age_info}{tz_display}"
                )

                if month not in months_dict:
                    months_dict[month] = []
                months_dict[month].append(entry)

            embed = discord.Embed(
                title=f"📅 {_('Geburtstagskalender')}", color=embed_color
            )

            for m_num in range(1, 13):
                if m_num in months_dict:
                    field_value = "\n".join(months_dict[m_num])

                    if len(field_value) > 1024:
                        field_value = field_value[:1020] + "..."

                    embed.add_field(
                        name=f"▫️ {month_names[m_num]}",
                        value=field_value,
                        inline=False,
                    )

            await interaction.followup.send(embed=embed)

        except Exception as e:
            print(f"Error in birthday-list: {e}")
            await eventmessages.unknown_error(
                interaction.guild, self.bot, interaction
            )


async def setup(bot):
    await bot.add_cog(BirthdayCommands(bot))