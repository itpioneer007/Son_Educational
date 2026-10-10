<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import SiteNav from "./layout/SiteNav.vue";

const mouse = ref({ x: 0.5, y: 0.5 });
const router = useRouter();

// 4张功能展示卡片
const showcaseItems = [
  {
    id: 1,
    title: "AI 智能备课",
    subtitle: "描述课题，一键生成教案与课件初稿",
    description:
      "填写学科、课题与教学要求，AI 自动生成结构完整的教案与课件初稿。<em>DeepSeek 驱动</em>，覆盖导入、讲授、练习到板书全流程。",
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"/><circle cx="19" cy="19" r="3"/><path d="M17 19h4"/></svg>`,
    gradient: "linear-gradient(135deg, #f97316 0%, #ef4444 50%, #f43f5e 100%)",
    accent: "#f97316",
    shape: "ripple",
    route: "/assistant",
    imageUrl: "/image/showcase/prepare.jpg",
  },
  {
    id: 2,
    title: "课件管理",
    subtitle: "精美模版一键套用，生成即用",
    description:
      "统一管理已生成的课件、教案、练习题与试卷，支持 <em>PPTX / DOCX / HTML</em> 一键导出。<em>5 套本地精美模版</em>，按学科自动匹配，只改内容不改设计。",
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h6M8 16h4"/></svg>`,
    gradient: "linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",
    accent: "#10b981",
    shape: "grid",
    route: "/lessons",
    imageUrl: "/image/showcase/cources.jpg",
  },
  {
    id: 3,
    title: "数据分析",
    subtitle: "教学趋势，可视化图表洞察",
    description:
      "<em>创作统计</em>仪表盘，以图表展示备课量趋势与内容类型分布。按 <em>今天 / 近 7 天 / 近 30 天 / 本季度</em> 多维度筛选，辅助教学规划。",
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="14" width="4" height="6" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="16" y="3" width="4" height="17" rx="1"/></svg>`,
    gradient: "linear-gradient(135deg, #f59e0b 0%, #d97706 50%, #b45309 100%)",
    accent: "#f59e0b",
    shape: "dots",
    route: "/features",
    imageUrl: "/image/showcase/analytics.jpg",
  },
  {
    id: 4,
    title: "教学社区",
    subtitle: "分享经验，与同行教师互动交流",
    description:
      "<em>教师教研社区</em>，发布教学话题与资源分享。支持 <em>点赞 / 评论 / 收藏</em> 互动，按学科分类浏览，与同行交流实践心得。",
    icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="3"/><circle cx="16" cy="8" r="3"/><path d="M3 20c0-3.3 2.2-6 5-6h2c2.8 0 5 2.7 5 6"/><path d="M14 14c2.8 0 5 2.7 5 6"/></svg>`,
    gradient: "linear-gradient(135deg, #ec4899 0%, #db2777 50%, #be185d 100%)",
    accent: "#ec4899",
    shape: "wave",
    route: "/community",
    imageUrl: "/image/showcase/community.jpg",
  },
];

const currentIndex = ref(0);
const isAnimating = ref(false);
const progress = ref(0);
let autoPlayTimer = null;
let progressTimer = null;
const AUTO_PLAY_INTERVAL = 4000; // 4秒切换

function nextSlide() {
  if (isAnimating.value) return;
  isAnimating.value = true;
  currentIndex.value = (currentIndex.value + 1) % showcaseItems.length;
  progress.value = 0;
  setTimeout(() => {
    isAnimating.value = false;
  }, 600);
}

function goToSlide(index) {
  if (isAnimating.value || index === currentIndex.value) return;
  isAnimating.value = true;
  currentIndex.value = index;
  progress.value = 0;
  setTimeout(() => {
    isAnimating.value = false;
  }, 600);
}

function navigateToFeature() {
  const item = showcaseItems[currentIndex.value];
  if (item.route) {
    router.push(item.route);
  }
}

function startAutoPlay() {
  progress.value = 0;
  progressTimer = setInterval(() => {
    progress.value += 100 / (AUTO_PLAY_INTERVAL / 50);
    if (progress.value >= 100) progress.value = 0;
  }, 50);
  autoPlayTimer = setInterval(nextSlide, AUTO_PLAY_INTERVAL);
}

function stopAutoPlay() {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer);
    autoPlayTimer = null;
  }
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
}

const lessonHighlights = [
  { value: "4 类教学材料", label: "课件·教案·练习·试卷", color: "#4c7dff" },
  { value: "5 套精美模版", label: "中国风·春天·历史等", color: "#23c3b2" },
  { value: "双模型驱动", label: "DeepSeek + 通义千问", color: "#8b5cf6" },
];

function onPointerMove(e) {
  mouse.value = {
    x: e.clientX / window.innerWidth,
    y: e.clientY / window.innerHeight,
  };
}

onMounted(() => {
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  startAutoPlay();
});

onUnmounted(() => {
  window.removeEventListener("pointermove", onPointerMove);
  stopAutoPlay();
});
</script>

<template>
  <div class="home">
    <SiteNav />

    <main class="hero">
      <div class="hero__inner">
        <div class="hero__copy">
          <p class="hero__eyebrow reveal" style="--i: 0">
            知启灵枢 · 教学课件工具
          </p>

          <h1 class="hero__title reveal" style="--i: 1">
            从备课思路到<br />课件初稿，<em>一气呵成</em>
          </h1>

          <p class="hero__lead reveal" style="--i: 2">
            描述教学目标与知识点，AI 自动套用精美模版生成课件 PPT、教案
            Word、课堂练习与试卷。<br />
            模版按学科自动匹配，生成后可对话式反复修改，满意再导出。
          </p>

          <div
            class="lesson-stats reveal"
            style="--i: 3"
            aria-label="教学智能体能力概览"
          >
            <article
              v-for="item in lessonHighlights"
              :key="item.label"
              class="lesson-stat"
              :style="{ '--card-accent': item.color }"
            >
              <strong :style="{ color: item.color }">{{ item.value }}</strong>
              <span>{{ item.label }}</span>
            </article>
          </div>

          <div class="hero__cta reveal" style="--i: 4">
            <RouterLink to="/assistant" class="btn btn--dark btn--lg">
              立即体验 AI 助手
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </RouterLink>
            <RouterLink to="/features" class="btn btn--ghost btn--lg"
              >了解核心功能</RouterLink
            >
          </div>
        </div>

        <div class="hero__stage reveal" style="--i: 2">
          <div class="showcase-wrapper">
            <!-- 扑克牌堆叠展示 -->
            <div class="card-stack">
              <div
                v-for="(item, index) in showcaseItems"
                :key="item.id"
                class="stack-card"
                :class="{
                  'stack-card--active': index === currentIndex,
                  'stack-card--behind':
                    index !== currentIndex &&
                    (index - currentIndex + showcaseItems.length) %
                      showcaseItems.length >=
                      4,
                }"
              >
                <!-- 视觉装饰卡片 -->
                <div
                  class="showcase-card"
                  :class="{
                    'showcase-card--clickable': index === currentIndex,
                  }"
                  @click="index === currentIndex && navigateToFeature()"
                >
                  <!-- 仅展示图片，无任何文字叠加 -->
                  <img
                    class="showcase-card__bg-img"
                    :src="item.imageUrl"
                    :alt="item.title"
                  />
                </div>
              </div>
            </div>

            <!-- 功能文字信息（图片下方） -->
            <div class="showcase-info" :key="currentIndex">
              <div
                class="showcase-info__icon"
                :style="{ color: showcaseItems[currentIndex].accent }"
                v-html="showcaseItems[currentIndex].icon"
              />
              <div class="showcase-info__title">
                {{ showcaseItems[currentIndex].title }}
              </div>
              <div class="showcase-info__subtitle">
                {{ showcaseItems[currentIndex].subtitle }}
              </div>
              <div
                class="showcase-info__desc"
                v-html="showcaseItems[currentIndex].description"
              />
              <div
                class="showcase-info__bar"
                :style="{ background: showcaseItems[currentIndex].accent }"
              />
            </div>

            <!-- 简化的进度指示器 -->
            <div class="mini-dots">
              <div
                v-for="(item, index) in showcaseItems"
                :key="item.id"
                class="mini-dot"
                :class="{ 'mini-dot--active': index === currentIndex }"
                @click="goToSlide(index)"
              >
                <div
                  v-if="index === currentIndex"
                  class="mini-dot__progress"
                  :style="{ transform: `scaleX(${progress / 100})` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  color: var(--ink);
}

/* Hero */
.hero {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 100px 28px 60px;
}

.hero__inner {
  max-width: 1180px;
  margin: 0 auto;
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 56px;
  align-items: center;
}

.hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #f97316;
}

.hero__title {
  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: clamp(2.125rem, 4.8vw, 3.5rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin-bottom: 24px;
  color: #1e293b;
}

.hero__title em {
  font-style: normal;
  color: #e11d48;
}

.hero__lead {
  max-width: 520px;
  font-size: 1rem;
  line-height: 1.8;
  color: var(--ink-soft);
  margin-bottom: 28px;
  padding-left: 20px;
  border-left: 3px solid rgba(249, 115, 22, 0.12);
  position: relative;
}

.lesson-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  max-width: 560px;
  margin-bottom: 30px;
}

.lesson-stat {
  position: relative;
  padding: 14px 16px 12px;
  border: 1px solid #eef2f6;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}
.lesson-stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}

.lesson-stat::after {
  content: "";
  position: absolute;
  inset: auto 14px 0;
  height: 2px;
  border-radius: 999px;
  background: var(--card-accent, #f97316);
  opacity: 0.3;
}

.lesson-stat strong {
  display: block;
  margin-bottom: 4px;
  font-family: var(--font-display);
  font-size: 1.15rem;
  line-height: 1.3;
  font-weight: 700;
}

.lesson-stat span {
  display: block;
  font-size: 0.78rem;
  line-height: 1.4;
  color: var(--ink-muted);
  font-weight: 500;
}

.hero__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  font-size: 0.9375rem;
  font-weight: 600;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition:
    transform 0.25s var(--ease-spring),
    box-shadow 0.25s,
    background 0.25s;
  white-space: nowrap;
}

.btn--dark {
  background: #f97316;
  color: #fff;
  box-shadow: 0 4px 16px rgba(249, 115, 22, 0.3);
}

.btn--dark:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(249, 115, 22, 0.4);
}

.btn--ghost {
  background: rgba(255, 255, 255, 0.55);
  color: var(--ink);
  border: 1px solid var(--border-strong);
  backdrop-filter: blur(8px);
}

.btn--ghost:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(10, 15, 26, 0.18);
}

.btn--lg {
  padding: 15px 26px;
  font-size: 0.95rem;
}

/* Float card */
.hero__stage {
  position: relative;
  min-height: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Showcase Card Stack */
.showcase-wrapper {
  position: relative;
  width: 100%;
  max-width: 620px;
  padding: 28px 28px 12px;
}

.card-stack {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  perspective: 1200px;
}

.stack-card {
  position: absolute;
  inset: 0;
  border-radius: 24px;
  background: transparent;
  box-shadow: none;
  transform-origin: center center;
  transition:
    opacity 0.5s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.65s cubic-bezier(0.22, 1, 0.36, 1);
  overflow: hidden;
  pointer-events: none;
  opacity: 0;
  transform: translateY(20px) scale(0.94);
}

.stack-card--active {
  transform: translateY(0) scale(1);
  opacity: 1;
  z-index: 10;
  pointer-events: auto;
  box-shadow:
    0 20px 60px -12px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(255, 255, 255, 0.9) inset;
}

.stack-card--behind {
  opacity: 0.06;
  transform: translateY(12px) translateX(-8px) rotate(-1deg) scale(0.96);
  z-index: 1;
}

/* ====== Showcase Visual Card ====== */
.showcase-card {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 24px;
}

.showcase-card__bg-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.showcase-card--clickable {
  cursor: pointer;
}

/* Showcase info below the card */
.showcase-info {
  text-align: center;
  margin-top: 28px;
  padding: 0 8px;
  position: relative;
  animation: infoFadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes infoFadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.showcase-info__icon {
  font-size: 2rem;
  margin-bottom: 6px;
  transition: color 0.5s ease;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
}
.showcase-info__icon :deep(svg) {
  width: 28px;
  height: 28px;
  display: block;
}
.showcase-info__title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 4px;
}
.showcase-info__subtitle {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: #64748b;
}
.showcase-info__desc {
  font-size: 0.85rem;
  color: #94a3b8;
  line-height: 1.65;
  max-width: 380px;
  margin: 0 auto;
  position: relative;
}
.showcase-info__desc :deep(em) {
  font-style: normal;
  font-weight: 700;
  color: #1e293b;
}
.showcase-info__bar {
  width: 40px;
  height: 3px;
  border-radius: 4px;
  margin: 14px auto 0;
  transition: background 0.5s ease;
  opacity: 0.5;
}

.ui-mockup {
  height: 100%;
  display: flex;
  flex-direction: column;
  font-family:
    system-ui,
    -apple-system,
    sans-serif;
}

.mockup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.mockup-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.mockup-dot:nth-child(1) {
  background: #ef4444;
}
.mockup-dot:nth-child(2) {
  background: #f59e0b;
}
.mockup-dot:nth-child(3) {
  background: #10b981;
}

.mockup-title {
  margin-left: auto;
  font-size: 0.85rem;
  color: #64748b;
  font-weight: 600;
}

.mockup-body {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

/* Chat Interface - Enhanced */
.ui-mockup--chat .mockup-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.chat-bubble {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  animation: fadeInUp 0.5s ease both;
}

.chat-bubble:nth-child(1) {
  animation-delay: 0.1s;
}
.chat-bubble:nth-child(2) {
  animation-delay: 0.2s;
}
.chat-bubble:nth-child(3) {
  animation-delay: 0.3s;
}

.chat-bubble--ai {
  justify-content: flex-start;
}
.chat-bubble--user {
  justify-content: flex-end;
}

.chat-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.chat-bubble--ai .chat-avatar {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}
.chat-bubble--user .chat-avatar {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15);
}

.chat-text {
  max-width: 78%;
  padding: 14px 18px;
  border-radius: 20px;
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: pre-line;
}

.chat-bubble--ai .chat-text {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(226, 232, 240, 0.8);
  color: #334155;
  border-bottom-left-radius: 6px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  backdrop-filter: blur(8px);
}

.chat-bubble--user .chat-text {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border-bottom-right-radius: 6px;
  box-shadow:
    0 4px 12px rgba(59, 130, 246, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}

.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  width: fit-content;
  margin-top: 4px;
  box-shadow:
    0 2px 8px rgba(0, 0, 0, 0.04),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  backdrop-filter: blur(8px);
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  background: #94a3b8;
  border-radius: 50%;
  animation: typingBounce 1.4s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typingBounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Upload Interface - Enhanced */
.ui-mockup--upload .mockup-body {
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-zone {
  border: 2px dashed rgba(203, 213, 225, 0.8);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  background: rgba(255, 255, 255, 0.7);
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
  backdrop-filter: blur(8px);
}

.upload-zone:hover {
  border-color: #3b82f6;
  background: rgba(255, 255, 255, 0.9);
}

.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
}
.upload-text {
  font-size: 1rem;
  color: #334155;
  font-weight: 600;
  margin-bottom: 6px;
}
.upload-hint {
  font-size: 0.8rem;
  color: #94a3b8;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  font-size: 0.9rem;
  box-shadow:
    0 2px 6px rgba(0, 0, 0, 0.03),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  backdrop-filter: blur(8px);
}

.file-icon {
  font-size: 1.3rem;
}
.file-name {
  flex: 1;
  color: #334155;
  font-weight: 500;
}
.file-status {
  color: #10b981;
  font-weight: 700;
  font-size: 1rem;
}

.file-item--processing .file-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* PPT Preview - Enhanced */
.ui-mockup--ppt .mockup-body {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.ui-mockup--ppt .mockup-body::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(
      circle at 20% 80%,
      rgba(59, 130, 246, 0.15) 0%,
      transparent 50%
    ),
    radial-gradient(
      circle at 80% 20%,
      rgba(6, 182, 212, 0.1) 0%,
      transparent 50%
    );
  pointer-events: none;
}

/* PPT Container Layout */
.ppt-container {
  display: flex;
  width: 100%;
  height: 100%;
  gap: 12px;
  padding: 16px;
}

/* 左侧缩略图导航 */
.ppt-sidebar {
  width: 80px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.ppt-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px 8px;
  text-align: center;
  cursor: pointer;
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.ppt-thumb:hover {
  background: rgba(255, 255, 255, 0.15);
}

.ppt-thumb--active {
  background: rgba(59, 130, 246, 0.25);
  border-color: rgba(59, 130, 246, 0.5);
}

.thumb-page {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 4px;
}

.thumb-title {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 主幻灯片区域 */
.ppt-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ppt-slide-content {
  width: 100%;
  max-width: 380px;
  aspect-ratio: 4/3;
  background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  box-shadow:
    0 24px 48px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  position: relative;
  z-index: 1;
}

.slide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.slide-badge {
  font-size: 0.7rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.slide-time {
  font-size: 0.7rem;
  color: #94a3b8;
}

.slide-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 6px;
  text-align: center;
}

.slide-subtitle {
  font-size: 0.9rem;
  color: #64748b;
  text-align: center;
  margin-bottom: 20px;
}

.slide-formula {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.formula-box {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border: 2px solid #3b82f6;
  border-radius: 12px;
  padding: 16px 32px;
  text-align: center;
}

.formula-text {
  display: block;
  font-size: 1.8rem;
  font-weight: 800;
  color: #1e40af;
  margin-bottom: 8px;
  font-family: "Times New Roman", serif;
}

.formula-desc {
  display: block;
  font-size: 0.75rem;
  color: #3b82f6;
  max-width: 200px;
  line-height: 1.4;
}

.slide-keypoints {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.keypoint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(241, 245, 249, 0.8);
  border-radius: 8px;
  font-size: 0.8rem;
  color: #475569;
}

.keypoint-icon {
  font-size: 1rem;
}

.slide-footer {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.slide-tags {
  display: flex;
  gap: 6px;
}

.slide-tag {
  font-size: 0.65rem;
  padding: 4px 10px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 12px;
  font-weight: 600;
}

.slide-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #64748b;
  cursor: pointer;
}

.nav-btn--primary {
  background: #3b82f6;
  color: white;
}

.nav-page {
  font-size: 0.75rem;
  color: #94a3b8;
}

/* 右侧工具栏 */
.ppt-toolbar {
  width: 44px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  padding: 12px 0;
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.toolbar-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.toolbar-btn--active {
  background: rgba(59, 130, 246, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.toolbar-divider {
  width: 24px;
  height: 1px;
  background: rgba(255, 255, 255, 0.2);
  margin: 4px 0;
}

/* Doc Editor - Enhanced */
.ui-mockup--doc .mockup-body {
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
  padding: 20px 24px;
}

.doc-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.doc-section {
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(241, 245, 249, 0.8);
  position: relative;
}
.doc-section:last-child {
  border-bottom: none;
}
.doc-section::before {
  content: "";
  position: absolute;
  left: -20px;
  top: 4px;
  width: 3px;
  height: 16px;
  background: linear-gradient(180deg, #3b82f6, #06b6d4);
  border-radius: 2px;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.doc-section:hover::before {
  opacity: 1;
}
.doc-h1 {
  font-size: 1rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.doc-h1::before {
  content: "";
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
}
.doc-p {
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.6;
  padding-left: 14px;
}
.doc-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 14px;
}
.doc-li {
  font-size: 0.9rem;
  color: #475569;
  padding-left: 16px;
  position: relative;
}

/* AI 备课工作台 */
.ui-mockup--workspace .workspace-body {
  display: flex;
  height: calc(100% - 44px);
  background: #f8fafc;
}

.workspace-sidebar {
  width: 140px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.sidebar-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 8px;
  border-radius: 8px;
  margin-bottom: 6px;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.task-item:hover {
  background: #f1f5f9;
}

.task-item--active {
  background: #eff6ff;
  border: 1px solid #dbeafe;
}

.task-icon {
  font-size: 1rem;
}

.task-name {
  flex: 1;
  font-size: 0.75rem;
  color: #334155;
  font-weight: 500;
}

.task-status {
  font-size: 0.6rem;
  padding: 2px 6px;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 10px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-btn {
  padding: 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.75rem;
  color: #475569;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
  text-align: left;
}

.quick-btn:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1e40af;
}

.workspace-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: #3b82f6;
  margin-bottom: 4px;
}

.generated-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 8px 0 8px 44px;
}

.preview-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.preview-icon {
  font-size: 1.5rem;
}

.preview-info {
  flex: 1;
}

.preview-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.preview-meta {
  font-size: 0.7rem;
  color: #94a3b8;
}

.preview-btn {
  padding: 6px 14px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  font-size: 0.85rem;
  background: #ffffff;
}

.chat-input::placeholder {
  color: #94a3b8;
}

.send-btn {
  width: 40px;
  height: 40px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 学情分析仪表盘 */
.ui-mookup--dashboard .dashboard-body {
  padding: 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card-mini {
  flex: 1;
  background: #ffffff;
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: #1e293b;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 6px;
}

.stat-trend {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  display: inline-block;
}

.trend-up {
  background: #d1fae5;
  color: #065f46;
}

.trend-down {
  background: #dbeafe;
  color: #1e40af;
}

.trend-warn {
  background: #fee2e2;
  color: #991b1b;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.section-icon {
  font-size: 1.1rem;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.knowledge-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.knowledge-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.knowledge-name {
  width: 100px;
  font-size: 0.8rem;
  color: #475569;
}

.knowledge-bar {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.knowledge-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.fill-warn {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.fill-avg {
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
}

.knowledge-percent {
  width: 36px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #1e293b;
  text-align: right;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
}

.suggestion-priority {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}

.priority-high {
  background: #fee2e2;
  color: #991b1b;
}

.priority-medium {
  background: #fef3c7;
  color: #92400e;
}

.suggestion-text {
  flex: 1;
  font-size: 0.8rem;
  color: #475569;
}

.action-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

/* 课件智能诊断 */
.ui-mockup--optimize .optimize-body {
  padding: 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.score-circle {
  width: 100px;
  height: 100px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #3b82f6, #06b6d4);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
}

.score-value {
  font-size: 2rem;
  font-weight: 800;
  color: white;
}

.score-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.9);
}

.optimize-sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.optimize-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.optimize-card--success {
  border-left: 4px solid #10b981;
}

.optimize-card--warning {
  border-left: 4px solid #f59e0b;
}

.optimize-card--info {
  border-left: 4px solid #3b82f6;
}

.optimize-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.optimize-icon {
  font-size: 1.2rem;
}

.optimize-title {
  flex: 1;
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.optimize-score {
  font-size: 0.85rem;
  font-weight: 800;
  color: #3b82f6;
}

.optimize-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 12px;
  line-height: 1.4;
}

.fix-btn {
  padding: 8px 16px;
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

/* 智能批改中心 */
.ui-mockup--grading .grading-body {
  padding: 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
}

.grading-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  align-items: center;
}

.grading-progress {
  flex-shrink: 0;
}

.progress-ring {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #10b981, #34d399);
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.25);
}

.progress-value {
  font-size: 1.4rem;
  font-weight: 800;
  color: white;
}

.progress-label {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.9);
}

.grading-summary {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.summary-label {
  font-size: 0.75rem;
  color: #64748b;
}

.summary-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
}

.error-analysis {
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #e2e8f0;
}

.analysis-title {
  font-size: 0.9rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 14px;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.error-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
}

.error-rank {
  width: 28px;
  height: 28px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
}

.error-content {
  flex: 1;
}

.error-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 2px;
}

.error-count {
  font-size: 0.7rem;
  color: #94a3b8;
}

.error-btn {
  padding: 6px 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
}

/* 智能资源库 */
.ui-mockup--resource .resource-body {
  padding: 16px;
  background: #f8fafc;
}

.resource-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.search-icon {
  font-size: 0.9rem;
  color: #94a3b8;
}

.search-input {
  flex: 1;
  border: none;
  font-size: 0.8rem;
  color: #334155;
  background: transparent;
}

.search-input::placeholder {
  color: #94a3b8;
}

.upload-btn {
  padding: 10px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.resource-categories {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  overflow-x: auto;
}

.category-btn {
  padding: 6px 14px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #64748b;
  cursor: pointer;
  white-space: nowrap;
}

.category-btn--active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.resource-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.resource-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resource-card--new {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.resource-thumb {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}

.resource-thumb--doc {
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
}

.resource-thumb--video {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
}

.resource-thumb--ai {
  background: linear-gradient(135deg, #ede9fe, #ddd6fe);
}

.resource-info {
  flex: 1;
}

.resource-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-meta {
  font-size: 0.65rem;
  color: #94a3b8;
}

.resource-actions {
  display: flex;
  gap: 6px;
}

.action-icon {
  width: 28px;
  height: 28px;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.doc-li {
  position: relative;
}
.doc-li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: #3b82f6;
  font-weight: 700;
}

/* Mini Dots Progress */
.mini-dots {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 24px;
}

.mini-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
}

.mini-dot:hover {
  background: #94a3b8;
  transform: scale(1.2);
}
.mini-dot--active {
  width: 32px;
  border-radius: 4px;
  background: #e2e8f0;
}

.mini-dot__progress {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #3b82f6, #06b6d4);
  border-radius: 4px;
  transform-origin: left;
  transition: transform 0.05s linear;
}

/* Showcase Hint (unused) */
.showcase-hint,
.hint-icon,
.hint-content,
.hint-title,
.hint-desc {
  display: none;
}

/* Old Float Styles */
.float-wrap {
  position: relative;
  width: 100%;
  max-width: 500px;
  aspect-ratio: 0.95 / 1;
  animation: float-main 7s ease-in-out infinite;
}

.float-card {
  position: absolute;
  border-radius: 30px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  background:
    linear-gradient(
      150deg,
      rgba(255, 255, 255, 0.88),
      rgba(248, 252, 255, 0.64)
    ),
    radial-gradient(circle at 80% 20%, rgba(0, 194, 212, 0.14), transparent 34%);
  backdrop-filter: blur(28px) saturate(1.35);
  box-shadow:
    0 1px 2px rgba(10, 15, 26, 0.04),
    0 34px 110px rgba(0, 87, 217, 0.16);
}

.float-card--back {
  inset: 8% -5% -8% 10%;
  transform: rotate(5deg);
  opacity: 0.42;
  animation: float-back 8s ease-in-out infinite;
}

.float-card--main {
  inset: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.float-card__chrome {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border);
  font-size: 0.75rem;
  color: var(--ink-muted);
}

.float-card__chrome span {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.float-card__chrome span:nth-child(1) {
  background: #ff6b6b;
}
.float-card__chrome span:nth-child(2) {
  background: #ffd166;
}
.float-card__chrome span:nth-child(3) {
  background: #06d6a0;
}
.float-card__chrome em {
  margin-left: auto;
  font-style: normal;
  font-weight: 500;
}

.float-card__content {
  padding: 22px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.visual-board {
  position: relative;
  padding: 10px;
  border-radius: 24px;
  background: linear-gradient(
    135deg,
    rgba(10, 15, 26, 0.06),
    rgba(255, 255, 255, 0.62)
  );
  border: 1px solid rgba(10, 15, 26, 0.06);
}

.visual-board__photo {
  position: relative;
  min-height: 238px;
  border-radius: 20px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(10, 15, 26, 0.02), rgba(10, 15, 26, 0.12)),
    radial-gradient(
      circle at 78% 22%,
      rgba(255, 255, 255, 0.98),
      transparent 18%
    ),
    linear-gradient(135deg, #dff1ff 0%, #f7fbff 43%, #c7e6ff 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.visual-board__photo::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.42) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.32) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.9), transparent 82%);
}

.board-screen {
  position: absolute;
  left: 28px;
  top: 24px;
  width: 58%;
  min-height: 146px;
  padding: 16px;
  border-radius: 18px;
  color: #fff;
  background:
    linear-gradient(145deg, rgba(0, 91, 181, 0.96), rgba(0, 194, 212, 0.82)),
    radial-gradient(circle at 15% 0%, rgba(255, 255, 255, 0.4), transparent 38%);
  box-shadow: 0 20px 50px rgba(0, 87, 217, 0.2);
}

.board-screen__tag {
  display: inline-flex;
  margin-bottom: 10px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
  font-size: 0.68rem;
  font-weight: 700;
}

.board-screen strong {
  display: block;
  font-family: var(--font-display);
  font-size: 1.08rem;
  line-height: 1.2;
}

.force-diagram {
  position: relative;
  height: 58px;
  margin-top: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.14);
}

.force-diagram__block {
  position: absolute;
  left: 18px;
  bottom: 16px;
  width: 46px;
  height: 24px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 10px 20px rgba(0, 35, 82, 0.16);
}

.force-diagram__arrow {
  position: absolute;
  left: 72px;
  bottom: 27px;
  width: 62px;
  height: 2px;
  background: #fff;
}

.force-diagram__arrow::after {
  content: "";
  position: absolute;
  right: -1px;
  top: -4px;
  width: 10px;
  height: 10px;
  border-top: 2px solid #fff;
  border-right: 2px solid #fff;
  transform: rotate(45deg);
}

.force-diagram__label {
  position: absolute;
  right: 12px;
  top: 12px;
  font-family: var(--font-display);
  font-size: 0.86rem;
  font-weight: 700;
}

.teacher-figure {
  position: absolute;
  right: 52px;
  bottom: 22px;
  width: 76px;
  height: 142px;
}

.teacher-figure__head,
.teacher-figure__body,
.teacher-figure__arm {
  position: absolute;
  display: block;
}

.teacher-figure__head {
  top: 0;
  left: 25px;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(145deg, #ffe2c2, #f5b980);
}

.teacher-figure__body {
  top: 36px;
  left: 18px;
  width: 48px;
  height: 84px;
  border-radius: 26px 26px 18px 18px;
  background: linear-gradient(180deg, #0a0f1a, #2e4966);
}

.teacher-figure__arm {
  top: 50px;
  left: 4px;
  width: 54px;
  height: 10px;
  border-radius: 999px;
  background: #f5b980;
  transform: rotate(-28deg);
  transform-origin: right center;
}

.student-desk {
  position: absolute;
  bottom: 0;
  width: 96px;
  height: 54px;
  border-radius: 22px 22px 0 0;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.86),
    rgba(221, 237, 250, 0.92)
  );
  box-shadow: 0 -12px 30px rgba(10, 15, 26, 0.08);
}

.student-desk::before {
  content: "";
  position: absolute;
  left: 34px;
  top: -24px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(145deg, #2f5f8e, #0a0f1a);
}

.student-desk--left {
  left: 28px;
}

.student-desk--right {
  right: 146px;
  transform: scale(0.86);
  opacity: 0.82;
}

.visual-board__caption {
  display: grid;
  grid-template-columns: 0.72fr 1fr;
  gap: 12px;
  align-items: center;
  padding: 12px 4px 2px;
}

.visual-board__caption strong {
  font-family: var(--font-display);
  font-size: 0.94rem;
  line-height: 1.35;
}

.visual-board__caption span {
  font-size: 0.76rem;
  line-height: 1.55;
  color: var(--ink-muted);
}

.workflow-rail {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.workflow-rail::before {
  content: "";
  position: absolute;
  left: 12%;
  right: 12%;
  top: 50%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 119, 230, 0.28),
    transparent
  );
}

.workflow-step {
  position: relative;
  z-index: 1;
  display: inline-flex;
  justify-content: center;
  padding: 8px 6px;
  border: 1px solid rgba(0, 119, 230, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink-muted);
  font-size: 0.72rem;
  font-weight: 700;
}

.workflow-step--active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(100deg, var(--accent), var(--cyan));
  box-shadow: 0 10px 24px rgba(0, 119, 230, 0.22);
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.material-card {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(10, 15, 26, 0.07);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
}

.material-card > span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 11px;
  background: rgba(0, 119, 230, 0.09);
  color: var(--accent-deep);
  font-size: 0.68rem;
  font-weight: 800;
}

.material-card strong,
.material-card small {
  display: block;
}

.material-card strong {
  margin-bottom: 2px;
  font-size: 0.8rem;
}

.material-card small {
  font-size: 0.68rem;
  line-height: 1.4;
  color: var(--ink-muted);
}

.mini-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.mini-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.875rem;
  color: var(--ink-soft);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(10, 15, 26, 0.12);
  flex-shrink: 0;
}

.dot--done {
  background: #06d6a0;
}

.dot--active {
  background: var(--accent);
  box-shadow: 0 0 0 4px rgba(0, 119, 230, 0.2);
  animation: pulse-dot 2s ease infinite;
}

.float-chip {
  position: absolute;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 15px;
  font-size: 0.8125rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: 999px;
  box-shadow: 0 10px 36px rgba(10, 15, 26, 0.08);
  white-space: nowrap;
}

.float-chip svg {
  width: 16px;
  height: 16px;
}

.float-chip--1 {
  top: 3%;
  right: -3%;
  color: var(--accent-deep);
  animation: float-chip-a 5.5s ease-in-out infinite;
}

.float-chip--2 {
  bottom: 11%;
  left: -9%;
  animation: float-chip-b 6.5s ease-in-out infinite 0.4s;
}

.float-chip--3 {
  right: -8%;
  bottom: 27%;
  color: #0e765b;
  animation: float-chip-a 6s ease-in-out infinite 0.8s;
}

/* Animations */
.reveal {
  opacity: 0;
  transform: translateY(22px);
  animation: reveal-up 0.85s var(--ease-out) forwards;
  animation-delay: calc(0.07s * var(--i, 0) + 0.1s);
}

@keyframes reveal-up {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes float-main {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-16px);
  }
}

@keyframes float-back {
  0%,
  100% {
    transform: rotate(5deg) translateY(0);
  }
  50% {
    transform: rotate(5deg) translateY(-12px);
  }
}

@keyframes float-chip-a {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes float-chip-b {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px) translateX(5px);
  }
}

@keyframes pulse-dot {
  0%,
  100% {
    box-shadow: 0 0 0 4px rgba(0, 119, 230, 0.2);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(0, 119, 230, 0.07);
  }
}

/* ── prefers-reduced-motion ── */
@media (prefers-reduced-motion: reduce) {
  .hero__inner .reveal {
    opacity: 1 !important;
    transform: none !important;
  }
  .showcase-info {
    animation: none !important;
  }
  .stack-card {
    transition: none !important;
  }
  .mini-dot__progress {
    transition: none !important;
  }
  .chat-bubble {
    animation: none !important;
  }
  .typing-indicator span {
    animation: none !important;
  }
  .file-item--processing .file-spinner {
    animation: none !important;
    border-top-color: #94a3b8;
  }
  .float-wrap {
    animation: none !important;
  }
  .float-card--back {
    animation: none !important;
  }
  [class*="float"] {
    animation: none !important;
  }
  [class*="pulse"] {
    animation: none !important;
  }
}

@media (max-width: 1024px) {
  .hero__inner {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 40px;
  }

  .hero__lead {
    margin-left: auto;
    margin-right: auto;
  }
  .lesson-stats {
    margin-left: auto;
    margin-right: auto;
  }
  .hero__cta {
    justify-content: center;
  }
  .hero__stage {
    min-height: 520px;
  }
  .showcase-wrapper {
    max-width: 520px;
    padding: 20px;
  }
  .showcase-info {
    margin-top: 20px;
  }
  .hint-icon {
    width: 40px;
    height: 40px;
    font-size: 1.3rem;
  }
}

@media (max-width: 768px) {
  .hero {
    padding: 96px 20px 48px;
  }
  .lesson-stats {
    grid-template-columns: 1fr;
  }
  .float-chip--1 {
    right: 0;
  }
  .float-chip--2 {
    left: 0;
  }
  .float-chip--3 {
    right: 0;
  }
  .material-grid {
    grid-template-columns: 1fr;
  }
  .showcase-wrapper {
    max-width: 460px;
    padding: 20px;
  }
  .mini-dots {
    margin-top: 20px;
  }
}

@media (max-width: 480px) {
  .hero__cta {
    flex-direction: column;
    width: 100%;
  }
  .hero__cta .btn {
    width: 100%;
  }
  .hero__stage {
    min-height: 480px;
  }
  .showcase-wrapper {
    max-width: 400px;
    padding: 16px;
  }
  .stack-card {
    border-radius: 18px;
  }
  .mini-dots {
    margin-top: 16px;
    gap: 8px;
  }
  .mini-dot {
    width: 6px;
    height: 6px;
  }
  .mini-dot--active {
    width: 24px;
  }
  .showcase-info {
    margin-top: 16px;
  }
  .hint-icon {
    width: 36px;
    height: 36px;
    font-size: 1.1rem;
    border-radius: 10px;
  }
  .hint-title {
    font-size: 0.9rem;
  }
  .hint-desc {
    font-size: 0.75rem;
  }
  .float-wrap {
    aspect-ratio: auto;
    min-height: 620px;
  }
  .float-card--main {
    inset: 18px 0 0;
  }
  .float-card--back {
    inset: 8% 3% 2% 7%;
  }
  .visual-board__caption {
    grid-template-columns: 1fr;
  }
  .workflow-rail {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .visual-board__photo {
    min-height: 214px;
  }
  .board-screen {
    left: 16px;
    width: 64%;
  }
  .teacher-figure {
    right: 22px;
    transform: scale(0.86);
    transform-origin: bottom right;
  }
}
</style>
