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

# --- FEATURE CONFIGURATION ---
FEATURES = {
    'topgg': os.getenv('TOPGG', 'False').lower() == 'true',
    'topgg_token': os.getenv('TOPGG_TOKEN'),
    'uptime_kuma': os.getenv('UPTIME_KUMA', 'False').lower() == 'true',
    'uptime_kuma_url': os.getenv('UPTIME_KUMA_URL'),
    'uptime_kuma_interval': int(os.getenv('UPTIME_KUMA_INTERVAL', 30)),
    'jishaku': os.getenv('JISHAKU', 'True').lower() == 'true',
    'support_server_sync': os.getenv('DISCORD_SUPPORT_SERVER'),
    'prefix': os.getenv('BOT_PREFIX'),
    'owner_id': os.getenv('OWNER_USER_ID'),
    'inform_about_server_join': os.getenv('INFORM_ABOUT_SERVER_JOIN', 'True').lower() == 'true',
    'inform_about_server_leave': os.getenv('INFORM_ABOUT_SERVER_LEAVE', 'True').lower() == 'true'
}

# --- BETA MANAGEMENT ---
beta = False
debug  = False

if beta:
    TOKEN = os.getenv('DISCORD_BETA_TOKEN')
else:
    TOKEN = os.getenv('DISCORD_TOKEN')

logger = logging.getLogger('discord.gateway')
if debug:
    logger.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)

from utils.logger import log

def setup_directories():
    for dir_name in ['cogs', 'data', 'data/custom_images']:
        log(f"Checking directory '{dir_name}'.")
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            log(f"Created directory '{dir_name}'.")

    data_path = 'data'
    if not os.path.exists(os.path.join(data_path, 'birthday_background.jpg')):
        log(f"'birthday_background.jpg' is missing in the directory'{data_path}'.", 'WARNING')
    if not os.path.exists(os.path.join(data_path, 'arial.ttf')):
        log(f"'arial.ttf' is missing in the directory '{data_path}'.", "WARNING")

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

class BirthdayBot(commands.Bot):
    def __init__(self):
        prefix = "bbeta." if beta else FEATURES.get('prefix', 'b.')
        super().__init__(command_prefix=prefix, intents=intents, help_command=None)
        self.guild_configs = {}
        self.kuma_url = FEATURES['uptime_kuma_url']
        self.kuma_interval = FEATURES['uptime_kuma_interval']
        self.version = os.getenv('PROJECT_VERSION')
        self.db_pool = None
        self.topgg = None

    async def setup_hook(self):
        log("Setting up translator...")
        await self.tree.set_translator(DiscordSlashTranslator())
        log("Translator set up.")

        log("Connecting to database...")
        try:
            self.db_pool: aiomysql.Pool = await aiomysql.create_pool(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER_NAME"),
                db=os.getenv("DB_NAME"),
                port=int(os.getenv("DB_PORT")),
                password=os.getenv("DB_PASSWORD"),
                autocommit=True
            )
            log("Database connected successfully!")
        except Exception as e:
            log(f"Database connection error: {e}", 'ERROR')

        log("Starting cog loading...")
        done = True
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    if debug:
                        log(f"Loading cog: {filename[:-3]}")
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    if debug:
                        log(f"Loaded cog: {filename[:-3]}")
                except Exception as e:
                    log(f"Error while loading cog '{filename[:-3]}': {e}", 'ERROR')
                    done = False

        if done:
            log("All cogs loaded successfully!")

        if FEATURES['jishaku']:
            try:
                await self.load_extension('jishaku')
                jsk = self.get_command('jsk')
                if jsk:
                    jsk.hidden = True
                log("Jishaku has been started successfully!")
            except Exception as e:
                log(f"Error while starting Jishaku: {e}", 'ERROR')
        else:
            log("Jishaku is disabled.")

        if debug:
            try:
                synced = await self.tree.sync()
                log(f"Synchronised {len(synced)} slash comamnds.")
            except Exception as e:
                log(f"Error while synchronizing slash commands: {e}", 'ERROR')

        if not beta and FEATURES['support_server_sync']:
            try:
                support_server_id = discord.Object(id=int(FEATURES['support_server_sync']))
                guild_synced = await self.tree.sync(guild=support_server_id)
                log(f"Successfully synced {len(guild_synced)} commands for the support server.")
            except Exception as e:
                log(f"Error while synchronizing support server commands: {e}", 'ERROR')

        if FEATURES['uptime_kuma'] and FEATURES['uptime_kuma_url']:
            self.uptime_ping.start()
            log("Uptime Kuma ping enabled.")
        else:
            log("Uptime Kuma is disabled.")


    async def on_ready(self):
        log(f'Bot logged in as {self.user}')
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Happy Birthdayyyyy! 🎂"))
        from cogs.birthday_check_task import load_all_guild_configs
        await load_all_guild_configs(self)

        if not beta and FEATURES['topgg'] and FEATURES['topgg_token']:
            self.topgg = topgg.DBLClient(self, FEATURES['topgg_token'])
            self.update_stats.start()
            log("TopGG statistics enabled.")
        else:
            log("TopGG is disabled.")

        log("------------------------------")
        log("Bot is ready!")


    async def on_guild_join(self, guild: discord.Guild):
        if FEATURES['inform_about_server_join']:
            owner_id = FEATURES['owner_id']
            owner = await self.fetch_user(owner_id)

            embed = discord.Embed(
                title="Birthdayyyyys has been added to a new server!",
                description="Hii, I'm on a new server now! :) \n \n"
                            f"🪧 Server name: '{guild.name}' ({guild.id})\n"
                            f"🧑‍🦱 Member count: {guild.member_count}\n"
                            f"👑 Server owner: {guild.owner.name}\n (https://discordid.netlify.app/?id={guild.owner_id}) \n"
                            f"💜 Boost level: {guild.premium_tier} ({guild.premium_subscription_count} Boosts)",
                color=discord.Color.blue()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            else:
                embed.set_thumbnail(url=self.user.display_avatar.url)
            try:
                await owner.send(embed=embed, content=f"{owner.mention} New server!")
            except discord.Forbidden:
                log("Failed to send notification to owner: No permission.", 'ERROR')

        log(f"Bot added to new guild: {guild.name} (ID: {guild.id})")
        from cogs.birthday_check_task import load_bot_config
        await load_bot_config(self, guild.id)


    async def on_guild_remove(self, guild):
        log(f"Bot removed from guild {guild.name} (ID: {guild.id}).")

        if guild.id in self.guild_configs:
            del self.guild_configs[guild.id]

        if FEATURES['inform_about_server_leave']:
            embed = discord.Embed(
                title="Birthdayyyyys has been removed from a server.",
                description="Hi! I've been removed from a server... damn. :c \n"
                            f"🪧 Server name: '{guild.name}' ({guild.id})\n"
                            f"🧑‍🦱 Member count: {guild.member_count}\n"
                            f"👑 Server owner: {guild.owner.name}\n (https://discordid.netlify.app/?id={guild.owner_id}) \n"
                            f"💜 Boost level: {guild.premium_tier} ({guild.premium_subscription_count} Boosts)",
                color=discord.Color.red()
            )
            owner_id = FEATURES['owner_id']
            owner = await self.fetch_user(owner_id)
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            else:
                embed.set_thumbnail(url=self.user.display_avatar.url)

            try:
                await owner.send(embed=embed, content=f"{owner.mention} Server removed.")
            except discord.Forbidden:
                log(f"Failed to send notification to {owner.global_name}: No permission.", 'ERROR')

        await remove_database_record(self, guild.id)

    @tasks.loop(seconds=30)
    async def uptime_ping(self):
        if self.is_ready():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.kuma_url) as response:
                        if response.status == 200:
                            if debug:
                                log("Uptime Kuma ping successful.", 'DEBUG')
                        else:
                            log(f"Uptime Kuma ping failed: Status {response.status}", 'WARNING')
            except Exception as e:
                log(f"Error during uptime ping: {e}", 'ERROR')

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
            log(f"Error sending server count to Top.gg: {e}", 'ERROR')

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
        log("ERROR: Please set a token in the .env file.", 'ERROR')
