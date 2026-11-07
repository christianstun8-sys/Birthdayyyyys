import discord
import asyncio
from discord.ext import commands
from utils.logger import log

class AlertCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='broadcast')
    async def send_global_announcement(self, ctx: commands.Context):
        await self.bot.wait_until_ready()

        success = 0
        fail = 0
        total_servers = len(self.bot.guilds)
        processed = 0

        def create_progress_bar(current: int, total: int, length: int = 20) -> str:
            filled = int(length * current / total) if total > 0 else 0
            bar = "█" * filled + "░" * (length - filled)
            return f"[{bar}]"

        status_embed = discord.Embed(
            title="📢 Broadcast in Progress",
            description=f"Sending announcement to {total_servers} servers...\n{create_progress_bar(0, total_servers)}\n\nProgress: 0/{total_servers} (0%)",
            color=discord.Color.yellow()
        )
        status_message = await ctx.send(embed=status_embed)

        for guild in self.bot.guilds:
            config = self.bot.guild_configs.get(guild.id, {})

            alert_id = config.get("alerts")
            target_channel = None

            if str(alert_id) == "0":
                processed += 1
                continue

            if alert_id is not None:
                target_channel = guild.get_channel(int(alert_id))

            if target_channel is None and alert_id is None:
                target_channel = guild.system_channel


            if target_channel:
                try:
                    color_val = config.get("config_embed_color", 0x45a6c9)
                    if isinstance(color_val, str):
                        color_val = int(color_val.replace("#", ""), 16)

                    embed = discord.Embed(
                        title="⚠️ Important Database Warning",
                        description=(
                            "Birthdayyyyys will be down for a short period of time, because of a database switch."
                        ),
                        color=color_val
                    )

                    embed.add_field(
                        name="💾 Database host gets discontinued",
                        value=(
                            "Birthdayyyyys currently uses the free service of Aiven for a secure and stable database hosting. "
                            "Where's the problem? Well, the free tier of Aiven will be discontinued on the 21st December 2026. From this date, all information of the bot's database gets deleted."
                          
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="🤔 What now?",
                        value=(
                            "I will transfer all data to a private database, which means, that Birthdayyyyys will not depend on any third-party service anymore. "
                            "The transfer will be on the 7th Nov (tomorrow) at 11am (UTC). At this time, the bot will be offline and will neither respond to any commands nor announce any birthdays. The end of the downtake is unknown so far."
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="❓ Will my data be safe?!",
                        value=(
                            "Yes, your data from the start of the downtake will be completely fine. Should you still encounter any data leaks, please contact me on the support server. "
                        ),
                        inline=False
                    )

                    embed.set_thumbnail(url=self.bot.user.avatar)
                    await target_channel.send(embed=embed)
                    success += 1

                    await asyncio.sleep(0.5)

                except discord.Forbidden:
                    fail += 1
                except Exception as e:
                    log(f"Error while broadcasting in {guild.name}: {e}", 'ERROR')
                    fail += 1
            else:
                fail += 1

            processed += 1

            if processed % 10 == 0 or processed == total_servers:
                percentage = int((processed / total_servers) * 100) if total_servers > 0 else 0
                updated_embed = discord.Embed(
                    title="📢 Broadcast in Progress",
                    description=f"Sending announcement to {total_servers} servers...\n{create_progress_bar(processed, total_servers)}\n\nProgress: {processed}/{total_servers} ({percentage}%)\n✅ Success: {success} | ❌ Failed: {fail}",
                    color=discord.Color.yellow()
                )
                await status_message.edit(embed=updated_embed)

        final_embed = discord.Embed(
            title="✅ Broadcast Complete",
            description=f"Successfully sent announcement to {total_servers} servers.\n{create_progress_bar(total_servers, total_servers)}\n\nProgress: {total_servers}/{total_servers} (100%)\n✅ Success: {success} | ❌ Failed: {fail}",
            color=discord.Color.green()
        )
        await status_message.edit(embed=final_embed)

        log(f"Broadcast done. Successful: {success}, Failed: {fail}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AlertCog(bot))
