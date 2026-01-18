import discord
from discord.ext import commands

class Setuphelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        welcome_embed = discord.Embed(
            title="👋 Hallo!",
            description="Vielen Dank für's Hinzufügen von Birthdayyyyys zu deinem Server! Bevor du anfängst, Birthdayyyyys einzurichten, sind hier einige erste Schritte, die du befolgen kannst.",
            color=discord.Color.blue()
        )

        welcome_embed.add_field(name="Kanal einstellen:", value="Gib `/config <channel>` ein, wobei `<channel>` der Kanal sein soll, wo Geburtstagsgrüße in Zukunft gesendet werden.", inline=False)
        welcome_embed.add_field(name="Nachrichten bearbeiten:", value="Nutze `/config`, um ins Konfigurations-Menü zu gelangen. Wähle dort die blauen Buttons `Nachricht (Kein/Mit Alter)`, um die Geburtstagsgrüße zu bearbeiten. Wenn der User, der Geburtstag hat, ein Geburtsjahr angegeben hat, wird Birthdayyyyys automatisch das Alter berechnen. \n "
                                                                      "Außerdem kannst du die Variablen (wie `%username`) nutzen, um die Nachrichten weiter anzupassen.", inline=False)
        welcome_embed.add_field(name="Bildgenerierung aktivieren:", value="Ein cooles Feature ist auch die Bildgenerierung. Sie wird ein Banner mit dem jeweiligen Profilbild und -namen generieren und an einen Geburtstagsgruß anhängen. \n"
                                                                          "Aktiviere das Feature, indem du `/config` nutzt, und auf den Button `Bilder An/Aus` klickst. Den Titel des Banners kannst du sogar mit den Nachrichtenkonfigurationen anpassen.", inline=False)
        welcome_embed.add_field(name="Geburtstag simulieren:", value="Wenn du deine Konfiguration überprüfen willst, kannst du `/birthday-test` nutzen.", inline=False)
        welcome_embed.add_field(name="Weitere Hilfe:", value="Falls du weitere Hilfe brauchst, kannst du `/help` nutzen. Wenn du Probleme hast, trete doch gerne dem Support Server bei: [https://discord.gg/utD4afUrgt](https://discord.gg/utD4afUrgt).")
        welcome_embed.set_thumbnail(url=self.bot.user.avatar)
        welcome_embed.set_footer(text="Danke für's Nutzen von Birthdayyyyys!")

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
