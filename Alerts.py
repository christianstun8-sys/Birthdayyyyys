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
                    title="📢 Birthdayyyyys Update 4.0",
                    description="Hallo! 👋 \n"
                                "Birthdayyyyys entwickelt sich immer weiter fort! Hier die neuesten News:",
                    color=color_val
                )

                embed.add_field(name="**Mehrsprachig**", value="Die Antworten sind nun auf deutsch und auf englisch verfügbar! Somit ist Birthdayyyyys offiziell **international**! Die Hauptsprache wird nun auf englisch sein (welche am Anfang genutzt wird und in der auch diese News kommen). Die Sprache kann jederzeit in der Konfiguration angepasst werden.", inline=False)
                embed.add_field(name="**Bessere Konfigurationen**", value="Birthdayyyyys nutzt nun Features vom Discord Components v2 Update: Ihr könnt nun sowohl den Kanal für die Geburtstagsnachrichten und die News, als auch die Geburtstagsrolle einfach über ein Formular auswählen. Darin ist nun eine interaktive Auswahl, welche das mühsame Eingeben der ID ersetzt.", inline=False)

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