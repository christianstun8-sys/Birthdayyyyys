import discord
import asyncio

async def send_global_announcement(bot):
    await bot.wait_until_ready()

    success = 0
    fail = 0

    for guild in bot.guilds:
        config = bot.guild_configs.get(guild.id, {})

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
                    title="📢 New Update: Database Upgrade, Features & Fixes!",
                    description=(
                        "The new update includes new features, bug fixes, performance improvements, "
                        "and a more secure database system.\n\n"
                        "I hope you like the new update. Thank you for using Birthdayyyyys! ❤️"
                    ),
                    color=color_val
                )

                embed.add_field(
                    name="⏰ Scheduled Messages & UI Updates",
                    value=(
                        "• **Custom Message Time:** You can now schedule birthday messages for a specific time instead of 00:00 using `/config`.\n"
                        "• **Calendar View:** `/birthday-list` now displays an organized calendar by months again.\n"
                        "• **Improved Config:** `/config` is now more user-friendly, showing current settings and using drop-down menus."
                    ),
                    inline=False
                )

                embed.add_field(
                    name="🗄️ Database Migration (Important!)",
                    value=(
                        "The bot is finally using a proper online database! All settings and birthdays should be carried over.\n\n"
                        "⚠️ **Missing data?** If any settings or birthdays are missing, please open a ticket on the support server "
                        "stating your Server ID or User ID by **20 August 2026** (<t:1787220000:R>). "
                        "After this date, old files will be deleted."
                    ),
                    inline=False
                )

                embed.set_thumbnail(url=bot.user.avatar)
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