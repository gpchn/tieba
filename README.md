# 四中贴吧

一个基于Python和Web技术构建的桌面贴吧应用，提供用户注册、登录、发帖、评论等功能。

## 功能特点

- 用户注册与登录
- 创建和管理贴吧
- 发布帖子
- 评论和点赞功能
- 热门贴吧展示
- 用户关注贴吧
- 现代化的用户界面

## 技术栈

- 后端：Python
- 数据库：MySQL
- 前端：HTML、CSS、JavaScript
- 桌面应用：PyWebView

## 安装与运行

### 环境要求

- Python 3.12+

### 安装依赖

```bash
# 使用uv安装依赖
uv sync
```

### 运行应用

```bash
python main.py
```

## 项目结构

```
tieba/
├── README.md         # 项目说明文档
├── main.py           # 应用入口文件
├── db.py             # 数据库操作模块
├── pyproject.toml    # 项目依赖配置
├── static/           # 静态资源目录
│   ├── css/
│   │   └── main.css  # 样式文件
│   ├── js/
│   │   └── main.js   # 前端交互逻辑
│   └── index.html    # 主页面
└── uv.lock           # 依赖锁定文件
```

## 开发与贡献

欢迎提交问题报告和功能请求。如果您想贡献代码，请先创建一个issue描述您的想法，然后提交一个pull request。

## 许可证

本项目采用 Apache 2.0 许可证。
