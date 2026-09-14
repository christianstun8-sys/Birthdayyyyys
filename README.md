# 🎂 Birthdayyyyys - Discord Birthday Bot

Ein moderner Discord Bot, der Geburtstage in deinem Server verwaltet und automatisch lustige Geburtstagsglückwünsche sendet!

<div align="center">

[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[🌐 Website](https://birthdayyyyys.christianst.xyz) • [📊 Top.gg](https://top.gg/bot/1389267222261792868) • [💬 Support-Server](https://discord.gg/utD4afUrgt) • [📥 Bot Einladung](https://discord.gg/utD4afUrgt)

</div>

---

## ✨ Features

- 🎉 **Automatische Geburtstagsbenachrichtigungen** - Der Bot sendet zu Mitternacht oder zu deiner eingestellten Zeit automatisch Glückwünsche
- 🎨 **Benutzerdefinierte Geburtstagsbilder** - Schöne, personalisierte Geburtstags-Embeds
- 🌍 **Mehrsprachigkeit** - Unterstützung für verschiedene Sprachen (über Babel & Locales)
- ⚙️ **Flexible Konfiguration** - Mit `/config` den Bot an deine Serveranforderungen anpassen
- 📅 **Kalenderansicht** - `/birthday-list` zeigt Geburtstage in einer organisierten Kalenderübersicht
- 🗄️ **Online-Datenbank** - Sichere Speicherung aller Daten in einer MySQL-Datenbank
- 📊 **Top.gg Integration** - Automatische Statistik-Updates auf [Top.gg](https://top.gg/bot/1389267222261792868)
- 🔔 **Alert-Kanäle** - Wähle einen speziellen Kanal für Geburtstagsbenachrichtigungen
- 🛠️ **Jishaku Support** - Debug-Tools für Bot-Entwicklung (versteckt)

---

## 🚀 Erste Schritte

### Anforderungen
- Python 3.8 oder höher
- MySQL Datenbank (oder MySQL-kompatibles Hosting)
- Discord Bot Token
- Top.gg Token (optional)

### Installation

1. **Repository klonen:**
```bash
git clone https://github.com/christianstun8-sys/Birthdayyyyys.git
cd Birthdayyyyys
```

2. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

3. **.env Datei erstellen:**
```env
DISCORD_TOKEN=dein_bot_token_hier
DISCORD_BETA_TOKEN=dein_beta_token_hier
DB_HOST=dein_db_host
DB_USER_NAME=dein_db_benutzername
DB_PASSWORD=dein_db_passwort
DB_NAME=dein_db_name
DB_PORT=3306
TOPGG_TOKEN=dein_topgg_token_hier
```

4. **Erforderliche Asset-Dateien hinzufügen:**
   - `data/birthday_background.jpg` - Hintergrundbild für Geburtstagsbilder
   - `data/arial.ttf` - Arial Font für Text-Rendering

5. **Bot starten:**
```bash
python main.py
```

---

## 📦 Dependencies

| Paket | Version | Zweck |
|-------|---------|-------|
| **discord.py** | Latest | Discord API Wrapper |
| **python-dotenv** | Latest | Umgebungsvariablen laden |
| **Pillow** | Latest | Bildverarbeitung für Geburtstags-Embeds |
| **aiohttp** | Latest | Asynchrone HTTP-Anfragen |
| **aiomysql** | Latest | Async MySQL Datenbankverbindung |
| **Babel** | Latest | Internationalisierung & Locales |
| **pytz** | Latest | Zeitzonen-Support |
| **jishaku** | Latest | Debugging Tools |
| **topggpy** | Latest | Top.gg API Integration |
| **cryptography** | Latest | Sicherheit für Datenbankverbindungen |

---

## 🏗️ Projektstruktur

```
Birthdayyyyys/
├── main.py                    # Bot-Einstiegspunkt & Core-Logik
├── Alerts.py                  # Broadcast-Funktionen für Ankündigungen
├── eventmessages.py           # Event-Message Handler für Fehlerbehandlung
├── requirements.txt           # Python Dependencies
├── mapping.cfg                # Konfigurationsmapping
│
├── cogs/                      # Discord.py Cogs (Modular aufgebaute Features)
│   ├── birthday_check_task.py # Hauptlogik für Geburtstagsbenachrichtigungen
│   └── ...weitere Cogs
│
├── utils/                     # Hilfsfunktionen
│   ├── discord_translator.py  # Discord Slash-Command Translator
│   ├── babel.py               # Babel-Integrationsfunktionen
│   └── ...weitere Utils
│
├── locales/                   # Sprachübersetzungen
│   ├── de.json               # Deutsche Übersetzungen
│   └── en.json               # Englische Übersetzungen
│
├── data/                      # Medien-Dateien
│   ├── birthday_background.jpg # Hintergrundbild
│   └── arial.ttf              # Font-Datei
│
└── databases/                # Lokale Datenbankdateien (automatisch erstellt)
```

---

## 🔑 Wichtige Features der main.py

### BirthdayBot Klasse
Die Hauptklasse mit folgenden Features:

- **Automatische Verzeichniserstellung** - `setup_directories()` erstellt alle notwendigen Ordner
- **Dynamisches Cog-System** - Alle Python-Dateien im `cogs/` Ordner werden automatisch geladen
- **Datenbank-Pool** - `aiomysql.Pool` für effiziente Datenbankverbindungen
- **Uptime-Monitoring** - Automatische Status-Updates an Uptime Kuma (`uptime_ping` Task)
- **Top.gg Integration** - Automatische Server-Statistiken alle 30 Minuten
- **Mehrsprachige Slash-Commands** - Discord Translator für automatische Lokalisierung

### Event Handler

```python
on_ready()          # Bot-Start, Guild-Configs laden, Top.gg initialisieren
on_guild_join()     # Benachrichtigung wenn Bot einem Server beitritt
on_guild_remove()   # Cleanup wenn Bot entfernt wird
```

### Background Tasks

- `uptime_ping()` (alle 30 Sekunden) - Kuma Uptime Status
- `update_stats()` (alle 30 Minuten) - Top.gg Serverstatistiken

---

## ⚙️ Konfiguration

Der Bot unterstützt Konfigurationen pro Server mit dem `/config` Command:

- **Alerts Channel** - Kanal für Geburtstagsbenachrichtigungen
- **Embed Color** - Farbe für Geburtstags-Embeds (Hex-Format)
- **Sprache** - Spracheinstellung für den Server
- **Message Time** - Uhrzeit für Geburtstagsglückwünsche

Die Einstellungen werden in der MySQL-Datenbank gespeichert.

---

## 🌐 Bot Links

| Plattform | Link |
|-----------|------|
| **Top.gg** | https://top.gg/bot/1389267222261792868 |
| **Website** | https://birthdayyyyys.christianst.xyz |
| **Support-Server** | https://discord.gg/utD4afUrgt |
| **Direkter Invite** | https://discord.gg/utD4afUrgt |

---

## 🔧 Entwicklung & Debugging

### Debug-Modus aktivieren
In `main.py` die Variable `debug = True` setzen:

```python
debug = True  # Aktiviert Debug-Logging
```

### Jishaku Shell
Der Bot lädt automatisch **jishaku** für erweiterte Debug-Features (versteckt vor normalen Usern).

### Bot-Token Management
- **Production**: Nutzt `DISCORD_TOKEN` aus `.env`
- **Beta**: Nutzt `DISCORD_BETA_TOKEN` (wenn `beta = True` in main.py)

---

## 📊 Datenbankstruktur

Der Bot nutzt eine MySQL-Datenbank mit folgenden Haupttabellen:

- **Geburtstage** - Speichert Geburtstage von Usern pro Server
- **Konfigurationen** - Speichert Server-spezifische Einstellungen
- **Alerts** - Protokolliert sendete Benachrichtigungen

---

## 🤝 Beiträge

Dieses Repo dient zu Demonstrationszwecken. Wenn du Verbesserungen hast, kannst du gerne ein Issue oder Pull Request öffnen!

---

## ⚠️ Wichtige Hinweise

- **Datenbankmigrationen**: Der Bot hat eine Online-Datenbank-Migration durchlaufen. Alte lokale Dateien werden nach einer Übergangsfrist gelöscht.
- **Missing Data**: Falls nach der Migration Daten fehlen, erstelle einen Ticket im [Support-Server](https://discord.gg/utD4afUrgt) mit deiner Server ID oder User ID.
- **Uptime Kuma**: Der Bot pingt automatisch einen Uptime Kuma Server alle 30 Sekunden (für Monitoring konfigurierbar).

---

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

---

<div align="center">

**Gemacht mit ❤️ von [ChristianSt.](https://github.com/christianstun8-sys)**

[🤖 Bot hinzufügen](https://discord.gg/utD4afUrgt) • [💬 Support](https://discord.gg/utD4afUrgt) • [🌐 Website](https://birthdayyyyys.christianst.xyz)

</div>
