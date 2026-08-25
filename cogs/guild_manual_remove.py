import discord
from discord.ext import commands

def get_first_writable_channel(guild):
    for channel in guild.text_channels:
        perms = channel.permissions_for(guild.me)
        if perms.view_channel and perms.send_messages:
            return channel
    return None

class ManualGuildRemover(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(name='guild_remove')
    async def guild_remove(self, ctx: commands.Context, guild_id: int, *, reason: str = "Violation of Terms of Service"):
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return await ctx.reply("❌ Server konnte nicht gefunden werden (Bot ist dort evtl. nicht mehr drauf).")

        embed = discord.Embed(
            title="❗ Birthdayyyyys left the server",
            description=f"Birthdayyyyys won't be available on this server anymore.\n\n**Reason:** {reason}\n\nPlease understand that Birthdayyyyys stands for open, respectful interaction.",
            color=discord.Color.dark_red()
        )

        channel = get_first_writable_channel(guild)
        if channel is not None:
            try:
                await channel.send(embed=embed)
            except discord.Forbidden:
                channel = None

        if channel is None:
            try:
                owner = guild.owner or await guild.fetch_member(guild.owner_id)
                await owner.send(embed=embed)
            except (discord.Forbidden, discord.HTTPException):
                await ctx.reply("⚠️ Nachricht konnte weder im Server noch per DM an den Owner gesendet werden. Bot verlässt den Server trotzdem.")

        await guild.leave()
        await ctx.reply(f"✅ Erfogreich von **{guild.name}** ({guild_id}) entfernt.")

async def setup(bot):
    await bot.add_cog(ManualGuildRemover(bot))