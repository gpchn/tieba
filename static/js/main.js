let currentUser = null;
let currentPostId = null;

function showNotification(message, type = "info") {
  const n = document.getElementById("notification");
  n.textContent = message;
  n.style.display = "block";
  n.className = "notification " + type;
  setTimeout(() => (n.style.display = "none"), 3000);
}

function showModal(modalId) {
  hideAllModals();
  const m = document.getElementById(modalId);
  if (m) m.style.display = "block";
}

function hideAllModals() {
  document
    .querySelectorAll(".modal")
    .forEach((m) => (m.style.display = "none"));
}

async function loadHotBars() {
  const bars = await window.pywebview.api.getHotBars(20);
  const userBars = await window.pywebview.api.getFollowedBars();
  console.log("获取到的用户关注贴吧:", userBars);
  const userBarIds = userBars && userBars.length > 0 ? new Set(userBars.map(b => b.id)) : new Set();

  // 检查用户是否登录
  const currentUser = await window.pywebview.api.getCurrentUser();
  const isLoggedIn = !!currentUser;
  console.log("用户登录状态:", isLoggedIn, "当前用户:", currentUser);

  const ul = document.getElementById("hot-bars");
  ul.innerHTML = "";
  for (const b of bars) {
    const li = document.createElement("li");
    li.className = "bar-item";

    // 根据登录状态和关注状态显示不同按钮
    let buttonHtml = "";
    if (isLoggedIn) {
      const isFollowed = userBarIds.has(b.id);
      buttonHtml = isFollowed 
        ? `<button class="btn-unfollow" onclick="unfollowBar(${b.id})">取消关注</button>`
        : `<button class="btn-follow" onclick="followBar(${b.id})">关注</button>`;
    } else {
      buttonHtml = `<button class="btn-follow" onclick="showLoginPrompt()">关注</button>`;
    }

    li.innerHTML = `<div class="bar-name">${escapeHtml(
      b.name
    )}</div><div class="bar-count">${
      b.post_count || 0
    }</div>${buttonHtml}`;
    li.onclick = (e) => {
      if (e.target.className !== "btn-follow" && e.target.className !== "btn-unfollow") {
        loadPostsInBar(b.id);
      }
    };
    ul.appendChild(li);
  }
  // also populate post-bar select with only followed bars
  const sel = document.getElementById("post-bar");
  if (sel) {
    sel.innerHTML = "";
    for (const b of userBars) {  // 只显示已关注的贴吧
      const opt = document.createElement("option");
      opt.value = b.id;
      opt.text = b.name;
      sel.appendChild(opt);
    }
  }
}

async function loadUserBars() {
  const bars = await window.pywebview.api.getFollowedBars();
  const ul = document.getElementById("user-bars");
  ul.innerHTML = "";
  for (const b of bars) {
    const li = document.createElement("li");
    li.className = "bar-item small";
    li.innerHTML = `<div class="bar-name">${escapeHtml(
      b.name
    )}</div><button class="btn-unfollow" onclick="unfollowBar(${
      b.id
    })">取消关注</button>`;
    li.onclick = (e) => {
      if (e.target.className !== "btn-unfollow") {
        loadPostsInBar(b.id);
      }
    };
    ul.appendChild(li);
  }
}

async function loadStats() {
  const stats = await window.pywebview.api.getStats();
  if (stats) {
    document.getElementById("stat-posts").textContent = formatNumber(stats.posts || 0);
    document.getElementById("stat-users").textContent = formatNumber(stats.users || 0);
    document.getElementById("stat-comments").textContent = formatNumber(stats.comments || 0);
  }
}

function formatNumber(num) {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + "万";
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + "k";
  }
  return num.toString();
}

function showLoginPrompt() {
  showNotification("请先登录后再进行此操作", "warning");
  setTimeout(() => {
    showModal("modal-login");
  }, 1000);
}

async function loadPostsInBar(barId) {
  const posts = await window.pywebview.api.getPostsInBar(barId, 1, 50);
  renderPosts(posts, barId);
}

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return "";
  try {
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now - date;

    // 如果小于1分钟
    if (diff < 60000) {
      return "刚刚";
    }
    // 如果小于1小时
    if (diff < 3600000) {
      return Math.floor(diff / 60000) + "分钟前";
    }
    // 如果小于1天
    if (diff < 86400000) {
      return Math.floor(diff / 3600000) + "小时前";
    }
    // 如果小于7天
    if (diff < 604800000) {
      return Math.floor(diff / 86400000) + "天前";
    }

    // 否则返回具体日期
    return date.toLocaleDateString();
  } catch (e) {
    return timeStr;
  }
}

function renderPosts(posts, barId) {
  const container = document.getElementById("posts-list");
  container.innerHTML = "";
  if (!posts || posts.length === 0) {
    container.innerHTML =
      "<div class='empty-state'><i class='fas fa-inbox'></i><p>暂无帖子</p></div>";
    return;
  }
  for (const p of posts) {
    const div = document.createElement("div");
    div.className = "post";

    // 获取用户名首字母作为头像
    const avatar = p.author_name ? p.author_name.charAt(0).toUpperCase() : "U";

    // 格式化时间
    const timeStr = formatTime(p.create_time);

    div.innerHTML = `
      <div class="post-header">
        <div class="post-avatar">${avatar}</div>
        <div class="post-meta">
          <div class="post-author">${escapeHtml(
            p.author_name || "匿名用户"
          )}</div>
          <div class="post-time">${timeStr}</div>
        </div>
      </div>
      <h3 class="post-title">${escapeHtml(p.title)}</h3>
      <div class="post-content">${escapeHtml(
        p.content
          ? p.content.slice(0, 200) + (p.content.length > 200 ? "..." : "")
          : ""
      )}</div>
      <div class="post-footer">
        <div class="post-stats">
          <span class="stat"><i class="fas fa-comment"></i> ${
            p.comment_count || 0
          }</span>
          <span class="stat"><i class="fas fa-heart"></i> ${
            p.like_count || 0
          }</span>
        </div>
        <div class="post-actions">
          <button class="btn btn-primary" onclick="openPost(${p.id})">
            <i class="fas fa-arrow-right"></i> 查看详情
          </button>
        </div>
      </div>`;
    container.appendChild(div);
  }
}

function escapeHtml(s) {
  if (!s) return "";
  return s.replace(
    /[&<>\"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

async function openPost(postId) {
  const post = await window.pywebview.api.getPostById(postId);
  if (!post) {
    showNotification("帖子不存在", "error");
    return;
  }

  currentPostId = postId;

  // 填充帖子详情
  // 填充帖子详情
  document.getElementById("detail-title").textContent = escapeHtml(post.title);
  document.getElementById(
    "detail-author"
  ).textContent = `作者: ${post.author_name || post.author_id}`;
  document.getElementById("detail-time").textContent = post.create_time;
  document.getElementById("detail-content").textContent = post.content;

  // 显示评论
  const commentsList = document.getElementById("comments-list");
  commentsList.innerHTML = "";
  if (post.comments && post.comments.length > 0) {
    for (const c of post.comments) {
      const commentDiv = document.createElement("div");
      commentDiv.className = "comment";

      // 创建评论内容区域
      const contentDiv = document.createElement("div");
      contentDiv.className = "comment-content";
      contentDiv.textContent = escapeHtml(c.content);
      commentDiv.appendChild(contentDiv);

      // 创建评论元信息区域
      const metaDiv = document.createElement("div");
      metaDiv.className = "comment-meta";

      // 创建作者信息部分
      const authorDiv = document.createElement("div");
      authorDiv.className = "comment-author";
      authorDiv.innerHTML = `${c.author_name}<span class="comment-time">${c.create_time}</span>`;
      metaDiv.appendChild(authorDiv);

      // 创建操作按钮部分
      const actionsDiv = document.createElement("div");
      actionsDiv.className = "comment-actions";

      // 添加点赞按钮
      const likeBtn = document.createElement("button");
      likeBtn.className = "comment-like-btn";

      // 检查当前用户是否已点赞此评论
      const isLiked = c.liked_by_user || false;
      if (isLiked) {
        likeBtn.classList.add("liked");
        likeBtn.innerHTML = `<i class="fas fa-thumbs-up"></i> 已点赞`;
      } else {
        likeBtn.innerHTML = `<i class="far fa-thumbs-up"></i> 点赞`;
      }

      likeBtn.onclick = () => likeComment(c.id);
      actionsDiv.appendChild(likeBtn);

      // 添加点赞数
      const likesSpan = document.createElement("span");
      likesSpan.className = "comment-likes";
      likesSpan.textContent = `${c.likes || 0}`;
      actionsDiv.insertBefore(likesSpan, actionsDiv.firstChild);

      metaDiv.appendChild(actionsDiv);

      commentDiv.appendChild(metaDiv);
      commentsList.appendChild(commentDiv);
    }
  } else {
    commentsList.innerHTML = "<p>暂无评论</p>";
  }
  // 显示帖子详情模态框
  showModal("modal-post-detail");
  (("\n"));
}

async function submitComment(postId, content) {
  // 检查用户是否登录
  if (!currentUser) {
    showLoginPrompt();
    return;
  }

  const r = await window.pywebview.api.createComment(postId, content, null);
  if (r && r.success) {
    showNotification("评论成功", "success");
    // 重新加载帖子详情以显示新评论
    openPost(postId);
  }
  else showNotification("评论失败:" + (r && r.error), "error");
}

async function submitCommentAction() {
  // 获取评论内容
  const content = document.getElementById("comment-content").value.trim();

  // 检查评论内容是否为空
  if (!content) {
    showNotification("请输入评论内容", "error");
    return;
  }

  // 调用submitComment函数
  await submitComment(currentPostId, content);

  // 清空评论框
  document.getElementById("comment-content").value = "";
}

async function likeComment(commentId) {
  // 检查用户是否登录
  if (!currentUser) {
    showLoginPrompt();
    return;
  }

  const r = await window.pywebview.api.likeComment(commentId);
  if (r && r.success) showNotification("已点赞");
  else showNotification("点赞失败");
}

async function login() {
  const u = document.getElementById("login-username").value.trim();
  const p = document.getElementById("login-password").value;
  const r = await window.pywebview.api.login(u, p);
  if (r.success) {
    currentUser = await window.pywebview.api.getCurrentUser();
    document.getElementById("btn-login").style.display = "none";
    document.getElementById("btn-register").style.display = "none";
    document.getElementById("btn-logout").style.display = "inline-block";
    hideAllModals();
    loadUserBars();
    showNotification("登录成功", "success");
  } else {
    showNotification("登录失败: " + (r.error || ""), "error");
  }
}

async function register() {
  const u = document.getElementById("register-username").value.trim();
  const p = document.getElementById("register-password").value;
  const r = await window.pywebview.api.register(u, p);
  if (r.success) {
    hideAllModals();
    showNotification("注册成功，请登录");
  } else showNotification("注册失败: " + (r.error || ""), "error");
}

function logout() {
  window.pywebview.api.logout();
  currentUser = null;
  document.getElementById("btn-login").style.display = "inline-block";
  document.getElementById("btn-register").style.display = "inline-block";
  document.getElementById("btn-logout").style.display = "none";
  showNotification("已退出");
}

async function createBar() {
  showModal("modal-create-bar");
}

async function submitCreateBar() {
  // 检查用户是否登录
  if (!currentUser) {
    showLoginPrompt();
    return;
  }

  const name = document.getElementById("bar-name").value.trim();
  if (!name) {
    showNotification("贴吧名称不能为空", "error");
    return;
  }

  const r = await window.pywebview.api.createBar(name);
  if (r.success) {
    showNotification("创建成功", "success");
    hideAllModals();
    loadHotBars();
    // 清空表单
    document.getElementById("bar-name").value = "";
    document.getElementById("bar-description").value = "";
  } else {
    showNotification("创建失败: " + (r.error || ""), "error");
  }
}

async function followBar(barId) {
  if (!currentUser) {
    showLoginPrompt();
    return;
  }
  const r = await window.pywebview.api.followBar(barId);
  if (r && r.success) {
    showNotification("关注成功", "success");
    loadUserBars();
  } else {
    showNotification("关注失败", "error");
  }
}

async function unfollowBar(barId) {
  if (!currentUser) {
    showNotification("请先登录", "error");
    return;
  }
  const r = await window.pywebview.api.unfollowBar(barId);
  if (r && r.success) {
    showNotification("已取消关注", "success");
    loadUserBars();
  } else {
    showNotification("取消关注失败", "error");
  }
}

async function submitPost() {
  // 检查用户是否登录
  if (!currentUser) {
    showLoginPrompt();
    return;
  }

  const barId = document.getElementById("post-bar").value;
  const title = document.getElementById("post-title").value.trim();
  const content = document.getElementById("post-content").value.trim();
  if (!title || !content) {
    showNotification("标题与内容不能为空", "error");
    return;
  }
  const r = await window.pywebview.api.createPost(
    parseInt(barId),
    title,
    content
  );
  if (r.success) {
    hideAllModals();
    showNotification("发帖成功");
    loadPostsInBar(barId);
  } else showNotification("发帖失败:" + (r.error || ""));
}

function search() {
  showNotification("搜索尚未实现");
}

async function loadLatestPosts() {
  const posts = await window.pywebview.api.getLatestPosts(1, 20);
  renderPosts(posts, null);
}

async function initApp() {
  // 绑定按钮
  document.getElementById("btn-login").onclick = () => showModal("modal-login");
  document.getElementById("btn-register").onclick = () =>
    showModal("modal-register");
  document.getElementById("btn-logout").onclick = logout;
  document.getElementById("login-submit").onclick = login;
  document.getElementById("register-submit").onclick = register;
  document.getElementById("btn-new-post").onclick = () =>
    showModal("modal-post");
  document.getElementById("post-submit").onclick = submitPost;
  document.getElementById("btn-create-bar").onclick = createBar;
  document.getElementById("create-bar-submit").onclick = submitCreateBar;
  document.getElementById("comment-submit").onclick = submitCommentAction;

  // load initial state
  try {
    currentUser = await window.pywebview.api.getCurrentUser();
    if (currentUser) {
      document.getElementById("btn-login").style.display = "none";
      document.getElementById("btn-register").style.display = "none";
      document.getElementById("btn-logout").style.display = "inline-block";
      loadUserBars();
    }
  } catch (e) {
    console.error(e);
  }
  await loadHotBars();
  await loadStats();
  await loadLatestPosts();
}

// 页面加载完成后初始化
window.addEventListener("pywebviewready", initApp);
