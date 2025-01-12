import sqlite3
import datetime
from typing import List, Dict, Optional


class DatabaseManager:
    def __init__(self, db_path='filmfusion.db'):
        self.db_path = db_path
        self.create_tables()

    def create_tables(self):
        """Create all required tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                last_sync TIMESTAMP
            )
        """)

        # Create movies table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        """)

        # Create user_movies table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_id2 INTEGER,
                movie_id INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (user_id2) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        """)

        # Create common_movies table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS common_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                movie_id INTEGER,
                movie_name TEXT NOT NULL,
                comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user1_id) REFERENCES users (id),
                FOREIGN KEY (user2_id) REFERENCES users (id),
                FOREIGN KEY (movie_id) REFERENCES movies (id)
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, username: str) -> dict:
        """Add a new user"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user_id = cur.lastrowid

        conn.commit()
        conn.close()

        return {"id": user_id, "username": username}

    def get_user(self, username: str) -> Optional[dict]:
        """Get user by username"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, username, last_sync FROM users WHERE username = ?", (username,))
        user = cur.fetchone()

        conn.close()

        if user:
            return {"id": user[0], "username": user[1], "last_sync": user[2]}
        return None

    def add_movie(self, movie_data: dict) -> dict:
        """Add a new movie or get existing one"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Check if movie exists
        cur.execute("SELECT id, title FROM movies WHERE title = ?", (movie_data['title'],))
        movie = cur.fetchone()

        if not movie:
            cur.execute("INSERT INTO movies (title) VALUES (?)", (movie_data['title'],))
            movie_id = cur.lastrowid
            conn.commit()
        else:
            movie_id = movie[0]

        conn.close()
        return {"id": movie_id, "title": movie_data['title']}

    def add_user_movie(self, username: str, username2: str, movie_data: dict):
        """Add a movie to user's list"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        try:
            # Get or create users
            user = self.get_user(username)
            if not user:
                user = self.add_user(username)

            user2 = self.get_user(username2)
            if not user2:
                user2 = self.add_user(username2)

            # Get or create movie
            movie = self.add_movie(movie_data)

            # Add to user_movies
            cur.execute("""
                INSERT INTO user_movies (user_id, user_id2, movie_id, added_date) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user['id'], user2['id'], movie['id']))

            conn.commit()
        finally:
            conn.close()

    def get_user_movies(self, username: str) -> List[dict]:
        """Get user's movie list"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT m.id, m.title 
            FROM movies m
            JOIN user_movies um ON um.movie_id = m.id
            JOIN users u ON um.user_id = u.id
            WHERE u.username = ?
        """, (username,))

        movies = []
        for row in cur.fetchall():
            movies.append({"id": row[0], "title": row[1]})

        conn.close()
        return movies

    def save_common_movies(self, username1: str, username2: str, common_movies: list) -> bool:
        """Save common movies between two users"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        try:
            user1 = self.get_user(username1)
            user2 = self.get_user(username2)

            if not user1 or not user2:
                return False

            # Clear previous common movies
            cur.execute("""
                DELETE FROM common_movies 
                WHERE (user1_id = ? AND user2_id = ?) 
                OR (user1_id = ? AND user2_id = ?)
            """, (user1['id'], user2['id'], user2['id'], user1['id']))

            # Insert new common movies
            for movie in common_movies:
                movie_obj = self.add_movie({'title': movie.title})

                cur.execute("""
                    INSERT INTO common_movies 
                    (user1_id, user2_id, movie_id, movie_name, comparison_date)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user1['id'], user2['id'], movie_obj['id'], movie.title))

            conn.commit()
            return True

        finally:
            conn.close()

    def get_common_movies_from_db(self, username1: str, username2: str) -> List[dict]:
        """Get common movies between two users from database"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        try:
            user1 = self.get_user(username1)
            user2 = self.get_user(username2)

            if not user1 or not user2:
                return []

            cur.execute("""
                SELECT m.id, m.title
                FROM movies m
                JOIN common_movies cm ON cm.movie_id = m.id
                WHERE (cm.user1_id = ? AND cm.user2_id = ?)
                OR (cm.user1_id = ? AND cm.user2_id = ?)
            """, (user1['id'], user2['id'], user2['id'], user1['id']))

            movies = []
            for row in cur.fetchall():
                movies.append({"id": row[0], "title": row[1]})

            return movies

        finally:
            conn.close()

    def update_user_sync_time(self, username: str):
        """Update user's last sync time"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        try:
            cur.execute("""
                UPDATE users 
                SET last_sync = CURRENT_TIMESTAMP 
                WHERE username = ?
            """, (username,))
            conn.commit()

        finally:
            conn.close()