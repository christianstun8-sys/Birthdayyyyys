# Birthdayyyyys

[![Discord Bots](https://top.gg/api/widget/1389267222261792868.svg)](https://top.gg/bot/1389267222261792868)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/M0E828EX0P)



A multi-functional Discord bot for birthday management and server administration.

Version: 6.0
Python: 3.8+
Discord.py: 2.0+

## Features

- **Birthday Management**: Automatic birthday notifications with custom banners
- **Multi-language Support**: Supports Arabic, Chinese (Simplified), Czech, English, French, Indonesian, Japanese, Korean, Polish, Portuguese, Russian, Spanish, Turkish, and Ukrainian
- **Slash Commands**: Modern Discord slash commands with translation support
- **Ticket System**: Complete ticket system for support
- **Temporary Voice Channels**: Automatic creation of temporary voice channels
- **Alerts**: Custom alert system for servers
- **TopGG Integration**: Automatic statistics posting to TopGG
- **Uptime Monitoring**: Integration with Uptime Kuma
- **Database Storage**: MySQL-based configuration storage
- **Custom Banner**: System for creating own images with a full customization within Discord

## Requirements

- Python 3.8 or higher
- MySQL database
- Discord Bot Token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/christianstun8/Birthdayyyyys.git
cd Birthdayyyyys
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create and configure `.env` file:
```bash
cp .env.example .env
```

## Configuration

Create a `.env` file in the project directory with the following variables:

```env
# Don't change this value, it's the version of the bot, obviously...
PROJECT_VERSION=6.0

# --- BOT CONFIGURATION ---
DISCORD_TOKEN=
DISCORD_BETA_TOKEN=
BOT_PREFIX=
OWNER_USER_ID=
# Valid values: True/False
INFORM_ABOUT_SERVER_JOIN=True
# Valid values: True/False
INFORM_ABOUT_SERVER_LEAVE=True
DISCORD_SUPPORT_SERVER= # Your support server ID, leave empty if you don't have one

# --- DATABASE CONFIGURATION ---
# Your database configuration, MySQL or any fork of it is supported
DB_HOST=-
DB_NAME=
DB_PORT=
DB_USER_NAME=
DB_PASSWORD=

# --- FEATURE CONFIGURATION ---
# TopGG: Enable/disable TopGG statistics posting
TOPGG=True
TOPGG_TOKEN=

# Uptime Kuma: Enable/disable uptime monitoring ping
# Valid values: True, False
UPTIME_KUMA=True
UPTIME_KUMA_URL= # Your Uptime Kuma URL, needs to be a post request
UPTIME_KUMA_INTERVAL=30 # In seconds, 30 by default

# Jishaku: Enable/disable Jishaku extension
JISHAKU=True
```

## Project Structure

```
Birthdayyyyys/
├── cogs/                    # Bot extensions
│   ├── birthday_check_task.py
│   ├── birthday_commands.py
│   ├── config_commands.py
│   ├── Ticket.py
│   ├── Tempvoice.py
│   └── ...
├── data/                    # Static data
│   ├── custom_images/
│   ├── birthday_background.jpg
│   └── arial.ttf
├── databases/               # Local databases
├── locales/                 # Translations
│   ├── messages.pot
│   ├── en/
│       ├── messages.mo
│       ├── messages.po
│   ├── de/
│   ├── es/
│   └── ...   
├── utils/                   # Utility functions
│   ├── discord_translator.py
│   ├── logger.py
│   └── babel.py
├── main.py                  # Bot entry point
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

## Usage

Start the bot with:
```bash
python main.py
```

### Commands

**Birthday Commands:**
- `/birthday-set` - Set your birthday (month, day, year, timezone)
- `/birthday-remove` - Remove your birthday
- `/birthday-show` - Show a user's birthday
- `/birthday-list` - List all birthdays on the server

**Configuration:**
- `/config` - Configure bot settings (channel, role, messages, images, etc.)
- `/config-test` - Test your birthday configuration

**Information:**
- `/info` - Display bot information
- `/help` - Show help and available commands
- `/ping` - Check bot latency

## Translations

The bot supports multiple languages. To add new languages:

1. Create a new directory in `locales/`
2. Add the `.po` files
3. Compile translations with:
```bash
pybabel compile -d locales
```

> [!TIP]
> There are default translation .po and .mo files already included. You can edit them anytime without problems though.

## Contributing

Contributions are welcome! Those will be implemented in the official bot. 

Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues or questions:
- Discord Server: https://discord.gg/utD4afUrgt
- GitHub Issues: https://github.com/christianstun8-sys/Birthdayyyyys/issues
- Documentation: https://birthdayyyyys.christianst.xyz/docs

## Links

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [TopGG](https://top.gg/)
- [Uptime Kuma](https://uptime.kuma.pet/)

---

Made by Christianst_ with <3

A little joke cuz I'm bored:

<a href="https://readme-jokes.vercel.app"><img align="center" src="https://readme-jokes.vercel.app/api" alt="README Jokes"></a>
