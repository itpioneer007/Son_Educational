<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from "vue";
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
const searchQuery = ref("");

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

// 大功能（构思层）：不生成文件，专注帮教师把想法理清楚、产出内容草稿
// 产出结果下方提供「转入生成」按钮，桥接到核心功能页落地成真实文件
const features = [
  {
    id: "plan",
    label: "备课构思",
    hint: "目标·重难点·导入·环节",
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
  },
  {
    id: "lesson",
    label: "教案草稿",
    hint: "完整教案文字稿",
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z"/><path d="M20 17v5H6.5A2.5 2.5 0 0 1 4 19.5"/></svg>',
  },
  {
    id: "quiz",
    label: "出题草稿",
    hint: "分层题目清单",
    icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h9l4 4v16H6z"/><path d="M14 2v4h4"/><path d="M9 13l2 2 4-4"/></svg>',
  },
];

// 「通用问答」入口图标（自由对话，对话历史仅在此功能下展示）
const chatIcon =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3H9l-3 3v-3H7a3 3 0 0 1-3-3V6z"/></svg>';

// 当前功能（'' = 通用问答）
const activeFeature = ref("");
// 最近一次通过功能表单触发的课题（用于「转入生成」桥接预填）
const lastFeatureTopic = ref("");

// 自定义兜底选项标识：下拉选中它时，旁边显示自定义输入框
const CUSTOM = "__custom__";

// 各功能的子需求表单：课题必填，其余字段用户可自行指定或选「自定义…」兜底
const featureForms = reactive({
  plan: {
    topic: "",
    lessonType: "新授课",
    lessonTypeCustom: "",
    textbook: "人教A版",
    textbookCustom: "",
    studentLevel: "普通班",
    studentLevelCustom: "",
    examAware: true,
    requirements: "",
  },
  lesson: {
    topic: "",
    lessonType: "新授课",
    lessonTypeCustom: "",
    textbook: "人教A版",
    textbookCustom: "",
    studentLevel: "普通班",
    studentLevelCustom: "",
    duration: "1课时",
    detail: "详案",
    detailCustom: "",
    requirements: "",
  },
  quiz: {
    topic: "",
    purpose: "课堂练习",
    purposeCustom: "",
    questionMix: "高考标准",
    questionMixCustom: "",
    studentLevel: "普通班",
    studentLevelCustom: "",
    difficulty: "中等",
    count: "8",
    countCustom: "",
    examAware: true,
    requirements: "",
  },
});

// 各字段的可选值（供下拉渲染；每个字段都带「自定义…」兜底）
const FIELD_OPTIONS = {
  lessonType: ["新授课", "复习课", "习题讲评课", "专题课"],
  textbook: [
    "人教A版",
    "人教B版",
    "苏教版",
    "北师大版",
    "湘教版",
    "沪教版",
    "其他",
  ],
  studentLevel: ["重点班", "普通班", "基础薄弱"],
  duration: ["1课时", "2课时", "3课时"],
  detail: ["详案（公开课/检查用）", "简案（日常用）"],
  purpose: ["课堂练习", "课后作业", "周测", "月考"],
  questionMix: ["高考标准（选择+填空+解答）", "全选择题", "全解答题"],
  difficulty: ["基础", "中等", "综合提升"],
  count: ["5", "8", "10", "15"],
};

// 三个功能各自的字段配置（顺序即展示顺序）
const planFields = [
  { key: "lessonType", label: "课型" },
  { key: "textbook", label: "教材版本" },
  { key: "studentLevel", label: "学生层次" },
];
const lessonFields = [
  { key: "lessonType", label: "课型" },
  { key: "textbook", label: "教材版本" },
  { key: "studentLevel", label: "学生层次" },
  { key: "duration", label: "课时" },
  { key: "detail", label: "教案详略" },
];
const quizFields = [
  { key: "purpose", label: "用途" },
  { key: "questionMix", label: "题型分布" },
  { key: "studentLevel", label: "学生层次" },
  { key: "difficulty", label: "难度" },
  { key: "count", label: "题量" },
];
// 当前功能要渲染的字段
const currentFields = computed(() => {
  if (activeFeature.value === "plan") return planFields;
  if (activeFeature.value === "lesson") return lessonFields;
  if (activeFeature.value === "quiz") return quizFields;
  return [];
});

// 取某字段的实际值：选中「自定义…」时用旁边的自定义输入，否则用选项值
function resolveField(form, key) {
  const v = form[key];
  if (v === CUSTOM) {
    return form[key + "Custom"]?.trim() || "（自定义，未填写）";
  }
  return v;
}

// 当前功能的展示信息
const currentFeature = computed(
  () => features.find((f) => f.id === activeFeature.value) || null,
);
const currentFeatureLabel = computed(() => currentFeature.value?.label || "");
const currentFeatureDesc = computed(() => currentFeature.value?.hint || "");
const currentFeatureIcon = computed(() => currentFeature.value?.icon || "");
const canRunFeature = computed(() => {
  const form = featureForms[activeFeature.value];
  return !!form && !!form.topic.trim();
});
// 生成中的按钮/提示文案，按功能区分，让用户明确知道正在处理
const generatingLabel = computed(() => {
  const labels = {
    plan: "正在构思…",
    lesson: "正在编写…",
    quiz: "正在出题…",
  };
  return labels[activeFeature.value] || "正在生成…";
});
// 对话历史仅在「通用问答」下展示
const isGeneral = computed(() => activeFeature.value === "");

// 桥接信息：把当前功能的草稿送入核心功能页生成文件（type 对应 /features）
const bridgeInfo = computed(() => {
  const topic = lastFeatureTopic.value;
  const feat = activeFeature.value;
  if (!feat || !topic) return null;
  const map = {
    plan: { type: "ppt", label: "生成课件", hint: "将构思转为课件" },
    lesson: { type: "doc", label: "生成教案", hint: "将草稿转为 DOCX 教案" },
    quiz: { type: "quiz", label: "生成练习", hint: "将题目转为练习卷" },
  };
  return map[feat] ? { ...map[feat], topic } : null;
});
// 最后一条是 AI 回复时才显示桥接按钮
const showBridge = computed(() => {
  const msgs = activeSession.value?.messages ?? [];
  return (
    bridgeInfo.value &&
    msgs.length > 0 &&
    msgs[msgs.length - 1].role === "assistant"
  );
});

// 选择功能：不直接触发 AI，先展示该功能的子需求表单
function selectFeature(feature) {
  if (activeFeature.value === feature) {
    activeFeature.value = "";
    return;
  }
  activeFeature.value = feature;
  // 切换功能时清除之前的临时会话，保证每次进入定向功能是全新对话
  assistant.clearEphemeral();
}

// 填写子需求后生成：把表单信息组装成结构化 prompt 交给 AI
async function runFeature() {
  if (isLoading.value) return;
  const feat = activeFeature.value;
  const form = featureForms[feat];
  if (!form || !form.topic.trim()) return;
  const topic = form.topic.trim();
  lastFeatureTopic.value = topic;

  // 组装本功能的全部需求字段（含自定义兜底后的实际值）
  const params = [];
  if (feat === "plan") {
    params.push(`课型：${resolveField(form, "lessonType")}`);
    params.push(`教材版本：${resolveField(form, "textbook")}`);
    params.push(`学生层次：${resolveField(form, "studentLevel")}`);
  } else if (feat === "lesson") {
    params.push(`课型：${resolveField(form, "lessonType")}`);
    params.push(`教材版本：${resolveField(form, "textbook")}`);
    params.push(`学生层次：${resolveField(form, "studentLevel")}`);
    params.push(`课时：${resolveField(form, "duration")}`);
    params.push(`教案详略：${resolveField(form, "detail")}`);
  } else if (feat === "quiz") {
    params.push(`用途：${resolveField(form, "purpose")}`);
    params.push(`题型分布：${resolveField(form, "questionMix")}`);
    params.push(`学生层次：${resolveField(form, "studentLevel")}`);
    params.push(`难度：${resolveField(form, "difficulty")}`);
    params.push(`题量：${resolveField(form, "count")} 道`);
  }

  const extra = form.requirements?.trim()
    ? `\n补充要求：${form.requirements.trim()}`
    : "";
  const examNote =
    feat !== "lesson" && form.examAware
      ? "\n请在产出中标注高考考频、常考题型与分值（复习/出题场景尤其重要）。"
      : "";

  let prompt = "";
  if (feat === "plan") {
    prompt = `请帮我把课题「${topic}」的这节课构思成一份教学方案。\n${params.join(
      "；",
    )}。\n内容须包含：教学目标、教学重难点、课堂导入、教学环节流程（标注时间）、板书设计建议。${examNote}${extra}\n请以清晰的结构输出，便于我参考后直接生成课件。`;
  } else if (feat === "lesson") {
    prompt = `请编写课题「${topic}」的完整教案草稿。\n${params.join(
      "；",
    )}。\n请按标准教案结构输出（教学目标、教学重难点、教学准备、教学过程并标注时间、板书设计、作业布置）。${extra}`;
  } else if (feat === "quiz") {
    prompt = `请围绕课题「${topic}」设计分层练习草稿。\n${params.join(
      "；",
    )}。\n按基础/提升/拓展分层，题型含选择、填空、简答，每题附参考答案与考察点。${examNote}${extra}`;
  }
  await handleSend(prompt);
}

// 桥接：把助手产出的草稿送入核心功能页生成真实文件（type=ppt|doc|quiz）
function goToFeatures(type, topic, content = "") {
  const query = { type };
  if (topic) query.topic = topic;
  // 草稿文本可能很长，放入 sessionStorage 避免超长 URL；
  // 核心功能页读取后自动预填学科/学段/教学目标/重难点等字段
  try {
    if (content) {
      sessionStorage.setItem(
        "zhike-features-bridge",
        JSON.stringify({ type, topic: topic || "", content, ts: Date.now() }),
      );
    }
  } catch {
    /* ignore */
  }
  router.push({ path: "/features", query });
}

// 取最后一条 AI 回复的完整文本，用于桥接预填核心功能的内容
const lastAssistantContent = computed(() => {
  const msgs = activeSession.value?.messages ?? [];
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].role === "assistant" && msgs[i].content) {
      return msgs[i].content;
    }
  }
  return "";
});

// const quickNotes = [
//   '支持资料',
//   '适合课件、教案、互动脚本共创',
//   '会话记录保存在本地浏览器',
// ]

const groupedSections = computed(() => {
  const grouped = assistant.groupSessionsByDate(sessions.value);
  return [
    { key: "today", label: "今天", items: grouped.today },
    { key: "yesterday", label: "昨天", items: grouped.yesterday },
    { key: "earlier", label: "更早", items: grouped.earlier },
  ].filter((group) => group.items.length);
});

function refresh() {
  // 状态已响应式共享，无需手动同步；若当前无激活会话则自动落到第一个
  const current = assistant.getActiveSession();
  if (!current && sessions.value.length) {
    assistant.setActive(sessions.value[0].id);
  }
}

function ensureSessionExists() {
  if (!assistant.getSessions().length) {
    assistant.createSession();
  }
  refresh();
}

function handleNewChat() {
  assistant.setActive(null);
  inputText.value = "";
  sidebarOpen.value = false;
}

function selectSession(id) {
  assistant.setActive(id);
  sidebarOpen.value = false;
  scrollToBottom();
}

function handleDeleteSession(id) {
  assistant.deleteSession(id);
  if (!sessions.value.length) {
    assistant.createSession();
  }
  refresh();
}

async function handleSend(text = inputText.value) {
  const content = (text || inputText.value).trim();
  if (!content || isLoading.value) return;

  inputText.value = "";
  isLoading.value = true;
  // 立即滚动到消息区，让用户第一时间看到 AI 的打字点反馈
  scrollToBottom();

  try {
    const isEphemeral = activeFeature.value !== "";

    if (!isEphemeral && !activeId.value) {
      const session = assistant.createSession();
      activeId.value = session.id;
    } else if (isEphemeral) {
      assistant.clearEphemeral();
    }

    await assistant.sendMessage(content, {
      feature: activeFeature.value,
      ephemeral: isEphemeral,
      onDelta: () => {
        scrollToBottom();
      },
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
  const msgs = activeSession.value.messages;
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
  refresh();
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
  // 进入页面先显示欢迎页，不自动加载历史会话
  activeId.value = null;
  document.addEventListener("click", (e) => {
    const link = e.target.closest(".internal-link");
    if (link) {
      e.preventDefault();
      const path = link.getAttribute("data-path");
      if (path) router.push(path);
    }
  });
});

watch(activeId, scrollToBottom);
</script>

<template>
  <div class="assistant-page">
    <nav class="feature-nav" aria-label="备课功能导航">
      <div class="feature-nav__head">
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5v15z"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M20 17v5H6.5A2.5 2.5 0 0 1 4 19.5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span>AI 备课</span>
      </div>

      <button
        class="feature-nav__item feature-nav__item--home"
        @click="router.push('/')"
      >
        <span class="feature-nav__icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 0 0 1 1h3m10-11l2 2m-2-2v10a1 1 0 0 1-1 1h-3m-6 0a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1m-6 0h6"
            />
          </svg>
        </span>
        <span class="feature-nav__label">返回主页</span>
      </button>

      <div class="feature-nav__divider" />

      <button
        class="feature-nav__item"
        :class="{ 'feature-nav__item--active': isGeneral }"
        @click="selectFeature('')"
        title="自由对话，对话历史在此展示"
      >
        <span class="feature-nav__icon" v-html="chatIcon"></span>
        <span class="feature-nav__label">通用问答</span>
      </button>

      <div class="feature-nav__divider" />

      <button
        v-for="f in features"
        :key="f.id"
        class="feature-nav__item"
        :class="{ 'feature-nav__item--active': activeFeature === f.id }"
        @click="selectFeature(f.id)"
        :title="f.hint"
      >
        <span class="feature-nav__icon" v-html="f.icon"></span>
        <span class="feature-nav__label">{{ f.label }}</span>
      </button>
    </nav>

    <aside
      v-if="isGeneral"
      class="assistant-sidebar"
      :class="{ 'assistant-sidebar--open': sidebarOpen }"
    >
      <div class="assistant-sidebar__top">
        <RouterLink
          to="/"
          class="icon-btn icon-btn--soft"
          title="返回首页"
          aria-label="返回首页"
          @click="sidebarOpen = false"
        >
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path
              d="M12 4l-6 6 6 6"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </RouterLink>
        <button class="new-chat-btn" @click="handleNewChat">
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M10 4v12M4 10h12"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
            />
          </svg>
          新对话
        </button>
      </div>

      <div v-if="isGeneral" class="sidebar-search">
        <svg
          class="sidebar-search__icon"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="M21 21l-4.35-4.35" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索对话…"
          aria-label="搜索对话历史"
          autocomplete="off"
          name="assistant-search"
          class="sidebar-search__input"
        />
      </div>

      <div v-if="isGeneral" class="assistant-sidebar__history">
        <section
          v-for="group in groupedSections"
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
                <svg viewBox="0 0 20 20" fill="none">
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
              aria-label="置顶/取消置顶"
              @click.stop="togglePin(session.id)"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                :stroke="session.isPinned ? '#4d98f4' : 'currentColor'"
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
              title="删除会话"
              aria-label="删除会话"
              @click.stop="handleDeleteSession(session.id)"
            >
              <svg viewBox="0 0 20 20" fill="none">
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
      </div>

      <div class="assistant-sidebar__foot">
        <RouterLink to="/" class="home-btn" @click="sidebarOpen = false">
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M12 4l-6 6 6 6"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          返回首页
        </RouterLink>

        <p class="assistant-sidebar__hint">
          <svg viewBox="0 0 16 16" fill="none">
            <path
              d="M8 1L2 4v4c0 3.3 2.6 6.4 6 7 3.4-.6 6-3.7 6-7V4L8 1z"
              stroke="currentColor"
              stroke-width="1.2"
            />
          </svg>
          对话记录仅保存在本地
        </p>
      </div>
    </aside>

    <div
      v-if="sidebarOpen && isGeneral"
      class="sidebar-overlay"
      @click="sidebarOpen = false"
    />

    <main class="assistant-main">
      <header class="assistant-mobile-bar">
        <button
          class="icon-btn icon-btn--soft"
          aria-label="打开侧边栏"
          @click="sidebarOpen = true"
        >
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M3 5h14M3 10h14M3 15h14"
              stroke="currentColor"
              stroke-width="1.6"
              stroke-linecap="round"
            />
          </svg>
        </button>
        <span class="assistant-mobile-bar__title">知课 AI 备课助手</span>
        <AiBadge name="qwen" size="sm" />
      </header>

      <div class="mode-bar">
        <button
          class="mode-btn"
          :class="{ 'mode-btn--active': isGeneral }"
          @click="selectFeature('')"
        >
          <span
            class="mode-btn__icon"
            aria-hidden="true"
            v-html="chatIcon"
          ></span>
          <span class="mode-btn__label">通用问答</span>
        </button>
        <button
          v-for="f in features"
          :key="f.id"
          class="mode-btn"
          :class="{ 'mode-btn--active': activeFeature === f.id }"
          @click="selectFeature(f.id)"
        >
          <span
            class="mode-btn__icon"
            aria-hidden="true"
            v-html="f.icon"
          ></span>
          <span class="mode-btn__label">{{ f.label }}</span>
        </button>
        <button class="mode-btn mode-btn--home" @click="router.push('/')">
          <span class="mode-btn__icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 0 0 1 1h3m10-11l2 2m-2-2v10a1 1 0 0 1-1 1h-3m-6 0a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1m-6 0h6"
              />
            </svg>
          </span>
          <span class="mode-btn__label">主页</span>
        </button>
      </div>

      <div class="assistant-shell" @click="handleInternalLink">
        <!-- 子需求选择栏：非通用功能时展示，填好指定信息后再触发 AI -->
        <div v-if="activeFeature" class="feature-panel">
          <div class="feature-panel__head">
            <span
              class="feature-panel__icon"
              aria-hidden="true"
              v-html="currentFeatureIcon"
            ></span>
            <strong class="feature-panel__title">
              {{ currentFeatureLabel }}
            </strong>
            <span class="feature-panel__desc">{{ currentFeatureDesc }}</span>
            <button
              class="feature-panel__close"
              title="关闭并返回通用问答"
              @click="selectFeature('')"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </div>

          <div class="feature-panel__form">
            <label class="fp-field fp-field--grow">
              <span class="fp-field__label">课题</span>
              <input
                class="fp-field__input"
                v-model="featureForms[activeFeature].topic"
                placeholder="请输入课题，如：函数的单调性…"
                @keyup.enter="runFeature()"
              />
            </label>

            <div class="fp-field--row">
              <template v-for="field in currentFields" :key="field.key">
                <label class="fp-field">
                  <span class="fp-field__label">{{ field.label }}</span>
                  <select
                    class="fp-field__select"
                    v-model="featureForms[activeFeature][field.key]"
                  >
                    <option
                      v-for="opt in FIELD_OPTIONS[field.key]"
                      :key="opt"
                      :value="opt"
                    >
                      {{ opt }}
                    </option>
                    <option :value="CUSTOM">自定义…</option>
                  </select>
                  <input
                    v-if="featureForms[activeFeature][field.key] === CUSTOM"
                    class="fp-field__input fp-field__input--custom"
                    v-model="featureForms[activeFeature][field.key + 'Custom']"
                    :placeholder="'自定义' + field.label"
                  />
                </label>
              </template>

              <label
                v-if="activeFeature !== 'lesson'"
                class="fp-field fp-field--switch"
              >
                <span class="fp-field__label">高考考点标注</span>
                <div class="fp-switch">
                  <button
                    type="button"
                    class="fp-switch__opt"
                    :class="{
                      'fp-switch__opt--on':
                        featureForms[activeFeature].examAware,
                    }"
                    @click="featureForms[activeFeature].examAware = true"
                  >
                    标注
                  </button>
                  <button
                    type="button"
                    class="fp-switch__opt"
                    :class="{
                      'fp-switch__opt--on':
                        !featureForms[activeFeature].examAware,
                    }"
                    @click="featureForms[activeFeature].examAware = false"
                  >
                    不标
                  </button>
                </div>
              </label>

              <label class="fp-field fp-field--grow">
                <span class="fp-field__label">补充要求（可选）</span>
                <input
                  class="fp-field__input"
                  v-model="featureForms[activeFeature].requirements"
                  placeholder="如：重点讲情境导入 / 用生活案例举例…"
                />
              </label>
            </div>
          </div>

          <button
            class="feature-panel__submit"
            :class="{ 'feature-panel__submit--loading': isLoading }"
            :disabled="!canRunFeature || isLoading"
            @click="runFeature()"
          >
            <span
              v-if="isLoading"
              class="feature-panel__spinner"
              aria-hidden="true"
            ></span>
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6l7-3z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            {{ isLoading ? generatingLabel : "开始生成" }}
          </button>

          <div v-if="isLoading" class="feature-panel__status" role="status">
            <span class="feature-panel__status-dots" aria-hidden="true"
              ><span /><span /><span
            /></span>
            AI 正在生成，教案/出题内容较长时可能需要 1~2 分钟，请稍候…
          </div>
        </div>

        <div v-if="!hasMessages && !isLoading && isGeneral" class="welcome">
          <div class="welcome__brand">
            <div class="welcome__logo">
              <span class="welcome__logo-icon">
                <svg
                  viewBox="0 0 40 40"
                  fill="none"
                  aria-hidden="true"
                  width="40"
                  height="40"
                >
                  <rect
                    width="40"
                    height="40"
                    rx="10"
                    fill="url(#welcome-ai-g)"
                  />
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
                      id="welcome-ai-g"
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
            </div>

            <h1 class="welcome__title">知课 AI 备课助手</h1>
            <p class="welcome__desc">
              帮你把备课想法理清楚：选择左侧「备课构思」「教案草稿」「出题草稿」，填写课题后一键生成内容草稿，满意后还可「转入生成」落地成真实文件；「通用问答」可自由对话。
            </p>
            <p class="welcome__power">
              <span class="welcome__power-label">对话由</span>
              <AiBadge name="qwen" />
              <span class="welcome__power-label">驱动</span>
            </p>
          </div>
        </div>

        <div v-else ref="messagesEl" class="messages">
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
                aria-label="复制消息"
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
                class="msg-action"
                title="重新生成"
                aria-label="重新生成回答"
                @click="regenerate(msg)"
                v-if="index === activeSession.messages.length - 1"
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

        <!-- 桥接：把助手草稿送入核心功能页生成真实文件 -->
        <div v-if="showBridge" class="bridge-bar">
          <div class="bridge-bar__text">
            <strong>{{ currentFeatureLabel }}已生成</strong>
            <span>满意的话，可一键转入核心功能生成真实文件</span>
          </div>
          <button
            class="bridge-bar__btn"
            @click="
              goToFeatures(
                bridgeInfo.type,
                bridgeInfo.topic,
                lastAssistantContent,
              )
            "
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M7 17L17 7" />
              <path d="M8 7h9v9" />
            </svg>
            {{ bridgeInfo.label }}
          </button>
        </div>

        <div class="input-area">
          <div
            v-if="activeFeature"
            class="mode-indicator"
            :title="currentFeatureDesc"
          >
            <span
              class="mode-indicator__icon"
              v-html="currentFeatureIcon"
            ></span>
            <span class="mode-indicator__label">
              当前功能：{{ currentFeatureLabel }} —— {{ currentFeatureDesc }}
            </span>
            <button
              class="mode-indicator__clear"
              title="返回通用问答"
              aria-label="返回通用问答"
              @click="selectFeature('')"
            >
              <svg viewBox="0 0 16 16" fill="none">
                <path
                  d="M4 4l8 8M12 4l-8 8"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <div class="input-wrap">
            <input
              v-model="inputText"
              type="text"
              placeholder="输入问题…"
              aria-label="输入您的问题"
              autocomplete="off"
              name="assistant-query"
              :disabled="isLoading"
              @keydown="onKeydown"
            />
            <button
              class="send-btn"
              :disabled="!inputText.trim() || isLoading"
              aria-label="发送消息"
              @click="handleSend()"
            >
              <svg viewBox="0 0 20 20" fill="none">
                <path d="M4 10l12-6-2 6 2 6-12-6z" fill="currentColor" />
              </svg>
            </button>
          </div>

          <p class="input-hint">
            <svg viewBox="0 0 16 16" fill="none">
              <path
                d="M8 1L2 4v4c0 3.3 2.6 6.4 6 7 3.4-.6 6-3.7 6-7V4L8 1z"
                stroke="currentColor"
                stroke-width="1.2"
              />
            </svg>
            对话内容仅保存在本地浏览器
          </p>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════
   Design Tokens & Page Shell
   ═══════════════════════════════════════════════ */
.assistant-page {
  --accent-blue: #2563eb;
  --accent-blue-dark: #1d4ed8;
  --coral: #f43f5e;
  --ink: #1a1a1a;
  --ink-soft: #4a4a4a;
  --ink-muted: #6b7280;
  --ink-faint: #9ca3af;
  --border-subtle: rgba(0, 0, 0, 0.07);
  --radius: 10px;
  --radius-sm: 8px;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.06);
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);

  display: flex;
  min-height: 100vh;
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
   Sidebar
   ═══════════════════════════════════════════════ */
.assistant-sidebar {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 16px;
  background: #ffffff;
  border-right: 1px solid var(--border-subtle);
}

.assistant-sidebar__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: none;
  color: var(--ink-faint);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.icon-btn--soft {
  background: #f3f4f6;
}

.icon-btn:hover {
  background: #e5e7eb;
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.new-chat-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent-blue);
  color: #fff;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.new-chat-btn:hover {
  background: var(--accent-blue-dark);
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.25);
}

.new-chat-btn svg {
  width: 14px;
  height: 14px;
}

.assistant-sidebar__history {
  flex: 1;
  padding: 16px 0;
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
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--ink-faint);
  letter-spacing: 0.04em;
}

.history-label::before,
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

.assistant-sidebar__foot {
  padding-top: 16px;
  border-top: 1px solid var(--border-subtle);
}

.home-btn {
  display: none;
}

.assistant-sidebar__hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 0.7rem;
  color: var(--ink-faint);
}

.assistant-sidebar__hint svg {
  width: 12px;
  height: 12px;
}

/* ---- Sidebar Search ---- */
.sidebar-search {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 12px 0 2px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  background: #f3f4f6;
  transition: background 0.2s ease;
}

.sidebar-search:focus-within {
  background: #e5e7eb;
}

.sidebar-search__icon {
  flex-shrink: 0;
  color: var(--ink-faint);
}

.sidebar-search__input {
  flex: 1;
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

/* ═══════════════════════════════════════════════
   Main Area
   ═══════════════════════════════════════════════ */
.assistant-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
}

.assistant-mobile-bar {
  display: none;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.assistant-mobile-bar__title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
}

.assistant-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 14px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* ═══════════════════════════════════════════════
   备课功能竖向导航（页面左端）
   ═══════════════════════════════════════════════ */
.feature-nav {
  width: 176px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 12px;
  background: #ffffff;
  border-right: 1px solid var(--border-subtle);
  gap: 2px;
}

.feature-nav__head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 10px 14px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--ink);
}

.feature-nav__head svg {
  width: 16px;
  height: 16px;
  color: var(--accent-blue);
}

.feature-nav__item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: var(--ink-soft);
  font-size: 0.84rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.feature-nav__item:hover {
  color: var(--accent-blue);
  background: #f5f7fb;
}

.feature-nav__item--active {
  color: var(--accent-blue);
  background: rgba(37, 99, 235, 0.08);
  font-weight: 600;
}

.feature-nav__item:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 2px #ffffff,
    0 0 0 4px var(--accent-blue);
}
.feature-nav__item--home {
  margin-bottom: 2px;
  background: #f0f4ff;
  border: 1px solid #d6e2ff;
  border-radius: 9px;
  color: #3b5fc2;
  font-weight: 600;
}
.feature-nav__item--home:hover {
  color: #1e40af;
  background: #dbe5ff;
}

.feature-nav__icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
}

.feature-nav__icon svg {
  width: 18px;
  height: 18px;
}

.feature-nav__label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.feature-nav__divider {
  height: 1px;
  margin: 8px 10px;
  background: var(--border-subtle);
}

/* ═══════════════════════════════════════════════
   Mode Bar（仅移动端横向兜底）
   ═══════════════════════════════════════════════ */
.mode-bar {
  display: none;
  gap: 2px;
  padding: 12px 20px 0;
  border-bottom: 1px solid var(--border-subtle);
  background: #ffffff;
  overflow-x: auto;
  scrollbar-width: none;
}

.mode-bar::-webkit-scrollbar {
  display: none;
}

/* ═══════════════════════════════════════════════
   子需求选择栏（非通用功能时展示）
   ═══════════════════════════════════════════════ */
.feature-panel {
  margin: 16px 20px 0;
  padding: 16px 18px 18px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, #fbfdff, #f7fafc);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.feature-panel__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.feature-panel__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 7px;
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent-blue);
}

.feature-panel__icon svg {
  width: 16px;
  height: 16px;
}

.feature-panel__title {
  font-size: 0.94rem;
  color: var(--ink);
}

.feature-panel__desc {
  font-size: 0.78rem;
  color: var(--ink-faint);
}

.feature-panel__close {
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.feature-panel__close svg {
  width: 15px;
  height: 15px;
}

.feature-panel__close:hover {
  background: rgba(15, 23, 42, 0.06);
  color: var(--ink);
}

.feature-panel__form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fp-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.fp-field--grow {
  flex: 1 1 100%;
}

.fp-field--row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.fp-field--row .fp-field {
  flex: 1 1 120px;
  max-width: 200px;
}

.fp-field__label {
  font-size: 0.74rem;
  font-weight: 600;
  color: var(--ink-soft);
}

.fp-field__input,
.fp-field__select {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: #ffffff;
  color: var(--ink);
  font-size: 0.86rem;
  font-family: inherit;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.fp-field__input:focus,
.fp-field__select:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

/* 自定义兜底：选「自定义…」后出现的输入框 */
.fp-field__input--custom {
  margin-top: 6px;
  padding: 7px 10px;
  font-size: 0.8rem;
  border-color: rgba(37, 99, 235, 0.35);
  background: #f8fbff;
}

/* 高考考点标注开关 */
.fp-switch {
  display: flex;
  gap: 0;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.fp-switch__opt {
  flex: 1;
  padding: 9px 12px;
  border: none;
  background: #ffffff;
  color: var(--ink-faint);
  font-size: 0.82rem;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.fp-switch__opt + .fp-switch__opt {
  border-left: 1px solid var(--border-subtle);
}

.fp-switch__opt--on {
  background: rgba(37, 99, 235, 0.08);
  color: var(--accent-blue);
  font-weight: 600;
}

.fp-switch__opt:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--accent-blue);
}

.feature-panel__submit {
  margin-top: 16px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--accent-blue);
  color: #ffffff;
  font-size: 0.88rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.15s ease;
}

.feature-panel__submit svg {
  width: 16px;
  height: 16px;
}

.feature-panel__submit:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.feature-panel__submit:disabled {
  background: #c3d3ee;
  cursor: not-allowed;
}

.feature-panel__submit--loading {
  background: #3b82f6;
  cursor: progress;
}
.feature-panel__submit--loading:disabled {
  background: #3b82f6;
  cursor: progress;
}

.feature-panel__spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: fp-spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes fp-spin {
  to {
    transform: rotate(360deg);
  }
}

.feature-panel__status {
  margin-top: 12px;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 9px 14px;
  border-radius: var(--radius-md);
  background: #eff6ff;
  border: 1px solid #dbeafe;
  color: #1d4ed8;
  font-size: 0.85rem;
  line-height: 1.4;
}

.feature-panel__status-dots {
  display: inline-flex;
  gap: 3px;
  flex-shrink: 0;
}
.feature-panel__status-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
  animation: typing 1.3s ease-in-out infinite;
}
.feature-panel__status-dots span:nth-child(2) {
  animation-delay: 0.2s;
}
.feature-panel__status-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

/* ═══════════════════════════════════════════════
   桥接栏（草稿 → 核心功能生成文件）
   ═══════════════════════════════════════════════ */
.bridge-bar {
  margin: 12px 20px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, #f0f6ff, #eaf2ff);
}

.bridge-bar__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.bridge-bar__text strong {
  font-size: 0.86rem;
  color: var(--accent-blue);
}

.bridge-bar__text span {
  font-size: 0.76rem;
  color: var(--ink-faint);
}

.bridge-bar__btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent-blue);
  color: #ffffff;
  font-size: 0.82rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.2s ease,
    transform 0.15s ease;
}

.bridge-bar__btn svg {
  width: 14px;
  height: 14px;
}

.bridge-bar__btn:hover {
  background: #1d4ed8;
  transform: translateY(-1px);
}

/* 键盘可达性：可交互元素统一可见焦点环 */
.feature-panel__submit:focus-visible,
.feature-panel__close:focus-visible,
.mode-btn:focus-visible,
.mode-indicator__clear:focus-visible,
.send-btn:focus-visible,
.new-chat-btn:focus-visible,
.home-btn:focus-visible,
.bridge-bar__btn:focus-visible,
.msg-action:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 2px #ffffff,
    0 0 0 4px var(--accent-blue);
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 12px 9px;
  border: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  background: transparent;
  color: var(--ink-faint);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
  position: relative;
  font-family: inherit;
  white-space: nowrap;
  flex-shrink: 0;
}

.mode-btn:hover {
  color: var(--accent-blue);
  background: #f8fafc;
}

.mode-btn--active {
  color: var(--accent-blue);
  background: transparent;
  font-weight: 600;
}

.mode-btn--active::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 8px;
  right: 8px;
  height: 2px;
  border-radius: 1px;
  background: var(--accent-blue);
}
.mode-btn--home {
  margin-left: auto;
  border-left: 1px solid #e2e8f0;
  padding-left: 16px;
  border-radius: var(--radius-sm);
  color: #3b5fc2;
  font-weight: 600;
}
.mode-btn--home:hover {
  color: #1e40af;
  background: #dbe5ff;
}

.mode-btn__icon {
  font-size: 1rem;
  line-height: 1;
  display: flex;
}

.mode-btn__icon svg {
  width: 15px;
  height: 15px;
}

.mode-btn__label {
  white-space: nowrap;
}

/* ═══════════════════════════════════════════════
   Welcome screen
   ═══════════════════════════════════════════════ */
.welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 32px 24px;
  text-align: center;
}

.welcome__brand {
  max-width: 520px;
}

.welcome__logo {
  margin: 0 auto 20px;
  display: grid;
  place-items: center;
}

.welcome__logo-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
}

.welcome__title {
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.35rem, 2.4vw, 1.7rem);
  font-weight: 700;
  line-height: 1.25;
  color: var(--ink);
  text-wrap: balance;
}

.welcome__desc {
  margin-top: 10px;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--ink-faint);
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.welcome__power {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  padding: 5px 12px;
  background: #f7f8fa;
  border: 1px solid var(--border);
  border-radius: 999px;
}

.welcome__power-label {
  font-size: 0.74rem;
  color: var(--ink-muted);
}

/* ═══════════════════════════════════════════════
   Messages
   ═══════════════════════════════════════════════ */
.messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 24px 28px;
}

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

/* Avatar styles */
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
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 0;
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
  padding: 12px 18px;
  background: #f0f4ff;
  color: var(--ink-soft);
  border-radius: 4px 14px 14px 14px;
  flex: 1;
  min-width: 0;
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

/* ──── AI 回复 Markdown 结构化样式（DeepSeek 风格） ────
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
/* H2 前面不再需要 hr 分割的多余留白 */
.message--assistant .message__bubble :deep(.markdown-body h2:first-child) {
  margin-top: 0;
}

/* H3 小标题：主题色字，强化层级 */
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

/* 列表：对齐紧凑、留呼吸 */
.message--assistant .message__bubble :deep(.markdown-body ul),
.message--assistant .message__bubble :deep(.markdown-body ol) {
  margin: 6px 0 10px;
  padding-left: 22px;
}
.message--assistant .message__bubble :deep(.markdown-body li) {
  margin: 4px 0;
}

/* 分隔线：弱化原粗分割，交给标题色条表达结构 */
.message--assistant .message__bubble :deep(.markdown-body hr) {
  margin: 14px 0;
  border: 0;
  border-top: 1px dashed rgba(37, 99, 235, 0.25);
}

/* 代码/公式：等宽、浅底、圆角 */
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

/* 段落间距收紧，信息密度更高 */
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
.message--assistant .message__bubble :deep(.markdown-body table:focus-visible) {
  outline: none;
}
/* 单元格内的换行统一，避免内容叠行错位 */
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
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-subtle);
  background: #ffffff;
}

/* ---- 当前定向任务指示条 ---- */
.mode-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding: 7px 10px;
  border: 1px solid rgba(37, 99, 235, 0.18);
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.06);
  color: var(--accent-blue);
  font-size: 0.78rem;
}

.mode-indicator__icon {
  flex-shrink: 0;
  display: flex;
}

.mode-indicator__icon svg {
  width: 16px;
  height: 16px;
}

.mode-indicator__label {
  flex: 1;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mode-indicator__clear {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.mode-indicator__clear:hover {
  color: #dc2626;
  background: #fef2f2;
}

.mode-indicator__clear svg {
  width: 13px;
  height: 13px;
}

.input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 3px 3px 16px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease;
}

.input-wrap:focus-within {
  border-color: var(--accent-blue);
  background: #fff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.input-wrap input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  padding: 10px 0;
  font-size: 0.92rem;
  color: var(--ink);
  font-family: inherit;
}

.input-wrap input::placeholder {
  color: var(--ink-faint);
}

.input-wrap input:disabled {
  opacity: 0.5;
}

.send-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 0.62rem;
  color: var(--ink-faint);
}

.input-hint svg {
  width: 12px;
  height: 12px;
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
@media (max-width: 768px) {
  .feature-nav {
    display: none;
  }

  .mode-bar {
    display: flex;
  }

  .assistant-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 50;
    transform: translateX(-100%);
    transition: transform 0.28s var(--ease-out);
  }

  .assistant-sidebar--open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 40;
    background: rgba(0, 0, 0, 0.08);
  }

  .assistant-main {
    padding: 12px;
  }

  .assistant-mobile-bar {
    display: flex;
  }

  .assistant-shell {
    border-radius: 12px;
  }

  .welcome {
    padding: 32px 18px 20px;
  }

  .welcome__logo-icon {
    width: 50px;
    height: 50px;
  }

  .messages {
    padding: 20px 16px;
  }

  .message {
    max-width: 94%;
  }

  .input-area {
    padding: 14px 14px 16px;
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
  .assistant-sidebar {
    transition: none !important;
  }
  .sidebar-overlay {
    transition: none !important;
  }
  .msg-action,
  .mode-btn,
  .feature-nav__item,
  .history-item,
  .history-row,
  .icon-btn,
  .send-btn,
  .input-wrap,
  .new-chat-btn,
  .sidebar-search,
  .history-delete,
  .history-pin {
    transition: none !important;
  }
  .send-btn:hover:not(:disabled) {
    transform: none;
  }
}
</style>
