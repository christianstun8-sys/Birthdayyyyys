import discord
from discord.ext import commands

class DBAlert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dbalert_send")
    async def dbalert_send(self, ctx):
        if ctx.message.author.id != 1235134572157603841:
            pass

        alertembed = discord.Embed(
            title="Datenbank-Reset",
            description="Hallo liebe Nutzer dieses kleinen Geburtstagsbots! 👋 \n "
                        "Der Bot wird **ab jetzt stabil** laufen! 🥳 Ich hoste ihn nun bei mir Zuhause, wo es erstmal keine Hostingprobleme geben sollte. \n"
                        "\n"
                        "Durch diesen Wechsel auf den neuen Server wurden jedoch alle Datenbanken zurückgesetzt. Ihr müsstet den Bot bitte nochmal neu konfiguieren. Das beinhaltet: \n"
                        "- benutzerdefinierte Nachrichten bzw Bilder \n"
                        "- Geburtstage \n"
                        "- Geburtstagsrollen \n"
                        "...und so ziemlich alles Andere. \n \n"
                        "Es tut mir sehr Leid für die Umstände. So etwas wird in Zukunft **nicht mehr vorkommen**. \n Vielen Dank für das Nutzen von Birthdayyyyys. :) \n LG, _chrxstianst.",
            color=discord.Color.blue()
        )

        for guild in self.bot.guilds:
            try:
                await guild.system_channel.send(embed=alertembed)
            except Exception as e:
                print(e)

async def setup(bot):
    await bot.add_cog(DBAlert(bot))