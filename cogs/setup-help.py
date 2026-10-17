import discord
from discord.ext import commands
from utils.babel import translator
from cogs.birthday_check_task import setup_database_record
from utils.logger import log

class SetupGuideView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.step = 1
        self.total_steps = 4
        self._ = translator.get_translation(bot.guild_configs.get(guild_id, {}).get("lang", "en"))
        self.prev_button.label = self._("Zurück")
        self.next_button.label = self._("Weiter")
        self.config_button.label = self._("Konfiguration öffnen")
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.step == 1
        self.next_button.label = self._("Abschließen") if self.step == self.total_steps else self._("Weiter")

    def get_step_embed(self) -> discord.Embed:
        color = discord.Color.blue()
        
        if self.step == 1:
            return discord.Embed(
                title=f"📋 {self._('Schritt 1/4: Kanal einstellen')}",
                description=self._("**Wähle den Kanal, in dem Geburtstagsgrüße gesendet werden sollen.**\n\n"
                                "Ohne einen Kanal werden keine Geburtstagsnachrichten versendet. "
                                "Du kannst den Systemkanal des Servers verwenden oder einen eigenen Kanal erstellen.\n\n"
                                "👉 Nutze `/config` und wähle 'Kanal' aus dem Menü."),
                color=color
            )
        elif self.step == 2:
            return discord.Embed(
                title=f"🎨 {self._('Schritt 2/4: Nachrichten anpassen')}",
                description=self._("**Passe die Geburtstagsgrüße an deinen Server an.**\n\n"
                                "Du kannst zwei verschiedene Nachrichten erstellen:\n"
                                "• Eine für Mitglieder ohne Geburtsjahr\n"
                                "• Eine für Mitglieder mit Geburtsjahr (zeigt das Alter an)\n\n"
                                "Verfügbare Variablen: `%username`, `%mention`, `%age`\n\n"
                                "👉 Nutze `/config` und wähle 'Nachricht (Mit/Ohne Alter)'."),
                color=color
            )
        elif self.step == 3:
            return discord.Embed(
                title=f"🖼️ {self._('Schritt 3/4: Bilder aktivieren')}",
                description=self._("**Aktiviere die automatische Bildgenerierung.**\n\n"
                                "Der Bot kann personalisierte Banner mit Profilbild und Namen erstellen. "
                                "Du kannst auch eigene Hintergrundbilder hochladen.\n\n"
                                "👉 Nutze `/config` und wähle 'Bilder An/Aus'."),
                color=color
            )
        elif self.step == 4:
            return discord.Embed(
                title=f"✅ {self._('Schritt 4/4: Testen & Mitglieder einladen')}",
                description=self._("**Teste deine Konfiguration und lade Mitglieder ein.**\n\n"
                                "• Teste mit `/config-test` um sicherzustellen, dass alles funktioniert\n"
                                "• Mitglieder können ihren Geburtstag mit `/birthday-set` festlegen\n"
                                "• Zeige alle Geburtstage mit `/birthday-list` an\n\n"
                                "🎉 Dein Server ist bereit für Geburtstage!"),
                color=discord.Color.green()
            )

    @discord.ui.button(label="Zurück", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.step > 1:
            self.step -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_step_embed(), view=self)

    @discord.ui.button(label="Weiter", style=discord.ButtonStyle.primary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.step < self.total_steps:
            self.step += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_step_embed(), view=self)
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title=self._("🎉 Setup abgeschlossen!"),
                    description=self._("Vielen Dank für das Einrichten von Birthdayyyyys!\n\n"
                                    "Bei Fragen nutze `/help` oder tritt dem Support Server bei: "
                                    "https://discord.gg/utD4afUrgt\n\n"
                                    "Wenn dir der Bot gefallen sollte, lass gerne eine Bewertung auf **__[TopGG](https://top.gg/bot/1389267222261792868)__** da!"),
                    color=discord.Color.green()
                ),
                view=None
            )

    @discord.ui.button(label="Konfiguration öffnen", style=discord.ButtonStyle.success, emoji="⚙️", row=2)
    async def config_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = self.bot.guild_configs.get(self.guild_id, {}).get("lang", "en")
        _ = translator.get_translation(lang)
        
        await interaction.response.defer(ephemeral=True)
        
        guild_id = interaction.guild.id
        await self.bot.load_bot_config(self.bot, guild_id)
        
        from cogs.config_commands import build_config_embed, MainConfigView
        embed = await build_config_embed(self.bot, guild_id)
        
        await interaction.followup.send(
            embed=embed,
            view=MainConfigView(self.bot, guild_id),
            ephemeral=True
        )

class Setuphelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):

        langs = ["de", "en", "fr", "es", "pl", "ru", "uk", "cs", "ar", "id", "ja", "ko", "pt", "tr", "zh"]
        lang = "en"
        for l in langs:
            if guild.preferred_locale.language_code.startswith(l):
                lang = l


        _ = translator.get_translation(lang)

        welcome_embed = discord.Embed(
            title=_("👋 Willkommen bei Birthdayyyyys!"),
            description=_("Danke, dass du Birthdayyyyys zu deinem Server hinzugefügt hast! "
                        "Folge dem interaktiven Guide unten, um den Bot in wenigen Minuten einzurichten."),
            color=discord.Color.blue()
        )

        welcome_embed.add_field(
            name=_("⚡ Schnellstart"),
            value=_("Klicke auf 'Guide starten' um durch die Einrichtung geführt zu werden. "
                    "Oder nutze direkt `/config` für alle Einstellungen."),
            inline=False
        )

        welcome_embed.add_field(
            name=_("📋 Die wichtigsten Befehle"),
            value=_("• `/config` - Bot konfigurieren\n"
                    "• `/birthday-set` - Geburtstag festlegen\n"
                    "• `/birthday-list` - Alle Geburtstage anzeigen\n"
                    "• `/help` - Weitere Hilfe"),
            inline=False
        )

        welcome_embed.add_field(
            name=_("💡 Brauchst du Hilfe?"),
            value=_("Support Server: https://discord.gg/utD4afUrgt"),
            inline=False
        )

        welcome_embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        welcome_embed.set_footer(text=_("Danke für's Nutzen von Birthdayyyyys!"))

        guide_view = SetupGuideView(self.bot, guild.id)

        sent = False

        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            try:
                await guild.system_channel.send(embed=welcome_embed, view=guide_view)
                sent = True
            except discord.Forbidden:
                pass

        if not sent:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    try:
                        await channel.send(embed=welcome_embed, view=guide_view)
                        sent = True
                        break
                    except discord.Forbidden:
                        continue

        if not sent:
            try:
                if guild.owner:
                    await guild.owner.send(embed=welcome_embed, view=guide_view)
            except discord.Forbidden:
                log(f"Could not send message to server {guild.name} or its owner.", 'WARNING')

        await setup_database_record(self.bot, guild.id, lang)

async def setup(bot):
    await bot.add_cog(Setuphelp(bot))