import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_statistics.db')
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER,
                    username TEXT,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS commands_stats (
                    user_id INTEGER,
                    command TEXT,
                    timestamp TIMESTAMP
                )
            ''')
            
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS anime_views (
                    user_id INTEGER,
                    title TEXT,
                    timestamp TIMESTAMP
                )
            ''')

    def log_user(self, user_id: int, username: str):
        now = datetime.now()
        with self.conn:
            # Проверяем, существует ли пользователь
            user = self.conn.execute(
                'SELECT * FROM user_stats WHERE user_id = ?', 
                (user_id,)
            ).fetchone()
            
            if not user:
                self.conn.execute(
                    'INSERT INTO user_stats VALUES (?, ?, ?, ?)',
                    (user_id, username, now, now)
                )
            else:
                self.conn.execute(
                    'UPDATE user_stats SET last_seen = ? WHERE user_id = ?',
                    (now, user_id)
                )

    def log_command(self, user_id: int, command: str):
        with self.conn:
            self.conn.execute(
                'INSERT INTO commands_stats VALUES (?, ?, ?)',
                (user_id, command, datetime.now())
            )

    def log_anime_view(self, user_id: int, title: str):
        with self.conn:
            self.conn.execute(
                'INSERT INTO anime_views VALUES (?, ?, ?)',
                (user_id, title, datetime.now())
            )

    def get_statistics(self):
        with self.conn:
            total_users = self.conn.execute(
                'SELECT COUNT(DISTINCT user_id) FROM user_stats'
            ).fetchone()[0]
            
            total_commands = self.conn.execute(
                'SELECT COUNT(*) FROM commands_stats'
            ).fetchone()[0]
            
            total_anime = self.conn.execute(
                'SELECT COUNT(*) FROM anime_views'
            ).fetchone()[0]
            
            top_anime = self.conn.execute('''
                SELECT title, COUNT(*) as count 
                FROM anime_views 
                GROUP BY title 
                ORDER BY count DESC 
                LIMIT 3
            ''').fetchall()
            
            return {
                'total_users': total_users,
                'total_commands': total_commands,
                'total_anime': total_anime,
                'top_anime': top_anime
            }
