import discord
from discord.ext import commands

# --- Config ---
news_role_id = 1453818662916984852
discord_role_id = 1453818699759747325
status_role_id = 1453818753350500383

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rulemsg')
    async def rulemsg(self, ctx):

        if ctx.author.id != 1235134572157603841:
            return

        if ctx.guild.id != 1453670454350057613:
            return

        rulesembed = discord.Embed(
            title="📚 Regelwerk",
            description="*Herzlich willkommen! Da wir uns alle hier wohl fühlen wollen, gelten hier einige Regeln*",
            color=discord.Color.blue()
        )

        rulesembed.add_field(
            name="1️⃣ Freundlicher Umgang",
            value="Behandle alle Mitglieder respektvoll und höflich. Beleidigungen, Provokationen oder toxisches Verhalten sind nicht erlaubt.",
            inline=False
        )

        rulesembed.add_field(
            name="2️⃣ Kein Spam",
            value="Spam, Flooding, unnötige Pings oder das wiederholte Posten gleicher Inhalte ist untersagt.",
            inline=False
        )

        rulesembed.add_field(
            name="3️⃣ Support nur zum Bot",
            value="Dieser Server dient ausschließlich dem Support rund um den Geburtstagsbot **Birthdayyyyys**. Off-Topic bitte vermeiden.",
            inline=False
        )

        rulesembed.add_field(
            name="4️⃣ Keine Werbung",
            value="Werbung für andere Bots, Server, Produkte oder Dienstleistungen ist ohne Genehmigung des Teams verboten.",
            inline=False
        )

        rulesembed.add_field(
            name="5️⃣ Kein NSFW-Inhalt",
            value="NSFW-, gewaltverherrlichende oder anderweitig unangemessene Inhalte sind strengstens untersagt.",
            inline=False
        )

        rulesembed.add_field(
            name="6️⃣ Discord ToS beachten",
            value="Die Discord Nutzungsbedingungen und Community-Richtlinien sind jederzeit einzuhalten.",
            inline=False
        )

        rulesembed.add_field(
            name="7️⃣ Anweisungen des Teams",
            value="Den Anweisungen des Serverteams ist Folge zu leisten. Das Team hat das letzte Wort.",
            inline=False
        )

        rulesembed.add_field(
            name="✅ Konsequenzen",
            value="Bei Regelverstößen können Verwarnungen, Timeouts oder Ausschlüsse vom Server folgen.",
            inline=False
        )

        await ctx.send(embed=rulesembed)

class RRButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="📣 Neuigkeiten", style=discord.ButtonStyle.grey, custom_id="newsrolebutton")
    async def newsrolebuttoncallback(self, interaction: discord.Interaction, button: discord.ui.Button):

        news_role = interaction.guild.get_role(news_role_id)
        if news_role:
            if news_role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(news_role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {news_role.mention} entfernt.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Neuigkeitenpings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(news_role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {news_role.mention} zugewiesen.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Neuigkeitenpings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.", ephemeral=True)

    @discord.ui.button(label="Discord Ping", emoji="<:discord:1454064310631399525>", custom_id="discordpingrolebutton", style=discord.ButtonStyle.grey)
    async def discordpingbuttoncallback(self,  interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(discord_role_id)
        if role:
            if role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {role.mention} entfernt.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Discord-Neuigkeiten-Pings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {role.mention} zugewiesen.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Discord-Neuigkeiten-Pings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.", ephemeral=True)


    @discord.ui.button(style=discord.ButtonStyle.grey, label="Status Ping", emoji="<:status:1454066673404612843>", custom_id="statuspingbutton")
    async def statuspingbuttoncallback(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(status_role_id)
        if role:
            if role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {role.mention} entfernt.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Statuspings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {role.mention} zugewiesen.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Statuspings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.", ephemeral=True)

class Reactionroles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='rr-panel')
    async def rr_panel(self, ctx):
        if ctx.author.id != 1235134572157603841:
            return

        if ctx.guild.id != 1453670454350057613:
            return

        rrpanelembed = discord.Embed(
            title="®️ Pingauswahl",
            description="Wähle hier aus, wann du gepingt werden möchtest.",
            color=discord.Color.blue()
        )

        await ctx.channel.send(embed=rrpanelembed, view=RRButtonsView())

async def setup(bot):
    await bot.add_cog(Rules(bot))
    await bot.add_cog(Reactionroles(bot))

    bot.add_view(RRButtonsView())
