<script setup>
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { marked } from "marked";
import {
  useAssistant,
  formatSessionTime,
} from "../composables/useAssistant.js";
import { useUserStore } from "../stores/userStore.js";
import AiBadge from "../components/AiBadge.vue";

const router = useRouter();
const assistant = useAssistant();
const userStore = useUserStore();

const inputText = ref("");
const isLoading = ref(false);
const sidebarOpen = ref(false);
const messagesEl = ref(null);
const landingInput = ref(null);
const searchQuery = ref("");

/**
 * 两态界面：
 *   home —— 主页面，居中提问入口，像 DeepSeek 首页
 *   chat —— 对话页，左侧历史记录 + 中间问答区
 * 用户在主页面发出第一条消息（或点开历史）后进入 chat。
 */
const view = ref("home");

// 直接绑定 composable 的模块级响应式状态，切页/刷新保持同一份数据
const sessions = computed(() => assistant.getSessions());
const activeId = computed({
  get: () => assistant.state.activeId,
  set: (v) => assistant.setActive(v),
});
const activeSession = computed(() => assistant.getActiveSession());
const hasMessages = computed(
  () => (activeSession.value?.messages.length ?? 0) > 0,
);

// 教师场景示例提问：点一下就能直接问，避免"打开后不知道问什么"
const SUGGESTIONS = [
  "《函数的单调性》这节课怎么设计导入？",
  "学生总把质数和奇数搞混，怎么讲清楚？",
  "帮我梳理这篇文言文的教学重难点",
  "基础薄弱的学生，作业该怎么分层布置？",
];

function groupSessions(list) {
  const grouped = assistant.groupSessionsByDate(list);
  return [
    { key: "today", label: "今天", items: grouped.today },
    { key: "yesterday", label: "昨天", items: grouped.yesterday },
    { key: "earlier", label: "更早", items: grouped.earlier },
  ].filter((group) => group.items.length);
}

const groupedSections = computed(() => groupSessions(sessions.value));

// 历史检索：标题命中或任一条消息正文命中都算匹配
const filteredSections = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return groupedSections.value;
  const matched = sessions.value.filter((s) => {
    if ((s.title || "").toLowerCase().includes(q)) return true;
    return (s.messages || []).some((m) =>
      (m.content || "").toLowerCase().includes(q),
    );
  });
  return groupSessions(matched);
});

function backHome() {
  view.value = "home";
  sidebarOpen.value = false;
  nextTick(() => landingInput.value?.focus());
}

// 主页面点「历史记录」：进入对话页；若已有会话但未选中，直接打开最近一条
function openHistory() {
  view.value = "chat";
  if (!activeId.value && sessions.value.length) {
    assistant.setActive(sessions.value[0].id);
    scrollToBottom();
  }
}

function handleNewChat() {
  assistant.setActive(null);
  inputText.value = "";
  view.value = "home";
  sidebarOpen.value = false;
  nextTick(() => landingInput.value?.focus());
}

function selectSession(id) {
  assistant.setActive(id);
  view.value = "chat";
  sidebarOpen.value = false;
  scrollToBottom();
}

function handleDeleteSession(id) {
  assistant.deleteSession(id);
  // 删完没有会话了，回主页面重新开始
  if (!sessions.value.length) {
    view.value = "home";
  }
}

async function handleSend(text = inputText.value) {
  const content = (text || inputText.value).trim();
  if (!content || isLoading.value) return;

  inputText.value = "";
  isLoading.value = true;
  // 立刻切到对话页，让用户第一时间看到自己的提问与 AI 打字反馈
  view.value = "chat";
  scrollToBottom();

  try {
    if (!activeId.value) {
      const session = assistant.createSession();
      activeId.value = session.id;
    }
    await assistant.sendMessage(content, {
      onDelta: () => scrollToBottom(),
    });
  } finally {
    isLoading.value = false;
  }
  await nextTick();
  scrollToBottom();
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });
}

function onKeydown(e) {
  // 回车发送，Shift+回车换行
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}

/**
 * 清洗 AI 输出中偶发的 LaTeX 标记，转成教师可读的 Unicode 形式。
 * 约定：AI 应已禁用 LaTeX，此为兜底，避免原始命令暴露造成乱码。
 */
function cleanLatex(text) {
  if (!text) return text;
  // 行内公式定界符：\( ... \) 与 $ ... $（含双 $$）→ 去掉定界符保留内容
  text = text.replace(
    /\$\$([\s\S]*?)\$\$|\\\(([\s\S]*?)\\\)|\$([^$\n]*?)\$/g,
    (m, a, b, c) => (a ?? b ?? c ?? "").trim(),
  );
  // 一次替换尽量覆盖常用 LaTeX 命令（先长后短，避免误伤）
  const map = [
    [/\\(?:times|c\?dot)/g, "×"],
    [/\\(?:cdots|ldots)/g, "…"],
    [/\\(?:cdot)/g, "·"],
    [/\\(?:frac)\{([^{}]*)\}\{([^{}]*)\}/g, (m, a, b) => `${a}/${b}`],
    [/\\(?:ne)/g, "≠"],
    [/\\(?:leq|le)/g, "≤"],
    [/\\(?:geq|ge)/g, "≥"],
    [/\\(?:approx|approxeq)/g, "≈"],
    [/\\(?:pm)/g, "±"],
    [/\\(?:infty)/g, "∞"],
    [/\\(?:times)/g, "×"],
    [/\\(?:sum)/g, "Σ"],
    [/\\(?:prod)/g, "∏"],
    [/\\(?:triangle)/g, "△"],
    [/\\(?:rightarrow|to)/g, "→"],
    [/\\(?:Rightarrow)/g, "⇒"],
    [/\\(?:leftrightarrow)/g, "↔"],
    [/\\(?:subseteq)/g, "⊆"],
    [/\\(?:cup)/g, "∪"],
    [/\\(?:cap)/g, "∩"],
    [/\\(?:forall)/g, "∀"],
    [/\\(?:exists)/g, "∃"],
    [/\\(?:partial)/g, "∂"],
    [/\\(?:alpha)/g, "α"],
    [/\\(?:beta)/g, "β"],
    [/\\(?:theta)/g, "θ"],
    [/\\(?:lambda)/g, "λ"],
    [/\\(?:sqrt)\{([^{}]*)\}/g, "√($1)"],
    [/\\(?:text)\{([^{}]*)\}/g, "$1"],
    [/\\(?:mathrm|mathbf|mathit|mbox)\{([^{}]*)\}/g, "$1"],
    [/\\(?:left|right)/g, ""],
    [/\\(?:big|Big|bigg|Bigg)(?:[lrg])?/g, ""],
    [/\\(?:qquad|quad)\{?[^{}]*\}?/g, "　"],
    [/\\(?:;|:|,|!)/g, " "],
    [/\\(?:cmidrule|hline|rule)/g, ""],
  ];
  for (const [re, rep] of map) {
    text = text.replace(re, rep);
  }
  // 下角标 m_1 → m₁；上角标 x^2 → x²（仅处理单字符下标，避免误伤普通 _）
  text = text.replace(/_([a-zA-Z0-9])\b/g, (m, c) => c);
  text = text.replace(/\^(\d)\b/g, (m, d) => mapSuperscript(d));
  // 清理残余的孤立反斜杠命令（去掉反斜杠本身，保留英文），防乱码
  text = text.replace(/\\[a-zA-Z]+/g, (m) => m.slice(1));
  return text;
}

function mapSuperscript(d) {
  return (
    {
      0: "⁰",
      1: "¹",
      2: "²",
      3: "³",
      4: "⁴",
      5: "⁵",
      6: "⁶",
      7: "⁷",
      8: "⁸",
      9: "⁹",
    }[d] || d
  );
}

function renderMarkdown(text) {
  const cleaned = cleanLatex(text);
  let html = marked(cleaned, { breaks: true, gfm: true });
  html = html.replace(
    /→\[([^\]]+)\]\((\/[^)]+)\)/g,
    '<a href="javascript:;" class="internal-link" data-path="$2">$1 →</a>',
  );
  return html;
}

function copyMessage(text) {
  navigator.clipboard.writeText(text);
}

function regenerate(msg) {
  const msgs = activeSession.value?.messages;
  if (!msgs) return;
  const idx = msgs.indexOf(msg);
  for (let i = idx - 1; i >= 0; i--) {
    if (msgs[i].role === "user") {
      msgs.splice(i);
      handleSend(msgs[i].content);
      break;
    }
  }
}

function rateMessage(msg, type) {
  msg.rated = type;
}

function togglePin(id) {
  assistant.pinSession(id);
}

function handleInternalLink(e) {
  const link = e.target.closest(".internal-link");
  if (link) {
    e.preventDefault();
    const path = link.getAttribute("data-path");
    if (path) router.push(path);
  }
}

onMounted(() => {
  // 进入页面先给主页面，不自动加载历史会话
  assistant.setActive(null);
  nextTick(() => landingInput.value?.focus());
});

watch(activeId, scrollToBottom);
</script>

<template>
  <div class="assistant-page">
    <!-- ══════════════ 主页面（DeepSeek 式提问入口） ══════════════ -->
    <div v-if="view === 'home'" class="landing">
      <header class="landing__bar">
        <RouterLink to="/" class="ghost-btn" title="返回主页">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M12 4l-6 6 6 6"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          返回主页
        </RouterLink>

        <button class="ghost-btn" @click="openHistory">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <circle
              cx="10"
              cy="10"
              r="7.4"
              stroke="currentColor"
              stroke-width="1.5"
            />
            <path
              d="M10 6v4.2l3 1.8"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
          历史记录
          <span v-if="sessions.length" class="ghost-btn__count">{{
            sessions.length
          }}</span>
        </button>
      </header>

      <div class="landing__body">
        <div class="landing__brand">
          <span class="landing__logo">
            <svg viewBox="0 0 40 40" fill="none" aria-hidden="true">
              <rect width="40" height="40" rx="10" fill="url(#landing-ai-g)" />
              <path
                d="M12 11c0-.55.45-1 1-1h6c.55 0 1 .45 1 1v16c0 .55-.45 1-1 1H13c-.55 0-1-.45-1-1V11z"
                fill="rgba(255,255,255,0.9)"
              />
              <path
                d="M20 11c0-.55.45-1 1-1h6c.55 0 1 .45 1 1v16c0 .55-.45 1-1 1h-6c-.55 0-1-.45-1-1V11z"
                fill="rgba(255,255,255,0.55)"
              />
              <rect
                x="19"
                y="11"
                width="2"
                height="16"
                rx="0.5"
                fill="rgba(255,255,255,0.2)"
              />
              <circle cx="31" cy="11" r="3" fill="#FDE68A" />
              <defs>
                <linearGradient
                  id="landing-ai-g"
                  x1="0"
                  y1="0"
                  x2="40"
                  y2="40"
                >
                  <stop stop-color="#2563EB" />
                  <stop stop-color="#1D4ED8" />
                </linearGradient>
              </defs>
            </svg>
          </span>
          <h1 class="landing__title">教师 AI 助手</h1>
          <p class="landing__desc">
            面向中小学教师的专业问答助手。聊的是课标、教材、课堂与学生，
            不闲聊、不跑题，给的是明天能直接用的教学建议。
          </p>
        </div>

        <div class="composer composer--lg">
          <textarea
            ref="landingInput"
            v-model="inputText"
            class="composer__input"
            rows="1"
            placeholder="向 AI 助教提问，例如：这节课的重难点该怎么确定？"
            aria-label="向 AI 助教提问"
            name="assistant-query-home"
            :disabled="isLoading"
            @keydown="onKeydown"
          ></textarea>
          <button
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
            aria-label="发送问题"
            @click="handleSend()"
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M4 10l12-6-2 6 2 6-12-6z" fill="currentColor" />
            </svg>
          </button>
        </div>

        <div class="chips">
          <button
            v-for="s in SUGGESTIONS"
            :key="s"
            class="chip"
            @click="handleSend(s)"
          >
            {{ s }}
          </button>
        </div>

        <p class="landing__foot">
          <span>对话由</span>
          <AiBadge name="qwen" size="sm" />
          <span>驱动 · 记录仅保存在本地浏览器</span>
        </p>
      </div>
    </div>

    <!-- ══════════════ 对话页（左历史 + 中问答） ══════════════ -->
    <div v-else class="chat-layout" @click="handleInternalLink">
      <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
        <div class="sidebar__top">
          <button class="new-chat-btn" @click="handleNewChat">
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M10 4v12M4 10h12"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
              />
            </svg>
            新对话
          </button>
          <RouterLink
            to="/"
            class="back-home-btn"
            title="返回主页"
            aria-label="返回主页"
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M3 10l7-6 7 6M5 9v6.5h10V9"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
            返回主页
          </RouterLink>
        </div>

        <div class="sidebar-search">
          <svg
            class="sidebar-search__icon"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="M21 21l-4.35-4.35" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索历史对话…"
            aria-label="搜索历史对话"
            autocomplete="off"
            name="assistant-search"
            class="sidebar-search__input"
          />
        </div>

        <div class="sidebar__history">
          <section
            v-for="group in filteredSections"
            :key="group.key"
            class="history-group"
          >
            <p class="history-label">{{ group.label }}</p>

            <div
              v-for="session in group.items"
              :key="session.id"
              class="history-row"
              :class="{ 'history-row--active': session.id === activeId }"
            >
              <button class="history-item" @click="selectSession(session.id)">
                <span class="history-item__icon">
                  <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path
                      d="M4 6a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3H9l-3 3v-3H7a3 3 0 0 1-3-3V6z"
                      stroke="currentColor"
                      stroke-width="1.4"
                    />
                  </svg>
                </span>
                <span class="history-item__content">
                  <strong>{{ session.title }}</strong>
                  <small>{{ formatSessionTime(session.updatedAt) }}</small>
                </span>
              </button>

              <button
                class="history-pin"
                title="置顶/取消置顶"
                aria-label="置顶或取消置顶"
                @click.stop="togglePin(session.id)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  :stroke="session.isPinned ? '#2563eb' : 'currentColor'"
                  stroke-width="2"
                  stroke-linecap="round"
                  aria-hidden="true"
                >
                  <path
                    d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2z"
                  />
                </svg>
              </button>

              <button
                class="history-delete"
                title="删除对话"
                aria-label="删除对话"
                @click.stop="handleDeleteSession(session.id)"
              >
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M6 6l8 8M14 6l-8 8"
                    stroke="currentColor"
                    stroke-width="1.6"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>
          </section>

          <p v-if="!filteredSections.length" class="sidebar__empty">
            {{ sessions.length ? "没有匹配的对话" : "还没有对话记录" }}
          </p>
        </div>

        <div class="sidebar__foot">
          <svg viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path
              d="M8 1L2 4v4c0 3.3 2.6 6.4 6 7 3.4-.6 6-3.7 6-7V4L8 1z"
              stroke="currentColor"
              stroke-width="1.2"
            />
          </svg>
          对话记录仅保存在本地
        </div>
      </aside>

      <div
        v-if="sidebarOpen"
        class="sidebar-overlay"
        @click="sidebarOpen = false"
      />

      <main class="conversation">
        <header class="conversation__bar">
          <button
            class="icon-btn icon-btn--drawer"
            aria-label="打开历史记录"
            @click="sidebarOpen = true"
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path
                d="M3 5h14M3 10h14M3 15h14"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
              />
            </svg>
          </button>
          <span class="conversation__title">{{
            activeSession?.title || "新对话"
          }}</span>
          <AiBadge name="qwen" size="sm" />
        </header>

        <div v-if="hasMessages" ref="messagesEl" class="messages">
          <div
            v-for="(msg, index) in activeSession?.messages"
            :key="msg.id"
            class="message"
            :class="`message--${msg.role}`"
          >
            <div class="message__avatar">
              <!-- AI 助手头像 -->
              <span
                v-if="msg.role === 'assistant'"
                class="avatar-icon ai-avatar"
              >
                <svg
                  viewBox="0 0 32 32"
                  fill="none"
                  aria-hidden="true"
                  class="ai-avatar-svg"
                >
                  <rect width="32" height="32" rx="8" fill="url(#chat-ai-g)" />
                  <path
                    d="M10 9c0-.55.45-1 1-1h4.5c.55 0 1 .45 1 1v12c0 .55-.45 1-1 1H11c-.55 0-1-.45-1-1V9z"
                    fill="rgba(255,255,255,0.88)"
                  />
                  <path
                    d="M15.5 9c0-.55.45-1 1-1H21c.55 0 1 .45 1 1v12c0 .55-.45 1-1 1h-4.5c-.55 0-1-.45-1-1V9z"
                    fill="rgba(255,255,255,0.55)"
                  />
                  <rect
                    x="14.5"
                    y="9"
                    width="3"
                    height="12"
                    rx="0.5"
                    fill="rgba(255,255,255,0.2)"
                  />
                  <circle cx="24.5" cy="9" r="2.5" fill="#FDE68A" />
                  <defs>
                    <linearGradient
                      id="chat-ai-g"
                      x1="0"
                      y1="0"
                      x2="32"
                      y2="32"
                    >
                      <stop stop-color="#2563EB" />
                      <stop stop-color="#1D4ED8" />
                    </linearGradient>
                  </defs>
                </svg>
              </span>
              <!-- 用户头像 -->
              <img
                v-else-if="userStore.getAvatar()"
                :src="userStore.getAvatar()"
                class="avatar-icon user-avatar-img"
                alt="头像"
              />
              <!-- 默认用户头像 -->
              <svg
                v-else
                viewBox="0 0 32 32"
                fill="none"
                class="avatar-icon"
                aria-hidden="true"
              >
                <circle cx="16" cy="16" r="16" fill="#edf2f9" />
                <circle cx="16" cy="12.5" r="4.5" fill="#6e8fb7" />
                <path
                  d="M5 27c0-6 5-10 11-10s11 4 11 10"
                  fill="#6e8fb7"
                  opacity="0.55"
                />
              </svg>
            </div>

            <div
              class="message__bubble"
              :class="{
                'message__bubble--typing':
                  msg.role === 'assistant' && !msg.content && !msg.error,
                'message__bubble--error': msg.role === 'assistant' && msg.error,
              }"
            >
              <div
                v-if="msg.content"
                class="markdown-body"
                v-html="renderMarkdown(msg.content)"
              ></div>
              <div v-else-if="msg.error" class="message__error-text">
                {{ msg.error }}
              </div>
              <template v-else><span /><span /><span /></template>
            </div>

            <div
              v-if="msg.role === 'assistant' && msg.content"
              class="message__actions"
            >
              <button
                class="msg-action"
                title="复制"
                aria-label="复制回答"
                @click="copyMessage(msg.content)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  aria-hidden="true"
                >
                  <rect x="9" y="9" width="13" height="13" rx="2" />
                  <path
                    d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                  />
                </svg>
              </button>
              <button
                v-if="index === activeSession.messages.length - 1"
                class="msg-action"
                title="重新生成"
                aria-label="重新生成回答"
                @click="regenerate(msg)"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  aria-hidden="true"
                >
                  <polyline points="23 4 23 10 17 10" />
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
                </svg>
              </button>
              <span class="msg-action-divider"></span>
              <button
                class="msg-action"
                :class="{ 'msg-action--on': msg.rated === 'up' }"
                title="有帮助"
                aria-label="评价有帮助"
                @click="rateMessage(msg, 'up')"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  aria-hidden="true"
                >
                  <path
                    d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
                  />
                </svg>
              </button>
              <button
                class="msg-action"
                :class="{ 'msg-action--on': msg.rated === 'down' }"
                title="需改进"
                aria-label="评价需改进"
                @click="rateMessage(msg, 'down')"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  aria-hidden="true"
                >
                  <path
                    d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="conversation__empty">
          <p>还没有对话内容</p>
          <button class="empty-action" @click="backHome">开始提问</button>
        </div>

        <div class="input-area">
          <div class="composer">
            <textarea
              v-model="inputText"
              class="composer__input"
              rows="1"
              placeholder="继续追问…"
              aria-label="继续追问"
              name="assistant-query"
              :disabled="isLoading"
              @keydown="onKeydown"
            ></textarea>
            <button
              class="send-btn"
              :disabled="!inputText.trim() || isLoading"
              aria-label="发送消息"
              @click="handleSend()"
            >
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M4 10l12-6-2 6 2 6-12-6z" fill="currentColor" />
              </svg>
            </button>
          </div>
          <p class="input-hint">
            AI 也会出错，重要教学内容请结合课标与教材核验
          </p>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════
   Design Tokens & Shell
   ═══════════════════════════════════════════════ */
.assistant-page {
  --accent-blue: #2563eb;
  --accent-blue-dark: #1d4ed8;
  --coral: #f43f5e;
  --ink: #1a1a1a;
  --ink-soft: #4a4a4a;
  --ink-muted: #6b7280;
  --ink-faint: #9ca3af;
  --border: rgba(0, 0, 0, 0.09);
  --border-subtle: rgba(0, 0, 0, 0.07);
  --radius: 10px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.06);
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);

  display: flex;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: #f7f5f2;
  color: #1a1a1a;
  font-family:
    system-ui,
    -apple-system,
    "Segoe UI",
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;
}

/* ═══════════════════════════════════════════════
   Landing（主页面）
   ═══════════════════════════════════════════════ */
.landing {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.landing__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 24px;
}

.ghost-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-muted);
  font-size: 0.82rem;
  font-family: inherit;
  text-decoration: none;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease;
}

.ghost-btn:hover {
  color: var(--ink);
  background: #ffffff;
  border-color: var(--border-subtle);
}

.ghost-btn svg {
  width: 15px;
  height: 15px;
}

.ghost-btn__count {
  min-width: 18px;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent-blue);
  font-size: 0.7rem;
  font-weight: 700;
  text-align: center;
}

.landing__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 26px;
  padding: 24px 24px 72px;
}

.landing__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.landing__logo svg {
  display: block;
  width: 52px;
  height: 52px;
}

.landing__title {
  margin-top: 16px;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.45rem, 2.6vw, 1.85rem);
  font-weight: 700;
  color: var(--ink);
  letter-spacing: 0.01em;
}

.landing__desc {
  margin-top: 10px;
  max-width: 420px;
  font-size: 0.88rem;
  line-height: 1.7;
  color: var(--ink-faint);
  text-wrap: balance;
}

/* ═══════════════════════════════════════════════
   Composer（输入框，主页与对话页共用）
   ═══════════════════════════════════════════════ */
.composer {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
  padding: 8px 8px 8px 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: var(--shadow-card);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.composer--lg {
  max-width: 620px;
  padding: 10px 10px 10px 18px;
  border-radius: 18px;
}

.composer:focus-within {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.composer__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  padding: 8px 0;
  font-size: 0.94rem;
  line-height: 1.55;
  color: var(--ink);
  font-family: inherit;
  resize: none;
  field-sizing: content;
  max-height: 160px;
  overflow-y: auto;
}

.composer__input::placeholder {
  color: var(--ink-faint);
}

.composer__input:disabled {
  opacity: 0.55;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  max-width: 620px;
}

.chip {
  padding: 8px 14px;
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  background: #ffffff;
  color: var(--ink-soft);
  font-size: 0.8rem;
  font-family: inherit;
  cursor: pointer;
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    transform 0.15s ease;
}

.chip:hover {
  color: var(--accent-blue);
  border-color: rgba(37, 99, 235, 0.35);
  transform: translateY(-1px);
}

.landing__foot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  color: var(--ink-faint);
}

/* ═══════════════════════════════════════════════
   Chat Layout
   ═══════════════════════════════════════════════ */
.chat-layout {
  flex: 1;
  min-width: 0;
  display: flex;
}

/* ---- Sidebar ---- */
.sidebar {
  width: 288px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 16px 14px;
  background: #ffffff;
  border-right: 1px solid var(--border-subtle);
}

.sidebar__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 14px;
}

.new-chat-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent-blue);
  color: #fff;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.new-chat-btn:hover {
  background: var(--accent-blue-dark);
  box-shadow: 0 1px 6px rgba(37, 99, 235, 0.28);
}

.new-chat-btn svg {
  width: 14px;
  height: 14px;
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: none;
  background: #f3f4f6;
  color: var(--ink-faint);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.icon-btn:hover {
  background: #e5e7eb;
  color: var(--ink-soft);
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

/* 返回主页：对话页顶部的次级出口，用实体描边 + 文字保证一眼可辨 */
.back-home-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 7px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: #ffffff;
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  line-height: 1;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.back-home-btn:hover {
  color: var(--accent-blue);
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.38);
  box-shadow: 0 1px 6px rgba(37, 99, 235, 0.14);
}

.back-home-btn svg {
  width: 15px;
  height: 15px;
}

.icon-btn--drawer {
  display: none;
}

.sidebar-search {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 11px;
  border-radius: var(--radius-sm);
  background: #f3f4f6;
  transition: background 0.2s ease;
}

.sidebar-search:focus-within {
  background: #e9ebef;
}

.sidebar-search__icon {
  flex-shrink: 0;
  color: var(--ink-faint);
}

.sidebar-search__input {
  flex: 1;
  min-width: 0;
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.82rem;
  color: var(--ink-soft);
  font-family: inherit;
}

.sidebar-search__input::placeholder {
  color: var(--ink-faint);
}

.sidebar__history {
  flex: 1;
  min-height: 0;
  padding: 14px 0;
  overflow-y: auto;
}

.history-group + .history-group {
  margin-top: 16px;
}

.history-label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--ink-faint);
  letter-spacing: 0.04em;
}

.history-label::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}

.history-row {
  position: relative;
  padding: 2px;
  border-radius: var(--radius);
  transition: background 0.2s ease;
}

.history-row + .history-row {
  margin-top: 3px;
}

.history-row:hover,
.history-row--active {
  background: #f3f4f6;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-width: 0;
  padding: 8px 68px 8px 10px;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  color: var(--ink-soft);
  font-family: inherit;
}

.history-item__icon {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: #f3f4f6;
  color: var(--ink-faint);
}

.history-item__icon svg {
  width: 14px;
  height: 14px;
}

.history-item__content {
  min-width: 0;
  display: grid;
}

.history-item__content strong,
.history-item__content small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item__content strong {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink);
}

.history-item__content small {
  margin-top: 2px;
  font-size: 0.68rem;
  color: var(--ink-faint);
}

.history-row--active .history-item__content strong {
  color: var(--accent-blue);
}

.history-delete,
.history-pin {
  position: absolute;
  top: 50%;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  opacity: 0;
  transform: translate(4px, -50%);
  transition:
    opacity 0.2s ease,
    transform 0.2s ease,
    color 0.2s ease,
    background 0.2s ease;
}

.history-pin {
  right: 36px;
}

.history-delete {
  right: 5px;
}

.history-row:hover .history-delete,
.history-row:hover .history-pin,
.history-delete:focus-visible,
.history-pin:focus-visible {
  opacity: 1;
  transform: translate(0, -50%);
}

.history-pin:hover {
  color: var(--accent-blue);
  background: #e5e7eb;
}

.history-delete:hover {
  color: var(--coral);
  background: #fef2f2;
}

.history-delete svg,
.history-pin svg {
  width: 14px;
  height: 14px;
}

.sidebar__empty {
  padding: 18px 10px;
  font-size: 0.78rem;
  color: var(--ink-faint);
  text-align: center;
}

.sidebar__foot {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
  font-size: 0.7rem;
  color: var(--ink-faint);
}

.sidebar__foot svg {
  width: 12px;
  height: 12px;
}

/* ═══════════════════════════════════════════════
   Conversation（中间问答区）
   ═══════════════════════════════════════════════ */
.conversation {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f7f5f2;
}

.conversation__bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(6px);
}

.conversation__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--ink);
}

.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 24px 28px;
}

.conversation__empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--ink-faint);
  font-size: 0.86rem;
}

.empty-action {
  padding: 8px 18px;
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: 999px;
  background: transparent;
  color: var(--accent-blue);
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s ease;
}

.empty-action:hover {
  background: rgba(37, 99, 235, 0.08);
}

/* ---- Message ---- */
.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  animation: msg-in 0.25s ease-out;
}

.message--assistant {
  align-self: stretch;
  max-width: 100%;
}

.message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
  max-width: min(560px, 70%);
}

.message--user .message__avatar {
  margin-top: 6px;
}

.message__avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
}

.ai-avatar {
  border-radius: 0;
  overflow: hidden;
}

.ai-avatar-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.user-avatar-img {
  border-radius: 50%;
  object-fit: cover;
}

.message__bubble {
  font-size: 0.9375rem;
  line-height: 1.7;
}

.message--assistant .message__bubble {
  flex: 1;
  min-width: 0;
  padding: 12px 18px;
  background: #ffffff;
  color: var(--ink-soft);
  border: 1px solid var(--border-subtle);
  border-radius: 4px 14px 14px 14px;
}

.message--user .message__bubble {
  padding: 12px 18px;
  border-radius: 14px 4px 14px 14px;
  background: var(--accent-blue);
  color: #fff;
  font-weight: 500;
}

.message__bubble--typing {
  display: flex;
  gap: 5px;
  padding: 18px 22px;
}

.message__bubble--typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #93a9e0;
  animation: typing 1.3s ease-in-out infinite;
}

.message__bubble--typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.message__bubble--typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.35;
  }
  30% {
    transform: translateY(-5px);
    opacity: 1;
  }
}

.message__bubble--error {
  padding: 14px 18px;
}

.message__error-text {
  font-size: 0.82rem;
  color: #dc2626;
  line-height: 1.6;
}

/* ──── AI 回复 Markdown 结构化样式 ────
   v-html 注入的内容无 scoped 属性，须用 :deep() 穿透。 */
.message--assistant .message__bubble :deep(.markdown-body) {
  font-size: 0.925rem;
  line-height: 1.75;
  color: var(--ink-soft);
  word-break: break-word;
}

/* H2 章节标题：左色条 + 主题色，突出"每个部分在讲什么" */
.message--assistant .message__bubble :deep(.markdown-body h2) {
  margin: 18px 0 10px;
  padding: 7px 12px;
  font-size: 1.02rem;
  font-weight: 700;
  color: var(--accent-blue-dark);
  background: rgba(37, 99, 235, 0.08);
  border-left: 3px solid var(--accent-blue);
  border-radius: 6px;
  line-height: 1.4;
}

.message--assistant .message__bubble :deep(.markdown-body h2:first-child) {
  margin-top: 0;
}

.message--assistant .message__bubble :deep(.markdown-body h3) {
  margin: 14px 0 8px;
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--accent-blue-dark);
}

/* 核心加粗关键词：主题高亮 */
.message--assistant .message__bubble :deep(.markdown-body strong) {
  color: var(--accent-blue-dark);
  font-weight: 700;
  background: linear-gradient(transparent 62%, rgba(37, 99, 235, 0.18) 0);
  padding: 0 1px;
}

.message--assistant .message__bubble :deep(.markdown-body ul),
.message--assistant .message__bubble :deep(.markdown-body ol) {
  margin: 6px 0 10px;
  padding-left: 22px;
}

.message--assistant .message__bubble :deep(.markdown-body li) {
  margin: 4px 0;
}

.message--assistant .message__bubble :deep(.markdown-body hr) {
  margin: 14px 0;
  border: 0;
  border-top: 1px dashed rgba(37, 99, 235, 0.25);
}

.message--assistant .message__bubble :deep(.markdown-body code),
.message--assistant .message__bubble :deep(.markdown-body pre) {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  background: rgba(37, 99, 235, 0.07);
  border-radius: 5px;
}

.message--assistant .message__bubble :deep(.markdown-body code) {
  padding: 1px 5px;
  font-size: 0.88em;
  color: #1d4ed8;
}

.message--assistant .message__bubble :deep(.markdown-body pre) {
  padding: 10px 12px;
  overflow-x: auto;
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.message--assistant .message__bubble :deep(.markdown-body pre code) {
  padding: 0;
  background: transparent;
}

.message--assistant .message__bubble :deep(.markdown-body p) {
  margin: 6px 0;
}

/* 表格：完整边框、表头区分、单元格对齐无错位 */
.message--assistant .message__bubble :deep(.markdown-body table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0 14px;
  font-size: 0.89rem;
  line-height: 1.55;
}

.message--assistant .message__bubble :deep(.markdown-body th),
.message--assistant .message__bubble :deep(.markdown-body td) {
  border: 1px solid rgba(37, 99, 235, 0.28);
  padding: 7px 11px;
  text-align: left;
  vertical-align: top;
  word-break: break-word;
  white-space: normal;
}

.message--assistant .message__bubble :deep(.markdown-body th) {
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent-blue-dark);
  font-weight: 700;
  border-bottom: 2px solid rgba(37, 99, 235, 0.4);
  white-space: nowrap;
}

.message--assistant
  .message__bubble
  :deep(.markdown-body tbody tr:nth-child(even)) {
  background: rgba(37, 99, 235, 0.04);
}

.message--assistant .message__bubble :deep(.markdown-body td br) {
  margin: 0;
}

@keyframes msg-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ---- Message Actions ---- */
.message__actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-top: 4px;
  margin-left: 46px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message--user .message__actions {
  display: none;
}

.message:hover .message__actions {
  opacity: 1;
}

.msg-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition:
    color 0.15s ease,
    background 0.15s ease;
}

.msg-action:hover {
  color: var(--accent-blue);
  background: #f3f4f6;
}

.msg-action--on {
  color: var(--accent-blue);
  background: rgba(37, 99, 235, 0.1);
}

.msg-action svg {
  width: 13px;
  height: 13px;
}

.msg-action-divider {
  width: 1px;
  height: 14px;
  background: var(--border-subtle);
  margin: 0 4px;
}

/* ═══════════════════════════════════════════════
   Input Area
   ═══════════════════════════════════════════════ */
.input-area {
  padding: 14px 24px 18px;
  border-top: 1px solid var(--border-subtle);
  background: #f7f5f2;
}

.send-btn {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 11px;
  background: var(--accent-blue);
  color: #fff;
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-blue-dark);
  transform: scale(1.05);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.send-btn svg {
  width: 16px;
  height: 16px;
}

.input-hint {
  margin-top: 9px;
  font-size: 0.66rem;
  color: var(--ink-faint);
  text-align: center;
}

/* ═══════════════════════════════════════════════
   Focus Ring
   ═══════════════════════════════════════════════ */
.send-btn:focus-visible,
.new-chat-btn:focus-visible,
.icon-btn:focus-visible,
.ghost-btn:focus-visible,
.chip:focus-visible,
.empty-action:focus-visible,
.msg-action:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 2px #ffffff,
    0 0 0 4px var(--accent-blue);
}

/* ═══════════════════════════════════════════════
   Sidebar Overlay (mobile)
   ═══════════════════════════════════════════════ */
.sidebar-overlay {
  display: none;
}

/* ═══════════════════════════════════════════════
   Responsive
   ═══════════════════════════════════════════════ */
@media (max-width: 860px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.28s var(--ease-out);
    box-shadow: 0 0 24px rgba(0, 0, 0, 0.12);
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgba(0, 0, 0, 0.12);
  }

  .icon-btn--drawer {
    display: inline-flex;
  }

  .conversation__bar {
    padding: 12px 16px;
  }

  .messages {
    padding: 18px 14px;
  }

  .message--user {
    max-width: 88%;
  }

  .input-area {
    padding: 12px 14px 14px;
  }

  .landing__bar {
    padding: 14px 16px;
  }

  .landing__body {
    padding: 16px 16px 48px;
    gap: 20px;
  }
}

/* ═══════════════════════════════════════════════
   Reduced Motion
   ═══════════════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
  .message {
    animation: none !important;
  }
  .message__bubble--typing span {
    animation: none !important;
  }
  .sidebar {
    transition: none !important;
  }
  .msg-action,
  .history-item,
  .history-row,
  .icon-btn,
  .back-home-btn,
  .ghost-btn,
  .chip,
  .send-btn,
  .composer,
  .new-chat-btn,
  .sidebar-search,
  .history-delete,
  .history-pin {
    transition: none !important;
  }
  .send-btn:hover:not(:disabled),
  .chip:hover {
    transform: none;
  }
}
</style>
