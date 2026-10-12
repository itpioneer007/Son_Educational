<script setup>
import { computed, nextTick, ref, watch } from "vue";
import { marked } from "marked";
import AiBadge from "./AiBadge.vue";

/**
 * 内容调整区：AI 生成的内容（流式）直接展示在这里，用户像对话一样阅读、
 * 提出修改意见；满意后点击「导出最终内容」才生成可下载文件。
 */
const props = defineProps({
  // 本条内容由哪些 AI 协同产出（AiBadge 的 name 列表）
  pipeline: { type: Array, default: () => [] },
  title: { type: String, default: "内容调整" },
  // [{ id, role, text, content（Markdown）, streaming }]
  messages: { type: Array, default: () => [] },
  // 正文已生成（可修改、可导出）
  ready: { type: Boolean, default: false },
  generating: { type: Boolean, default: false },
  // 正在导出最终文件
  exporting: { type: Boolean, default: false },
  progress: { type: Number, default: 0 },
  stage: { type: String, default: "" },
  filename: { type: String, default: "" },
  placeholder: { type: String, default: "说明要修改的地方…" },
});

const emit = defineEmits(["send", "export"]);

const draft = ref("");
const listRef = ref(null);

// 对话里 AI 一方的头像：取该面板最终产出内容的引擎
// （课件 = 讯飞智文，教案/练习/试卷 = DeepSeek）。
// 仅作为对话头像出现，不在界面上暴露"生成引擎"字样。
const assistantEngine = computed(
  () => props.pipeline[props.pipeline.length - 1] || "deepseek",
);

// 正文已生成且当前未在处理时，才允许导出最终文件
const canExport = computed(() => props.ready && !props.generating);

const statusText = computed(() => {
  if (props.exporting) return "正在导出…";
  if (props.generating) return "生成中";
  if (props.filename) return "已导出";
  if (props.ready) return "可查看 / 修改";
  return "未开始";
});

const canSend = computed(
  () => props.ready && !props.generating && draft.value.trim() !== "",
);

function submit() {
  if (!canSend.value) return;
  emit("send", draft.value.trim());
  draft.value = "";
}

// Markdown 渲染：流式内容以 Markdown 形式实时呈现
function renderMd(md) {
  return marked.parse(md || "", { gfm: true, breaks: true });
}

// 正文是否已开始流式输出：末尾那条 assistant 消息一旦有内容，即视为「文字已经
// 开始往外冒」。此时正文本身就是最直观的进度，底部的「正在生成」提示可以隐去，
// 只在首 token 到达前的静默期（大模型首字延迟可能有几十秒）才需要它占位。
const hasLiveContent = computed(() => {
  const list = props.messages;
  for (let i = list.length - 1; i >= 0; i -= 1) {
    const m = list[i];
    if (m.role === "assistant" && m.streaming) return !!m.content;
  }
  return false;
});

// 内容增长（含流式追加）时保持滚动到底部，便于持续阅读
const contentLength = computed(() =>
  props.messages.reduce(
    (n, m) =>
      n + (m.content ? m.content.length : 0) + (m.text ? m.text.length : 0),
    0,
  ),
);

watch(contentLength, async () => {
  await nextTick();
  const el = listRef.value;
  if (!el) return;
  // 正文区已随内容自适应高度、不再内部滚动，「跟随到底」因此改为跟随页面。
  // 仅当内容末尾仍在视口内（读者处于跟随状态）时才滚，避免打断向上翻阅。
  if (el.getBoundingClientRect().bottom <= window.innerHeight + 200) {
    el.lastElementChild?.scrollIntoView({ behavior: "auto", block: "end" });
  }
});
</script>

<template>
  <section class="revise" :aria-label="title">
    <header class="revise__head">
      <h3 class="revise__title">{{ title }}</h3>
      <span
        class="revise__status"
        :class="{
          'is-active': generating,
          'is-ready': !generating && ready,
        }"
        aria-live="polite"
        >{{ statusText }}</span
      >
    </header>

    <div ref="listRef" class="revise__list">
      <article
        v-for="m in messages"
        :key="m.id"
        class="revise__msg"
        :class="m.role"
      >
        <span class="revise__avatar" aria-hidden="true">
          <AiBadge
            v-if="m.role === 'assistant'"
            :name="assistantEngine"
            size="md"
            :show-label="false"
          />
          <svg
            v-else
            viewBox="0 0 24 24"
            width="15"
            height="15"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="8" r="3.6" />
            <path d="M5 20c0-3.4 3.1-5.6 7-5.6s7 2.2 7 5.6" />
          </svg>
        </span>
        <!-- 流式阶段用纯文本逐字呈现（Markdown 语法原样显示，等定稿再一次性解析），
             定稿后切换为渲染好的 HTML —— 避免每来一个 delta 就重跑整篇 marked.parse
             （长文时是 O(n²)，是「一整段一整段往外跳」的主因）。 -->
        <div
          v-if="m.role === 'assistant' && m.content && m.streaming"
          class="revise__bubble revise__md is-streaming"
        ><span class="revise__cursor" aria-hidden="true"></span>{{ m.content }}</div>
        <div
          v-else-if="m.role === 'assistant' && m.content"
          class="revise__bubble revise__md"
          v-html="renderMd(m.content)"
        ></div>
        <p v-else class="revise__bubble">{{ m.text }}</p>
      </article>

      <!-- 正文生成阶段：真流式下正文在逐段冒出，百分比反而让人以为「卡住了」，
           因此只给一个脉动提示，且正文一开始输出就隐去；
           导出阶段正文已定稿静止、没有别的活性证据，仍保留进度条。 -->
      <div
        v-if="generating && (exporting || !hasLiveContent)"
        class="revise__working"
        aria-live="polite"
      >
        <template v-if="exporting">
          <div class="revise__bar">
            <div
              class="revise__bar-fill"
              :style="{ width: progress + '%' }"
            ></div>
          </div>
          <p class="revise__stage">
            {{ stage || "正在导出…" }} · {{ progress }}%
          </p>
        </template>
        <p v-else class="revise__live">
          <span class="revise__dots" aria-hidden="true"
            ><i></i><i></i><i></i
          ></span>
          <span>{{ stage || "正在生成…" }}</span>
        </p>
      </div>
    </div>

    <footer class="revise__foot">
      <textarea
        v-model="draft"
        class="revise__input"
        rows="2"
        name="revise-instruction"
        :placeholder="
          ready
            ? placeholder
            : '先在左侧填写信息并点击生成，初版生成后可在这里修改'
        "
        :disabled="!ready || generating"
        aria-label="修改意见"
        @keydown.enter.exact.prevent="submit"
      ></textarea>
      <div class="revise__actions">
        <!-- 满意后再导出：点击才生成最终文件并下载 -->
        <button
          type="button"
          class="revise__export"
          :class="{ 'is-disabled': !canExport }"
          :disabled="!canExport"
          @click="emit('export')"
        >
          {{ exporting ? "正在导出…" : "导出最终内容" }}
        </button>
        <button
          type="button"
          class="revise__send"
          :disabled="!canSend"
          @click="submit"
        >
          提交修改
        </button>
      </div>

      <!-- 底部扩展区：课件面板在此挂载模板选择条 -->
      <slot name="footer-tools" />
    </footer>
  </section>
</template>

<style scoped>
.revise {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.revise__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.revise__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ink);
}

.revise__status {
  flex: none;
  padding: 2px 10px;
  font-size: 0.72rem;
  color: var(--ink-muted);
  background: #f4f5f7;
  border-radius: 999px;
}

.revise__status.is-active {
  color: var(--accent-deep);
  background: rgba(43, 108, 176, 0.1);
}

.revise__status.is-ready {
  color: #1f6b45;
  background: rgba(35, 195, 178, 0.14);
}

.revise__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 220px;
  padding: 18px 20px;
  /* 不设 max-height：正文有多长面板就撑多高，跟着内容往下走；
     旧写法 max-height:46vh + overflow-y:auto 会把内容锁在固定高度的框里内滚 */
  overscroll-behavior: contain;
}

.revise__msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 92%;
}

.revise__msg.assistant {
  align-self: flex-start;
}

.revise__msg.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.revise__avatar {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-top: 1px;
}

.revise__msg.user .revise__avatar {
  color: #fff;
  background: var(--accent);
  border-radius: 50%;
}

.revise__bubble {
  margin: 0;
  padding: 10px 13px;
  font-size: 0.84rem;
  line-height: 1.7;
  color: var(--ink-soft);
  background: #f4f5f7;
  border-radius: 10px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.revise__msg.user .revise__bubble {
  color: #fff;
  background: var(--accent);
}

/* ── AI 正文（Markdown）排版 ─────────────────── */
.revise__md {
  white-space: normal;
  width: 100%;
}

.revise__md :deep(h1) {
  margin: 2px 0 8px;
  font-size: 1.02rem;
  font-weight: 700;
  color: var(--ink);
}

.revise__md :deep(h2) {
  margin: 14px 0 6px;
  padding-left: 8px;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ink);
  border-left: 3px solid var(--accent);
}

.revise__md :deep(h3) {
  margin: 12px 0 4px;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--accent-deep);
}

.revise__md :deep(p) {
  margin: 6px 0;
}

.revise__md :deep(ul),
.revise__md :deep(ol) {
  margin: 6px 0 6px 18px;
  padding: 0;
}

.revise__md :deep(li) {
  margin: 3px 0;
}

.revise__md :deep(strong) {
  color: var(--ink);
}

.revise__md :deep(h1:first-child) {
  margin-top: 0;
}

/* 流式阶段：正文以纯文本原样呈现，保留换行；块级布局与定稿后一致，切换无跳动 */
.revise__md.is-streaming {
  white-space: pre-wrap;
  word-break: break-word;
}

/* 打字机光标：一个贴在行尾闪烁的竖条，给出「正在输出」的活性反馈 */
.revise__cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-right: 2px;
  vertical-align: text-bottom;
  background: var(--accent-deep);
  animation: revise-blink 1s steps(2, start) infinite;
}

@keyframes revise-blink {
  to {
    visibility: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  .revise__cursor {
    animation: none;
  }
}

.revise__working {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-self: flex-start;
  width: 100%;
  max-width: 92%;
  padding-left: 38px;
}

.revise__bar {
  height: 4px;
  background: var(--border);
  border-radius: 999px;
  overflow: hidden;
}

.revise__bar-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s var(--ease-out);
}

.revise__stage {
  margin: 0;
  font-size: 0.74rem;
  color: var(--ink-muted);
}

/* ── 生成中的脉动提示（无百分比）─────────────────
   真流式下正文会逐段冒出，正文本身就是进度；
   这个提示只在首 token 到达前的静默期占位，正文一开始输出即隐去。 */
.revise__live {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  align-self: flex-start;
  margin: 0;
  font-size: 0.78rem;
  color: var(--accent-deep);
}

.revise__dots {
  display: inline-flex;
  gap: 3px;
}

.revise__dots i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  animation: revise-dot 1.2s infinite ease-in-out both;
}

.revise__dots i:nth-child(2) {
  animation-delay: 0.16s;
}

.revise__dots i:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes revise-dot {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-2px);
  }
}

.revise__foot {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--border);
}

.revise__input {
  width: 100%;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 0.84rem;
  line-height: 1.6;
  color: var(--ink);
  background: #fbfbfd;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  resize: vertical;
}

.revise__input::placeholder {
  color: #9aa1ac;
}

.revise__input:disabled {
  background: #f7f7f9;
  cursor: not-allowed;
}

.revise__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.revise__export {
  padding: 10px 18px;
  font-family: inherit;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--accent-deep);
  text-decoration: none;
  background: #fff;
  border: 1px solid var(--accent);
  border-radius: 10px;
  cursor: pointer;
  transition:
    background-color 0.18s var(--ease-out),
    transform 0.18s var(--ease-out);
}

.revise__export:hover {
  background: rgba(43, 108, 176, 0.08);
  transform: translateY(-1px);
}

.revise__export.is-disabled {
  color: #9aa1ac;
  background: #f7f7f9;
  border-color: var(--border-strong);
  cursor: not-allowed;
}

.revise__export.is-disabled:hover {
  background: #f7f7f9;
  transform: none;
}

.revise__send {
  padding: 10px 22px;
  font-family: inherit;
  font-size: 0.86rem;
  font-weight: 700;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition:
    background-color 0.18s var(--ease-out),
    transform 0.18s var(--ease-out);
}

.revise__send:hover:not(:disabled) {
  background: var(--accent-deep);
  transform: translateY(-1px);
}

.revise__send:disabled {
  color: #9aa1ac;
  background: #eef0f3;
  cursor: not-allowed;
}

.revise__input:focus-visible,
.revise__send:focus-visible,
.revise__export:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .revise__bar-fill,
  .revise__send,
  .revise__export {
    transition: none;
  }
  .revise__dots i {
    animation: none;
    opacity: 0.7;
  }
}
</style>
