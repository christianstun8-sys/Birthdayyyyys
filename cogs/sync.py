import discord
from discord.ext import commands

class SyncCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync")
    async def sync(self, ctx):
        if ctx.author.id != 1235134572157603841:
            return

        loadingembed = discord.Embed(
                title="<a:loading:1458892675456434187> Synchronizing slash commands, please wait...",
                color=discord.Color.light_grey()
            )

        msg = await ctx.send(embed=loadingembed)
        no_sc = False
        error = None
        synced = False
        embed = None
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
                title=f"<a:tickgreen:1458893404736848046> I've successfully synchronized {len(synced)} slash commands",
                color=discord.Color.green()
            )

        if success and no_sc:
            embed = discord.Embed(
                title="<a:error:1458895434612215939> Error!",
                description="There are no slash commands to synchronize, silly.",
                color=discord.Color.red()
            )

        if not success:
            embed = discord.Embed(
                title="<a:error:1458895434612215939> Error!",
                description="While synchronizing the slash commands, I encountered an error. \n\n"
                            f"`{error}`",
                color=discord.Color.red()
            )

        await msg.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(SyncCommand(bot))
