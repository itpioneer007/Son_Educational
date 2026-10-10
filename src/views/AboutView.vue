<script setup>
import { RouterLink } from "vue-router";
import SiteNav from "../components/layout/SiteNav.vue";

const capabilities = [
  {
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 01-12.4 8.3L3 22l1.7-5.6A9 9 0 1121 12z"/></svg>',
    title: "理解教学意图",
    desc: "通过文字多轮对话，主动询问并确认教学目标、核心知识点、讲授逻辑、重难点与课堂互动设计。",
  },
  {
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 20L18 8a3 3 0 00-4.2-4.2L4 13.5"/><path d="M14 6l-8 8"/></svg>',
    title: "融合教学要素",
    desc: "把课标要求、教材章节、学情特点与讲授风格一并纳入生成约束，产出贴合真实课堂的材料。",
  },
  {
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"/></svg>',
    title: "生成教学内容",
    desc: "输出结构完整的课件 PPT、教案 Word，以及课堂练习与试卷，模版按学科自动匹配。",
  },
  {
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.5 9a9 9 0 0115.4-3.4L23 10M1 14l4.1 4.4A9 9 0 0020.5 15"/></svg>',
    title: "支持迭代优化",
    desc: "形成「对话 → 生成 → 反馈 → 再生成」闭环，支持预览修改与下载后自行编辑细节。",
  },
];

const values = [
  {
    title: "对话式输入",
    desc: "用自然语言描述课标、教材、学情与教学要求，AI 理解后按结构生成",
  },
  {
    title: "多格式输出",
    desc: "一键导出课件 PPTX、教案 DOCX，以及课堂练习与试卷 HTML",
  },
  { title: "可迭代", desc: "生成初稿后可反复提出修改意见，预览满意后再下载" },
];

const team = [
  { name: "教学场景设计", role: "课堂调研 · 交互方案" },
  { name: "AI 模型工程", role: "语言模型集成 · 提示词工程" },
  { name: "前端开发", role: "Vue3 · 课件编辑器" },
];
</script>

<template>
  <div class="about-page">
    <SiteNav />

    <main>
      <section class="hero">
        <p class="eyebrow">About</p>
        <h1>关于知启灵枢</h1>
        <p class="hero__lead">
          面向中小学教师的 AI 备课工具，整合教师问答、内容创作、教学档案与教研社区。
          从教学目标到课件、教案、课堂练习与试卷，覆盖备课到反思的全流程。
        </p>
      </section>

      <section class="block">
        <div class="block__grid">
          <div class="block__content">
            <h2>项目背景</h2>
            <p>
              随着教育信息化 2.0
              行动的深入推进，人工智能技术正成为重塑教学模式的核心驱动力。
              当前，虽然 AI 辅助教学工具层出不穷，但多数工具功能单一、操作割裂，
              未能形成以教师教学思路为核心的闭环工作流。
            </p>
            <p>
              教师在使用这些工具时，仍需耗费大量时间在课件的内容组织、格式调整、资源搜寻等重复性劳动上，
              而非专注于教学逻辑与创意的构思。生成式 AI
              和多模态理解技术的成熟，为破解这一困境提供了可能。
            </p>
          </div>
          <div class="block__aside">
            <div class="quote-card">
              <p>「从备课思路到课件产出，在一套工具内完成」</p>
              <span>— 知启灵枢</span>
            </div>
          </div>
        </div>
      </section>

      <section class="block">
        <h2 class="block__title">解决的问题</h2>
        <div class="problem-grid">
          <article class="problem-card">
            <h3>备课工具分散</h3>
            <p>
              教案用 Word、课件用 PPT、素材从各处搜集，切换窗口耗费大量时间。
            </p>
          </article>
          <article class="problem-card">
            <h3>格式调整繁琐</h3>
            <p>内容写好了还要花时间排版、配图、调样式，重复劳动多。</p>
          </article>
          <article class="problem-card">
            <h3>资源查找耗时</h3>
            <p>找一份合适的课件模板或教学素材，往往要在网站间来回对比。</p>
          </article>
        </div>
      </section>

      <section class="block">
        <h2 class="block__title">四大核心能力</h2>
        <div class="cap-grid">
          <article
            v-for="cap in capabilities"
            :key="cap.title"
            class="cap-card"
          >
            <span class="cap-card__icon" v-html="cap.icon"></span>
            <h3>{{ cap.title }}</h3>
            <p>{{ cap.desc }}</p>
          </article>
        </div>
      </section>

      <section class="block">
        <h2 class="block__title">我们的理念</h2>
        <div class="values-row">
          <article v-for="v in values" :key="v.title" class="value-card">
            <h3>{{ v.title }}</h3>
            <p>{{ v.desc }}</p>
          </article>
        </div>
      </section>

      <section class="block">
        <h2 class="block__title">团队构成</h2>
        <div class="team-grid">
          <article v-for="member in team" :key="member.name" class="team-card">
            <div class="team-card__avatar">{{ member.name.charAt(0) }}</div>
            <h3>{{ member.name }}</h3>
            <p>{{ member.role }}</p>
          </article>
        </div>
      </section>

      <section class="block block--competition">
        <div class="competition-card">
          <div class="competition-card__badge">竞赛项目</div>
          <h2>中国大学生服务外包创新创业大赛</h2>
          <p>教育信息化创新赛道 · 大模型驱动的中小学 AI 备课平台</p>
        </div>
      </section>

      <section class="cta">
        <h2>准备好开始课件共创了吗？</h2>
        <p>从 AI 助手对话开始，体验以教学思路驱动的智能生成流程。</p>
        <div class="cta__actions">
          <RouterLink to="/assistant" class="btn btn--dark"
            >开始共创</RouterLink
          >
          <RouterLink to="/features" class="btn btn--ghost"
            >探索核心功能</RouterLink
          >
        </div>
      </section>
    </main>

    <footer class="footer">
      <div class="footer__inner">
        <div class="footer__brand">
          <strong>知启灵枢</strong>
          <p>大模型驱动的中小学 AI 备课平台</p>
        </div>
        <div class="footer__links">
          <RouterLink to="/features">核心功能</RouterLink>
          <RouterLink to="/assistant">AI 助手</RouterLink>
          <RouterLink to="/community">社区</RouterLink>
        </div>
        <p class="footer__copy">
          © {{ new Date().getFullYear() }} 知启灵枢 · 保留所有权利
        </p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.about-page {
  position: relative;
  min-height: 100vh;
  color: var(--ink);
}

main {
  position: relative;
  z-index: 1;
  max-width: 960px;
  margin: 0 auto;
  padding: 120px 28px 0;
}

.hero {
  text-align: center;
  margin-bottom: 72px;
}

.eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 16px;
}

.hero h1 {
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 800;
  letter-spacing: -0.04em;
  margin-bottom: 20px;
}

.hero__lead {
  max-width: 640px;
  margin: 0 auto;
  font-size: 1.0625rem;
  line-height: 1.75;
  color: var(--ink-soft);
}

.block {
  margin-bottom: 64px;
}

.block__title {
  font-family: var(--font-display);
  font-size: 1.375rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 24px;
}

.block__grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 32px;
  align-items: start;
}

.block__content h2 {
  font-family: var(--font-display);
  font-size: 1.375rem;
  font-weight: 800;
  margin-bottom: 20px;
}

.block__content p {
  font-size: 0.9375rem;
  line-height: 1.78;
  color: var(--ink-soft);
  margin-bottom: 16px;
}

.quote-card {
  padding: 28px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(16px);
  box-shadow: 0 16px 48px rgba(0, 87, 217, 0.06);
}

.quote-card p {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.5;
}

.quote-card span {
  font-size: 0.8125rem;
  color: var(--ink-muted);
}

.problem-grid,
.cap-grid,
.values-row,
.team-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.cap-grid {
  grid-template-columns: repeat(2, 1fr);
}

.problem-card,
.cap-card,
.value-card,
.team-card {
  padding: 24px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
  transition:
    transform 0.3s var(--ease-out),
    box-shadow 0.3s;
}

.problem-card:hover,
.cap-card:hover,
.value-card:hover,
.team-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 36px rgba(10, 15, 26, 0.06);
}

.problem-card h3,
.cap-card h3,
.value-card h3,
.team-card h3 {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 10px;
}

.problem-card p,
.cap-card p,
.value-card p,
.team-card p {
  font-size: 0.875rem;
  line-height: 1.65;
  color: var(--ink-soft);
}

.cap-card__icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 12px;
}

.team-card {
  text-align: center;
}

.team-card__avatar {
  width: 48px;
  height: 48px;
  margin: 0 auto 14px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-display);
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--accent-deep));
}

.competition-card {
  padding: 40px;
  text-align: center;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(0, 119, 230, 0.15);
  background: linear-gradient(
    135deg,
    rgba(0, 119, 230, 0.06) 0%,
    rgba(0, 194, 212, 0.04) 100%
  );
}

.competition-card__badge {
  display: inline-block;
  padding: 6px 14px;
  margin-bottom: 16px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent-deep);
  background: rgba(0, 119, 230, 0.1);
  border-radius: 999px;
}

.competition-card h2 {
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.competition-card p {
  font-size: 0.9375rem;
  color: var(--ink-soft);
}

.cta {
  text-align: center;
  padding: 56px 32px;
  margin-bottom: 48px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
}

.cta h2 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 12px;
}

.cta p {
  font-size: 0.9375rem;
  color: var(--ink-soft);
  margin-bottom: 24px;
}

.cta__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.btn {
  display: inline-flex;
  align-items: center;
  padding: 13px 24px;
  font-size: 0.9375rem;
  font-weight: 600;
  border-radius: 999px;
  text-decoration: none;
  transition:
    transform 0.25s var(--ease-spring),
    box-shadow 0.25s;
}

.btn--dark {
  background: var(--ink);
  color: #fff;
  box-shadow: 0 2px 8px rgba(10, 15, 26, 0.12);
}

.btn--dark:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(10, 15, 26, 0.16);
}

.btn--ghost {
  color: var(--ink);
  border: 1px solid var(--border-strong);
  background: transparent;
}

.btn--ghost:hover {
  background: rgba(255, 255, 255, 0.6);
}

.footer {
  position: relative;
  z-index: 1;
  border-top: 1px solid var(--border);
  padding: 40px 28px;
  background: rgba(255, 255, 255, 0.5);
}

.footer__inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 24px;
}

.footer__brand strong {
  font-family: var(--font-display);
  font-size: 1rem;
}

.footer__brand p {
  font-size: 0.8125rem;
  color: var(--ink-muted);
  margin-top: 4px;
}

.footer__links {
  display: flex;
  gap: 20px;
  margin-left: auto;
}

.footer__links a {
  font-size: 0.875rem;
  color: var(--ink-soft);
  text-decoration: none;
  transition: color 0.2s;
}

.footer__links a:hover {
  color: var(--ink);
}

.footer__copy {
  width: 100%;
  font-size: 0.8125rem;
  color: var(--ink-muted);
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

@media (max-width: 768px) {
  .block__grid {
    grid-template-columns: 1fr;
  }
  .problem-grid,
  .values-row,
  .team-grid {
    grid-template-columns: 1fr;
  }
  .cap-grid {
    grid-template-columns: 1fr;
  }
  .footer__links {
    margin-left: 0;
    width: 100%;
  }
  .cta__actions {
    flex-direction: column;
  }
  .cta__actions .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
