#!/usr/bin/env python3
# coding=utf-8

import webview
from pathlib import Path
import db


ROOT_DIR = Path(__file__).parent
STATIC_DIR = ROOT_DIR / "static"
USER_DATA_DIR = ROOT_DIR / "userdata"


class Api:
    def __init__(self):
        # 简单的内存会话，仅用于桌面应用示例
        self.current_user_id = None

    def _ensure_logged_in(self):
        if not self.current_user_id:
            raise RuntimeError("not_logged_in")

    def login(self, username, password):
        """用户登录，成功后返回 {success: True, user_id: id} 或 {success: False, error: msg}"""
        user_id = db.login_user(username, password)  # type: ignore
        if user_id:
            self.current_user_id = user_id
            return {"success": True, "user_id": user_id}
        else:
            return {"success": False, "error": "用户名或密码错误"}

    def register(self, username, password):
        """用户注册，返回 {success: True, user_id} 或 {success: False, error}"""
        user_id = db.register_user(username, password)  # type: ignore
        return {"success": True, "user_id": user_id}

    def logout(self):
        self.current_user_id = None
        return {"success": True}

    def getCurrentUser(self):
        """获取当前用户信息或 null"""
        if not self.current_user_id:
            return None
        user = db.get_user_by_id(self.current_user_id)  # type: ignore
        return user

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
        comments = db.get_comments_in_post(post_id, page=1, per_page=100)  # type: ignore
        post["comments"] = comments
        return post

    def createComment(self, post_id, content, reply_to=None):
        self._ensure_logged_in()
        comment_id = db.create_comment(post_id, content, self.current_user_id, reply_to)  # type: ignore
        return {"success": True, "comment_id": comment_id}

    def likeComment(self, comment_id):
        self._ensure_logged_in()
        db.like_comment(comment_id)  # type: ignore
        return {"success": True}

    def getUserById(self, user_id):
        return db.get_user_by_id(user_id)  # type: ignore

    def getPostsInBar(self, bar_id, page=1, per_page=20):
        posts = db.get_posts_in_bar(bar_id, page, per_page)
        return posts

    def getCommentsInPost(self, post_id, page=1, per_page=50):
        return db.get_comments_in_post(post_id, page, per_page)

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
        return db.get_latest_posts(page, per_page)  # type: ignore


main_window = webview.create_window(
    title="Tieba",
    url=f"file://{STATIC_DIR}/index.html",
    js_api=Api(),
    height=800,
    width=1200,
)

if __name__ == "__main__":
    webview.start(http_server=True, debug=True)
