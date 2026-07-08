import discord
from discord.ext import commands
import aiosqlite
from pathlib import Path
from discord.app_commands import locale_str


class RenameModal(discord.ui.Modal, title="Kanal umbenennen"):
    def __init__(self, voice_channel: discord.VoiceChannel):
        super().__init__()
        self.voice_channel = voice_channel

    new_name = discord.ui.TextInput(
        label="Neuer Kanalname / New Channel Name",
        placeholder="Schreibe den neuen Namen hier hin.\nWrite the new name here.",
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.voice_channel.edit(name=self.new_name.value)
        await interaction.response.send_message(
            f"Der Kanal wurde erfolgreich zu **{self.new_name.value}** umbenannt.\n"
            f"*The channel was successfully renamed to **{self.new_name.value}**.*",
            ephemeral=True
        )

class LimitModal(discord.ui.Modal, title="Benutzerlimit ändern"):
    def __init__(self, voice_channel: discord.VoiceChannel):
        super().__init__()
        self.voice_channel = voice_channel

    new_limit = discord.ui.TextInput(
        label="Neues Benutzerlimit (0-99) / New User Limit",
        placeholder="Füge eine Nummer zwischen 0 und 99 ein. (0 für unendlich)...\nEnter a number between 0 and 99. (0 for infinite)...",
        max_length=2,
        min_length=1
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.new_limit.value)
            if 0 <= limit <= 99:
                await self.voice_channel.edit(user_limit=limit)
                await interaction.response.send_message(
                    f"Das Benutzerlimit wurde erfolgreich zu **{limit}** gesetzt.\n"
                    f"*The user limit was successfully set to **{limit}**.*",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Das Limit muss zwischen 0 und 99 sein.\n"
                    "*The limit must be between 0 and 99.*",
                    ephemeral=True
                )
        except ValueError:
            await interaction.response.send_message(
                "Unbekannte Zahl. Bitte füge eine valide Nummer ein.\n"
                "*Unknown number. Please enter a valid number.*",
                ephemeral=True
            )

class TempVoiceView(discord.ui.View):
    def __init__(self, creator_id: int, voice_channel: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.voice_channel = voice_channel

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message(
                "Nur der Kanalersteller kann das ändern.\n"
                "*Only the channel creator can change this.*",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Sperren / Lock", style=discord.ButtonStyle.red, custom_id="tempvoice_lock", emoji="🚫")
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.voice_channel.set_permissions(interaction.guild.default_role, connect=False)

        button.disabled = True
        self.children[1].disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"🔒 Der Kanal {self.voice_channel.mention} wurde gesperrt.\n"
            f"*🔒 The channel {self.voice_channel.mention} has been locked.*",
            ephemeral=True
        )

    @discord.ui.button(label="Öffnen / Unlock", style=discord.ButtonStyle.green, custom_id="tempvoice_unlock", emoji="🔓", disabled=True)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.voice_channel.set_permissions(interaction.guild.default_role, connect=True)

        button.disabled = True
        self.children[0].disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"🔓 Der Kanal {self.voice_channel.mention} wurde wieder geöffnet.\n"
            f"*🔓 The channel {self.voice_channel.mention} has been unlocked.*",
            ephemeral=True
        )

    @discord.ui.button(label="Verstecken / Hide", style=discord.ButtonStyle.red, custom_id="tempvoice_hide", emoji="🌙")
    async def hide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.voice_channel.set_permissions(interaction.guild.default_role, view_channel=False)

        button.disabled = True
        self.children[3].disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"🌑 Der Kanal {self.voice_channel.mention} wurde vor allen versteckt.\n"
            f"*🌑 The channel {self.voice_channel.mention} has been hidden from everyone.*",
            ephemeral=True
        )

    @discord.ui.button(label="Auftauchen / Show", style=discord.ButtonStyle.green, custom_id="tempvoice_show", emoji="🔍", disabled=True)
    async def show_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.voice_channel.set_permissions(interaction.guild.default_role, view_channel=True)

        button.disabled = True
        self.children[2].disabled = False

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            f"💡 Der Kanal {self.voice_channel.mention} ist wieder für jeden sichtbar.\n"
            f"*💡 The channel {self.voice_channel.mention} is now visible to everyone again.*",
            ephemeral=True
        )

    @discord.ui.button(label="Umbennenen / Rename", style=discord.ButtonStyle.blurple, custom_id="tempvoice_rename", emoji="📝", row=2)
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RenameModal(self.voice_channel))

    @discord.ui.button(label="Limit ändern / Change Limit", style=discord.ButtonStyle.blurple, custom_id="tempvoice_limit", emoji="🎚️", row=2)
    async def limit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(LimitModal(self.voice_channel))

class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = Path(__file__).parent.parent / "databases" / 'TempVoice.db'
        self.temp_channels_data = {}

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS tempvoice (
                                                         guild_id INTEGER PRIMARY KEY,
                                                         channel_id INTEGER NOT NULL
                )
                """
            )
            await db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.init_db()

    @discord.app_commands.command(
        name='tempvoice',
        description=locale_str('Setzt einen Kanal für das Tempvoice-Feature. / Sets a channel for the TempVoice feature.')
    )
    @discord.app_commands.guilds(discord.Object(id=1453670454350057613))
    async def tempvoice_command(self, interaction: discord.Interaction, channel: discord.VoiceChannel):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "Dieser Kanal kann nur auf einem Server ausgeführt werden.\n"
                "*This command can only be executed on a server.*",
                ephemeral=True
            )
            return

        if interaction.user.id == 1235134572157603841:

            guild_id = guild.id
            tempvoicechannel_id = channel.id

            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        "INSERT OR REPLACE INTO tempvoice (guild_id, channel_id) VALUES (?, ?)",
                        (guild_id, tempvoicechannel_id)
                    )
                    await db.commit()

                category = discord.utils.get(guild.categories, name='🔊┃TempVoices')
                if not category:
                    category = await guild.create_category(name='🔊┃TempVoices')

                await interaction.response.send_message(
                    f"Der Kanal {channel.mention} wurde erfolgreich als TempVoice Kanal gesetzt.\n"
                    f"*The channel {channel.mention} was successfully set as a TempVoice channel.*",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"Ein Fehler ist aufgetreten: {e}\n"
                    f"*An error occurred: {e}*",
                    ephemeral=True
                )

        else:
            await interaction.response.send_message(
                "⚠️ Du hast dazu keine Berechtigung.\n"
                "*⚠️ You do not have permission to do this.*",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        if not guild:
            return

        if guild.id != 1453670454350057613:
            return

        if after.channel is not None and before.channel != after.channel:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute("SELECT channel_id FROM tempvoice WHERE guild_id = ?", (guild.id,))
                    row = await cursor.fetchone()

                if row and after.channel.id == row[0]:
                    category = discord.utils.get(guild.categories, name='TempVoices')
                    if not category:
                        overwrites = after.channel.category.overwrites if after.channel.category else None
                        category = await guild.create_category(name='TempVoices', overwrites=overwrites)

                    new_voice_channel = await category.create_voice_channel(name=f"voice-{member.name}")
                    await member.move_to(new_voice_channel)

                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }

                    text_channel = await category.create_text_channel(
                        name=f"interface-{member.name}",
                        topic=f"Interface für {new_voice_channel.name} von {member.name} / Interface for {new_voice_channel.name} by {member.name}",
                        overwrites=overwrites
                    )

                    embed = discord.Embed(
                        title="TempVoice Interface",
                        color=discord.Color.orange(),
                        description=f"🎧 Willkommen zum Interface, **{member.name}**.\n"
                                    f"*🎧 Welcome to the interface, **{member.name}**.*\n\n"
                                    f"➡️ Benutze die **Buttons** unten um deinen Kanal einzustellen.\n"
                                    f"*➡️ Use the **buttons** below to configure your channel.*\n\n"
                                    f"➡️ **WICHTIG:** Dieser Kanal wird zusammen mit deinem Tempvoice-Kanal gelöscht, wenn der Tempvoice-Kanal leer ist.\n"
                                    f"*➡️ **IMPORTANT:** This channel will be deleted along with your TempVoice channel when the TempVoice channel is empty.*"
                    )

                    view = TempVoiceView(creator_id=member.id, voice_channel=new_voice_channel)
                    await text_channel.send(embed=embed, view=view)

                    self.temp_channels_data[new_voice_channel.id] = {
                        'creator': member.id,
                        'interface': text_channel.id
                    }

            except Exception as e:
                print(f"Ein Fehler ist im Event on_voice_state_update aufgetreten: {e}")

        if before.channel is not None and "voice-" in before.channel.name.lower():

            if len(before.channel.members) == 0:
                vc_id = before.channel.id

                data = self.temp_channels_data.get(vc_id)

                try:
                    if data and 'interface' in data:
                        interface_id = data['interface']
                        interface_channel = guild.get_channel(interface_id)

                        if interface_channel:
                            await interface_channel.delete()

                    await before.channel.delete()

                    if vc_id in self.temp_channels_data:
                        del self.temp_channels_data[vc_id]

                except discord.errors.Forbidden:
                    print(f"ERROR: Bot lacks 'Manage Channels' permission to delete {before.channel.name} or its interface.")
                except Exception as e:
                    print(f"An error occurred while deleting the channels {before.channel.name}: {e}")

async def setup(bot):
    await bot.add_cog(TempVoice(bot))