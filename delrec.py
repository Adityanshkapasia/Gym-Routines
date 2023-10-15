import sqlite3

DATABASE = 'users.db'

def clear_all_records():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Delete all records from users table
    c.execute('DELETE FROM users')

    # Delete all records from posts table
    c.execute('DELETE FROM posts')

    # Delete all records from likes table
    c.execute('DELETE FROM likes')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    print("All records deleted successfully!")

clear_all_records()
