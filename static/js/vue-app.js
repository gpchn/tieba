// Vue应用初始化
const { createApp, ref, reactive, computed, onMounted } = Vue;

// 全局变量跟踪Vue应用状态
window.vueAppStatus = {
  initialized: false,
  mounted: false,
  error: null
};

const TiebaApp = {
  setup() {
    // 状态管理
    const state = reactive({
      // 用户信息
      currentUser: null,

      // 模态框状态
      modals: {
        login: false,
        register: false,
        post: false,
        postDetail: false,
        createBar: false
      },

      // 数据
      hotBars: [],
      userBars: [],
      posts: [],
      currentPost: null,
      comments: [],
      currentBar: null, // 当前选中的贴吧
      stats: {
        posts: 0,
        users: 0,
        comments: 0
      }
    });

    // 表单数据
    const loginForm = reactive({
      username: '',
      password: ''
    });

    const registerForm = reactive({
      username: '',
      password: ''
    });

    const postForm = reactive({
      barId: '',
      title: '',
      content: ''
    });

    const createBarForm = reactive({
      name: '',
      description: ''
    });

    const commentForm = reactive({
      content: ''
    });

    const searchQuery = ref('');

    // 计算属性
    const isLoggedIn = computed(() => !!state.currentUser);

    // 工具函数
    const escapeHtml = (s) => {
      if (!s) return "";
      return s.replace(
        /[&<>"]/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
      );
    };
    
    // 显示贴吧名称，自动添加'吧'字
    const displayBarName = (name) => {
      if (!name) return '';
      // 如果名称已经以'吧'结尾，直接返回
      if (name.endsWith('吧')) return name;
      // 否则添加'吧'字
      return name + '吧';
    };

    const formatNumber = (num) => {
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + "万";
      } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + "k";
      }
      return num.toString();
    };

    const formatTime = (timeStr) => {
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
    };

    const showNotification = (message, type = "info") => {
      const n = document.getElementById("notification");
      n.textContent = message;
      n.style.display = "block";
      n.className = "notification " + type;
      setTimeout(() => (n.style.display = "none"), 3000);
    };

    // 模态框控制
    const showModal = (modalName) => {
      console.log("showModal called with:", modalName);
      // 关闭所有模态框
      Object.keys(state.modals).forEach(key => {
        state.modals[key] = false;
      });
      // 打开指定模态框
      state.modals[modalName] = true;
      console.log("Modal state after showModal:", state.modals);
    };

    const hideAllModals = () => {
      Object.keys(state.modals).forEach(key => {
        state.modals[key] = false;
      });
    };

    // 判断贴吧是否已关注
    const isBarFollowed = (barId) => {
      return state.userBars.some(bar => bar.id === barId);
    };

    // API调用函数
    const loadHotBars = async () => {
      try {
        const bars = await window.pywebview.api.getHotBars(20);
        const userBars = await window.pywebview.api.getFollowedBars();
        state.hotBars = bars;
        state.userBars = userBars;
      } catch (error) {
        console.error("加载热门贴吧失败:", error);
        showNotification("加载热门贴吧失败", "error");
      }
    };

    const loadUserBars = async () => {
      try {
        const bars = await window.pywebview.api.getFollowedBars();
        state.userBars = bars;
      } catch (error) {
        console.error("加载用户关注贴吧失败:", error);
        showNotification("加载用户关注贴吧失败", "error");
      }
    };

    const loadStats = async () => {
      try {
        const stats = await window.pywebview.api.getStats();
        state.stats = stats || { posts: 0, users: 0, comments: 0 };
      } catch (error) {
        console.error("加载统计数据失败:", error);
      }
    };

    const loadLatestPosts = async () => {
      try {
        const posts = await window.pywebview.api.getLatestPosts(1, 20);
        state.posts = posts || [];
        // 更新页面标题
        document.querySelector('.page-title').textContent = '最新帖子';
        // 更新按钮激活状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
          btn.classList.remove('active');
        });
        document.querySelector('.filter-btn:first-child').classList.add('active');
      } catch (error) {
        console.error("加载最新帖子失败:", error);
        showNotification("加载最新帖子失败", "error");
      }
    };

    const loadHotPosts = async () => {
      try {
        const posts = await window.pywebview.api.getHotPosts(1, 20);
        state.posts = posts || [];
        // 更新页面标题
        document.querySelector('.page-title').textContent = '热门帖子';
        // 更新按钮激活状态
        document.querySelectorAll('.filter-btn').forEach(btn => {
          btn.classList.remove('active');
        });
        document.querySelector('.filter-btn:nth-child(2)').classList.add('active');
        showNotification("已加载热门帖子", "success");
      } catch (error) {
        console.error("加载热门帖子失败:", error);
        showNotification("加载热门帖子失败", "error");
      }
    };

    const refreshPosts = async () => {
      // 添加旋转动画类
      const refreshBtn = document.querySelector('.refresh-btn i');
      if (refreshBtn) {
        refreshBtn.classList.add('fa-spin');
      }
      
      try {
        // 获取当前页面标题，判断当前是哪种帖子列表
        const pageTitle = document.querySelector('.page-title').textContent;
        
        if (pageTitle.includes('最新')) {
          await loadLatestPosts();
        } else if (pageTitle.includes('热门')) {
          await loadHotPosts();
        } else {
          // 默认加载最新帖子
          await loadLatestPosts();
        }
        
        showNotification("帖子已刷新", "success");
      } catch (error) {
        console.error("刷新帖子失败:", error);
        showNotification("刷新帖子失败", "error");
      } finally {
        // 移除旋转动画类
        if (refreshBtn) {
          setTimeout(() => {
            refreshBtn.classList.remove('fa-spin');
          }, 500);
        }
      }
    };

    const loadPostsInBar = async (barId) => {
      try {
        // 查找贴吧信息
        const bar = state.userBars.find(b => b.id === barId) || 
                   state.hotBars.find(b => b.id === barId);
        
        if (bar) {
          // 设置当前贴吧
          state.currentBar = bar;
        }
        
        const posts = await window.pywebview.api.getPostsInBar(barId, 1, 50);
        state.posts = posts || [];
      } catch (error) {
        console.error("加载贴吧帖子失败:", error);
        showNotification("加载贴吧帖子失败", "error");
      }
    };
    
    const backToLatestPosts = () => {
      // 清除当前贴吧
      state.currentBar = null;
      // 加载最新帖子
      loadLatestPosts();
    };

    const openPost = async (postId) => {
      console.log("openPost called with postId:", postId);
      try {
        console.log("Calling getPostById API...");
        const post = await window.pywebview.api.getPostById(postId);
        console.log("Received post:", post);
        if (!post) {
          showNotification("帖子不存在", "error");
          return;
        }

        state.currentPost = post;
        state.comments = post.comments || [];
        console.log("Opening post detail modal...");
        showModal('postDetail');
      } catch (error) {
        console.error("加载帖子详情失败:", error);
        showNotification("加载帖子详情失败", "error");
      }
    };

    // 用户认证相关函数
    const submitLogin = async () => {
      if (!loginForm.username || !loginForm.password) {
        showNotification("用户名和密码不能为空", "error");
        return;
      }

      try {
        const result = await window.pywebview.api.login(loginForm.username, loginForm.password);
        if (result.success) {
          state.currentUser = await window.pywebview.api.getCurrentUser();
          showNotification("登录成功", "success");
          hideAllModals();
          loadUserBars();
          loadHotBars();

          // 清空表单
          loginForm.username = '';
          loginForm.password = '';
        } else {
          showNotification("登录失败: " + (result.error || ""), "error");
        }
      } catch (error) {
        console.error("登录失败:", error);
        showNotification("登录失败", "error");
      }
    };

    const submitRegister = async () => {
      if (!registerForm.username || !registerForm.password) {
        showNotification("用户名和密码不能为空", "error");
        return;
      }

      try {
        const result = await window.pywebview.api.register(registerForm.username, registerForm.password);
        if (result.success) {
          showNotification("注册成功，请登录", "success");
          hideAllModals();
          showModal('login');

          // 清空表单
          registerForm.username = '';
          registerForm.password = '';
        } else {
          showNotification("注册失败: " + (result.error || ""), "error");
        }
      } catch (error) {
        console.error("注册失败:", error);
        showNotification("注册失败", "error");
      }
    };

    const logout = async () => {
      try {
        await window.pywebview.api.logout();
        state.currentUser = null;
        state.userBars = [];
        showNotification("已退出");
      } catch (error) {
        console.error("退出登录失败:", error);
        showNotification("退出登录失败", "error");
      }
    };

    // 贴吧相关函数
    const followBar = async (barId) => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "warning");
        showModal('login');
        return;
      }

      try {
        const result = await window.pywebview.api.followBar(barId);
        if (result && result.success) {
          showNotification("关注成功", "success");
          loadUserBars();
          loadHotBars();
        } else {
          showNotification("关注失败", "error");
        }
      } catch (error) {
        console.error("关注贴吧失败:", error);
        showNotification("关注贴吧失败", "error");
      }
    };

    const unfollowBar = async (barId) => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "error");
        return;
      }

      try {
        const result = await window.pywebview.api.unfollowBar(barId);
        if (result && result.success) {
          showNotification("已取消关注", "success");
          loadUserBars();
          loadHotBars();
        } else {
          showNotification("取消关注失败", "error");
        }
      } catch (error) {
        console.error("取消关注失败:", error);
        showNotification("取消关注失败", "error");
      }
    };

    const submitCreateBar = async () => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "warning");
        showModal('login');
        return;
      }

      if (!createBarForm.name.trim()) {
        showNotification("贴吧名称不能为空", "error");
        return;
      }
      
      // 确保贴吧名称不以'吧'结尾
      let barName = createBarForm.name.trim();
      if (barName.endsWith('吧')) {
        barName = barName.slice(0, -1);
        createBarForm.name = barName;
      }

      try {
        const result = await window.pywebview.api.createBar(barName);
        if (result.success) {
          showNotification("创建成功", "success");
          hideAllModals();
          loadHotBars();

          // 清空表单
          createBarForm.name = '';
          createBarForm.description = '';
        } else {
          showNotification("创建失败: " + (result.error || ""), "error");
        }
      } catch (error) {
        console.error("创建贴吧失败:", error);
        showNotification("创建贴吧失败", "error");
      }
    };

    // 帖子相关函数
    const openPostInBar = (barId) => {
      // 设置当前贴吧ID
      postForm.barId = barId;
      
      // 显示发帖模态框
      showModal('post');
    };

    const submitPost = async () => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "warning");
        showModal('login');
        return;
      }

      if (!postForm.title.trim() || !postForm.content.trim()) {
        showNotification("标题与内容不能为空", "error");
        return;
      }

      try {
        const result = await window.pywebview.api.createPost(
          parseInt(postForm.barId),
          postForm.title,
          postForm.content
        );
        if (result.success) {
          showNotification("发帖成功", "success");
          hideAllModals();
          loadPostsInBar(postForm.barId);

          // 清空表单
          postForm.barId = '';
          postForm.title = '';
          postForm.content = '';
        } else {
          showNotification("发帖失败: " + (result.error || ""), "error");
        }
      } catch (error) {
        console.error("发帖失败:", error);
        showNotification("发帖失败", "error");
      }
    };

    // 评论相关函数
    const submitComment = async () => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "warning");
        showModal('login');
        return;
      }

      if (!commentForm.content.trim()) {
        showNotification("评论内容不能为空", "error");
        return;
      }

      try {
        const result = await window.pywebview.api.createComment(
          state.currentPost.id,
          commentForm.content,
          null
        );
        if (result.success) {
          showNotification("评论成功", "success");
          // 重新加载帖子详情以显示新评论
          openPost(state.currentPost.id);

          // 清空表单
          commentForm.content = '';
        } else {
          showNotification("评论失败: " + (result.error || ""), "error");
        }
      } catch (error) {
        console.error("评论失败:", error);
        showNotification("评论失败", "error");
      }
    };

    const likeComment = async (commentId) => {
      if (!isLoggedIn.value) {
        showNotification("请先登录", "warning");
        showModal('login');
        return;
      }

      try {
        const result = await window.pywebview.api.likeComment(commentId);
        if (result && result.success) {
          showNotification("已点赞");
          // 重新加载评论以更新点赞状态
          openPost(state.currentPost.id);
        } else {
          showNotification("点赞失败", "error");
        }
      } catch (error) {
        console.error("点赞失败:", error);
        showNotification("点赞失败", "error");
      }
    };

    // 搜索函数
    const search = () => {
      showNotification("搜索功能尚未实现", "info");
    };
    
    // 打开创建贴吧模态框
    const createBar = () => {
      showModal('createBar');
    };

    // 初始化应用
    const initApp = async () => {
      try {
        // 加载用户信息
        state.currentUser = await window.pywebview.api.getCurrentUser();

        // 加载数据
        await Promise.all([
          loadHotBars(),
          loadStats(),
          loadLatestPosts(),
          isLoggedIn.value ? loadUserBars() : Promise.resolve()
        ]);
      } catch (error) {
        console.error("初始化应用失败:", error);
        showNotification("初始化应用失败", "error");
      }
    };

    // 生命周期钩子
    onMounted(() => {
      // 如果pywebview已经准备好，立即初始化
      if (window.pywebview && window.pywebview.api) {
        initApp();
      } else {
        // 否则等待pywebview准备好
        window.addEventListener("pywebviewready", initApp);
      }
    });

    // 返回所有需要在模板中使用的变量和函数
    return {
      // 状态
      state,

      // 表单数据
      loginForm,
      registerForm,
      postForm,
      createBarForm,
      commentForm,
      searchQuery,

      // 计算属性
      isLoggedIn,

      // 工具函数
      escapeHtml,
      displayBarName,
      formatNumber,
      formatTime,

      // 模态框控制
      showModal,
      hideAllModals,

      // 判断函数
      isBarFollowed,

      // 数据加载函数
      loadPostsInBar,
      loadLatestPosts,
      loadHotPosts,
      refreshPosts,
      openPost,
      openPostInBar,
      backToLatestPosts,

      // 用户认证函数
      submitLogin,
      submitRegister,
      logout,

      // 贴吧相关函数
      followBar,
      unfollowBar,
      submitCreateBar,

      // 帖子相关函数
      submitPost,

      // 评论相关函数
      submitComment,
      likeComment,

      // 搜索函数
      search,
      
      // 打开创建贴吧模态框
      createBar,
      

    };
  }
};

// 创建Vue应用
// 确保DOM加载完成后再挂载Vue应用
document.addEventListener('DOMContentLoaded', () => {
  console.log("DOM loaded, creating Vue app...");
  window.vueAppStatus.initialized = true;
  
  try {
    // 创建Vue应用实例但不立即挂载
    const app = createApp(TiebaApp);
    
    // 等待pywebview准备好后再挂载
    if (window.pywebview && window.pywebview.api) {
      // pywebview已经准备好，直接挂载
      console.log("pywebview ready, mounting Vue app...");
      app.mount('#app');
      window.vueAppStatus.mounted = true;
      
      // 隐藏加载动画
      setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
          loadingScreen.style.opacity = '0';
          setTimeout(() => {
            loadingScreen.style.display = 'none';
          }, 500); // 等待淡出动画完成
        }
      }, 500); // 延迟一点时间，让应用完全加载
    } else {
      // 监听pywebviewready事件，然后挂载应用
      console.log("Waiting for pywebview to be ready...");
      window.addEventListener('pywebviewready', () => {
        console.log("pywebviewready event fired, mounting Vue app...");
        app.mount('#app');
        window.vueAppStatus.mounted = true;
        
        // 隐藏加载动画
        setTimeout(() => {
          const loadingScreen = document.getElementById('loading-screen');
          if (loadingScreen) {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
              loadingScreen.style.display = 'none';
            }, 500); // 等待淡出动画完成
          }
        }, 500); // 延迟一点时间，让应用完全加载
      });
    }
  } catch (error) {
    console.error("Failed to initialize Vue app:", error);
    window.vueAppStatus.error = error;
    
    // 即使出错也要隐藏加载动画，避免用户卡在加载界面
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.style.opacity = '0';
      setTimeout(() => {
        loadingScreen.style.display = 'none';
      }, 500);
    }
  }
});
