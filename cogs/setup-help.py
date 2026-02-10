import discord
from discord.ext import commands
from utils.babel import translator

class Setuphelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        lang = "de"
        if guild.preferred_locale == "en-US" or guild.preferred_locale == "en-GB":
            lang = "en"

        _ = translator.get_translation(lang)

        welcome_embed = discord.Embed(
            title=_("👋 Hallo!"),
            description=_("Vielen Dank für's Hinzufügen von Birthdayyyyys zu deinem Server! Bevor du anfängst, Birthdayyyyys einzurichten, sind hier einige erste Schritte, die du befolgen kannst."),
            color=discord.Color.blue()
        )

        welcome_embed.add_field(
            name=_("Kanal einstellen:"),
            value=_("Nutze `/config` und klicke auf den Button `Kanal`, um den Geburtstagskanal zu setzen."),
            inline=False
        )
        welcome_embed.add_field(
            name=_("Nachrichten bearbeiten:"),
            value=_("Nutze `/config` und klicke auf den Button `Nachricht (Mit/Ohne Alter)`, um die Geburtstagsgrüße zu bearbeiten. Wenn der User ein Geburtsjahr angegeben hat, berechnet der Bot automatisch das Alter. Nutze Variablen wie `%username`, um Nachrichten anzupassen."),
            inline=False
        )
        welcome_embed.add_field(
            name=_("Bildgenerierung aktivieren:"),
            value=_("Ein cooles Feature ist die Bildgenerierung. Sie erstellt ein Banner mit Profilbild und Namen. Aktiviere dies mit `/config` -> `Bilder An/Aus`."),
            inline=False
        )
        welcome_embed.add_field(
            name=_("Konfiguration testen:"),
            value=_("Wenn du deine Konfiguration überprüfen willst, kannst du `/config-test` nutzen."),
            inline=False
        )
        welcome_embed.add_field(
            name=_("Weitere Hilfe:"),
            value=_("Falls du weitere Hilfe brauchst, nutze `/help`. Bei Problemen tritt gerne dem Support Server bei: https://discord.gg/utD4afUrgt.")
        )

        welcome_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        welcome_embed.set_footer(text=_("Danke für's Nutzen von Birthdayyyyys!"))

        sent = False

        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            try:
                await guild.system_channel.send(embed=welcome_embed)
                sent = True
            except discord.Forbidden:
                pass

        if not sent:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=welcome_embed)
                        sent = True
                        break
                    except discord.Forbidden:
                        continue

        if not sent:
            try:
                if guild.owner:
                    await guild.owner.send(embed=welcome_embed)
            except discord.Forbidden:
                print(f"Konnte keine Nachricht an Server {guild.name} oder dessen Owner senden.")

async def setup(bot):
    await bot.add_cog(Setuphelp(bot))