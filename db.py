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

# 用户点赞帖子表
CREATE_TABLE_POST_LIKES_COMMAND = """
    CREATE TABLE IF NOT EXISTS post_likes (
        user_id INT NOT NULL,
        post_id INT NOT NULL,
        PRIMARY KEY (user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (post_id) REFERENCES posts(id)
    );
"""

# 用户点赞评论表
CREATE_TABLE_COMMENT_LIKES_COMMAND = """
    CREATE TABLE IF NOT EXISTS comment_likes (
        user_id INT NOT NULL,
        comment_id INT NOT NULL,
        PRIMARY KEY (user_id, comment_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (comment_id) REFERENCES comments(id)
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

# 取消关注贴吧
DELETE_USER_BAR_COMMAND = """
DELETE FROM user_bars WHERE user_id = %s AND bar_id = %s
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

# 取消点赞评论
UNLIKE_COMMENT_COMMAND = """
UPDATE comments
SET likes = likes - 1
WHERE id = %s
"""

# 检查用户是否已点赞评论
CHECK_COMMENT_LIKED_COMMAND = """
SELECT COUNT(*) as liked FROM comment_likes WHERE user_id = %s AND comment_id = %s
"""

# 点赞评论记录
INSERT_COMMENT_LIKE_COMMAND = """
INSERT INTO comment_likes (user_id, comment_id) VALUES (%s, %s)
"""

# 取消点赞评论记录
DELETE_COMMENT_LIKE_COMMAND = """
DELETE FROM comment_likes WHERE user_id = %s AND comment_id = %s
"""

# 获取评论点赞数
GET_COMMENT_LIKES_COMMAND = """
SELECT COUNT(*) as likes FROM comment_likes WHERE comment_id = %s
"""

# 检查用户是否已点赞帖子
CHECK_POST_LIKED_COMMAND = """
SELECT COUNT(*) as liked FROM post_likes WHERE user_id = %s AND post_id = %s
"""

# 点赞帖子
LIKE_POST_COMMAND = """
INSERT INTO post_likes (user_id, post_id) VALUES (%s, %s)
"""

# 取消点赞帖子
UNLIKE_POST_COMMAND = """
DELETE FROM post_likes WHERE user_id = %s AND post_id = %s
"""

# 获取帖子点赞数
GET_POST_LIKES_COMMAND = """
SELECT COUNT(*) as likes FROM post_likes WHERE post_id = %s
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
SELECT p.id, p.bar_id, p.title, p.content, p.author_id, p.create_time, u.name as author_name
FROM posts p
JOIN users u ON p.author_id = u.id
WHERE p.id = %s
"""

# 查询用户
GET_USER_BY_ID_COMMAND = """
SELECT id, type, name, exp FROM users WHERE id = %s
"""

# 查询贴吧的所有帖子
GET_POSTS_IN_BAR_COMMAND = """
SELECT p.id, p.title, p.author_id, p.create_time, p.content, u.name as author_name
FROM posts p
JOIN users u ON p.author_id = u.id
WHERE p.bar_id = %s
ORDER BY p.create_time DESC
LIMIT %s OFFSET %s
"""

# 查询帖子的所有评论
GET_COMMENTS_IN_POST_COMMAND = """
SELECT c.id, c.content, c.author_id, c.create_time, c.likes, u.name as author_name
FROM comments c
JOIN users u ON c.author_id = u.id
WHERE c.post_id = %s
ORDER BY c.create_time ASC
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
    cursor.execute(CREATE_TABLE_POST_LIKES_COMMAND)
    cursor.execute(CREATE_TABLE_COMMENT_LIKES_COMMAND)
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
def like_comment(cursor, user_id, comment_id):
    """切换评论点赞状态（点赞或取消点赞）"""
    # 检查用户是否已点赞该评论
    cursor.execute(CHECK_COMMENT_LIKED_COMMAND, (user_id, comment_id))
    is_liked = cursor.fetchone()["liked"] > 0

    if is_liked:
        # 已点赞，则取消点赞
        cursor.execute(DELETE_COMMENT_LIKE_COMMAND, (user_id, comment_id))
        cursor.execute(UNLIKE_COMMENT_COMMAND, (comment_id,))
        result = {"is_liked": False}
    else:
        # 未点赞，则点赞
        cursor.execute(INSERT_COMMENT_LIKE_COMMAND, (user_id, comment_id))
        cursor.execute(LIKE_COMMENT_COMMAND, (comment_id,))
        # 点赞增加经验值（给评论作者）
        cursor.execute("SELECT author_id FROM comments WHERE id = %s", (comment_id,))
        comment = cursor.fetchone()
        if comment:
            cursor.execute(ADD_USER_EXP_COMMAND, (1, comment["author_id"]))
        result = {"is_liked": True}

    # 获取更新后的点赞数
    cursor.execute(GET_COMMENT_LIKES_COMMAND, (comment_id,))
    likes_count = cursor.fetchone()["likes"]
    result["likes"] = likes_count
    result["success"] = True

    return result


@with_db_connection
def toggle_post_like(cursor, user_id, post_id):
    """切换帖子点赞状态（点赞或取消点赞）"""
    # 检查用户是否已点赞该帖子
    cursor.execute(CHECK_POST_LIKED_COMMAND, (user_id, post_id))
    is_liked = cursor.fetchone()["liked"] > 0

    if is_liked:
        # 已点赞，则取消点赞
        cursor.execute(UNLIKE_POST_COMMAND, (user_id, post_id))
        result = {"is_liked": False}
    else:
        # 未点赞，则点赞
        cursor.execute(LIKE_POST_COMMAND, (user_id, post_id))
        # 点赞增加经验值（给帖子作者）
        cursor.execute("SELECT author_id FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        if post:
            cursor.execute(ADD_USER_EXP_COMMAND, (2, post["author_id"]))
        result = {"is_liked": True}

    # 获取更新后的点赞数
    cursor.execute(GET_POST_LIKES_COMMAND, (post_id,))
    likes_count = cursor.fetchone()["likes"]
    result["likes"] = likes_count
    result["success"] = True

    return result


@with_db_connection
def check_post_liked(cursor, user_id, post_id):
    """检查用户是否已点赞该帖子"""
    cursor.execute(CHECK_POST_LIKED_COMMAND, (user_id, post_id))
    is_liked = cursor.fetchone()["liked"] > 0
    return is_liked


@with_db_connection
def get_post_likes(cursor, post_id):
    """获取帖子的点赞数"""
    cursor.execute(GET_POST_LIKES_COMMAND, (post_id,))
    return cursor.fetchone()


@with_db_connection
def get_bar_by_name(cursor, bar_name):
    """根据名称获取贴吧信息"""
    cursor.execute(GET_BAR_BY_NAME_COMMAND, (bar_name,))
    return cursor.fetchone()


@with_db_connection
def get_post_by_id(cursor, post_id):
    """根据ID获取帖子信息"""
    cursor.execute(GET_POST_BY_ID_COMMAND, (post_id,))
    post = cursor.fetchone()

    if not post:
        return None

    # 转换datetime对象为字符串
    if "create_time" in post and hasattr(post["create_time"], "strftime"):
        post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")

    return post


@with_db_connection
def get_user_by_id(cursor, user_id):
    """根据ID获取用户信息"""
    cursor.execute(GET_USER_BY_ID_COMMAND, (user_id,))
    return cursor.fetchone()


@with_db_connection
def get_posts_in_bar(cursor, bar_id, page=1, per_page=20, user_id=None):
    """获取贴吧的帖子列表（分页）"""
    offset = (page - 1) * per_page
    cursor.execute(GET_POSTS_IN_BAR_COMMAND, (bar_id, per_page, offset))
    posts = cursor.fetchall()

    # 为每个帖子添加点赞数和当前用户是否已点赞
    for post in posts:
        # 转换datetime对象为字符串
        if "create_time" in post and hasattr(post["create_time"], "strftime"):
            post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")

        # 获取点赞数
        cursor.execute(GET_POST_LIKES_COMMAND, (post["id"],))
        post["likes"] = cursor.fetchone()["likes"]

        # 如果提供了用户ID，检查用户是否已点赞该帖子
        if user_id is not None:
            cursor.execute(CHECK_POST_LIKED_COMMAND, (user_id, post["id"]))
            post["is_liked"] = cursor.fetchone()["liked"] > 0
        else:
            post["is_liked"] = False

        # 获取评论数
        cursor.execute(
            "SELECT COUNT(*) as count FROM comments WHERE post_id = %s", (post["id"],)
        )
        post["comments_count"] = cursor.fetchone()["count"]

    return posts


@with_db_connection
def get_comments_in_post(cursor, post_id, page=1, per_page=50, user_id=None):
    """获取帖子的评论列表（分页）"""
    offset = (page - 1) * per_page
    cursor.execute(GET_COMMENTS_IN_POST_COMMAND, (post_id, per_page, offset))
    comments = cursor.fetchall()

    # 转换datetime对象为字符串
    for comment in comments:
        if "create_time" in comment and hasattr(comment["create_time"], "strftime"):
            comment["create_time"] = comment["create_time"].strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        
        # 获取点赞数
        cursor.execute(GET_COMMENT_LIKES_COMMAND, (comment["id"],))
        comment["likes"] = cursor.fetchone()["likes"]
        
        # 如果提供了用户ID，检查用户是否已点赞该评论
        if user_id is not None:
            cursor.execute(CHECK_COMMENT_LIKED_COMMAND, (user_id, comment["id"]))
            comment["liked_by_user"] = cursor.fetchone()["liked"] > 0
        else:
            comment["liked_by_user"] = False

    return comments


@with_db_connection
def get_hot_bars(cursor, limit=10):
    """获取热门贴吧"""
    cursor.execute(GET_HOT_BARS_COMMAND, (limit,))
    bars = cursor.fetchall()

    # 转换datetime对象为字符串
    for bar in bars:
        if "create_time" in bar and hasattr(bar["create_time"], "strftime"):
            bar["create_time"] = bar["create_time"].strftime("%Y-%m-%d %H:%M:%S")

    return bars


@with_db_connection
def get_user_bars(cursor, user_id):
    """获取用户关注的贴吧"""
    cursor.execute(GET_USER_BARS_COMMAND, (user_id,))
    bars = cursor.fetchall()

    # 转换datetime对象为字符串
    for bar in bars:
        if "create_time" in bar and hasattr(bar["create_time"], "strftime"):
            bar["create_time"] = bar["create_time"].strftime("%Y-%m-%d %H:%M:%S")

    return bars


@with_db_connection
def follow_bar(cursor, user_id, bar_id):
    """用户关注贴吧"""
    try:
        cursor.execute(INSERT_USER_BAR_COMMAND, (user_id, bar_id))
        return True
    except Exception:
        # 可能已经关注
        return False


@with_db_connection
def unfollow_bar(cursor, user_id, bar_id):
    """用户取消关注贴吧"""
    cursor.execute(DELETE_USER_BAR_COMMAND, (user_id, bar_id))
    return cursor.rowcount > 0


@with_db_connection
def get_stats(cursor):
    """获取社区统计信息"""
    stats = {}

    # 获取帖子总数
    cursor.execute("SELECT COUNT(*) as count FROM posts")
    stats["posts"] = cursor.fetchone()["count"]

    # 获取用户总数
    cursor.execute("SELECT COUNT(*) as count FROM users")
    stats["users"] = cursor.fetchone()["count"]

    # 获取评论总数
    cursor.execute("SELECT COUNT(*) as count FROM comments")
    stats["comments"] = cursor.fetchone()["count"]

    # 获取今日发帖数
    cursor.execute(
        "SELECT COUNT(*) as count FROM posts WHERE DATE(create_time) = CURDATE()"
    )
    stats["today_posts"] = cursor.fetchone()["count"]

    # 获取今日注册用户数
    cursor.execute(
        "SELECT COUNT(*) as count FROM users WHERE DATE(CURRENT_TIMESTAMP) = CURDATE()"
    )
    stats["today_users"] = cursor.fetchone()["count"]

    return stats


@with_db_connection
def search_posts(cursor, query, user_id=None):
    """搜索帖子（标题和内容）"""
    # 构建搜索查询
    search_query = f"%{query}%"
    
    # 搜索帖子
    cursor.execute("""
    SELECT p.id, p.title, p.content, p.bar_id, p.author_id, p.create_time,
           b.name as bar_name, u.name as author_name
    FROM posts p
    JOIN bars b ON p.bar_id = b.id
    JOIN users u ON p.author_id = u.id
    WHERE p.title LIKE %s OR p.content LIKE %s
    ORDER BY p.create_time DESC
    LIMIT 100
    """, (search_query, search_query))
    
    posts = cursor.fetchall()
    
    # 为每个帖子添加点赞数和当前用户是否已点赞
    for post in posts:
        # 转换datetime对象为字符串
        if "create_time" in post and hasattr(post["create_time"], "strftime"):
            post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        
        # 获取点赞数
        cursor.execute(GET_POST_LIKES_COMMAND, (post["id"],))
        post["likes"] = cursor.fetchone()["likes"]
        
        # 如果提供了用户ID，检查用户是否已点赞该帖子
        if user_id is not None:
            cursor.execute(CHECK_POST_LIKED_COMMAND, (user_id, post["id"]))
            post["is_liked"] = cursor.fetchone()["liked"] > 0
        else:
            post["is_liked"] = False
        
        # 获取评论数
        cursor.execute(
            "SELECT COUNT(*) as count FROM comments WHERE post_id = %s", (post["id"],)
        )
        post["comments_count"] = cursor.fetchone()["count"]
    
    return posts


@with_db_connection
def get_latest_posts(cursor, page=1, per_page=20, user_id=None):
    """获取最新帖子列表（分页）"""
    offset = (page - 1) * per_page

    # 查询最新帖子，并关联贴吧名称和用户名
    query = """
    SELECT p.id, p.title, p.content, p.bar_id, p.author_id, p.create_time,
           b.name as bar_name, u.name as author_name
    FROM posts p
    JOIN bars b ON p.bar_id = b.id
    JOIN users u ON p.author_id = u.id
    ORDER BY p.create_time DESC
    LIMIT %s OFFSET %s
    """

    cursor.execute(query, (per_page, offset))
    posts = cursor.fetchall()

    # 为每个帖子添加点赞数和当前用户是否已点赞
    for post in posts:
        # 转换datetime对象为字符串
        if "create_time" in post and hasattr(post["create_time"], "strftime"):
            post["create_time"] = post["create_time"].strftime("%Y-%m-%d %H:%M:%S")

        # 获取点赞数
        cursor.execute(GET_POST_LIKES_COMMAND, (post["id"],))
        post["likes"] = cursor.fetchone()["likes"]

        # 如果提供了用户ID，检查用户是否已点赞该帖子
        if user_id is not None:
            cursor.execute(CHECK_POST_LIKED_COMMAND, (user_id, post["id"]))
            post["is_liked"] = cursor.fetchone()["liked"] > 0
        else:
            post["is_liked"] = False

        # 获取评论数
        cursor.execute(
            "SELECT COUNT(*) as count FROM comments WHERE post_id = %s", (post["id"],)
        )
        post["comments_count"] = cursor.fetchone()["count"]

    return posts


@with_db_connection
def reset_all_dbs(cursor):
    # 不要修改删除顺序，有依赖
    for table in ("post_likes", "user_bars", "comments", "posts", "bars", "users"):
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    cursor.execute(CREATE_TABLE_USER_COMMAND)
    cursor.execute(CREATE_TABLE_BARS_COMMAND)
    cursor.execute(CREATE_TABLE_POSTS_COMMAND)
    cursor.execute(CREATE_TABLE_COMMENTS_COMMAND)
    cursor.execute(CREATE_TABLE_USER_BARS_COMMAND)
    cursor.execute(CREATE_TABLE_POST_LIKES_COMMAND)
    cursor.execute(CREATE_TABLE_COMMENT_LIKES_COMMAND)

    cursor.execute(
        INSERT_USER_COMMAND,
        ("U", "testUser", hash_password("testPassword", "testSalt"), "testSalt", 100),
    )
