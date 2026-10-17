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
                        title="🚀 Update: Version 6 is Here!",
                        description=(
                            "After several weeks of work, I’m finally able to announce the latest update: **Version 6**!\n"
                            "In this version, all sorts of things have been tweaked and improved."
                        ),
                        color=color_val
                    )

                    embed.add_field(
                        name="🖼️ Banner Configuration",
                        value=(
                            "• **Official Feature:** The image upload system has been improved and is no longer in beta!\n"
                            "• **New Customisation Menu:** A brand-new menu lets you customise the entire birthday banner. Edit the position of text and avatar, adjust text colours, enable/disable elements, resize them, and more!\n"
                            "• **Text Configuration:** Text settings are now handled directly via this menu (no longer edited via the embed message configuration)."
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="🗣️ New Languages",
                        value=(
                            "**7 new languages** have been added to the bot:\n"
                            "🇸🇦 Arabic  •  🇮🇩 Indonesian  •  🇯🇵 Japanese  •  🇰🇷 Korean\n"
                            "🇵🇹 Portuguese  •  🇹🇷 Turkish  •  🇨🇳 Chinese"
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="✍️ Other Configurations & Warnings ⚠️",
                        value=(
                            "• **Custom Texts:** You can now change both the image title and the second text for even more personal creative freedom!\n"
                            "• **User Thumbnail:** In the default message configuration, you can now toggle whether the user's thumbnail should be displayed. This might be expanded in the future... 🤫\n"
                            "• **Configuration Warnings:** Wondering why something isn't working? The config menu now displays helpful warnings for potential errors (e.g., missing permissions)."
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="📄 Documentation & GitHub 🐙",
                        value=(
                            "• **Full Docs:** Comprehensive documentation is now available at [birthdayyyyys.christianst.xyz/docs](https://birthdayyyyys.christianst.xyz/docs), detailing every feature.\n"
                            "• **Free Hosting:** The bot can now be hosted completely free of charge; the repository has been updated for better feature configuration.\n\n"
                            "A huge thank you for helping the bot reach over **120 servers** so far! 🎉"
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