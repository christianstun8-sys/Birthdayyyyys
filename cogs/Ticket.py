from pathlib import Path

import discord
from discord.app_commands import locale_str
from discord.ext import commands
import aiosqlite
import asyncio
import io

log_channel_id = 1454156865997897969
team_role_id = 1454153903884210307
CLOSED_CATEGORY_ID = 1454155712954634352
OPEN_CATEGORY_ID = 1454155831435329730
CLAIMED_CATEGORY_ID = 1454156056220405821

BASE_DIR = Path(__file__).parent.parent / "databases"
TICKETS_DB = BASE_DIR / 'tickets.db'

async def init_db():
    async with aiosqlite.connect(TICKETS_DB) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                                                   channel_id INTEGER PRIMARY KEY,
                                                   user_id INTEGER NOT NULL,
                                                   status TEXT NOT NULL,
                                                   claimed_by INTEGER
            )
            """
        )
        await db.commit()

async def get_ticket_data(channel_id):
    async with aiosqlite.connect(TICKETS_DB) as db:
        async with db.execute("SELECT user_id, status, claimed_by FROM tickets WHERE channel_id = ?", (channel_id,)) as cursor:
            return await cursor.fetchone()

async def create_transcript(channel: discord.TextChannel):
    transcript_text = f"Transkript für Ticket: {channel.name}\n"
    transcript_text += f"ID: {channel.id}\n"
    transcript_text += "-" * 30 + "\n\n"

    async for message in channel.history(limit=None, oldest_first=True):
        timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        content = message.content

        if message.embeds:
            for embed in message.embeds:
                embed_info = f"[Embed: {embed.title if embed.title else ''} - {embed.description if embed.description else ''}]"
                content += f"\n{embed_info}"

        transcript_text += f"[{timestamp}] {message.author}: {content}\n"

    return io.BytesIO(transcript_text.encode('utf-8'))

async def log_to_channel(bot, guild, embed, file=None):
        log_channel = bot.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(embed=embed, file=file)

async def move_ticket_category(channel: discord.TextChannel, status: str, claimed_by_id: int = None):

    category_id = None
    if status == 'geschlossen':
        category_id = CLOSED_CATEGORY_ID
    elif status == 'offen':
        if claimed_by_id:
            category_id = CLAIMED_CATEGORY_ID
        else:
            category_id = OPEN_CATEGORY_ID

    if category_id:
        category = channel.guild.get_channel(category_id)
        if category and isinstance(category, discord.CategoryChannel):
            await channel.edit(category=category)


class ConfirmDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Ja, löschen", style=discord.ButtonStyle.red, custom_id="confirm_delete_button")
    async def confirm_delete_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        ticket_data = await get_ticket_data(interaction.channel_id)
        if not ticket_data:
            return await interaction.response.send_message("❌ Dieses Ticket existiert nicht mehr in der Datenbank.", ephemeral=True)

        await interaction.response.send_message("Ticket wird in 5 Sekunden gelöscht...", ephemeral=True)

        channel = interaction.channel

        transcript_file = await create_transcript(channel)
        file = discord.File(transcript_file, filename=f"transcript-{channel.name}.txt")

        log_embed = discord.Embed(
            title="Ticket Gelöscht",
            description=f"Ticket **{channel.name}** wurde von {interaction.user.mention} gelöscht.",
            color=discord.Color.dark_red()
        )

        await asyncio.sleep(5)

        async with aiosqlite.connect(TICKETS_DB) as db:
            await db.execute("DELETE FROM tickets WHERE channel_id = ?", (channel.id,))
            await db.commit()

        await log_to_channel(interaction.client, interaction.guild, log_embed, file=file)
        await channel.delete()

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.green, custom_id="cancel_delete_button")
    async def cancel_delete_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="✅ Löschvorgang abgebrochen",
                              color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)

class ClosedTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔓 Wieder öffnen", style=discord.ButtonStyle.green, custom_id="ticket_open_button")
    async def open_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("⚠️ Du hast nicht die Berechtigung, dieses Ticket zu öffnen!", ephemeral=True)

        channel = interaction.channel
        ticket_data = await get_ticket_data(channel.id)

        if not ticket_data:
            return await interaction.response.send_message("❌ Fehler: Ticket nicht in der Datenbank gefunden.", ephemeral=True)
        if ticket_data[1] == 'offen':
            return await interaction.response.send_message("⚠️ Dieses Ticket ist bereits geöffnet.", ephemeral=True)

        overwrites_to_update = {}
        for target, permissions in channel.overwrites.items():
            if isinstance(target, (discord.Member, discord.User, discord.Role)) and permissions.read_messages:
                overwrites_to_update[target] = discord.PermissionOverwrite(
                    send_messages=True,
                    read_messages=True,
                    read_message_history=True
                )

        for target, overwrite in overwrites_to_update.items():
            await channel.set_permissions(target, overwrite=overwrite)

        async with aiosqlite.connect(TICKETS_DB) as db:
            await db.execute("UPDATE tickets SET status = ? WHERE channel_id = ?", ('offen', channel.id))
            await db.commit()

        await move_ticket_category(channel, 'offen')

        log_embed = discord.Embed(
            title="Ticket Wiedereröffnet",
            description=f"Ticket {channel.mention} wurde von {interaction.user.mention} wieder geöffnet.",
            color=discord.Color.green()
        )
        await log_to_channel(interaction.client, interaction.guild, log_embed)

        embed = discord.Embed(title="🔓 Ticket wieder geöffnet", description=f"{interaction.user.mention} hat das Ticket geöffnet!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=OpenTicketView())

    @discord.ui.button(label="⛔ Löschen", style=discord.ButtonStyle.red, custom_id="delete_ticket_button")
    async def delete_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("⚠️ Du hast nicht die Berechtigung, dieses Ticket zu löschen!", ephemeral=True)

        ticket_data = await get_ticket_data(interaction.channel_id)
        if not ticket_data:
            return await interaction.response.send_message("❌ Ticket-Daten nicht gefunden.", ephemeral=True)

        embed = discord.Embed(
            title="❗ Bist du sicher?",
            description="Diese Aktion kann **nicht** rückgängig gemacht werden. Der Channel wird permanent gelöscht.",
            color=discord.Color.dark_red()
        )
        await interaction.response.send_message(embed=embed, view=ConfirmDeleteView(), ephemeral=True)

class OpenTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Schließen", style=discord.ButtonStyle.red, custom_id="ticket_close_button")
    async def close_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("⚠️ Du hast nicht die Berechtigung, dieses Ticket zu schließen.", ephemeral=True)

        channel = interaction.channel
        ticket_data = await get_ticket_data(channel.id)

        if not ticket_data:
            return await interaction.response.send_message("❌ Fehler: Ticket nicht in der Datenbank gefunden.", ephemeral=True)
        if ticket_data[1] == 'geschlossen':
            return await interaction.response.send_message("⚠️ Dieses Ticket ist bereits geschlossen.", ephemeral=True)

        overwrites_to_update = {}
        for target, permissions in channel.overwrites.items():
            is_team_or_bot = isinstance(target, discord.Role) and target.id == team_role_id or target.id == interaction.guild.me.id
            if not is_team_or_bot and permissions.send_messages:
                overwrites_to_update[target] = discord.PermissionOverwrite(
                    send_messages=False,
                    read_messages=True,
                    read_message_history=True
                )

        user_id = ticket_data[0]
        member = interaction.guild.get_member(user_id)
        if member and member not in overwrites_to_update:
            overwrites_to_update[member] = discord.PermissionOverwrite(
                send_messages=False,
                read_messages=True,
                read_message_history=True
            )

        for target, overwrite in overwrites_to_update.items():
            await channel.set_permissions(target, overwrite=overwrite)

        async with aiosqlite.connect(TICKETS_DB) as db:
            await db.execute("UPDATE tickets SET status = ?, claimed_by = NULL WHERE channel_id = ?", ('geschlossen', channel.id))
            await db.commit()

        await move_ticket_category(channel, 'geschlossen')

        log_embed = discord.Embed(
            title="Ticket Geschlossen",
            description=f"Ticket {channel.mention} wurde von {interaction.user.mention} geschlossen.",
            color=discord.Color.orange()
        )
        await log_to_channel(interaction.client, interaction.guild, log_embed)

        embed = discord.Embed(
            title="🔒 Ticket geschlossen",
            description=f"{interaction.user.mention} hat das Ticket geschlossen.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=ClosedTicketView())

class TicketClaimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="👍 Claim", style=discord.ButtonStyle.secondary, custom_id="ticket_claim_button")
    async def claim_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("⚠️ Du hast nicht die Berechtigung, dieses Ticket zu claimen.", ephemeral=True)

        ticket_data = await get_ticket_data(interaction.channel.id)
        if not ticket_data:
            return await interaction.response.send_message("❌ Fehler: Ticket nicht in der Datenbank gefunden.", ephemeral=True)

        if ticket_data[1] != 'offen':
            return await interaction.response.send_message("⚠️ Nur offene Tickets können geclaimt werden.", ephemeral=True)

        claimed_by_id = ticket_data[2]
        new_claimed_by_id = None

        async with aiosqlite.connect(TICKETS_DB) as db:
            if claimed_by_id is None:
                new_claimed_by_id = interaction.user.id
                await db.execute("UPDATE tickets SET claimed_by = ? WHERE channel_id = ?", (new_claimed_by_id, interaction.channel.id))
                embed = discord.Embed(description=f"{interaction.user.mention} hat dieses Ticket geclaimt.", color=discord.Color.blue())
                await move_ticket_category(interaction.channel, 'offen', claimed_by_id=new_claimed_by_id)

                log_embed = discord.Embed(
                    title="Ticket Geclaimt",
                    description=f"Ticket {interaction.channel.mention} wurde von {interaction.user.mention} geclaimt.",
                    color=discord.Color.blue()
                )
                await log_to_channel(interaction.client, interaction.guild, log_embed)

            elif claimed_by_id == interaction.user.id:
                await db.execute("UPDATE tickets SET claimed_by = NULL WHERE channel_id = ?", (interaction.channel.id,))
                embed = discord.Embed(description=f"{interaction.user.mention} hat den Claim für dieses Ticket entfernt.", color=discord.Color.blue())
                await move_ticket_category(interaction.channel, 'offen', claimed_by_id=None)

                log_embed = discord.Embed(
                    title="Ticket Unclaimed",
                    description=f"{interaction.user.mention} hat den Claim für {interaction.channel.mention} aufgehoben.",
                    color=discord.Color.light_grey()
                )
                await log_to_channel(interaction.client, interaction.guild, log_embed)

            else:
                claimer = interaction.guild.get_member(claimed_by_id)
                return await interaction.response.send_message(f"Dieses Ticket ist bereits von {claimer.mention if claimer else 'einem Teammitglied'} geclaimt.", ephemeral=True)

            await db.commit()
            await interaction.response.send_message(embed=embed)

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✉️ Ticket erstellen", style=discord.ButtonStyle.green, custom_id="ticket_create_button")
    async def create_ticket_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect(TICKETS_DB) as db:
            async with db.execute("SELECT channel_id FROM tickets WHERE user_id = ? AND status = ?", (interaction.user.id, 'offen')) as cursor:
                existing_ticket = await cursor.fetchone()

            if existing_ticket:
                return await interaction.followup.send(f"Du hast bereits ein offenes Ticket: <#{existing_ticket[0]}>", ephemeral=True)

            guild = interaction.guild
            category = guild.get_channel(OPEN_CATEGORY_ID)
            if not category:
                await interaction.followup.send("Fehler: Die Kategorie für offene Tickets wurde nicht gefunden.", ephemeral=True)
                return

            op = interaction.user
            team_role = guild.get_role(team_role_id)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                op: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                team_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
            }

            channel_name = f"ticket-{interaction.user.name}"
            new_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, category=category)

            await db.execute(
                "INSERT INTO tickets (channel_id, user_id, status) VALUES (?, ?, ?)",
                (new_channel.id, interaction.user.id, 'offen')
            )
            await db.commit()

        embed = discord.Embed(
            title=f"Willkommen, {interaction.user.display_name}!",
            description="Bitte beschreibe dein Anliegen so detailliert wie möglich. Ein Teammitglied wird sich in Kürze um dich kümmern.",
            color=discord.Color.blue()
        )
        log_embed = discord.Embed(
            title="Neues Ticket!",
            description=f"{interaction.user.mention} ({interaction.user.id}) hat ein neues Ticket erstellt: {new_channel.mention}",
            color=discord.Color.blue()
        )

        await new_channel.send(embed=embed, view=OpenTicketView(), content=f"{interaction.user.mention}")
        await new_channel.send(view=TicketClaimView())
        await interaction.followup.send(f"Dein Ticket wurde erstellt: {new_channel.mention}", ephemeral=True)

        await log_to_channel(interaction.client, interaction.guild, log_embed)

class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await init_db()
        self.bot.add_view(TicketCreateView())
        self.bot.add_view(OpenTicketView())
        self.bot.add_view(ClosedTicketView())
        self.bot.add_view(ConfirmDeleteView())
        self.bot.add_view(TicketClaimView())

    @commands.command(name="ticket-panel")
    @commands.has_permissions(manage_messages=True)
    async def ticketpanel(self, ctx: commands.Context):
        if ctx.guild.id != 1453670454350057613:
            return

        embed = discord.Embed(
            title="Ticket erstellen",
            description="Klicke auf den Button, um ein neues Ticket zu erstellen und unser Team zu kontaktieren.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketCreateView())

class AddMember(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="ticket-addmember", description=locale_str("Fügt einen Benutzer zum aktuellen Ticket hinzu."))
    @discord.app_commands.guilds(discord.Object(id=1453670454350057613))
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    @discord.app_commands.describe(member="Der Benutzer, der zum Ticket hinzugefügt werden soll.")
    async def ticket_add_member(self, interaction: discord.Interaction, member: discord.Member):
        channel = interaction.channel
        ticket_data = await get_ticket_data(channel.id)
        if not ticket_data:
            return await interaction.response.send_message("❌ Dieser Befehl kann nur in einem registrierten Ticket-Kanal verwendet werden.", ephemeral=True)

        overwrites = channel.overwrites_for(member)
        overwrites.read_messages = True
        overwrites.send_messages = True

        try:
            await channel.set_permissions(member, overwrite=overwrites)
            await interaction.response.send_message(f"{member.mention} wurde dem Ticket erfolgreich hinzugefügt.")

            log_embed = discord.Embed(
                title="Mitglied Hinzugefügt",
                description=f"{interaction.user.mention} hat {member.mention} zum Ticket {channel.mention} hinzugefügt.",
                color=discord.Color.blue()
            )
            await log_to_channel(interaction.client, interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("Ich habe nicht die Berechtigung, die Berechtigungen für diesen Benutzer zu ändern. Bitte überprüfe meine Rollen.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ein Fehler ist aufgetreten: {e}", ephemeral=True)


class RemoveMember(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.app_commands.command(name="ticket-removemember", description=locale_str("Entfernt einen Nutzer aus dem aktuellen Ticket."))
    @discord.app_commands.checks.has_permissions(manage_messages=True)
    @discord.app_commands.guilds(discord.Object(id=1453670454350057613))
    @discord.app_commands.describe(member="Der Benutzer, der vom Ticket entfernt werden soll.")
    async def ticket_remove_member(self, interaction: discord.Interaction, member: discord.Member):
        channel = interaction.channel
        ticket_data = await get_ticket_data(channel.id)
        if not ticket_data:
            return await interaction.response.send_message("❌ Dieser Befehl kann nur in einem registrierten Ticket-Kanal verwendet werden.", ephemeral=True)

        overwrites = channel.overwrites_for(member)
        overwrites.read_messages = False
        overwrites.send_messages = False

        try:
            await channel.set_permissions(member, overwrite=overwrites)
            await interaction.response.send_message(f"{member.mention} wurde vom Ticket erfolgreich entfernt.")

            log_embed = discord.Embed(
                title="Mitglied Entfernt",
                description=f"{interaction.user.mention} hat {member.mention} aus dem Ticket {channel.mention} entfernt.",
                color=discord.Color.blue()
            )
            await log_to_channel(interaction.client, interaction.guild, log_embed)

        except discord.Forbidden:
            await interaction.response.send_message("Ich habe nicht die Berechtigung, die Berechtigungen für diesen Benutzer zu ändern. Bitte überprüfe meine Rollen.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ein Fehler ist aufgetreten: {e}", ephemeral=True)


    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        if guild.id != 1453670454350057613:
            return

        async with aiosqlite.connect(TICKETS_DB) as db:
            async with db.execute("SELECT channel_id FROM tickets WHERE user_id = ?", (member.id,)) as cursor:
                rows = await cursor.fetchall()
                channel_ids = [row[0] for row in rows]

        for channel_id in channel_ids:
            channel = guild.get_channel(channel_id)
            if not channel:
                try:
                    channel = await guild.fetch_channel(channel_id)
                except discord.NotFound:
                    channel = None

            if channel:
                try:
                    await channel.delete(reason="Nutzer hat den Support-Server verlassen.")
                except discord.Forbidden:
                    print(f"Keine Rechte um Ticket-Kanal {channel_id} zu löschen.")
                except Exception as e:
                    print(f"Fehler beim Löschen des Kanals {channel_id}: {e}")

        if channel_ids:
            async with aiosqlite.connect(TICKETS_DB) as db:
                await db.execute("DELETE FROM tickets WHERE user_id = ?", (member.id,))
                await db.commit()


async def setup(bot):
    await bot.add_cog(TicketCog(bot))
    await bot.add_cog(AddMember(bot))
    await bot.add_cog(RemoveMember(bot))