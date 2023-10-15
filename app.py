from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'some_secret_key'
app.permanent_session_lifetime = timedelta(minutes=30)  # Set session to expire after 30 minutes

DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['username'] = user['username']
            session['user_id'] = user['id']  # <-- This is the line we added for userid post id
            return redirect(url_for('landing'))
        else:
            flash('Incorrect username or password.')

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()

        flash('Successfully signed up! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/landing')
def landing():
    if 'username' in session:
        conn = get_db_connection()
        posts = conn.execute('''
            SELECT posts.id, users.username, posts.body_part, posts.content, posts.likes
            FROM posts JOIN users ON posts.user_id = users.id
            ORDER BY posts.id DESC
        ''').fetchall()
        conn.close()
        return render_template('landing.html', username=session['username'], posts=posts)
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'username' in session:
        body_part = request.form['body_part']
        content = request.form['content']

        # Insert the new post into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (user_id, body_part, content) VALUES (?, ?, ?)', 
                     (session['user_id'], body_part, content))
        conn.commit()
        conn.close()
        return redirect(url_for('landing'))
    return redirect(url_for('login'))



@app.route('/like_post/<int:post_id>')
def like_post(post_id):
    if 'username' in session:
        conn = get_db_connection()

        # Check if user has already liked this post
        liked = conn.execute('SELECT * FROM likes WHERE user_id = ? AND post_id = ?', 
                             (session['user_id'], post_id)).fetchone()

        # If not liked, increment the likes count and add a record to the Likes table
        if not liked:
            conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
            conn.execute('INSERT INTO likes (user_id, post_id) VALUES (?, ?)', (session['user_id'], post_id))
            conn.commit()

        conn.close()
        return redirect(url_for('landing'))
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run()
