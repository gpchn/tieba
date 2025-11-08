#!/usr/bin/env python3
# coding=utf-8

import webview
from pathlib import Path
import db
import json
import os


ROOT_DIR = Path(__file__).parent
STATIC_DIR = ROOT_DIR / "static"
USER_DATA_DIR = ROOT_DIR / "userdata"


class Api:
    def __init__(self):
        # 简单的内存会话，仅用于桌面应用示例
        self.current_user_id = None
        self.session_file = str(USER_DATA_DIR / "session.json")  # 转换为字符串
        # 确保用户数据目录存在
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        # 初始化时尝试加载已保存的会话
        self._load_session()

    def _load_session(self):
        """从文件加载会话信息并尝试自动登录"""
        try:
            if os.path.exists(self.session_file):  # 使用os.path.exists替代Path.exists
                with open(self.session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    username = session_data.get("username")
                    password = session_data.get("password")

                    if username and password:
                        # 尝试自动登录
                        user_id = db.login_user(username, password)  # type: ignore
                        if user_id:
                            self.current_user_id = user_id
                            return {
                                "success": True,
                                "auto_login": True,
                                "user_id": user_id,
                            }
                        else:
                            # 密码错误，清除会话
                            os.remove(self.session_file)
                            return {
                                "success": False,
                                "error": "保存的密码已失效，请重新登录",
                            }
        except Exception as e:
            print(f"加载会话失败: {e}")
            self.current_user_id = None
        return {"success": False, "error": "未找到有效的登录信息"}

    def _save_session(self, username, password):
        """保存用户名和密码到文件"""
        try:
            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump({"username": username, "password": password}, f)
        except Exception as e:
            print(f"保存会话失败: {e}")

    def _ensure_logged_in(self):
        if not self.current_user_id:
            raise RuntimeError("not_logged_in")

    def login(self, username, password):
        """用户登录，成功后返回 {success: True, user_id: id} 或 {success: False, error: msg}"""
        user_id = db.login_user(username, password)  # type: ignore
        if user_id:
            self.current_user_id = user_id
            # 保存用户名和密码以便自动登录
            self._save_session(username, password)
            return {"success": True, "user_id": user_id}
        else:
            return {"success": False, "error": "用户名或密码错误"}

    def register(self, username, password):
        """用户注册，返回 {success: True, user_id} 或 {success: False, error}"""
        user_id = db.register_user(username, password)  # type: ignore
        return {"success": True, "user_id": user_id}

    def logout(self):
        self.current_user_id = None
        # 清除保存的会话
        try:
            if os.path.exists(self.session_file):  # 使用os.path.exists替代Path.exists
                os.remove(self.session_file)  # 使用os.remove替代Path.unlink
        except Exception as e:
            print(f"清除会话失败: {e}")
        return {"success": True}

    def getCurrentUser(self):
        """获取当前用户信息或 null"""
        if not self.current_user_id:
            return None
        user = db.get_user_by_id(self.current_user_id)  # type: ignore
        return user

    def getAutoLoginStatus(self):
        """获取自动登录状态"""
        return self._load_session()

    def createBar(self, name):
        """创建贴吧（需要登录）"""
        self._ensure_logged_in()
        bar_id = db.create_bar(name, self.current_user_id)  # type: ignore
        return {"success": True, "bar_id": bar_id}

    def getBarByName(self, name):
        return db.get_bar_by_name(name)  # type: ignore

    def createPost(self, bar_id, title, content):
        self._ensure_logged_in()
        post_id = db.create_post(bar_id, title, content, self.current_user_id)  # type: ignore
        return {"success": True, "post_id": post_id}

    def getPostById(self, post_id):
        post = db.get_post_by_id(post_id)  # type: ignore
        if not post:
            return None

        # 获取点赞数
        try:
            post["likes"] = db.get_post_likes(post_id)["likes"]  # type: ignore
        except:
            post["likes"] = 0

        # 如果用户已登录，检查是否已点赞该帖子
        if self.current_user_id:
            try:
                post["is_liked"] = db.check_post_liked(self.current_user_id, post_id)  # type: ignore
            except:
                post["is_liked"] = False
        else:
            post["is_liked"] = False

        comments = db.get_comments_in_post(post_id, page=1, per_page=100, user_id=self.current_user_id)  # type: ignore
        post["comments"] = comments
        return post

    def createComment(self, post_id, content, reply_to=None):
        self._ensure_logged_in()
        comment_id = db.create_comment(post_id, content, self.current_user_id, reply_to)  # type: ignore
        return {"success": True, "comment_id": comment_id}

    def likeComment(self, comment_id):
        self._ensure_logged_in()
        result = db.like_comment(self.current_user_id, comment_id)  # type: ignore
        return result

    def toggleLike(self, post_id):
        """切换帖子点赞状态（点赞或取消点赞）"""
        self._ensure_logged_in()
        result = db.toggle_post_like(self.current_user_id, post_id)  # type: ignore
        return result

    def getUserById(self, user_id):
        return db.get_user_by_id(user_id)  # type: ignore

    def getPostsInBar(self, bar_id, page=1, per_page=20):
        posts = db.get_posts_in_bar(bar_id, page, per_page, self.current_user_id)  # type: ignore
        return posts

    def getCommentsInPost(self, post_id, page=1, per_page=50):
        return db.get_comments_in_post(post_id, page, per_page, user_id=self.current_user_id)

    def getHotBars(self, limit=10):
        return db.get_hot_bars(limit)

    def getFollowedBars(self):
        if not self.current_user_id:
            return []
        return db.get_user_bars(self.current_user_id)  # type: ignore

    def followBar(self, bar_id):
        """关注贴吧（需要登录）"""
        self._ensure_logged_in()
        result = db.follow_bar(self.current_user_id, bar_id)  # type: ignore
        return {"success": result}

    def unfollowBar(self, bar_id):
        """取消关注贴吧（需要登录）"""
        self._ensure_logged_in()
        result = db.unfollow_bar(self.current_user_id, bar_id)  # type: ignore
        return {"success": result}

    def getStats(self):
        """获取社区统计信息"""
        return db.get_stats()  # type: ignore

    def getLatestPosts(self, page=1, per_page=20):
        """获取最新帖子（分页）"""
        return db.get_latest_posts(page, per_page, self.current_user_id)  # type: ignore
        
    def searchPosts(self, query):
        """搜索帖子"""
        if not query or not query.strip():
            return []
        return db.search_posts(query.strip(), self.current_user_id)  # type: ignore


main_window = webview.create_window(
    title="Tieba",
    url=f"file://{STATIC_DIR}/index.html",
    js_api=Api(),
    height=800,
    width=1200,
)

if __name__ == "__main__":
    webview.start(http_server=True, debug=True)
