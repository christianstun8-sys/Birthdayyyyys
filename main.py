import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import aiohttp
import logging
from utils.discord_translator import DiscordSlashTranslator
from cogs.birthday_check_task import remove_database_record
import aiomysql
import topgg

load_dotenv()

# --- BETA VERWALTUNG (Nur für Beta-Versionen!) ---
beta = True
debug  = False

if beta:
    TOKEN = os.getenv('DISCORD_BETA_TOKEN')
else:
    TOKEN = os.getenv('DISCORD_TOKEN')

logger = logging.getLogger('discord.gateway')
if debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

def setup_directories():
    for dir_name in ['cogs', 'data', 'data/custom_images']:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Verzeichnis '{dir_name}' erstellt.")

    data_path = 'data'
    if not os.path.exists(os.path.join(data_path, 'birthday_background.jpg')):
        print(f"ACHTUNG: 'birthday_background.jpg' fehlt im Verzeichnis '{data_path}'. Bitte einfügen.")
    if not os.path.exists(os.path.join(data_path, 'arial.ttf')):
        print(f"ACHTUNG: 'arial.ttf' fehlt im Verzeichnis '{data_path}'. Bitte einfügen.")

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

class BirthdayBot(commands.Bot):
    def __init__(self):
        prefix = "bbeta." if beta else "b."
        super().__init__(command_prefix=prefix, intents=intents, help_command=None)
        self.guild_configs = {}
        self.kuma_url = "https://status.christianst.xyz/api/push/bELLyg8wcQ?status=up&msg=OK&ping="
        self.version = 5.6
        self.db_pool = None
        self.topgg = None

    async def setup_hook(self):
        await self.tree.set_translator(DiscordSlashTranslator())
        try:
            self.db_pool: aiomysql.Pool = await aiomysql.create_pool(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER_NAME"),
                db=os.getenv("DB_NAME"),
                port=int(os.getenv("DB_PORT")),
                password=os.getenv("DB_PASSWORD"),
                autocommit=True
            )
            print("✅💾 Datenbank verbunden!")
        except Exception as e:
            print(e)

        print("Starte Cogs-Ladevorgang...")
        done = True
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    if debug:
                        print(f"[DEBUG] '{filename[:-3]}' Cog geladen.")
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

        if debug:
            try:
                synced = await self.tree.sync()
                print(f"Synchronisierte {len(synced)} Befehle.")
            except Exception as e:
                print(f"Fehler beim Synchronisieren der Befehle: {e}")
        if not beta:
            try:
                support_server_id = discord.Object(id=1453670454350057613)
                guild_synced = await self.tree.sync(guild=support_server_id)
                print(f"Erfolgreich {len(guild_synced)} Befehle für den Support-Server gesynct.")
            except Exception as e:
                print(f"Fehler beim Synchronisieren der Support-Server-Befehle: {e}")

        self.uptime_ping.start()


    async def on_ready(self):
        print(f'Bot eingeloggt als {self.user}')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Happy Birthdayyyyy! 🎂"))
        from cogs.birthday_check_task import load_all_guild_configs
        await load_all_guild_configs(self)

        if not beta:
            self.topgg = topgg.DBLClient(self, os.getenv("TOPGG_TOKEN"))
            self.update_stats.start()

        print("------------------------------")
        print("Bot bereit!")


    async def on_guild_join(self, guild: discord.Guild):
        christianst_id = 1235134572157603841
        christianst = self.get_user(christianst_id)

        embed = discord.Embed(
            title="Birthdayyyyys ist auf einem neuen Server!",
            description="Hii Chris, ich bin auf einem neuen Server hinzugefügt worden! :) \n \n"
                        f"🪧 Servername: '{guild.name}' ({guild.id})\n"
                        f"🧑‍🦱 Mitgliederanzahl: {guild.member_count}\n"
                        f"👑 Serverinhaber: {guild.owner.name}\n (https://discord.gg/users/{guild.owner.id}/) \n"
                        f"💜 Boostlevel: {guild.premium_tier} ({guild.premium_subscription_count} Boosts)",
            color=discord.Color.blue()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        else:
            embed.set_thumbnail(url=self.user.display_avatar.url)
        try:
            await christianst.send(embed=embed, content=f"{christianst.mention} Neuer Server!")
        except discord.Forbidden:
            print("❌ Fehler: Keine Berechtigung, Christianst_ eine Nachricht zu senden.")

        print(f"Bot wurde einer neuen Guild hinzugefügt: {guild.name} (ID: {guild.id})")
        from cogs.birthday_check_task import load_bot_config
        await load_bot_config(self, guild.id)


    async def on_guild_remove(self, guild):
        print(f"Bot wurde aus Guild {guild.name} (ID: {guild.id}) entfernt. Schade... :(")

        if guild.id in self.guild_configs:
            del self.guild_configs[guild.id]


        embed = discord.Embed(
            title="Birthdayyyyys wurde aus einem Server entfernt.",
            description="Hi Chris! Ich wurde aus einem Server rausgeworfen. :c \n"
                        f"🪧 Servername: '{guild.name}' ({guild.id})\n"
                        f"🧑‍🦱 Mitgliederanzahl: {guild.member_count}\n"
                        f"👑 Serverinhaber: {guild.owner.name}\n (https://discord.gg/users/{guild.owner.id}/) \n"
                        f"💜 Boostlevel: {guild.premium_tier} ({guild.premium_subscription_count} Boosts)",
            color=discord.Color.red()
        )
        christianst_id = 1235134572157603841
        christianst = self.get_user(christianst_id)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        else:
            embed.set_thumbnail(url=self.user.display_avatar.url)


        try:
            await christianst.send(embed=embed, content=f"{christianst.mention} Server entfernt.")
        except discord.Forbidden:
            print(f"Konnte keine Nachricht an {christianst.global_name} senden.")

        await remove_database_record(self, guild.id)

    @tasks.loop(seconds=30)
    async def uptime_ping(self):
        if self.is_ready():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.kuma_url) as response:
                        if response.status == 200:
                            if debug:
                                print("[DEBUG] Uptime Kuma erfolgreich gepingt.")
                        else:
                            print(f"Kuma-Ping fehlgeschlagen: Status {response.status}")
            except Exception as e:
                print(f"Fehler beim Uptime-Ping: {e}")

    @uptime_ping.before_loop
    async def before_uptime_ping(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        if not hasattr(self, 'topgg') or self.topgg is None:
            return

        try:
            await self.topgg.post_guild_count()
        except Exception as e:
            print(f"❌ Fehler beim Senden der Serveranzahl an Top.gg: {e}")

    @update_stats.before_loop
    async def before_update_stats(self):
        await self.wait_until_ready()

    async def close(self):
        if self.db_pool:
            self.db_pool.close()
            await self.db_pool.wait_closed()

if __name__ == '__main__':
    setup_directories()
    if TOKEN:
        bot = BirthdayBot()
        bot.run(TOKEN)
    else:
        print("Fehler: Discord Bot Token nicht gefunden. Bitte setze die DISCORD_TOKEN Umgebungsvariable.")
