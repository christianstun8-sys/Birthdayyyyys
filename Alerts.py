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
                    title="⚠️ Config-Problems",
                    description="Hi! 👋 \n"
                                "**__English:__**\n"
                                "Birthdayyyyys had some heavy issues with the configurations. Users couldn't save their settings, even if the bot said so."
                                "This problem is now fixed. You can now save your configurations again as you'd like.\n"
                                "Also, the language-switcher wasn't working. The language just stayed german. \n"
                                "Now, you can set your language again!\nSorry for the inconvenience.\n\nBy the way: if you enjoy using Birthdayyyyys, consider rating us on top.gg and other Discord Bot lists! That would really help Birthdayyyyys growing!"
                                "\nThanks for using Birthdayyyyys!\n\n"
                                "**__Deutsch:__**\n"
                                "Birthdayyyyys hatte einige schwerwiegende Probleme mit den Konfigurationen. Benutzer konnten ihre Einstellungen nicht speichern, selbst, als der Bot es bestätigt hatte."
                                "Dieser Bug wurde gefixt! Ihr könnt nun wieder eure Konfigurationen setzen, wie ihr wollt.\n"
                                "Außerdem hat die Spracheinstellung nicht funktioniert. Die Bot-Sprache blieb weiterhin auf deutsch."
                                "\nNun könnt ihr wieder die Sprache einstellen.\nEntschuldigung für die Unannehmlichkeiten.\n\nÜbrigens: wenn ihr Freude an Birthdayyyyys habt, erwägt eine Bewertung auf top.gg und anderen Discord Bot Listen. Das würde Birthdayyyyys wirklich beim Wachsen helfen!"
                                "\nDanke für's Nutzen von Birthdayyyyys!",
                    color=color_val
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