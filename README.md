# Birthdayyyyys - Discord Birthday Bot

A modern Discord bot that manages birthdays in your server and automatically sends fun birthday greetings!

<div align="center">

[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[Website](https://birthdayyyyys.christianst.xyz) | [Top.gg](https://top.gg/bot/1389267222261792868) | [Support Server](https://discord.gg/utD4afUrgt) | [Invite Bot](https://discord.gg/utD4afUrgt)

</div>

---

## Features

- **Automatic Birthday Notifications** - The bot sends congratulations at midnight or at your configured time
- **Customizable Birthday Images** - Beautiful, personalized birthday embeds with background images
- **Multi-language Support** - Support for multiple languages via Babel and localization files
- **Flexible Configuration** - Customize the bot to your server's needs with `/config` command
- **Calendar View** - `/birthday-list` displays birthdays in an organized calendar format
- **Online Database** - Secure storage of all data in a MySQL database
- **Top.gg Integration** - Automatic statistics updates to [Top.gg](https://top.gg/bot/1389267222261792868)
- **Alert Channels** - Choose a dedicated channel for birthday notifications
- **Jishaku Support** - Debug tools for bot development (hidden from regular users)

---

## Getting Started

### Requirements
- Python 3.8 or higher
- MySQL Database (or MySQL-compatible hosting)
- Discord Bot Token
- Top.gg Token (optional)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/christianstun8-sys/Birthdayyyyys.git
cd Birthdayyyyys
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create .env file:**
```env
DISCORD_TOKEN=your_bot_token_here
DISCORD_BETA_TOKEN=your_beta_token_here
DB_HOST=your_database_host
DB_USER_NAME=your_database_username
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
DB_PORT=3306
TOPGG_TOKEN=your_topgg_token_here
```

4. **Add required asset files:**
   - `data/birthday_background.jpg` - Background image for birthday images
   - `data/arial.ttf` - Arial font for text rendering

5. **Start the bot:**
```bash
python main.py
```

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **discord.py** | Latest | Discord API Wrapper |
| **python-dotenv** | Latest | Load environment variables |
| **Pillow** | Latest | Image processing for birthday embeds |
| **aiohttp** | Latest | Asynchronous HTTP requests |
| **aiomysql** | Latest | Async MySQL database connection |
| **Babel** | Latest | Internationalization and localization |
| **pytz** | Latest | Timezone support |
| **jishaku** | Latest | Debugging tools |
| **topggpy** | Latest | Top.gg API integration |
| **cryptography** | Latest | Security for database connections |

---

## Project Structure

```
Birthdayyyyys/
├── main.py                    # Bot entry point and core logic
├── Alerts.py                  # Broadcast functions for announcements
├── eventmessages.py           # Event message handler for error handling
├── requirements.txt           # Python dependencies
├── mapping.cfg                # Configuration mapping
│
├── cogs/                      # Discord.py cogs (modular features)
│   ├── birthday_check_task.py # Main logic for birthday notifications
│   └── ...additional cogs
│
├── utils/                     # Helper functions
│   ├── discord_translator.py  # Discord slash command translator
│   ├── babel.py               # Babel integration functions
│   └── ...additional utilities
│
├── locales/                   # Language translations
│   ├── de.json               # German translations
│   └── en.json               # English translations
│
├── data/                      # Media files
│   ├── birthday_background.jpg # Background image
│   └── arial.ttf              # Font file
│
└── databases/                # Local database files (auto-created)
```

---

## Key Features in main.py

### BirthdayBot Class
The main class with the following features:

- **Automatic Directory Creation** - `setup_directories()` creates all necessary folders
- **Dynamic Cog System** - All Python files in the `cogs/` folder are automatically loaded
- **Database Pool** - `aiomysql.Pool` for efficient database connections
- **Uptime Monitoring** - Automatic status updates to Uptime Kuma (`uptime_ping` task)
- **Top.gg Integration** - Automatic server statistics every 30 minutes
- **Multi-language Slash Commands** - Discord Translator for automatic localization

### Event Handlers

```python
on_ready()          # Bot startup, load guild configs, initialize Top.gg
on_guild_join()     # Notification when bot joins a server
on_guild_remove()   # Cleanup when bot is removed
```

### Background Tasks

- `uptime_ping()` (every 30 seconds) - Kuma uptime status
- `update_stats()` (every 30 minutes) - Top.gg server statistics

---

## Configuration

The bot supports per-server configuration with the `/config` command:

- **Alerts Channel** - Channel for birthday notifications
- **Embed Color** - Color for birthday embeds (hex format)
- **Language** - Language preference for the server
- **Message Time** - Time for birthday greetings

All settings are stored in the MySQL database.

---

## Bot Links

| Platform | Link |
|----------|------|
| **Top.gg** | https://top.gg/bot/1389267222261792868 |
| **Website** | https://birthdayyyyys.christianst.xyz |
| **Support Server** | https://discord.gg/utD4afUrgt |
| **Direct Invite** | https://discord.gg/utD4afUrgt |

---

## Development & Debugging

### Activate Debug Mode
In `main.py`, set the `debug` variable to `True`:

```python
debug = True  # Enables debug logging
```

### Jishaku Shell
The bot automatically loads **jishaku** for advanced debugging features (hidden from regular users).

### Bot Token Management
- **Production**: Uses `DISCORD_TOKEN` from `.env`
- **Beta**: Uses `DISCORD_BETA_TOKEN` (when `beta = True` in main.py)

---

## Database Structure

The bot uses a MySQL database with the following main tables:

- **Birthdays** - Stores birthdays of users per server
- **Configurations** - Stores server-specific settings
- **Alerts** - Logs sent notifications

---

## Contributing

This repository serves for demonstration purposes. If you have improvements, feel free to open an issue or pull request!

---

## Important Notes

- **Database Migration**: The bot has undergone an online database migration. Old local files will be deleted after a transition period.
- **Missing Data**: If data is missing after migration, create a ticket in the [Support Server](https://discord.gg/utD4afUrgt) with your Server ID or User ID.
- **Uptime Kuma**: The bot automatically pings an Uptime Kuma server every 30 seconds (configurable for monitoring).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with love by [ChristianSt.](https://github.com/christianstun8-sys)

[Add Bot](https://discord.gg/utD4afUrgt) | [Support](https://discord.gg/utD4afUrgt) | [Website](https://birthdayyyyys.christianst.xyz)

</div>
