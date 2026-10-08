<script setup>
import { computed, nextTick, ref, watch } from "vue";
import AiBadge from "./AiBadge.vue";

/**
 * 内容调整区：生成初版后，用户在这里用一句话说明要改的地方，
 * 提交后由后端带原内容重新生成，满意即可下载新版文件。
 */
const props = defineProps({
  // 本条内容由哪些 AI 协同产出（AiBadge 的 name 列表）
  pipeline: { type: Array, default: () => [] },
  title: { type: String, default: "内容调整" },
  // [{ id, role: 'assistant' | 'user', text, filename }]
  messages: { type: Array, default: () => [] },
  // 是否已有可调整的初版（没有时输入区引导用户先去左侧生成）
  ready: { type: Boolean, default: false },
  generating: { type: Boolean, default: false },
  progress: { type: Number, default: 0 },
  stage: { type: String, default: "" },
  taskId: { type: [String, Number], default: null },
  filename: { type: String, default: "" },
  placeholder: { type: String, default: "说明要修改的地方…" },
});

const emit = defineEmits(["send"]);

const API_BASE = "http://localhost:8000/api/courseware";
const draft = ref("");
const listRef = ref(null);

const downloadUrl = computed(() =>
  props.taskId ? `${API_BASE}/${props.taskId}/download` : "",
);

const statusText = computed(() => {
  if (props.generating) return "生成中";
  if (props.filename) return "可下载";
  if (props.ready) return "待调整";
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

watch(
  () => props.messages.length,
  async () => {
    await nextTick();
    if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight;
  },
);
</script>

<template>
  <section class="revise" :aria-label="title">
    <header class="revise__head">
      <h3 class="revise__title">{{ title }}</h3>
      <span
        class="revise__status"
        :class="{
          'is-active': generating,
          'is-ready': !generating && filename,
        }"
        aria-live="polite"
        >{{ statusText }}</span
      >
    </header>

    <div v-if="pipeline.length" class="revise__engines">
      <span class="revise__engines-label">生成引擎</span>
      <AiBadge v-for="k in pipeline" :key="k" :name="k" size="sm" />
    </div>

    <div ref="listRef" class="revise__list">
      <article
        v-for="m in messages"
        :key="m.id"
        class="revise__msg"
        :class="m.role"
      >
        <p class="revise__bubble">{{ m.text }}</p>
        <p v-if="m.filename" class="revise__file">
          <span class="revise__file-name">{{ m.filename }}</span>
          <a class="revise__download" :href="downloadUrl">下载文件</a>
        </p>
      </article>

      <div v-if="generating" class="revise__working" aria-live="polite">
        <div class="revise__bar">
          <div
            class="revise__bar-fill"
            :style="{ width: progress + '%' }"
          ></div>
        </div>
        <p class="revise__stage">{{ stage || "处理中…" }} · {{ progress }}%</p>
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
      <button
        type="button"
        class="revise__send"
        :disabled="!canSend"
        @click="submit"
      >
        提交修改
      </button>

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

.revise__engines {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 20px;
  background: #fbfbfd;
  border-bottom: 1px solid var(--border);
}

.revise__engines-label {
  font-size: 0.72rem;
  color: var(--ink-muted);
}

.revise__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 220px;
  max-height: 46vh;
  padding: 18px 20px;
  overflow-y: auto;
  overscroll-behavior: contain;
}

.revise__msg {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 88%;
}

.revise__msg.assistant {
  align-self: flex-start;
}

.revise__msg.user {
  align-self: flex-end;
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

.revise__file {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  margin: 0;
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.revise__file-name {
  flex: 1;
  min-width: 0;
  font-size: 0.8rem;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.revise__download {
  flex: none;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent);
  text-decoration: none;
}

.revise__download:hover {
  text-decoration: underline;
}

.revise__working {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-self: flex-start;
  width: 100%;
  max-width: 88%;
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

.revise__send {
  align-self: flex-end;
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
.revise__download:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .revise__bar-fill,
  .revise__send {
    transition: none;
  }
}
</style>
