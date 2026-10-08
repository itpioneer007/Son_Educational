<script setup>
import { computed } from "vue";

/**
 * 分步向导：只负责步骤导航与内容插槽，不关心具体字段。
 * 每个步骤用同名具名插槽承载内容，最后一步可通过 #actions 插槽放主操作按钮。
 */
const props = defineProps({
  // [{ key, title, desc }]
  steps: { type: Array, required: true },
  modelValue: { type: Number, default: 0 },
  // 最后一步是否展示「下一步」之外的默认导航（默认展示）
  showNext: { type: Boolean, default: true },
});

const emit = defineEmits(["update:modelValue"]);

const currentIndex = computed(() =>
  Math.min(Math.max(props.modelValue, 0), props.steps.length - 1),
);
const currentKey = computed(() => props.steps[currentIndex.value]?.key);
const isLast = computed(() => currentIndex.value === props.steps.length - 1);

function go(index) {
  if (index === currentIndex.value) return;
  emit("update:modelValue", index);
}

function prev() {
  if (currentIndex.value > 0) emit("update:modelValue", currentIndex.value - 1);
}

function next() {
  if (!isLast.value) emit("update:modelValue", currentIndex.value + 1);
}

function stateOf(index) {
  if (index < currentIndex.value) return "done";
  if (index === currentIndex.value) return "current";
  return "todo";
}
</script>

<template>
  <div class="wizard">
    <ol class="wizard__steps">
      <li
        v-for="(step, i) in steps"
        :key="step.key"
        class="wizard__step"
        :class="`is-${stateOf(i)}`"
      >
        <button
          type="button"
          class="wizard__step-btn"
          :aria-current="stateOf(i) === 'current' ? 'step' : undefined"
          @click="go(i)"
        >
          <span class="wizard__idx" aria-hidden="true">{{ i + 1 }}</span>
          <span class="wizard__meta">
            <span class="wizard__title">{{ step.title }}</span>
            <span v-if="step.desc" class="wizard__desc">{{ step.desc }}</span>
          </span>
        </button>
      </li>
    </ol>

    <div class="wizard__body">
      <slot :name="currentKey" />
    </div>

    <div class="wizard__foot">
      <button
        type="button"
        class="wizard__nav"
        :disabled="currentIndex === 0"
        @click="prev"
      >
        上一步
      </button>
      <button
        v-if="showNext && !isLast"
        type="button"
        class="wizard__nav wizard__nav--primary"
        @click="next"
      >
        下一步
      </button>
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.wizard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wizard__steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.wizard__step {
  flex: 1 1 0;
  min-width: 132px;
}

.wizard__step-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  font-family: inherit;
  text-align: left;
  background: #fbfbfd;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition:
    border-color 0.18s var(--ease-out),
    background-color 0.18s var(--ease-out);
}

.wizard__step-btn:hover {
  border-color: var(--border-strong);
}

.wizard__idx {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--ink-muted);
  background: #eef0f3;
  border-radius: 999px;
}

.wizard__meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.wizard__title {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink);
}

.wizard__desc {
  font-size: 0.7rem;
  color: var(--ink-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wizard__step.is-current .wizard__step-btn {
  background: rgba(43, 108, 176, 0.06);
  border-color: var(--accent);
}

.wizard__step.is-current .wizard__idx {
  color: #fff;
  background: var(--accent);
}

.wizard__step.is-done .wizard__idx {
  color: #1f6b45;
  background: rgba(35, 195, 178, 0.18);
}

.wizard__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wizard__foot {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 4px;
}

.wizard__nav {
  padding: 9px 20px;
  font-family: inherit;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--ink-soft);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 9px;
  cursor: pointer;
  transition:
    border-color 0.18s var(--ease-out),
    background-color 0.18s var(--ease-out);
}

.wizard__nav:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.wizard__nav:disabled {
  color: #b6bcc6;
  background: #f7f7f9;
  border-color: var(--border);
  cursor: not-allowed;
}

.wizard__nav--primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.wizard__nav--primary:hover:not(:disabled) {
  background: var(--accent-deep);
  border-color: var(--accent-deep);
  color: #fff;
}

.wizard__step-btn:focus-visible,
.wizard__nav:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  .wizard__step-btn,
  .wizard__nav {
    transition: none;
  }
}
</style>