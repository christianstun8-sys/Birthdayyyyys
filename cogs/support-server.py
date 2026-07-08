import discord
from discord.ext import commands

discord_role_id = 1453818699759747325
status_role_id = 1453818753350500383
news_role_id = 1453818662916984852

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
            title="📚 Regelwerk / Rules",
            description="Herzlich willkommen! Da wir uns alle hier wohl fühlen wollen, gelten hier einige Regeln.\n*Welcome! Since we all want to feel comfortable here, a few rules apply.*",
            color=discord.Color.blue()
        )

        rulesembed.add_field(
            name="1️⃣ Freundlicher Umgang / Respectful Behavior",
            value="Behandle alle Mitglieder respektvoll und höflich. Beleidigungen, Provokationen oder toxisches Verhalten sind nicht erlaubt.\n*Treat all members respectfully and politely. Insults, provocations, or toxic behavior are not allowed.*",
            inline=False
        )

        rulesembed.add_field(
            name="2️⃣ Kein Spam / No Spam",
            value="Spam, Flooding, unnötige Pings oder das wiederholte Posten gleicher Inhalte ist untersagt.\n*Spam, flooding, unnecessary pings, or repeatedly posting the same content is prohibited.*",
            inline=False
        )

        rulesembed.add_field(
            name="3️⃣ Support nur zum Bot / Bot Support Only",
            value="Dieser Server dient ausschließlich dem Support rund um den Geburtstagsbot **Birthdayyyyys**. Off-Topic bitte vermeiden.\n*This server is exclusively for support regarding the birthday bot **Birthdayyyyys**. Please avoid off-topic discussions.*",
            inline=False
        )

        rulesembed.add_field(
            name="4️⃣ Keine Werbung / No Advertising",
            value="Werbung für andere Bots, Server, Produkte oder Dienstleistungen ist ohne Genehmigung des Teams verboten.\n*Advertising for other bots, servers, products, or services is prohibited without team permission.*",
            inline=False
        )

        rulesembed.add_field(
            name="5️⃣ Kein NSFW-Inhalt / No NSFW Content",
            value="NSFW-, gewaltverherrlichende oder anderweitig unangemessene Inhalte sind strengstens untersagt.\n*NSFW, violent, or otherwise inappropriate content is strictly prohibited.*",
            inline=False
        )

        rulesembed.add_field(
            name="6️⃣ Discord ToS beachten / Follow Discord ToS",
            value="Die Discord Nutzungsbedingungen und Community-Richtlinien sind jederzeit einzuhalten.\n*The Discord Terms of Service and Community Guidelines must be followed at all times.*",
            inline=False
        )

        rulesembed.add_field(
            name="7️⃣ Anweisungen des Teams / Team Instructions",
            value="Den Anweisungen des Serverteams ist Folge zu leisten. Das Team hat das letzte Wort.\n*Instructions from the server team must be followed. The team has the final say.*",
            inline=False
        )

        rulesembed.add_field(
            name="✅ Konsequenzen / Consequences",
            value="Bei Regelverstößen können Verwarnungen, Timeouts oder Ausschlüsse vom Server folgen.\n*Rule violations may result in warnings, timeouts, or bans from the server.*",
            inline=False
        )

        await ctx.send(embed=rulesembed)

class RRButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📣 Neuigkeiten / News", style=discord.ButtonStyle.grey, custom_id="newsrolebutton")
    async def newsrolebuttoncallback(self, interaction: discord.Interaction, button: discord.ui.Button):

        news_role = interaction.guild.get_role(news_role_id)
        if news_role:
            if news_role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(news_role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {news_role.mention} entfernt.\n*✅ The role {news_role.mention} has been removed from you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Neuigkeitenpings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(news_role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {news_role.mention} zugewiesen.\n*✅ The role {news_role.mention} has been successfully assigned to you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Neuigkeitenpings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.\n*❌ Error: Role not found.*", ephemeral=True)

    @discord.ui.button(label="Discord Ping", emoji="<:discord:1454064310631399525>", custom_id="discordpingrolebutton", style=discord.ButtonStyle.grey)
    async def discordpingbuttoncallback(self,  interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(discord_role_id)
        if role:
            if role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {role.mention} entfernt.\n*✅ The role {role.mention} has been removed from you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Discord-Neuigkeiten-Pings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {role.mention} zugewiesen.\n*✅ The role {role.mention} has been successfully assigned to you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Discord-Neuigkeiten-Pings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.\n*❌ Error: Role not found.*", ephemeral=True)


    @discord.ui.button(style=discord.ButtonStyle.grey, label="Status Ping", emoji="<:status:1454066673404612843>", custom_id="statuspingbutton")
    async def statuspingbuttoncallback(self, interaction: discord.Interaction, button: discord.ui.Button):

        role = interaction.guild.get_role(status_role_id)
        if role:
            if role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde die Rolle {role.mention} entfernt.\n*✅ The role {role.mention} has been removed from you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen/Entfernen des Statuspings an {interaction.user.name}: {e}")

            else:
                try:
                    await interaction.user.add_roles(role)
                    await interaction.response.send_message(f"✅ Dir wurde erfolgreich die Rolle {role.mention} zugewiesen.\n*✅ The role {role.mention} has been successfully assigned to you.*", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("❌ Fehler: Ich habe keine Berechtigung, deine Rollen zu verwalten.\n*❌ Error: I do not have permission to manage your roles.*", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Fehler: {e}\n*❌ Error: {e}*", ephemeral=True)
                    print(f"❌ Fehler beim Zuweisen des Statuspings an {interaction.user.name}: {e}")

        else:
            await interaction.response.send_message("❌ Fehler: Rolle nicht gefunden.\n*❌ Error: Role not found.*", ephemeral=True)

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
            title="®️ Pingauswahl / Ping Selection",
            description="Wähle hier aus, wann du gepingt werden möchtest.\n*Select here when you want to be pinged.*",
            color=discord.Color.blue()
        )

        await ctx.channel.send(embed=rrpanelembed, view=RRButtonsView())

async def setup(bot):
    await bot.add_cog(Rules(bot))
    await bot.add_cog(Reactionroles(bot))

    bot.add_view(RRButtonsView())