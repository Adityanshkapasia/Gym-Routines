from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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

@app.route('/landing', defaults={'body_part': None}, methods=['GET', 'POST'])
@app.route('/landing/<body_part>/', methods=['GET', 'POST'])
def landing(body_part):
    conn = get_db_connection()
    if body_part:
        posts = conn.execute('SELECT p.id, p.content, p.likes, p.body_part, u.username FROM posts p JOIN users u ON p.user_id = u.id WHERE p.body_part = ? ORDER BY p.id DESC', (body_part,)).fetchall()
    else:
        posts = conn.execute('SELECT p.id, p.content, p.likes, p.body_part, u.username FROM posts p JOIN users u ON p.user_id = u.id ORDER BY p.id DESC').fetchall()
    conn.close()
    return render_template('landing.html', posts=posts)




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



@app.route('/like_post/<int:post_id>', methods=['POST'])
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
            new_like_count = conn.execute('SELECT likes FROM posts WHERE id = ?', (post_id,)).fetchone()[0]
            conn.close()
            return jsonify({"likes": new_like_count, "success": True})

        conn.close()
        return jsonify({"success": False, "message": "You've already liked this post!"})
    
    return jsonify({"success": False, "message": "Please login first."})

@app.route('/my_routines')
def my_routines():
    if 'username' in session:
        conn = get_db_connection()
        # Fetching all posts created by the logged-in user
        posts = conn.execute('''
            SELECT posts.id, users.username, posts.body_part, posts.content, posts.likes
            FROM posts JOIN users ON posts.user_id = users.id
            WHERE users.username = ?
            ORDER BY posts.id DESC
        ''', (session['username'],)).fetchall()
        conn.close()
        return render_template('landing.html', username=session['username'], posts=posts)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
