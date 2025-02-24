import aiosqlite
from config import DATABASE

# --- Database Initialization ---
async def init_db():
    """Создаёт таблицы базы данных при необходимости."""
    try:
        async with aiosqlite.connect(DATABASE) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS social_circle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contact_id INTEGER,
                    contact_name TEXT,
                    UNIQUE(user_id, contact_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS useful_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    contact_name TEXT,
                    contact_phone TEXT,
                    description TEXT,
                    UNIQUE(user_id, contact_phone)
                )
            ''')

            await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON social_circle (user_id);')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_contact_id ON social_circle (contact_id);')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_user_id_useful ON useful_contacts (user_id);')
            await db.commit()

            print("БД успешно инициализирована")
            
