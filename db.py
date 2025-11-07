from pymysql import connect
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from hashlib import sha256
from os import urandom, getenv

load_dotenv()

# ========================
# 数据库表结构定义
# ========================
CREATE_TABLE_USER_COMMAND = """
    -- 用户表
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        type CHAR(1) NOT NULL COMMENT '用户类型（Teacher, Student, Class）',
        name VARCHAR(255) NOT NULL UNIQUE, -- 用户名唯一
        password VARCHAR(255) NOT NULL COMMENT '哈希后的密码',
        salt VARCHAR(255) NOT NULL COMMENT '密码盐值',
        exp INT NOT NULL DEFAULT 0 COMMENT '经验值'
    );
"""

CREATE_TABLE_BARS_COMMAND = """
    -- 贴吧表
    CREATE TABLE IF NOT EXISTS bars (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE, -- 贴吧名称唯一
        owner_id INT NOT NULL,
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(id) -- 关联用户
    );
"""

CREATE_TABLE_POSTS_COMMAND = """
    -- 帖子表
    CREATE TABLE IF NOT EXISTS posts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        bar_id INT NOT NULL COMMENT '所属贴吧ID', -- 关键字段
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        author_id INT NOT NULL,
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bar_id) REFERENCES bars(id), -- 关联贴吧
        FOREIGN KEY (author_id) REFERENCES users(id) -- 关联用户
    );
"""

CREATE_TABLE_COMMENTS_COMMAND = """
    -- 评论表
    CREATE TABLE IF NOT EXISTS comments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        post_id INT NOT NULL COMMENT '所属帖子ID', -- 关键字段
        content TEXT NOT NULL,
        author_id INT NOT NULL,
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        likes INT NOT NULL DEFAULT 0,
        reply_to_user INT COMMENT '回复目标用户ID（可为空）',
        FOREIGN KEY (post_id) REFERENCES posts(id), -- 关联帖子
        FOREIGN KEY (author_id) REFERENCES users(id), -- 关联用户
        FOREIGN KEY (reply_to_user) REFERENCES users(id) -- 关联被回复用户
    );
"""

# 用户关注的贴吧表
CREATE_TABLE_USER_BARS_COMMAND = """
    CREATE TABLE IF NOT EXISTS user_bars (
        user_id INT NOT NULL,
        bar_id INT NOT NULL,
        PRIMARY KEY (user_id, bar_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (bar_id) REFERENCES bars(id)
    );
"""

# ========================
# SQL 操作模板
# ========================
# 插入用户
INSERT_USER_COMMAND = """
INSERT INTO users (type, name, password, salt, exp)
VALUES (%s, %s, %s, %s, %s)
"""

# 插入贴吧
INSERT_BAR_COMMAND = """
INSERT INTO bars (name, owner_id)
VALUES (%s, %s)
"""

# 用户关注贴吧
INSERT_USER_BAR_COMMAND = """
INSERT INTO user_bars (user_id, bar_id)
VALUES (%s, %s)
"""

# 插入帖子
INSERT_POST_COMMAND = """
INSERT INTO posts (bar_id, title, content, author_id)
VALUES (%s, %s, %s, %s)
"""

# 插入评论
INSERT_COMMENT_COMMAND = """
INSERT INTO comments (post_id, content, author_id, reply_to_user)
VALUES (%s, %s, %s, %s)
"""

# 点赞评论
LIKE_COMMENT_COMMAND = """
UPDATE comments
SET likes = likes + 1
WHERE id = %s
"""

# 用户登录验证
LOGIN_USER_COMMAND = """
SELECT id, password, salt FROM users WHERE name = %s
"""

# 查询贴吧
GET_BAR_BY_NAME_COMMAND = """
SELECT id, name, owner_id, create_time FROM bars WHERE name = %s
"""

# 查询帖子
GET_POST_BY_ID_COMMAND = """
SELECT id, bar_id, title, content, author_id, create_time
FROM posts WHERE id = %s
"""

# 查询用户
GET_USER_BY_ID_COMMAND = """
SELECT id, type, name, exp FROM users WHERE id = %s
"""

# 查询贴吧的所有帖子
GET_POSTS_IN_BAR_COMMAND = """
SELECT id, title, author_id, create_time
FROM posts WHERE bar_id = %s
ORDER BY create_time DESC
LIMIT %s OFFSET %s
"""

# 查询帖子的所有评论
GET_COMMENTS_IN_POST_COMMAND = """
SELECT id, content, author_id, create_time, likes
FROM comments WHERE post_id = %s
ORDER BY create_time ASC
LIMIT %s OFFSET %s
"""

# 增加用户经验
ADD_USER_EXP_COMMAND = """
UPDATE users SET exp = exp + %s WHERE id = %s
"""

# 获取热门贴吧（按帖子数量排序）
GET_HOT_BARS_COMMAND = """
SELECT b.id, b.name, COUNT(p.id) as post_count
FROM bars b
LEFT JOIN posts p ON b.id = p.bar_id
GROUP BY b.id
ORDER BY post_count DESC
LIMIT %s
"""

# 获取用户关注的贴吧
GET_USER_BARS_COMMAND = """
SELECT b.id, b.name 
FROM user_bars ub
JOIN bars b ON ub.bar_id = b.id
WHERE ub.user_id = %s
"""


# ========================
# 数据库连接管理
# ========================
DB_PASSWORD = str(getenv("pswd"))


def get_db_connection():
    """创建并返回数据库连接"""
    return connect(
        host="mysql2.sqlpub.com",
        port=3307,
        user="gpchndb",
        password=DB_PASSWORD,
        database="gpchndb",
        charset="utf8mb4",
        cursorclass=DictCursor,
    )


def with_db_connection(func):
    """数据库连接装饰器"""

    def wrapper(*args, **kwargs):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                result = func(cursor, *args, **kwargs)
                conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    return wrapper


# ========================
# API 功能实现
# ========================
@with_db_connection
def create_tables(cursor):
    """创建所有数据库表"""
    cursor.execute(CREATE_TABLE_USER_COMMAND)
    cursor.execute(CREATE_TABLE_BARS_COMMAND)
    cursor.execute(CREATE_TABLE_POSTS_COMMAND)
    cursor.execute(CREATE_TABLE_COMMENTS_COMMAND)
    cursor.execute(CREATE_TABLE_USER_BARS_COMMAND)
    return True


def hash_password(password, salt):
    """使用SHA256哈希密码"""
    return sha256((password + salt).encode()).hexdigest()


@with_db_connection
def register_user(cursor, username, password, user_type="U"):
    """用户注册"""
    # 生成随机盐值
    salt = urandom(16).hex()
    hashed_pw = hash_password(password, salt)

    cursor.execute(INSERT_USER_COMMAND, (user_type, username, hashed_pw, salt, 0))
    return cursor.lastrowid


@with_db_connection
def login_user(cursor, username, password):
    """用户登录验证"""
    cursor.execute(LOGIN_USER_COMMAND, (username,))
    user = cursor.fetchone()

    if not user:
        return None

    # 验证密码
    hashed_pw = hash_password(password, user["salt"])
    if hashed_pw == user["password"]:
        return user["id"]
    return None


@with_db_connection
def create_bar(cursor, bar_name, owner_id):
    """创建贴吧"""
    cursor.execute(INSERT_BAR_COMMAND, (bar_name, owner_id))
    bar_id = cursor.lastrowid

    # 用户自动关注自己创建的贴吧
    cursor.execute(INSERT_USER_BAR_COMMAND, (owner_id, bar_id))

    return bar_id


@with_db_connection
def create_post(cursor, bar_id, title, content, author_id):
    """创建帖子"""
    cursor.execute(INSERT_POST_COMMAND, (bar_id, title, content, author_id))
    post_id = cursor.lastrowid

    # 发帖增加经验值
    cursor.execute(ADD_USER_EXP_COMMAND, (10, author_id))

    return post_id


@with_db_connection
def create_comment(cursor, post_id, content, author_id, reply_to_user=None):
    """创建评论"""
    cursor.execute(INSERT_COMMENT_COMMAND, (post_id, content, author_id, reply_to_user))
    comment_id = cursor.lastrowid

    # 评论增加经验值
    cursor.execute(ADD_USER_EXP_COMMAND, (5, author_id))

    return comment_id


@with_db_connection
def like_comment(cursor, comment_id):
    """点赞评论"""
    cursor.execute(LIKE_COMMENT_COMMAND, (comment_id,))

    # 点赞增加经验值（给评论作者）
    cursor.execute("SELECT author_id FROM comments WHERE id = %s", (comment_id,))
    comment = cursor.fetchone()
    if comment:
        cursor.execute(ADD_USER_EXP_COMMAND, (1, comment["author_id"]))

    return True


@with_db_connection
def get_bar_by_name(cursor, bar_name):
    """根据名称获取贴吧信息"""
    cursor.execute(GET_BAR_BY_NAME_COMMAND, (bar_name,))
    return cursor.fetchone()


@with_db_connection
def get_post_by_id(cursor, post_id):
    """根据ID获取帖子信息"""
    cursor.execute(GET_POST_BY_ID_COMMAND, (post_id,))
    return cursor.fetchone()


@with_db_connection
def get_user_by_id(cursor, user_id):
    """根据ID获取用户信息"""
    cursor.execute(GET_USER_BY_ID_COMMAND, (user_id,))
    return cursor.fetchone()


@with_db_connection
def get_posts_in_bar(cursor, bar_id, page=1, per_page=20):
    """获取贴吧的帖子列表（分页）"""
    offset = (page - 1) * per_page
    cursor.execute(GET_POSTS_IN_BAR_COMMAND, (bar_id, per_page, offset))
    return cursor.fetchall()


@with_db_connection
def get_comments_in_post(cursor, post_id, page=1, per_page=50):
    """获取帖子的评论列表（分页）"""
    offset = (page - 1) * per_page
    cursor.execute(GET_COMMENTS_IN_POST_COMMAND, (post_id, per_page, offset))
    return cursor.fetchall()


@with_db_connection
def get_hot_bars(cursor, limit=10):
    """获取热门贴吧"""
    cursor.execute(GET_HOT_BARS_COMMAND, (limit,))
    return cursor.fetchall()


@with_db_connection
def get_user_bars(cursor, user_id):
    """获取用户关注的贴吧"""
    cursor.execute(GET_USER_BARS_COMMAND, (user_id,))
    return cursor.fetchall()


@with_db_connection
def reset_all_dbs(cursor):
    cursor.execute("DROP TABLE IF EXISTS comments")
    cursor.execute("DROP TABLE IF EXISTS posts")
    cursor.execute("DROP TABLE IF EXISTS bars")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS user_bars")

    cursor.execute(CREATE_TABLE_USER_COMMAND)
    cursor.execute(CREATE_TABLE_BARS_COMMAND)
    cursor.execute(CREATE_TABLE_POSTS_COMMAND)
    cursor.execute(CREATE_TABLE_COMMENTS_COMMAND)
    cursor.execute(CREATE_TABLE_USER_BARS_COMMAND)

    cursor.execute(
        INSERT_USER_COMMAND,
        ("?", "testUser", hash_password("testPassword", "testSalt"), "testSalt", 100),
    )
