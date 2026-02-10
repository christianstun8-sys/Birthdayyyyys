import os
import aiosqlite
import asyncio

async def migrate_add_language_column():
    """
    Geht alle Datenbanken im Ordner 'databases' durch und fügt
    die Spalte 'lang' zur Tabelle 'guild_settings' hinzu, falls sie fehlt.
    """
    db_folder = 'databases'

    # Sicherstellen, dass der Ordner existiert
    if not os.path.exists(db_folder):
        print(f"Ordner '{db_folder}' wurde nicht gefunden.")
        return

    # Alle .db Dateien im Ordner auflisten
    db_files = [f for f in os.listdir(db_folder) if f.endswith('.db')]

    print(f"Starte Migration für {len(db_files)} Datenbanken...")

    for db_file in db_files:
        db_path = os.path.join(db_folder, db_file)

        try:
            async with aiosqlite.connect(db_path) as db:
                # Prüfen, ob die Spalte 'lang' bereits existiert, um Fehler zu vermeiden
                async with db.execute("PRAGMA table_info(guild_settings)") as cursor:
                    columns = await cursor.fetchall()
                    column_names = [col[1] for col in columns]

                if 'lang' not in column_names:
                    # Spalte hinzufügen mit Standardwert 'en'
                    await db.execute("ALTER TABLE guild_settings ADD COLUMN lang TEXT DEFAULT 'en'")
                    await db.commit()
                    print(f"✅ 'lang' erfolgreich hinzugefügt zu: {db_file}")
                else:
                    print(f"ℹ️ 'lang' bereits vorhanden in: {db_file}")

        except Exception as e:
            print(f"❌ Fehler bei der Migration von {db_file}: {e}")

    print("Migration abgeschlossen.")

# Beispiel für den Aufruf (falls du das Skript separat testen willst):
# if __name__ == "__main__":
#     asyncio.run(migrate_add_language_column())