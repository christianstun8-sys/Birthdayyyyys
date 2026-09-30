from datetime import date, datetime
import discord
from discord import app_commands
from discord.ext import commands
import pytz

import eventmessages
from utils.babel import translator

class BirthdayPaginatorView(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], author_id: int):
        super().__init__(timeout=180)
        self.pages = pages
        self.author_id = author_id
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author_id:
            return

        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current_page], view=self
        )

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_button(
            self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.author_id:
            return

        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.pages[self.current_page], view=self
        )

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
                    VALUES (%s, %s, %s, %s, %s, %s) AS new
                    ON DUPLICATE KEY UPDATE
                        month = new.month,
                        day = new.day,
                        year = new.year,
                        timezone = new.timezone
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

            pages = []
            title = f"📅 {_('Geburtstagskalender')}"

            current_embed = discord.Embed(title=title, color=embed_color)
            current_size = len(title)

            for m_num in range(1, 13):
                if m_num not in months_dict:
                    continue

                entries = months_dict[m_num]
                field_name = f"▫️ {month_names[m_num]}"
                current_value_lines = []

                for entry in entries:
                    test_val = "\n".join(current_value_lines + [entry])
                    if len(test_val) > 1024:
                        f_val = "\n".join(current_value_lines)
                        if current_size + len(field_name) + len(f_val) > 5500:
                            pages.append(current_embed)
                            current_embed = discord.Embed(title=title, color=embed_color)
                            current_size = len(title)

                        current_embed.add_field(name=field_name, value=f_val, inline=False)
                        current_size += len(field_name) + len(f_val)
                        current_value_lines = [entry]
                    else:
                        current_value_lines.append(entry)

                if current_value_lines:
                    f_val = "\n".join(current_value_lines)
                    if current_size + len(field_name) + len(f_val) > 5500:
                        pages.append(current_embed)
                        current_embed = discord.Embed(title=title, color=embed_color)
                        current_size = len(title)

                    current_embed.add_field(name=field_name, value=f_val, inline=False)
                    current_size += len(field_name) + len(f_val)

            if len(current_embed.fields) > 0:
                pages.append(current_embed)

            if not pages:
                await interaction.followup.send(
                    _("⚠️ Es sind noch keine Geburtstage registriert."), ephemeral=True
                )
                return

            if len(pages) == 1:
                await interaction.followup.send(embed=pages[0])
            else:
                view = BirthdayPaginatorView(pages=pages, author_id=interaction.user.id)
                await interaction.followup.send(embed=pages[0], view=view)

        except Exception as e:
            print(f"Error in birthday-list: {e}")
            try:
                await interaction.followup.send(
                    _("Ein unbekannter Fehler ist aufgetreten. Bitte melde dich beim Support-"
                      "Server."), ephemeral=True
                )
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(BirthdayCommands(bot))