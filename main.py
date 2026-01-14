import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiosqlite

import Alerts

load_dotenv()

# --- BETA VERWALTUNG (Nur für Beta-Versionen!) ---
beta = False

if beta:
    TOKEN = os.getenv('DISCORD_BETA_TOKEN')
else:
    TOKEN = os.getenv('DISCORD_TOKEN')

def setup_directories():
    for dir_name in ['databases', 'cogs', 'data']:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Verzeichnis '{dir_name}' erstellt.")

    data_path = 'data'
    if not os.path.exists(os.path.join(data_path, 'birthday_background.jpg')):
        print(f"ACHTUNG: 'birthday_background.jpg' fehlt im Verzeichnis '{data_path}'. Bitte einfügen.")
    if not os.path.exists(os.path.join(data_path, 'arial.ttf')):
        print(f"ACHTUNG: 'arial.ttf' fehlt im Verzeichnis '{data_path}'. Bitte einfügen.")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class BirthdayBot(commands.Bot):
    def __init__(self):

        prefix = []
        if beta:
            prefix.append("beta!")
        else:
            prefix.append("!")

        super().__init__(command_prefix=prefix, intents=intents, help_command=None)
        self.guild_configs = {}

    async def setup_hook(self):
        print("Starte Cogs-Ladevorgang...")
        done = True
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                except Exception as e:
                    print(f"❌ Fehler beim Laden von Cog '{filename[:-3]}': {e}")
                    done = False

        if done:
            print("✅ Alle Cogs geladen!")

        try:
            await self.load_extension('jishaku')
            jsk = self.get_command('jsk')
            if jsk:
                jsk.hidden = True
            print("✅ Jishaku erfolgreich geladen!")
        except Exception as e:
            print(f"Fehler beim Laden von Jishaku: {e}")

        if beta:
            try:
                synced = await self.tree.sync()
                print(f"Synchronisierte {len(synced)} Befehle.")
            except Exception as e:
                print(f"Fehler beim Synchronisieren der Befehle: {e}")

        try:
            support_server_id = discord.Object(id=1453670454350057613)
            guild_synced = await self.tree.sync(guild=support_server_id)
            print(f"Erfolgreich {len(guild_synced)} Befehle für den Support-Server gesynct.")
        except Exception as e:
            print(f"Fehler beim Synchronisieren der Support-Server-Befehle: {e}")

        @self.command(name="restart", hidden=True)
        async def restart_cmd(ctx):
            if ctx.author.id == 1235134572157603841:
                await ctx.send("⌛ Starte neu...")
                await self.close()
            else:
                return

        self.db = await aiosqlite.connect("databases/tickets.db")

    async def on_ready(self):
        print(f'Bot eingeloggt als {self.user}')
        print('------------------------------')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Happy Birthdayyyyy! 🎂"))
        from cogs.birthday_check_task import load_all_guild_configs
        await load_all_guild_configs(self)

        print("------------------------------")
        print("Bot bereit!")


    async def on_guild_join(self, guild):
        christianst_id = 1235134572157603841
        christianst = self.get_user(christianst_id)

        embed = discord.Embed(
            title="Birthdayyyyys ist auf einem neuen Server!",
            description="Hii Chris, ich bin auf einem neuen Server hinzugefügt worden! :) \n \n"
                        f"🪧 Servername: '{guild.name}' ({guild.id})\n"
                        f"🧑‍🦱 Mitgliederanzahl: '{guild.member_count}'\n"
                        f"👑 Serverinhaber: {guild.owner.name}\n (https://discord.gg/users/{guild.owner.id}/) \n"
                        f"💜 Boostlevel: {guild.premium_tier} ({guild.premium_subscription_count} Boosts)",
            color=discord.Color.blue()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        else:
            embed.set_thumbnail(url=self.user.display_avatar.url)
        try:
            await christianst.send(embed=embed)
        except discord.Forbidden:
            print("❌ Fehler: Keine Berechtigung, Christianst_ eine Nachricht zu senden.")

        print(f"Bot wurde einer neuen Guild hinzugefügt: {guild.name} (ID: {guild.id})")
        from cogs.birthday_check_task import load_bot_config
        await load_bot_config(self, guild.id)

    async def on_guild_remove(self, guild):
        print(f"Bot wurde aus Guild {guild.name} (ID: {guild.id}) entfernt. Schade... :(")
        if guild.id in self.guild_configs:
            del self.guild_configs[guild.id]

        db_path = "databases" / f"guild_{guild.id}.db"
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == '__main__':
    setup_directories()
    if TOKEN:
        bot = BirthdayBot()
        bot.run(TOKEN)
    else:
        print("Fehler: Discord Bot Token nicht gefunden. Bitte setze die DISCORD_TOKEN Umgebungsvariable.")