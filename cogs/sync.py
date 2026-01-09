import discord
from discord.ext import commands
import asyncio

class SyncCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    async def sync(self, ctx):
        if ctx.author.id != 1235134572157603841:
            return

        loadingembed = discord.Embed(
                title="<a:loading:1458892675456434187> Synchronisiere Slash-Befehle, einen Moment...",
                color=discord.Color.light_grey()
            )

        msg = await ctx.send(embed=loadingembed)
        success = None
        no_sc = False
        try:
            synced = await self.bot.tree.sync()
            success = True
        except Exception as e:
            success = False
            error = e

        if len(synced) == 0 and success == True:
            no_sc = True

        if success and not no_sc:
            embed = discord.Embed(
                title=f"<a:tickgreen:1458893404736848046> Ich habe erfolgreich {len(synced)} Slash-Befehle gesynct",
                color=discord.Color.green()
            )

        if success and no_sc:
            embed = discord.Embed(
                title="<a:error:1458895434612215939> Fehler!",
                description="Es wurden keine Slash-Befehle zum Syncen gefunden.",
                color=discord.Color.red()
            )

        if not success:
            embed = discord.Embed(
                title="<a:error:1458895434612215939> Fehler!",
                description="Während dem Syncen ist ein Fehler aufgetreten. \n\n"
                            f"`{error}`",
                color=discord.Color.red()
            )

        await msg.edit(embed=embed)
        await asyncio.sleep(15)
        await msg.delete()

async def setup(bot):
    await bot.add_cog(SyncCommand(bot))
