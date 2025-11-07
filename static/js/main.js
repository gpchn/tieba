let currentUser = null;

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
  const ul = document.getElementById("hot-bars");
  ul.innerHTML = "";
  for (const b of bars) {
    const li = document.createElement("li");
    li.className = "bar-item";
    li.innerHTML = `<div class="bar-name">${escapeHtml(
      b.name
    )}</div><div class="bar-count">${b.post_count || 0}</div>`;
    li.onclick = () => loadPostsInBar(b.id);
    ul.appendChild(li);
  }
  // also populate post-bar select
  const sel = document.getElementById("post-bar");
  if (sel) {
    sel.innerHTML = "";
    for (const b of bars) {
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
    li.textContent = b.name;
    li.onclick = () => loadPostsInBar(b.id);
    ul.appendChild(li);
  }
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
    const avatar = p.author_id ? p.author_id.charAt(0).toUpperCase() : "U";

    // 格式化时间
    const timeStr = formatTime(p.create_time);

    div.innerHTML = `
      <div class="post-header">
        <div class="post-avatar">${avatar}</div>
        <div class="post-meta">
          <div class="post-author">${escapeHtml(
            p.author_id || "匿名用户"
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
  // 显示简单 detail 窗口
  const html = [
    `<h3>${escapeHtml(post.title)}</h3>`,
    `<div class="meta">作者:${post.author_id} · ${post.create_time}</div>`,
    `<div class="content">${escapeHtml(post.content)}</div>`,
    `<h4>评论</h4>`,
  ];
  for (const c of post.comments || []) {
    html.push(
      `<div class="comment">${escapeHtml(c.content)} <div class="meta">by ${
        c.author_id
      } · ${c.create_time} · 点赞 ${c.likes}</div></div>`
    );
  }
  const w = window.open("", "_blank");
  w.document.write(html.join("\n"));
}

async function submitComment(postId, content) {
  const r = await window.pywebview.api.createComment(postId, content, null);
  if (r && r.success) showNotification("评论成功", "success");
  else showNotification("评论失败:" + (r && r.error), "error");
}

async function likeComment(commentId) {
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
  const name = prompt("贴吧名称");
  if (!name) return;
  const r = await window.pywebview.api.createBar(name);
  if (r.success) {
    showNotification("创建成功");
    loadHotBars();
  } else showNotification("创建失败:" + (r.error || ""));
}

async function submitPost() {
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
}

// 页面加载完成后初始化
window.addEventListener("pywebviewready", initApp);
