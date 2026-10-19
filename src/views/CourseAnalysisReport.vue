<script setup>
import { ref, onMounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import SiteNav from "../components/layout/SiteNav.vue";
import { dateKey } from "../utils/demoData.js";

const router = useRouter();

// ==================== 课程数据（含能力模块分析） ====================
const courses = [
  {
    id: "lesson-1",
    title: "牛顿第二定律系统精讲",
    subject: "物理",
    gradeLevel: "高一",
    teacher: "黄冈名师",
    duration: "38分钟",
    difficulty: "中等偏难",
    // 能力模块分布（基于课程内容分析）
    abilityModules: [
      {
        name: "概念理解",
        value: 25,
        color: "#4c7dff",
        description: "定律定义、物理意义理解",
      },
      {
        name: "公式应用",
        value: 30,
        color: "#2fa8c9",
        description: "F=ma公式变形与计算",
      },
      {
        name: "图像分析",
        value: 15,
        color: "#7c6cf0",
        description: "a-F、a-m关系图像",
      },
      {
        name: "实验探究",
        value: 20,
        color: "#2fb37a",
        description: "控制变量法实验设计",
      },
      {
        name: "综合解题",
        value: 10,
        color: "#e0a04a",
        description: "连接体、正交分解综合题",
      },
    ],
    keyPoints: [
      "F=ma核心公式",
      "矢量性、瞬时性、独立性",
      "正交分解法",
      "连接体问题",
    ],
    teachingMethods: ["实验演示", "例题精讲", "互动问答", "归纳总结"],
  },
  {
    id: "lesson-2",
    title: "鸦片战争全景解析",
    subject: "历史",
    gradeLevel: "八年级",
    teacher: "螺蛳历史",
    duration: "15分钟",
    difficulty: "基础",
    abilityModules: [
      {
        name: "史实记忆",
        value: 20,
        color: "#4c7dff",
        description: "时间、地点、人物记忆",
      },
      {
        name: "因果分析",
        value: 25,
        color: "#2fa8c9",
        description: "战争爆发原因分析",
      },
      {
        name: "史料解读",
        value: 20,
        color: "#7c6cf0",
        description: "条约内容、史料分析",
      },
      {
        name: "影响评价",
        value: 25,
        color: "#e0a04a",
        description: "历史影响与意义评价",
      },
      {
        name: "时空观念",
        value: 10,
        color: "#2fb37a",
        description: "中外历史联系对比",
      },
    ],
    keyPoints: [
      "贸易逆差与鸦片走私",
      "虎门销烟",
      "《南京条约》",
      "半殖民地半封建社会",
    ],
    teachingMethods: ["动画演示", "史料展示", "时间轴梳理", "对比分析"],
  },
  {
    id: "lesson-3",
    title: "加速度概念深度讲解",
    subject: "物理",
    gradeLevel: "高一",
    teacher: "黄冈中学",
    duration: "25分钟",
    difficulty: "基础",
    abilityModules: [
      {
        name: "概念建构",
        value: 35,
        color: "#4c7dff",
        description: "加速度定义与物理意义",
      },
      {
        name: "图像理解",
        value: 30,
        color: "#7c6cf0",
        description: "v-t图像斜率分析",
      },
      {
        name: "计算应用",
        value: 20,
        color: "#2fa8c9",
        description: "a=Δv/Δt计算",
      },
      {
        name: "生活联系",
        value: 10,
        color: "#2fb37a",
        description: "生活实例分析",
      },
      {
        name: "易错辨析",
        value: 5,
        color: "#e0a04a",
        description: "速度与加速度区分",
      },
    ],
    keyPoints: ["加速度定义式", "加速度与速度关系", "v-t图像斜率", "方向判断"],
    teachingMethods: ["生活实例", "图像教学", "概念辨析", "练习巩固"],
  },
];

// ==================== 能力模块归类（图例即归类口径） ====================
const abilityLegend = [
  {
    category: "认知理解类",
    items: ["概念理解", "概念建构", "史实记忆"],
    color: "#4c7dff",
    meaning: "概念建立与记忆层面的内容",
  },
  {
    category: "应用分析类",
    items: ["公式应用", "计算应用", "因果分析", "图像分析", "图像理解"],
    color: "#2fa8c9",
    meaning: "把知识迁移到具体问题与材料中的训练",
  },
  {
    category: "综合评价类",
    items: ["综合解题", "影响评价", "史料解读", "时空观念"],
    color: "#7c6cf0",
    meaning: "跨知识点的综合判断与评价",
  },
  {
    category: "实验探究类",
    items: ["实验探究", "生活联系", "易错辨析"],
    color: "#2fb37a",
    meaning: "实验设计、生活联系与易错辨析",
  },
];

const CATEGORY_MEANING = Object.fromEntries(
  abilityLegend.map((g) => [g.category, g.meaning]),
);

function categoryOf(name) {
  const group = abilityLegend.find((g) => g.items.includes(name));
  return group ? group.category : "其他能力";
}

// ==================== 图表实例存储 ====================
const chartInstances = ref([]);
const reportRef = ref(null);
const generatedAt = ref(new Date().toLocaleString("zh-CN"));

// ==================== 生成饼图配置 ====================
function generatePieOption(course) {
  const data = course.abilityModules.map((item) => ({
    value: item.value,
    name: item.name,
    itemStyle: { color: item.color },
    description: item.description,
  }));

  return {
    // 居中显示模块数量，代替原先塞在图表顶部的课程标题
    title: {
      text: String(course.abilityModules.length),
      subtext: "能力模块",
      left: "36%",
      top: "42%",
      textAlign: "center",
      textStyle: {
        fontSize: 26,
        fontWeight: 700,
        color: "#0f172a",
        fontFamily: "inherit",
      },
      subtextStyle: {
        fontSize: 11,
        color: "#93a3b5",
      },
    },
    tooltip: {
      trigger: "item",
      formatter: function (params) {
        const module = course.abilityModules.find(
          (m) => m.name === params.name,
        );
        return `
          <div style="padding: 2px 4px; max-width: 200px;">
            <div style="font-weight: 600; margin-bottom: 4px; color: ${params.color}">
              ${params.name}
            </div>
            <div style="font-size: 12px; color: #6b7c93; margin-bottom: 4px; line-height: 1.5;">
              ${module?.description || ""}
            </div>
            <div style="font-size: 12px; color: #33475b;">
              权重 ${params.value}% · 占本节 ${params.percent}%
            </div>
          </div>
        `;
      },
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "rgba(10, 15, 26, 0.08)",
      borderWidth: 1,
      extraCssText:
        "box-shadow: 0 8px 24px rgba(10,15,26,0.10); border-radius: 10px;",
    },
    legend: {
      orient: "vertical",
      right: 0,
      top: "center",
      itemGap: 13,
      itemWidth: 8,
      itemHeight: 8,
      icon: "circle",
      textStyle: {
        fontSize: 11,
        color: "#5b6b80",
      },
      formatter: function (name) {
        const item = data.find((d) => d.name === name);
        return `${name}   ${item?.value}%`;
      },
    },
    series: [
      {
        name: "能力模块",
        type: "pie",
        radius: ["50%", "76%"],
        center: ["36%", "50%"],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: { show: false },
        labelLine: { show: false },
        emphasis: {
          scale: true,
          scaleSize: 4,
          itemStyle: {
            shadowBlur: 14,
            shadowColor: "rgba(15, 23, 42, 0.14)",
          },
        },
        data: data,
        animationType: "scale",
        animationEasing: "cubicOut",
      },
    ],
  };
}

// ==================== 初始化图表 ====================
function initCharts() {
  courses.forEach((course) => {
    const chartDom = document.getElementById(`chart-${course.id}`);
    if (chartDom) {
      // 用 svg 渲染器：导出报告时整份图表能随 HTML 一起带走（canvas 不行）
      const chart = echarts.init(chartDom, null, { renderer: "svg" });
      const option = generatePieOption(course);
      chart.setOption(option);
      chartInstances.value.push(chart);
    }
  });
}

// ==================== 响应式处理 ====================
function handleResize() {
  chartInstances.value.forEach((chart) => {
    chart && chart.resize();
  });
}

// ==================== 导出报告 ====================
// 演示环境没有后端导出服务：把当前已渲染好的报告（含 ECharts 输出的 SVG）
// 打包成一份可离线打开、可继续打印为 PDF 的 HTML 文件下载。
// 图表必须用 svg 渲染器，否则画在 canvas 上、导出后是一片空白。
function exportReport() {
  const node = reportRef.value;
  if (!node) return;
  const styles = Array.from(document.querySelectorAll("style"))
    .map((s) => s.textContent || "")
    .join("\n");
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>课程内容可视化分析报告</title>
<style>body{margin:0;padding:24px;background:#f7f9fc;font-family:system-ui,"PingFang SC","Microsoft YaHei",sans-serif;}
${styles}</style>
</head>
<body>${node.outerHTML}</body>
</html>`;
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `课程内容可视化分析报告-${dateKey()}.html`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// ==================== 打印报告 ====================
function printReport() {
  window.print();
}

// ==================== 生命周期 ====================
onMounted(() => {
  nextTick(() => {
    initCharts();
    window.addEventListener("resize", handleResize);
  });
});

// ==================== 统计：全部由课程数据推导 ====================
const totalCourses = computed(() => courses.length);

const totalMinutes = computed(() =>
  courses.reduce((sum, c) => sum + (parseInt(c.duration, 10) || 0), 0),
);

const avgDuration = computed(() =>
  Math.round(totalMinutes.value / courses.length),
);

const subjectCount = computed(
  () => new Set(courses.map((c) => c.subject)).size,
);

const subjectBreakdown = computed(() => {
  const dist = new Map();
  courses.forEach((c) =>
    dist.set(c.subject, (dist.get(c.subject) || 0) + 1),
  );
  return [...dist.entries()]
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => `${name} ${count} 课时`)
    .join(" · ");
});

const totalWeight = computed(() =>
  courses.reduce(
    (sum, c) =>
      sum + c.abilityModules.reduce((s, m) => s + m.value, 0),
    0,
  ),
);

const moduleStats = computed(() => {
  const map = new Map();
  courses.forEach((c) =>
    c.abilityModules.forEach((m) => {
      const rec = map.get(m.name) || { name: m.name, total: 0, courses: 0 };
      rec.total += m.value;
      rec.courses += 1;
      map.set(m.name, rec);
    }),
  );
  return [...map.values()].sort((a, b) => a.total - b.total);
});

const moduleCount = computed(() => moduleStats.value.length);

// 按「能力类别」汇总权重，得到真实的类别占比
const categoryStats = computed(() => {
  const agg = abilityLegend.map((g) => ({
    category: g.category,
    color: g.color,
    items: g.items,
    meaning: g.meaning,
    total: 0,
    courses: 0,
  }));
  const byCat = new Map(agg.map((a) => [a.category, a]));

  courses.forEach((course) => {
    const seen = new Set();
    course.abilityModules.forEach((m) => {
      const rec = byCat.get(categoryOf(m.name));
      if (!rec) return;
      rec.total += m.value;
      if (!seen.has(rec.category)) {
        rec.courses += 1;
        seen.add(rec.category);
      }
    });
  });

  const grand = agg.reduce((s, a) => s + a.total, 0) || 1;
  // 最大余数法取整：四舍五入会让各卡百分比加起来不等于 100%
  const rawShares = agg.map((a) => (a.total / grand) * 100);
  const shares = rawShares.map((v) => Math.floor(v));
  let rest = 100 - shares.reduce((s, v) => s + v, 0);
  rawShares
    .map((v, i) => ({ i, frac: v - Math.floor(v) }))
    .sort((a, b) => b.frac - a.frac)
    .forEach((o) => {
      if (rest > 0) {
        shares[o.i] += 1;
        rest -= 1;
      }
    });

  return agg
    .map((a, i) => ({ ...a, share: shares[i] }))
    .sort((a, b) => b.total - a.total);
});

const dominantCategory = computed(() => categoryStats.value[0]);
const laggingCategory = computed(
  () => categoryStats.value[categoryStats.value.length - 1],
);

// 每节课排名前两位的模块合计占比，再取平均 → 主干集中度
const primaryConcentration = computed(() => {
  const shares = courses.map((c) => {
    const sorted = [...c.abilityModules].sort((a, b) => b.value - a.value);
    return sorted[0].value + sorted[1].value;
  });
  return Math.round(
    shares.reduce((s, v) => s + v, 0) / (shares.length || 1),
  );
});

const DIFFICULTY_RANK = { 基础: 0, "中等偏难": 1, "较难": 2, 难: 3 };

const difficultyStats = computed(() => {
  const dist = new Map();
  courses.forEach((c) =>
    dist.set(c.difficulty, (dist.get(c.difficulty) || 0) + 1),
  );
  return [...dist.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => (DIFFICULTY_RANK[a.label] ?? 9) - (DIFFICULTY_RANK[b.label] ?? 9));
});

// 每节课的「AI 识读」：由模块排序与占比直接推导
function buildCourseInsight(course) {
  const sorted = [...course.abilityModules].sort((a, b) => b.value - a.value);
  const first = sorted[0];
  const second = sorted[1];
  const weakest = sorted[sorted.length - 1];
  const coreShare = first.value + second.value;
  const average = Math.round(100 / sorted.length);

  const verdict =
    coreShare >= 60 ? "主干集中" : coreShare >= 50 ? "重心清晰" : "分布均衡";

  const deviation = coreShare - primaryConcentration.value;
  const compare =
    deviation === 0
      ? `与三节课平均 ${primaryConcentration.value}% 持平`
      : `较三节课平均 ${primaryConcentration.value}% ${deviation > 0 ? "高" : "低"} ${Math.abs(deviation)} 个百分点`;

  const note =
    `本节 ${course.duration}的内容里，「${first.name}」占 ${first.value}%，` +
    `与「${second.name}」（${second.value}%）合计 ${coreShare}%，${compare}；` +
    `「${weakest.name}」仅 ${weakest.value}%，低于本节模块均值 ${average}%，` +
    `属于可以在后续课时补强的环节。`;

  const action =
    weakest.value <= 10
      ? `补 1 组「${weakest.name}」专项练习`
      : weakest.value <= 20
        ? `课堂小结中强化「${weakest.name}」`
        : `保持节奏，关注「${weakest.name}」掌握情况`;

  return {
    coreShare,
    verdict,
    note,
    action,
    focus: `${first.name} + ${second.name}`,
    weakest: weakest.name,
    weakestShare: weakest.value,
  };
}

const courseInsights = computed(() =>
  Object.fromEntries(courses.map((c) => [c.id, buildCourseInsight(c)])),
);

// ==================== 摘要与结论 ====================
const summaryLead = computed(() => {
  const top = dominantCategory.value;
  const low = laggingCategory.value;
  return `${courses.length} 个课时样本的能力标注明显向${top.category}集中（${top.share}%），` +
    `${low.category}仅 ${low.share}%；教学重心清晰，但能力覆盖的均衡性仍有优化空间。`;
});

const summaryStats = computed(() => [
  {
    label: "主干集中度（前两项模块均值）",
    value: `${primaryConcentration.value}%`,
  },
  {
    label: `最大类别 · ${dominantCategory.value.category}`,
    value: `${dominantCategory.value.share}%`,
  },
  {
    label: `最弱类别 · ${laggingCategory.value.category}`,
    value: `${laggingCategory.value.share}%`,
  },
]);

const keyFindings = computed(() => {
  const stats = categoryStats.value;
  const top = stats[0];
  const low = stats[stats.length - 1];
  const weakest = moduleStats.value[0];

  const byCore = courses
    .map((c) => {
      const sorted = [...c.abilityModules].sort((a, b) => b.value - a.value);
      return {
        title: c.title,
        core: sorted[0].value + sorted[1].value,
        lead: sorted[0].name,
      };
    })
    .sort((a, b) => b.core - a.core);

  return [
    {
      lead: `${top.category}是覆盖最广的能力方向`,
      text:
        `占全部能力标注的 ${top.share}%，${top.courses} 门课程均有涉及，` +
        `内容主要落在${CATEGORY_MEANING[top.category] || "相关环节"}。`,
      metric: `${top.share}%`,
    },
    {
      lead: `「${byCore[0].title}」的重心最集中`,
      text:
        `该课时前两位模块合计 ${byCore[0].core}%，高于三节课平均 ${primaryConcentration.value}%；` +
        `主要投入方向为「${byCore[0].lead}」。`,
      metric: `${byCore[0].core}%`,
    },
    {
      lead: `${low.category}与「${weakest.name}」是覆盖盲区`,
      text:
        `${low.category}仅占 ${low.share}%，有 ${courses.length - low.courses} 门课程完全没有涉及；` +
        `细分模块「${weakest.name}」只在 ${weakest.courses} 门课中出现，权重合计 ${weakest.total}%。`,
      metric: `${low.share}%`,
    },
  ];
});

const adviceList = computed(() => {
  const low = laggingCategory.value;
  const weakest = moduleStats.value[0];
  const missing = courses
    .filter(
      (c) =>
        !c.abilityModules.some((m) => categoryOf(m.name) === low.category),
    )
    .map((c) => c.title);
  const diff = difficultyStats.value
    .map((d) => `${d.label} ${d.count} 门`)
    .join(" · ");
  const hasHard = courses.some(
    (c) => c.difficulty === "较难" || c.difficulty === "难",
  );
  // 用该类目里最轻量的一个模块作切入点，避免给历史课建议「做实验」
  const entry = low.items[low.items.length - 1];

  return [
    {
      priority: "高",
      title: `补齐${low.category}环节`,
      text: missing.length
        ? `${missing.map((t) => `《${t}》`).join("、")}未涉及${low.category}，建议${missing.length > 1 ? "各" : ""}以「${entry}」为切入点补 1 个环节，把该类权重从 ${low.share}% 提上来。`
        : `该类权重仅 ${low.share}%，建议在课时小结中补充对应练习。`,
    },
    {
      priority: "中",
      title: `为「${weakest.name}」安排专项练习`,
      text: `「${weakest.name}」只在 ${weakest.courses} 门课程中出现，合计权重 ${weakest.total}%，是样本中最低的模块，适合用课后小测补齐。`,
    },
    {
      priority: "低",
      title: hasHard ? "保持现有难度梯度" : "补充一节高难度拓展课",
      text: hasHard
        ? `当前难度分布为 ${diff}，梯度完整，可按现有节奏排课。`
        : `当前难度分布为 ${diff}，最高只到「中等偏难」，建议增加 1 节拓展课，形成基础 → 进阶 → 拓展的完整梯度。`,
    },
  ];
});
</script>

<template>
  <div class="report-page">
    <SiteNav />

    <div class="report-shell">
      <!-- 报告本体：导出与打印都只取这一块 -->
      <div class="analysis-report" ref="reportRef">
        <!-- 报告头部 -->
        <header class="report-hero">
          <div class="hero-main">
            <span class="hero-icon" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path
                  d="M3 4.5A1.5 1.5 0 0 1 4.5 3h11A1.5 1.5 0 0 1 17 4.5v11a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 3 15.5v-11z"
                  stroke="currentColor"
                  stroke-width="1.4"
                />
                <path
                  d="M6.4 12.6V9.2M9.8 12.6V6.8M13.2 12.6v-2.2"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                />
              </svg>
            </span>
            <div class="hero-text">
              <p class="hero-eyebrow">AI 课程内容分析</p>
              <h1>课程内容可视化分析报告</h1>
              <p class="hero-meta">
                覆盖 {{ totalCourses }} 个课时 · {{ totalMinutes }} 分钟 ·
                {{ moduleCount }} 个能力模块 · {{ subjectCount }} 个学科
              </p>
            </div>
          </div>

          <div class="hero-actions">
            <button class="report-btn" type="button" @click="router.back()">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M11.5 5.5 7 10l4.5 4.5M7 10h7"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              返回
            </button>
            <button class="report-btn" type="button" @click="printReport">
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M6.5 7.5V4h7v3.5"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
                <path
                  d="M4.5 7.5h11A1.5 1.5 0 0 1 17 9v4a1 1 0 0 1-1 1h-2v2.5H6V14H4a1 1 0 0 1-1-1V9a1.5 1.5 0 0 1 1.5-1.5z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                />
              </svg>
              打印
            </button>
            <button
              class="report-btn report-btn--primary"
              type="button"
              @click="exportReport"
            >
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M10 3.5v8M6.8 8.6 10 12l3.2-3.4M4 14.5V16h12v-1.5"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              导出报告
            </button>
          </div>
        </header>

        <!-- 概览指标 -->
        <section class="metric-strip">
          <article class="metric">
            <span class="metric__icon" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path
                  d="M4 4.2A2.2 2.2 0 0 1 6.2 2H16v13.4H6.2A2.2 2.2 0 0 0 4 17.6V4.2z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                />
                <path
                  d="M4 15.4a2.2 2.2 0 0 1 2.2-2.2H16"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
              </svg>
            </span>
            <div class="metric__body">
              <p class="metric__value">
                {{ totalCourses }}<span class="metric__unit">课时</span>
              </p>
              <p class="metric__label">分析样本</p>
              <p class="metric__hint">{{ subjectBreakdown }}</p>
            </div>
          </article>

          <article class="metric">
            <span class="metric__icon" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <circle
                  cx="10"
                  cy="10"
                  r="7"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <path
                  d="M10 6v4.2l2.6 1.6"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
            </span>
            <div class="metric__body">
              <p class="metric__value">
                {{ avgDuration }}<span class="metric__unit">分钟</span>
              </p>
              <p class="metric__label">平均课时时长</p>
              <p class="metric__hint">累计 {{ totalMinutes }} 分钟内容</p>
            </div>
          </article>

          <article class="metric">
            <span class="metric__icon" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <path
                  d="M10 2.8 17 6.4l-7 3.6-7-3.6 7-3.6z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                />
                <path
                  d="m3 10 7 3.6 7-3.6M3 13.6 10 17.2l7-3.6"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linejoin="round"
                />
              </svg>
            </span>
            <div class="metric__body">
              <p class="metric__value">
                {{ moduleCount }}<span class="metric__unit">项</span>
              </p>
              <p class="metric__label">识别到的能力模块</p>
              <p class="metric__hint">
                归入 {{ categoryStats.length }} 类能力方向
              </p>
            </div>
          </article>

          <article class="metric">
            <span class="metric__icon" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="none">
                <circle
                  cx="10"
                  cy="10"
                  r="7"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <circle
                  cx="10"
                  cy="10"
                  r="3.4"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <circle cx="10" cy="10" r="0.9" fill="currentColor" />
              </svg>
            </span>
            <div class="metric__body">
              <p class="metric__value">
                {{ primaryConcentration }}<span class="metric__unit">%</span>
              </p>
              <p class="metric__label">主干集中度</p>
              <p class="metric__hint">每节课前两项模块的平均占比</p>
            </div>
          </article>
        </section>

        <!-- AI 分析摘要 -->
        <section class="ai-summary">
          <div class="ai-summary__main">
            <div class="ai-summary__head">
              <span class="ai-summary__badge">
                <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                  <path
                    d="M10 2.6l1.5 4.5 4.5 1.5-4.5 1.5L10 14.6 8.5 10.1 4 8.6l4.5-1.5L10 2.6z"
                    stroke="currentColor"
                    stroke-width="1.4"
                    stroke-linejoin="round"
                  />
                </svg>
                AI 分析摘要
              </span>
              <span class="ai-summary__note">
                由课时内容与能力标注自动生成
              </span>
            </div>
            <p class="ai-summary__lead">{{ summaryLead }}</p>
            <div class="ai-summary__stats">
              <div
                v-for="item in summaryStats"
                :key="item.label"
                class="summary-stat"
              >
                <span class="summary-stat__value">{{ item.value }}</span>
                <span class="summary-stat__label">{{ item.label }}</span>
              </div>
            </div>
          </div>

          <aside class="ai-summary__aside">
            <h4>分析口径</h4>
            <dl>
              <div>
                <dt>样本范围</dt>
                <dd>{{ totalCourses }} 课时 / {{ totalMinutes }} 分钟</dd>
              </div>
              <div>
                <dt>学科分布</dt>
                <dd>{{ subjectBreakdown }}</dd>
              </div>
              <div>
                <dt>判断依据</dt>
                <dd>能力模块权重占比，合计 {{ totalWeight }}</dd>
              </div>
              <div>
                <dt>归类方式</dt>
                <dd>模块 → 能力类别，共 {{ categoryStats.length }} 类</dd>
              </div>
            </dl>
          </aside>
        </section>

        <!-- 能力模块归类 -->
        <section class="legend-section">
          <div class="section-head">
            <h2 class="section-title">能力模块归类</h2>
            <p class="section-desc">
              按能力性质把 {{ moduleCount }} 个模块归入
              {{ categoryStats.length }} 类，百分比为该类在全部能力标注中的权重
            </p>
          </div>
          <div class="legend-grid">
            <article
              v-for="cat in categoryStats"
              :key="cat.category"
              class="legend-card"
            >
              <div class="legend-card__head">
                <span
                  class="legend-dot"
                  :style="{ background: cat.color }"
                  aria-hidden="true"
                ></span>
                <span class="legend-category">{{ cat.category }}</span>
                <span class="legend-share">{{ cat.share }}%</span>
              </div>
              <p class="legend-meaning">{{ cat.meaning }}</p>
              <div class="legend-items">
                <span
                  v-for="subItem in cat.items"
                  :key="subItem"
                  class="legend-item"
                >
                  {{ subItem }}
                </span>
              </div>
            </article>
          </div>
        </section>

        <!-- 课程分析 -->
        <section class="charts-section">
          <div class="section-head">
            <h2 class="section-title">各课时能力模块分布</h2>
            <p class="section-desc">
              环形图为该课时各能力模块的权重；下方结论由模块占比直接推导，可用于备课复盘
            </p>
          </div>

          <div class="charts-grid">
            <article
              v-for="(course, index) in courses"
              :key="course.id"
              class="course-card"
              :class="{
                'course-card--wide':
                  courses.length % 2 === 1 && index === courses.length - 1,
              }"
            >
              <header class="course-card__head">
                <div>
                  <h3 class="course-card__title">{{ course.title }}</h3>
                  <p class="course-meta">
                    <span>{{ course.subject }}</span>
                    <i>·</i>
                    <span>{{ course.gradeLevel }}</span>
                    <i>·</i>
                    <span>{{ course.duration }}</span>
                    <i>·</i>
                    <span>{{ course.teacher }}</span>
                  </p>
                </div>
                <span class="difficulty-chip" :data-level="course.difficulty">
                  {{ course.difficulty }}
                </span>
              </header>

              <div :id="`chart-${course.id}`" class="chart-container"></div>

              <div class="ai-read">
                <div class="ai-read__head">
                  <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                    <path
                      d="M10 2.6l1.5 4.5 4.5 1.5-4.5 1.5L10 14.6 8.5 10.1 4 8.6l4.5-1.5L10 2.6z"
                      stroke="currentColor"
                      stroke-width="1.4"
                      stroke-linejoin="round"
                    />
                  </svg>
                  <span>AI 识读</span>
                  <span class="ai-read__tag">
                    {{ courseInsights[course.id].verdict }}
                  </span>
                </div>
                <p class="ai-read__text">
                  {{ courseInsights[course.id].note }}
                </p>
                <ul class="ai-read__rows">
                  <li>
                    <span class="ai-read__k">教学重心</span>
                    <span class="ai-read__v">
                      {{ courseInsights[course.id].focus }}
                    </span>
                    <span class="ai-read__p">
                      {{ courseInsights[course.id].coreShare }}%
                    </span>
                  </li>
                  <li>
                    <span class="ai-read__k">相对薄弱</span>
                    <span class="ai-read__v">
                      {{ courseInsights[course.id].weakest }}
                    </span>
                    <span class="ai-read__p">
                      {{ courseInsights[course.id].weakestShare }}%
                    </span>
                  </li>
                  <li>
                    <span class="ai-read__k">建议动作</span>
                    <span class="ai-read__v">
                      {{ courseInsights[course.id].action }}
                    </span>
                  </li>
                </ul>
              </div>

              <div class="course-tags">
                <div class="tag-group">
                  <h4>核心知识点</h4>
                  <div class="tag-list">
                    <span
                      v-for="point in course.keyPoints"
                      :key="point"
                      class="detail-tag"
                    >
                      {{ point }}
                    </span>
                  </div>
                </div>
                <div class="tag-group">
                  <h4>教学方法</h4>
                  <div class="tag-list">
                    <span
                      v-for="method in course.teachingMethods"
                      :key="method"
                      class="detail-tag detail-tag--method"
                    >
                      {{ method }}
                    </span>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>

        <!-- 洞察与建议 -->
        <section class="insight-section">
          <div class="section-head">
            <h2 class="section-title">分析洞察与建议</h2>
            <p class="section-desc">
              以下结论与建议均由样本统计推导，数字可回溯到上方各课时图表
            </p>
          </div>

          <div class="insight-grid">
            <div class="panel">
              <h3>关键发现</h3>
              <ol class="finding-list">
                <li v-for="(item, index) in keyFindings" :key="item.lead">
                  <span class="finding__idx">
                    {{ String(index + 1).padStart(2, "0") }}
                  </span>
                  <div class="finding__body">
                    <p class="finding__lead">{{ item.lead }}</p>
                    <p class="finding__text">{{ item.text }}</p>
                  </div>
                  <span class="finding__metric">{{ item.metric }}</span>
                </li>
              </ol>
            </div>

            <div class="panel">
              <h3>教学建议</h3>
              <ul class="advice-list">
                <li v-for="item in adviceList" :key="item.title">
                  <span class="advice__badge" :data-priority="item.priority">
                    {{ item.priority }}
                  </span>
                  <div>
                    <p class="advice__title">{{ item.title }}</p>
                    <p class="advice__text">{{ item.text }}</p>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <!-- 报告页脚 -->
        <footer class="report-footer">
          <div class="footer-info">
            <span>生成时间 {{ generatedAt }}</span>
            <i>·</i>
            <span>
              样本 {{ totalCourses }} 课时 / {{ totalMinutes }} 分钟 /
              {{ totalWeight }} 能力权重
            </span>
            <i>·</i>
            <span>分析引擎 知启灵枢 · 课程内容理解</span>
          </div>
          <div class="footer-links">
            <a href="#" @click.prevent="printReport">打印报告</a>
            <i>|</i>
            <a href="#" @click.prevent="exportReport">导出 HTML</a>
          </div>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ==================== 页面骨架 ==================== */
.report-page {
  min-height: 100vh;
  background: #f7f9fc;
}

.report-shell {
  max-width: 1200px;
  margin: 0 auto;
  padding: 100px 24px 56px;
}

.analysis-report {
  font-family: var(--font-body);
  color: var(--ink);
}

/* ==================== 报告头部 ==================== */
.report-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  padding: 26px 28px;
  margin-bottom: 20px;
  border-radius: 20px;
  border: 1px solid rgba(0, 119, 230, 0.12);
  background: linear-gradient(118deg, #f2f8ff 0%, #ffffff 58%, #fbfdff 100%);
  box-shadow: 0 1px 2px rgba(10, 15, 26, 0.03);
}

.hero-main {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
}

.hero-icon {
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: #e6f1fe;
  color: #0b6bd1;
}

.hero-icon svg {
  width: 22px;
  height: 22px;
}

.hero-eyebrow {
  margin: 0 0 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: #5a8fd0;
}

.hero-text h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.01em;
  color: #0f172a;
}

.hero-meta {
  margin: 8px 0 0;
  font-size: 0.82rem;
  color: #6b7c93;
}

.hero-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.report-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 38px;
  padding: 0 15px;
  border-radius: 11px;
  border: 1px solid rgba(10, 15, 26, 0.1);
  background: rgba(255, 255, 255, 0.9);
  color: #33475b;
  font-size: 0.83rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s,
    transform 0.2s;
}

.report-btn svg {
  width: 15px;
  height: 15px;
}

.report-btn:hover {
  background: #ffffff;
  border-color: rgba(10, 15, 26, 0.18);
  transform: translateY(-1px);
}

.report-btn--primary {
  border-color: transparent;
  background: #0077e6;
  color: #fff;
  box-shadow: 0 2px 10px rgba(0, 119, 230, 0.22);
}

.report-btn--primary:hover {
  background: #0068c9;
  box-shadow: 0 6px 18px rgba(0, 119, 230, 0.28);
}

/* ==================== 概览指标 ==================== */
.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}

.metric {
  display: flex;
  align-items: flex-start;
  gap: 13px;
  padding: 18px 18px 16px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: #fff;
}

.metric__icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 11px;
  background: #f1f6fd;
  color: #4c7dff;
}

.metric__icon svg {
  width: 18px;
  height: 18px;
}

.metric__body {
  min-width: 0;
}

.metric__value {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: #0f172a;
}

.metric__unit {
  margin-left: 3px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #8595a8;
}

.metric__label {
  margin: 4px 0 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: #33475b;
}

.metric__hint {
  margin: 3px 0 0;
  font-size: 0.73rem;
  color: #93a3b5;
}

/* ==================== AI 分析摘要 ==================== */
.ai-summary {
  position: relative;
  display: grid;
  grid-template-columns: 1.55fr 1fr;
  gap: 30px;
  padding: 24px 26px 24px 30px;
  margin-bottom: 28px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #fff;
  overflow: hidden;
}

.ai-summary::before {
  content: "";
  position: absolute;
  left: 0;
  top: 22px;
  bottom: 22px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #4c7dff, #8ec6ff);
}

.ai-summary__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.ai-summary__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  font-weight: 700;
  color: #1e3554;
}

.ai-summary__badge svg {
  width: 15px;
  height: 15px;
  color: #4c7dff;
}

.ai-summary__note {
  font-size: 0.73rem;
  color: #9aa9ba;
}

.ai-summary__lead {
  margin: 0 0 16px;
  font-size: 0.92rem;
  line-height: 1.85;
  color: #3d4f66;
}

.ai-summary__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 26px;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 12px;
  border-left: 2px solid rgba(76, 125, 255, 0.18);
}

.summary-stat__value {
  font-size: 1.15rem;
  font-weight: 800;
  color: #2563eb;
  letter-spacing: -0.01em;
}

.summary-stat__label {
  font-size: 0.73rem;
  color: #8595a8;
}

.ai-summary__aside {
  padding-left: 26px;
  border-left: 1px solid rgba(10, 15, 26, 0.07);
}

.ai-summary__aside h4 {
  margin: 0 0 12px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #8595a8;
}

.ai-summary__aside dl {
  margin: 0;
  display: grid;
  gap: 9px;
}

.ai-summary__aside dl > div {
  display: flex;
  gap: 10px;
  font-size: 0.78rem;
  line-height: 1.5;
}

.ai-summary__aside dt {
  flex-shrink: 0;
  width: 60px;
  color: #9aa9ba;
}

.ai-summary__aside dd {
  margin: 0;
  color: #33475b;
}

/* ==================== 章节标题 ==================== */
.section-head {
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.08rem;
  font-weight: 700;
  color: #0f172a;
}

.section-desc {
  margin: 6px 0 0;
  font-size: 0.79rem;
  color: #93a3b5;
}

/* ==================== 能力模块归类 ==================== */
.legend-section {
  margin-bottom: 28px;
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.legend-card {
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: #fff;
}

.legend-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-category {
  font-size: 0.86rem;
  font-weight: 700;
  color: #1e293b;
}

.legend-share {
  margin-left: auto;
  font-size: 0.85rem;
  font-weight: 800;
  color: #5b6b80;
}

.legend-meaning {
  margin: 7px 0 12px;
  font-size: 0.74rem;
  line-height: 1.6;
  color: #93a3b5;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.legend-item {
  padding: 4px 9px;
  border-radius: 7px;
  background: #f5f8fc;
  border: 1px solid rgba(10, 15, 26, 0.05);
  font-size: 0.72rem;
  color: #5b6b80;
}

/* ==================== 课时卡片 ==================== */
.charts-section {
  margin-bottom: 28px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
  gap: 18px;
}

.course-card {
  display: flex;
  flex-direction: column;
  padding: 22px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #fff;
}

/* 奇数张时最后一张横跨整行，避免右侧留下大片空白 */
.course-card--wide {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1.02fr 1fr;
  grid-template-areas:
    "head head"
    "chart read"
    "chart tags";
  column-gap: 30px;
  align-items: start;
}

.course-card--wide .course-card__head {
  grid-area: head;
}

.course-card--wide .chart-container {
  grid-area: chart;
  height: 340px;
}

.course-card--wide .ai-read {
  grid-area: read;
  margin-top: 8px;
}

.course-card--wide .course-tags {
  grid-area: tags;
}

.course-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.course-card__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.course-meta {
  margin: 6px 0 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #8595a8;
}

.course-meta i {
  font-style: normal;
  color: #cfd9e4;
}

.difficulty-chip {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
}

.difficulty-chip[data-level="基础"] {
  background: #eef8f2;
  color: #1d8f5b;
}

.difficulty-chip[data-level="中等偏难"] {
  background: #fdf5e8;
  color: #b5791a;
}

.difficulty-chip[data-level="较难"],
.difficulty-chip[data-level="难"] {
  background: #fdeeee;
  color: #bd4a3f;
}

.chart-container {
  width: 100%;
  height: 300px;
  margin: 6px 0 4px;
}

/* ==================== AI 识读 ==================== */
.ai-read {
  padding: 14px 16px;
  border-radius: 13px;
  border: 1px solid rgba(0, 119, 230, 0.1);
  background: #f7faff;
}

.ai-read__head {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 9px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #3b6ea8;
}

.ai-read__head svg {
  width: 14px;
  height: 14px;
  color: #4c7dff;
}

.ai-read__tag {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e9f6ee;
  font-size: 0.7rem;
  font-weight: 600;
  color: #1d8f5b;
}

.ai-read__text {
  margin: 0 0 11px;
  font-size: 0.82rem;
  line-height: 1.8;
  color: #4a5a6e;
}

.ai-read__rows {
  list-style: none;
  margin: 0;
  padding: 10px 0 0;
  border-top: 1px dashed rgba(0, 119, 230, 0.14);
  display: grid;
  gap: 7px;
}

.ai-read__rows li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 0.78rem;
}

.ai-read__k {
  flex-shrink: 0;
  width: 56px;
  color: #93a3b5;
}

.ai-read__v {
  color: #33475b;
}

.ai-read__p {
  margin-left: auto;
  font-weight: 700;
  color: #2563eb;
}

/* ==================== 标签 ==================== */
.course-tags {
  margin-top: 16px;
  padding-top: 15px;
  border-top: 1px solid rgba(10, 15, 26, 0.06);
  display: grid;
  gap: 12px;
}

.tag-group h4 {
  margin: 0 0 8px;
  font-size: 0.76rem;
  font-weight: 600;
  color: #93a3b5;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.detail-tag {
  padding: 5px 10px;
  border-radius: 8px;
  background: #f3f7fc;
  font-size: 0.75rem;
  color: #3b6ea8;
}

.detail-tag--method {
  background: #f2f8f4;
  color: #2c8b62;
}

/* ==================== 洞察与建议 ==================== */
.insight-section {
  margin-bottom: 28px;
}

.insight-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 18px;
  align-items: start;
}

.panel {
  padding: 22px 24px;
  border-radius: 18px;
  border: 1px solid var(--border);
  background: #fff;
}

.panel h3 {
  margin: 0 0 16px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
}

.finding-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px;
}

.finding-list li {
  display: flex;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(10, 15, 26, 0.06);
}

.finding-list li:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.finding__idx {
  flex-shrink: 0;
  padding-top: 1px;
  font-family: var(--font-display);
  font-size: 0.72rem;
  font-weight: 700;
  color: #9fb6d4;
}

.finding__body {
  min-width: 0;
}

.finding__lead {
  margin: 0 0 5px;
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
}

.finding__text {
  margin: 0;
  font-size: 0.79rem;
  line-height: 1.75;
  color: #64748b;
}

.finding__metric {
  flex-shrink: 0;
  align-self: flex-start;
  font-size: 1rem;
  font-weight: 800;
  color: #2563eb;
}

.advice-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 14px;
}

.advice-list li {
  display: flex;
  gap: 10px;
}

.advice__badge {
  flex-shrink: 0;
  height: fit-content;
  margin-top: 1px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.68rem;
  font-weight: 700;
}

.advice__badge[data-priority="高"] {
  background: #fdeeee;
  color: #bd4a3f;
}

.advice__badge[data-priority="中"] {
  background: #fdf5e8;
  color: #b5791a;
}

.advice__badge[data-priority="低"] {
  background: #f1f5f9;
  color: #64748b;
}

.advice__title {
  margin: 0 0 4px;
  font-size: 0.83rem;
  font-weight: 700;
  color: #33475b;
}

.advice__text {
  margin: 0;
  font-size: 0.78rem;
  line-height: 1.7;
  color: #7b8b9e;
}

/* ==================== 页脚 ==================== */
.report-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 16px 22px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.7);
}

.footer-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  color: #93a3b5;
}

.footer-info i {
  font-style: normal;
  color: #cfd9e4;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.78rem;
}

.footer-links a {
  color: #3b7dd8;
  font-weight: 600;
  text-decoration: none;
}

.footer-links a:hover {
  color: #2563eb;
  text-decoration: underline;
}

.footer-links i {
  font-style: normal;
  color: #cfd9e4;
}

/* ==================== 打印 ==================== */
@media print {
  .report-page {
    background: #fff;
  }

  .report-shell {
    padding: 0;
    max-width: none;
  }

  :deep(.nav) {
    display: none !important;
  }

  .report-hero {
    background: #fff;
    box-shadow: none;
  }

  .hero-actions,
  .footer-links {
    display: none;
  }

  .course-card,
  .panel,
  .legend-card {
    break-inside: avoid;
    page-break-inside: avoid;
  }
}

/* ==================== 响应式 ==================== */
@media (max-width: 1100px) {
  .metric-strip {
    grid-template-columns: repeat(2, 1fr);
  }

  .ai-summary {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .ai-summary__aside {
    padding-left: 0;
    padding-top: 18px;
    border-left: none;
    border-top: 1px solid rgba(10, 15, 26, 0.07);
  }

  .legend-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .course-card--wide {
    grid-column: auto;
    display: flex;
    flex-direction: column;
  }

  .course-card--wide .chart-container {
    height: 300px;
  }

  .course-card--wide .ai-read {
    margin-top: 0;
  }

  .insight-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .report-shell {
    padding: 88px 16px 40px;
  }

  .report-hero {
    flex-direction: column;
    align-items: flex-start;
    padding: 20px;
  }

  .hero-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .metric-strip {
    grid-template-columns: 1fr;
  }

  .legend-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 260px;
  }

  .report-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
