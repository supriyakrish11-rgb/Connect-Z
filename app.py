import os
import uuid
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, url_for
from database import get_db_connection, create_tables, add_fake_data

app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Secret key for login sessions
app.secret_key = "social_media_secret_key"

# Create database tables
create_tables()
add_fake_data()


# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():
    return redirect("/login")


# ==========================
# LOGIN PAGE
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/home")

        return "Invalid username or password"

    return render_template("login.html")


# ==========================
# REGISTER PAGE
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Check passwords
        if password != confirm_password:
            return "Passwords do not match"

        connection = get_db_connection()

        try:

            connection.execute(
                """
                INSERT INTO users
                (fullname, username, email, password)
                VALUES (?, ?, ?, ?)
                """,
                (fullname, username, email, password)
            )

            connection.commit()

        except Exception as error:

            connection.close()

            return f"Registration failed: {error}"

        connection.close()

        return redirect("/login")

    return render_template("register.html")


# ==========================
# HOME / FEED
# ==========================

@app.route("/home")
def home_page():

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    posts = connection.execute(
        """
        SELECT posts.*, users.username, users.fullname, users.profile_image
            , (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
            , EXISTS(
                SELECT 1 FROM likes
                WHERE likes.post_id = posts.id AND likes.user_id = ?
            ) AS liked_by_user
            , (SELECT COUNT(*) FROM comments WHERE comments.post_id = posts.id) AS comment_count
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
        """,
        (session["user_id"],)
    ).fetchall()

    comments_by_post = {post["id"]: [] for post in posts}
    if comments_by_post:
        comments = connection.execute(
            """
            SELECT comments.post_id, comments.comment, users.username, users.fullname
            FROM comments
            JOIN users ON comments.user_id = users.id
            ORDER BY comments.created_at ASC
            """
        ).fetchall()

        for comment in comments:
            if comment["post_id"] in comments_by_post:
                comments_by_post[comment["post_id"]].append(comment)

    connection.close()

    return render_template(
        "home.html",
        posts=posts,
        comments_by_post=comments_by_post,
        username=session["username"]
    )
@app.route("/create_post", methods=["POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("login"))

    caption = request.form.get("caption", "").strip()
    image = request.files.get("image")

    if not caption or not image or not image.filename:
        return redirect(url_for("home_page"))

    original_name = secure_filename(image.filename)
    extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return redirect(url_for("home_page"))

    filename = f"{uuid.uuid4().hex}.{extension}"
    image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    content = f"[image:/static/uploads/{filename}] {caption}"

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO posts (user_id, content)
        VALUES (?, ?)
    """, (session["user_id"], content))

    connection.commit()
    connection.close()

    return redirect(url_for("home"))
# ==========================
# LIKE / UNLIKE POST
# ==========================

@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):

    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    existing_like = connection.execute(
        """
        SELECT * FROM likes
        WHERE user_id = ? AND post_id = ?
        """,
        (session["user_id"], post_id)
    ).fetchone()

    if existing_like:
        connection.execute(
            """
            DELETE FROM likes
            WHERE user_id = ? AND post_id = ?
            """,
            (session["user_id"], post_id)
        )
    else:
        connection.execute(
            """
            INSERT INTO likes (user_id, post_id)
            VALUES (?, ?)
            """,
            (session["user_id"], post_id)
        )

    connection.commit()
    connection.close()

    return redirect("/home")


# ==========================
# ADD COMMENT
# ==========================

@app.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):

    if "user_id" not in session:
        return redirect("/login")

    comment = request.form["comment"]

    if comment.strip() == "":
        return redirect("/home")

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO comments (user_id, post_id, comment)
        VALUES (?, ?, ?)
        """,
        (session["user_id"], post_id, comment)
    )

    connection.commit()
    connection.close()

    return redirect("/home")

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

@app.route("/test")
def test():
    return "Test route is working!"

# ==========================
# RUN APPLICATION
# ==========================

if __name__ == "__main__":
    app.run(debug=True)