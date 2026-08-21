import sqlite3


DATABASE = "database.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            bio TEXT DEFAULT '',
            profile_image TEXT DEFAULT ''
        )
    """)

    # Posts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Likes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            UNIQUE(user_id, post_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    # Comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    # Followers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS followers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            following_id INTEGER NOT NULL,
            UNIQUE(follower_id, following_id),
            FOREIGN KEY (follower_id) REFERENCES users(id),
            FOREIGN KEY (following_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


def add_fake_data():

    connection = get_db_connection()
    cursor = connection.cursor()

    # ==========================
    # ADD FAKE USERS
    # ==========================

    fake_users = [
        ("Priya Kumar", "priya", "priya@gmail.com", "1234", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=160&h=160&fit=crop&crop=faces"),
        ("Rahul Kumar", "rahul", "rahul@gmail.com", "1234", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=160&h=160&fit=crop&crop=faces"),
        ("Anu Priya", "anu", "anu@gmail.com", "1234", "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=160&h=160&fit=crop&crop=faces")
    ]

    for user in fake_users:

        existing_user = cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (user[1],)
        ).fetchone()

        if existing_user is None:

            cursor.execute("""
                INSERT INTO users
                (fullname, username, email, password, profile_image)
                VALUES (?, ?, ?, ?, ?)
            """, user)

        else:
            cursor.execute(
                "UPDATE users SET profile_image = ? WHERE username = ?",
                (user[4], user[1])
            )

    connection.commit()


    # ==========================
    # GET FAKE USER IDs
    # ==========================

    priya = cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("priya",)
    ).fetchone()

    rahul = cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("rahul",)
    ).fetchone()

    anu = cursor.execute(
        "SELECT id FROM users WHERE username = ?",
        ("anu",)
    ).fetchone()


    # ==========================
    # ADD FAKE POSTS
    # ==========================

    fake_posts = [
        (
            priya["id"],
            "[image:https://images.unsplash.com/photo-1500534623283-312aade485b7?w=900] Chasing soft light and quieter mornings."
        ),
        (
            rahul["id"],
            "[image:https://images.unsplash.com/photo-1519608487953-e999c86e7455?w=900] The city looks different after dark."
        ),
        (
            anu["id"],
            "[image:https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900] A little coffee, a lot of ideas."
        )
    ]

    for post in fake_posts:

        existing_post = cursor.execute(
            """
            SELECT id FROM posts
            WHERE user_id = ? AND content = ?
            """,
            post
        ).fetchone()

        if existing_post is None:

            cursor.execute("""
                INSERT INTO posts
                (user_id, content)
                VALUES (?, ?)
            """, post)

    demo_posts = cursor.execute(
        """
        SELECT id, user_id, content FROM posts
        WHERE content LIKE '[image:%'
        ORDER BY id ASC
        """
    ).fetchall()

    fake_user_ids = {
        "priya": priya["id"],
        "rahul": rahul["id"],
        "anu": anu["id"]
    }

    demo_comments = [
        ("This light is unreal.", "rahul"),
        ("Adding this to my moodboard.", "anu"),
        ("The atmosphere here is perfect.", "priya")
    ]

    for demo_post in demo_posts:
        for username, user_id in fake_user_ids.items():
            if user_id != demo_post["user_id"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO likes (user_id, post_id) VALUES (?, ?)",
                    (user_id, demo_post["id"])
                )

        for comment_text, username in demo_comments[:2]:
            cursor.execute(
                """
                INSERT INTO comments (user_id, post_id, comment)
                SELECT ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM comments
                    WHERE user_id = ? AND post_id = ? AND comment = ?
                )
                """,
                (
                    fake_user_ids[username], demo_post["id"], comment_text,
                    fake_user_ids[username], demo_post["id"], comment_text
                )
            )

    connection.commit()
    connection.close()

    print("Fake users and posts added successfully!")


if __name__ == "__main__":
    create_tables()
    print("Database created successfully!")