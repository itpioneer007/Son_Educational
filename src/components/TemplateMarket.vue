<script setup>
import { computed, ref, watch } from "vue";
import AiBadge from "./AiBadge.vue";

/**
 * PPT 模板选择：只对接讯飞智文模板。
 * 常驻「模板条」（当前模板 + 备注/配图开关 + 模板市场入口）+ 模板市场弹层。
 * 模板数据由父级持有，本组件只做展示与选择，通过事件回写。
 * 上游模板接口不支持翻页/筛选，可用模板就固定那一批，因此市场内按风格归类展示。
 */
const props = defineProps({
  sparkTemplates: { type: Array, default: () => [] },
  sparkLoading: { type: Boolean, default: false },
  sparkError: { type: String, default: "" },
  selectedSparkId: { type: String, default: "" },
  cardNote: { type: Boolean, default: true },
  figure: { type: Boolean, default: true },
  // 图片地址归一化函数（复用父级的 previewUrl）
  resolvePreview: { type: Function, default: (p) => p || "" },
});

const emit = defineEmits([
  "spark-change",
  "refresh-spark",
  "card-note-change",
  "figure-change",
]);

const open = ref(false);
const keyword = ref("");
const activeStyle = ref("");
const detail = ref(null);

const currentTemplate = computed(
  () =>
    props.sparkTemplates.find((t) => t.id === props.selectedSparkId) || null,
);

const currentLabel = computed(() =>
  currentTemplate.value ? currentTemplate.value.name : "默认模板（推荐）",
);

// 按风格归类（模板自带 style，如 卡通 / 简约 / 商务 / 创意 / 国风 / 节日）
const styles = computed(() => {
  const seen = new Set();
  props.sparkTemplates.forEach((t) => {
    if (t.style) seen.add(t.style);
  });
  return Array.from(seen);
});

const filteredTemplates = computed(() => {
  const kw = keyword.value.trim().toLowerCase();
  return props.sparkTemplates.filter((t) => {
    if (activeStyle.value && t.style !== activeStyle.value) return false;
    if (!kw) return true;
    return `${t.name || ""} ${t.style || ""} ${t.industry || ""}`
      .toLowerCase()
      .includes(kw);
  });
});

function imgOf(t) {
  return props.resolvePreview(t?.preview) || "";
}

function openMarket() {
  detail.value = currentTemplate.value || null;
  open.value = true;
}

function closeMarket() {
  open.value = false;
}

function applyTemplate(t) {
  emit("spark-change", t.id);
  closeMarket();
}

function useDefault() {
  emit("spark-change", "");
  closeMarket();
}

// 打开市场时，若模板尚未加载则拉取一次首页
watch(open, (v) => {
  if (
    v &&
    !props.sparkTemplates.length &&
    !props.sparkLoading &&
    !props.sparkError
  ) {
    emit("refresh-spark");
  }
});
</script>

<template>
  <div class="mk">
    <!-- 模板条 -->
    <div class="mk__strip">
      <div class="mk__strip-row">
        <AiBadge name="zhiwen" />
        <span class="mk__brand-hint">智能排版 + 自动配图</span>
      </div>

      <div class="mk__strip-row mk__strip-row--current">
        <div class="mk__thumb">
          <img
            v-if="currentTemplate && imgOf(currentTemplate)"
            :src="imgOf(currentTemplate)"
            alt=""
          />
          <span v-else class="mk__thumb-fallback">讯</span>
        </div>
        <div class="mk__current-meta">
          <span class="mk__current-name">{{ currentLabel }}</span>
          <span class="mk__current-hint">生成本课件时套用的版式</span>
        </div>
        <button type="button" class="mk__browse" @click="openMarket">
          模板市场
        </button>
      </div>

      <div class="mk__strip-row mk__options">
        <label class="mk__option">
          <input
            type="checkbox"
            :checked="cardNote"
            @change="emit('card-note-change', $event.target.checked)"
          />
          生成演讲备注
        </label>
        <label class="mk__option">
          <input
            type="checkbox"
            :checked="figure"
            @change="emit('figure-change', $event.target.checked)"
          />
          自动配图
        </label>
        <span class="mk__option-hint">开启备注与配图会消耗更多讯飞额度</span>
      </div>
    </div>

    <!-- 模板市场弹层 -->
    <Teleport to="body">
      <div v-if="open" class="mk-overlay" @click.self="closeMarket">
        <div
          class="mk-modal"
          role="dialog"
          aria-modal="true"
          aria-label="PPT 模板市场"
        >
          <header class="mk-modal__head">
            <h4 class="mk-modal__title">讯飞智文模板市场</h4>
            <input
              v-model="keyword"
              type="search"
              class="mk-modal__search"
              placeholder="搜索模板名称 / 风格 / 行业"
              aria-label="搜索模板"
            />
            <button
              type="button"
              class="mk-modal__close"
              aria-label="关闭"
              @click="closeMarket"
            >
              ×
            </button>
          </header>

          <div class="mk-modal__body">
            <section class="mk-content">
              <div v-if="sparkLoading" class="mk-content__note">
                正在加载讯飞模板…
              </div>
              <div
                v-else-if="sparkError"
                class="mk-content__note mk-content__note--warn"
              >
                {{ sparkError }}
                <button
                  type="button"
                  class="mk-content__retry"
                  @click="emit('refresh-spark')"
                >
                  重试
                </button>
              </div>

              <!-- 按风格筛选（上游返回的模板数量有限，归类比翻页实用） -->
              <div v-if="styles.length" class="mk-chips">
                <button
                  type="button"
                  class="mk-chip"
                  :class="{ 'is-active': activeStyle === '' }"
                  @click="activeStyle = ''"
                >
                  全部
                </button>
                <button
                  v-for="s in styles"
                  :key="s"
                  type="button"
                  class="mk-chip"
                  :class="{ 'is-active': activeStyle === s }"
                  @click="activeStyle = s"
                >
                  {{ s }}
                </button>
              </div>

              <div v-if="filteredTemplates.length" class="mk-grid">
                <button
                  v-for="t in filteredTemplates"
                  :key="t.id"
                  type="button"
                  class="mk-card"
                  :class="{ 'is-active': detail && detail.id === t.id }"
                  @click="detail = t"
                >
                  <span class="mk-card__thumb">
                    <img
                      v-if="imgOf(t)"
                      :src="imgOf(t)"
                      alt=""
                      loading="lazy"
                    />
                    <span v-else class="mk-card__thumb-fallback">{{
                      t.name
                    }}</span>
                  </span>
                  <span class="mk-card__name">{{ t.name }}</span>
                  <span v-if="t.industry" class="mk-card__badge">{{
                    t.industry
                  }}</span>
                </button>
              </div>
              <p v-else-if="!sparkLoading" class="mk-content__empty">
                没有匹配的模板，试试其他关键词
              </p>
            </section>

            <aside class="mk-detail">
              <template v-if="detail">
                <div class="mk-detail__preview">
                  <img
                    v-if="imgOf(detail)"
                    :src="imgOf(detail)"
                    alt="模板预览"
                  />
                  <span v-else class="mk-detail__preview-fallback">{{
                    detail.name
                  }}</span>
                </div>
                <h5 class="mk-detail__name">{{ detail.name }}</h5>
                <p class="mk-detail__badges">
                  <span class="mk-badge">讯飞模板</span>
                  <span v-if="detail.industry" class="mk-badge mk-badge--muted">
                    {{ detail.industry }}
                  </span>
                </p>
                <button
                  type="button"
                  class="mk-detail__use"
                  @click="applyTemplate(detail)"
                >
                  使用此模板
                </button>
              </template>
              <p v-else class="mk-detail__empty">从左侧选择模板查看详情</p>

              <button
                type="button"
                class="mk-detail__default"
                @click="useDefault"
              >
                使用默认模板（推荐）
              </button>
            </aside>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── 模板条 ─────────────────────────────────── */
.mk {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px dashed var(--border-strong);
}

.mk__strip {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mk__strip-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mk__brand-hint {
  font-size: 0.72rem;
  color: var(--ink-muted);
}

.mk__strip-row--current {
  padding: 8px 10px;
  background: #fbfbfd;
  border: 1px solid var(--border);
  border-radius: 10px;
}

.mk__thumb {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 30px;
  overflow: hidden;
  background: #eef0f3;
  border-radius: 6px;
}

.mk__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mk__thumb-fallback {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--ink-muted);
}

.mk__current-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}

.mk__current-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mk__current-hint {
  font-size: 0.7rem;
  color: var(--ink-muted);
}

.mk__browse {
  flex: none;
  padding: 7px 14px;
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.18s var(--ease-out);
}

.mk__browse:hover {
  background: var(--accent-deep);
}

.mk__options {
  flex-wrap: wrap;
  gap: 14px;
}

.mk__option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--ink-soft);
  cursor: pointer;
}

.mk__option-hint {
  font-size: 0.7rem;
  color: var(--ink-muted);
}

/* ── 弹层 ───────────────────────────────────── */
.mk-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(16, 24, 38, 0.44);
}

.mk-modal {
  display: flex;
  flex-direction: column;
  width: min(1080px, 100%);
  height: min(720px, 90vh);
  overflow: hidden;
  background: #fff;
  border-radius: 14px;
  box-shadow: var(--shadow-lg);
}

.mk-modal__head {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.mk-modal__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--ink);
}

.mk-modal__search {
  flex: 1;
  max-width: 340px;
  padding: 8px 12px;
  font-family: inherit;
  font-size: 0.82rem;
  color: var(--ink);
  background: #fbfbfd;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
}

.mk-modal__close {
  margin-left: auto;
  width: 30px;
  height: 30px;
  font-size: 1.1rem;
  line-height: 1;
  color: var(--ink-muted);
  background: #f4f5f7;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.mk-modal__close:hover {
  color: var(--ink);
  background: #eceef1;
}

.mk-modal__body {
  display: grid;
  grid-template-columns: 1fr 260px;
  flex: 1;
  min-height: 0;
}

/* 列表 */
.mk-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 16px;
  overflow-y: auto;
}

.mk-content__note {
  margin-bottom: 10px;
  font-size: 0.76rem;
  color: var(--ink-muted);
}

.mk-content__note--warn {
  color: #9a6a12;
}

.mk-content__retry {
  margin-left: 8px;
  padding: 2px 10px;
  font-family: inherit;
  font-size: 0.74rem;
  color: var(--accent);
  background: #fff;
  border: 1px solid var(--accent);
  border-radius: 6px;
  cursor: pointer;
}

/* 风格筛选 */
.mk-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.mk-chip {
  padding: 5px 13px;
  font-family: inherit;
  font-size: 0.76rem;
  color: var(--ink-soft);
  background: #f7f8fa;
  border: 1px solid var(--border);
  border-radius: 999px;
  cursor: pointer;
  transition:
    color 0.16s var(--ease-out),
    background-color 0.16s var(--ease-out),
    border-color 0.16s var(--ease-out);
}

.mk-chip:hover {
  border-color: var(--border-strong);
}

.mk-chip.is-active {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.mk-content__empty {
  margin: 40px 0;
  font-size: 0.84rem;
  text-align: center;
  color: var(--ink-muted);
}

.mk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.mk-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 6px;
  font-family: inherit;
  text-align: left;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition:
    border-color 0.16s var(--ease-out),
    box-shadow 0.16s var(--ease-out);
}

.mk-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-sm);
}

.mk-card.is-active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

.mk-card__thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: #eef0f3;
  border-radius: 7px;
}

.mk-card__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mk-card__thumb-fallback {
  padding: 6px;
  font-size: 0.72rem;
  text-align: center;
  color: var(--ink-muted);
}

.mk-card__name {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mk-card__badge {
  align-self: flex-start;
  padding: 1px 8px;
  font-size: 0.68rem;
  color: var(--ink-muted);
  background: #f4f5f7;
  border-radius: 999px;
}

/* 详情 */
.mk-detail {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border-left: 1px solid var(--border);
  overflow-y: auto;
}

.mk-detail__preview {
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: #eef0f3;
  border-radius: 10px;
}

.mk-detail__preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mk-detail__preview-fallback {
  font-size: 0.78rem;
  color: var(--ink-muted);
}

.mk-detail__name {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink);
}

.mk-detail__badges {
  display: flex;
  gap: 6px;
  margin: 0;
}

.mk-badge {
  padding: 2px 9px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent-deep);
  background: rgba(43, 108, 176, 0.1);
  border-radius: 999px;
}

.mk-badge--muted {
  color: var(--ink-muted);
  background: #f4f5f7;
}

.mk-detail__use {
  margin-top: auto;
  padding: 10px 16px;
  font-family: inherit;
  font-size: 0.84rem;
  font-weight: 700;
  color: #fff;
  background: var(--accent);
  border: none;
  border-radius: 9px;
  cursor: pointer;
}

.mk-detail__use:hover {
  background: var(--accent-deep);
}

.mk-detail__empty {
  margin: 40px 0;
  font-size: 0.8rem;
  text-align: center;
  color: var(--ink-muted);
}

.mk-detail__default {
  padding: 8px 12px;
  font-family: inherit;
  font-size: 0.78rem;
  color: var(--ink-soft);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  cursor: pointer;
}

.mk-detail__default:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* 焦点可见性 */
.mk__browse:focus-visible,
.mk-modal__close:focus-visible,
.mk-card:focus-visible,
.mk-chip:focus-visible,
.mk-content__retry:focus-visible,
.mk-detail__use:focus-visible,
.mk-detail__default:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (max-width: 900px) {
  .mk-modal__body {
    grid-template-columns: 1fr;
  }

  .mk-detail {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mk__browse,
  .mk-card {
    transition: none;
  }
}
</style>
