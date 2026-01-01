
import sqlite3
from werkzeug.security import generate_password_hash

print("Initializing database...")
conn = sqlite3.connect("pingpong.db")
c = conn.cursor()

# 删除旧表（如果存在）- 注意：这会清空数据！
c.execute("DROP TABLE IF EXISTS matches")
c.execute("DROP TABLE IF EXISTS users")

# 创建 Users 表
c.execute('''
CREATE TABLE users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE,
 password_hash TEXT,
 role TEXT,
 rating INTEGER DEFAULT 0
)
''')

# 创建 Matches 表 (包含新的 score 字段)
c.execute('''
CREATE TABLE matches (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER,
 opponent TEXT,
 result TEXT,
 delta INTEGER,
 score TEXT,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 创建默认管理员: admin / admin
admin_pass = generate_password_hash("admin")
c.execute("INSERT INTO users (username, password_hash, role, rating) VALUES (?, ?, ?, ?)",
          ("admin", admin_pass, "admin", 1500))

conn.commit()
conn.close()
print("Database initialized.")
print("Default Admin User Created:")
print("Username: admin")
print("Password: admin")
