import discord
import asyncio
from discord.ext import commands
class AlertCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='broadcast')
    async def send_global_announcement(self):
        await self.bot.wait_until_ready()

        success = 0
        fail = 0

        for guild in self.bot.guilds:
            config = self.bot.guild_configs.get(guild.id, {})

            alert_id = config.get("alerts")
            target_channel = None

            if str(alert_id) == "0":
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
                        title="🎨 New Feature: Multiple Random Background Images!",
                        description=(
                            "I've updated the birthday card system to give your server's birthday "
                            "wishes a fresh and dynamic look!\n\n"
                            "Thank you for using Birthdayyyyys! ❤️"
                        ),
                        color=color_val
                    )

                    embed.add_field(
                        name="🖼️ Custom Image Gallery & Randomization",
                        value=(
                            "• **Upload Multiple Images:** Server admins can now upload and manage multiple background images in `/config`.\n"
                            "• **Random Backgrounds:** Every time a birthday card is generated, the bot randomly selects one of your uploaded images!\n"
                            "• If no custom images are uploaded, the bot seamlessly uses the sleek default background."
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="⚙️ Updated Config & Testing",
                        value=(
                            "• **Interactive Gallery View:** Easily browse and delete your uploaded images directly inside the `/config` UI.\n"
                            "• **Instant Test Command:** Use `/config-test` to preview how your birthday cards look with random backgrounds before the real celebration."
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
                    print(f"Fehler in {guild.name}: {e}")
                    fail += 1
            else:
                fail += 1

        print(f"Broadcast FERTIG. Erfolgreich: {success}, Fehlgeschlagen: {fail}")