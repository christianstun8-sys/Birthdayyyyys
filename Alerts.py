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
                    title="📢 Birthdayyyyys Update 3.0",
                    description="Hallo! 👋 \n"
                                "Es hat sich einiges, und ich meine EINIGES an **Birthdayyyyys geändert**. 😱 Hier die Änderungen für den offiziellen Release **3.0**.",
                    color=color_val
                )

                embed.add_field(name="**Custom Zeitzonen**", value="Jeder Benutzer kann nun seine eigene Zeitzone auswählen! Davor galt UTC als Zeitzone. Die Zeitzone kann mit `/birthday-set [timezone]` gesetzt werden. Standard: **Europe/Berlin**", inline=False)
                embed.add_field(name="**Neue Configs**", value="Die Configs wurden geupdatet! Es gibt nun nur noch einen Befehl: `/config [channel] [role]`. Dort ist ein Panel mit Buttons, wo ihr Birthdayyyyys viel besser konfigurieren könnt.", inline=False)
                embed.add_field(name="**Besseres /help**", value="Der `/help`Befehl wurde verschönert und es wurden Extra-Auswahlen für einzelne Befehle hinzugefügt.", inline=False)
                embed.add_field(name="**Alert-Config**", value="Ihr könnt nun diese Alerts ebenfalls konfigurieren! Nutzt dafür `/config` und ändert den **Alert Kanal**. Mehr Infos in `/help [command: config]`.", inline=False)
                embed.add_field(name="**Besseres /ping**", value="Der `/ping`-Befehl wurde detaillierter und besser designt.", inline=False)
                embed.add_field(name="**Geburtstagsrollen**", value="Es gibt nun Geburtstagsrollen, die am Geburtstag vergeben werden. Diese können über `/config` angepasst werden.", inline=False)
                embed.add_field(name="\u200b", value="\u200b", inline=False)
                embed.add_field(name="__Außerdem:__", value="\u200b", inline=False)
                embed.add_field(name="**Support-Server**", value="Birthdayyyyys hat nun seinen eigenen Discord Support Server: https://discord.gg/utD4afUrgt. Hier kommen noch mehr Updates.", inline=False)
                embed.add_field(name="**Discord Botlisten**", value="Birthdayyyyys ist nun auf **top.gg**, auf **discordbotlist.com** und auf **discordlist.gg** verfügbar! 🥳 In Zukunft wird er auch auf weiteren Listen verfügbar sein.", inline=False)

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