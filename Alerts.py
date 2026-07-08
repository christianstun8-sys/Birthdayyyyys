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
                    title="📢 New Update: Languages, Birthday Management & Fixes!",
                    description=(
                        "A number of changes have been made to Birthdayyyyys. "
                        "There are now new languages and more!\n\n"
                        "If you like Birthdayyyyys, I’d really appreciate it if you could leave a rating on "
                        "**__[Top.GG](https://top.gg/bot/1389267222261792868)__**. Since it currently has an "
                        "unfair rating of **1 ⭐**, it would be great if we could set that straight. "
                        "Thanks for using Birthdayyyyys! ❤️"
                    ),
                    color=color_val
                )

                embed.add_field(
                    name="🌍 New Languages",
                    value="As promised, I’ve now added Spanish, French, Polish, Russian, and Ukrainian to Birthdayyyyys. This should help expand our reach, which I’d be very happy about.",
                    inline=False
                )

                embed.add_field(
                    name="🛡️ Support Server",
                    value="The server is gradually being switched over to English. However, German support will still be available.",
                    inline=False
                )

                embed.add_field(
                    name="🎂 Birthday Management",
                    value="You can now manage other users’ birthdays on your server! To do this, use `/birthday-set` or `/birthday-remove` as usual, but there’s now a new optional parameter: `user`. If you have administrator permissions, you can now use this.",
                    inline=False
                )

                embed.add_field(
                    name="🗣️ Command Translation",
                    value="The descriptions of slash commands will now be adapted to the language of your Discord client, rather than defaulting to German.",
                    inline=False
                )

                embed.add_field(
                    name="🖼️ Fixed Birthday Banner",
                    value="The banner was causing some issues, such as misalignment and scaling. These have been fixed. Additionally, transparent avatars are finally displayed as transparent.",
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