<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
import { useUserStore } from "../stores/userStore.js";
import {
  getCoursewareHistory,
  deleteCoursewareTask,
  downloadFile,
} from "../composables/useCoursewareApi.js";
import { seededInt, dateKey } from "../utils/demoData.js";

// ── 演示数据源（所有统计口径的唯一出处）────────────────────
// AdminView 属「有界面无后端」的演示模块：看板上的备课量、课时、班级学情
// 本应来自服务端。这里集中生成一份数据，种子 = 自然日 + 指标名：
//   ① 同一天刷新结果恒定，不会乱跳，看不出是现算的；
//   ② 跨天缓慢变化，像真有人在每天使用。
// 图表数值与下方「洞察」文案都从这份数据取值 / 推导，因此不会再出现
// 「文案写 15 个、图上却画 8 个」这种自相矛盾。
const demo = (() => {
  const key = dateKey();
  const n = (name, min, max) => seededInt(`zqls-admin:${key}:${name}`, min, max);
  const list = (name, len, min, max) =>
    Array.from({ length: len }, (_, i) => n(`${name}-${i}`, min, max));
  /** 从 base 起步、每项累加 0..step 的递增序列（模拟"逐步变好"的趋势） */
  const rising = (name, len, base, step) => {
    let v = base;
    return Array.from({ length: len }, (_, i) => {
      v += n(`${name}-${i}`, 0, step);
      return v;
    });
  };

  const clsNames = ["高一(3)班", "高二(1)班", "高三(2)班"];

  // 工作台：本周每日生成量 / 课件类型占比 / 学科产出
  const weekly = list("weekly", 7, 4, 16);
  const kind = [
    n("kind-0", 38, 52),
    n("kind-1", 18, 28),
    n("kind-2", 12, 20),
    n("kind-3", 8, 16),
  ];
  const subject = list("subject", 6, 18, 50);

  // 课程表：一周 5 天 × 7 节的课时密度 / 年级周课时 / 学期进度 / 每日类型 / 利用率
  const heat = [];
  for (let d = 0; d < 5; d += 1) {
    for (let p = 0; p < 7; p += 1) heat.push([d, p, n(`heat-${d}-${p}`, 0, 4)]);
  }
  const gradeHours = [n("gh-0", 11, 14), n("gh-1", 8, 12), n("gh-2", 6, 10)];
  const progress = n("progress", 58, 74);
  const dayTypes = [
    list("dt-0", 5, 2, 4),
    list("dt-1", 5, 0, 2),
    list("dt-2", 5, 0, 2),
    list("dt-3", 5, 0, 2),
  ];
  const util = list("util", 5, 66, 92);

  // 班级：三班五维能力 / 分数段分布 / 历次考试均分走势
  const radar3 = clsNames.map((_, c) => list(`radar-${c}`, 5, 58, 92));
  const scoreDist3 = clsNames.map((_, c) => list(`dist-${c}`, 5, 2, 15));
  const examTrend3 = clsNames.map((_, c) =>
    rising(`exam-${c}`, 6, n(`exam-${c}-base`, 66, 78), 3),
  );

  // 成绩：分数段 / 班级均分走势 / 学科能力 / 参与度散点 / 学生名单
  const gradeDist = [
    n("gd-0", 4, 8),
    n("gd-1", 10, 15),
    n("gd-2", 18, 26),
    n("gd-3", 24, 32),
    n("gd-4", 14, 20),
  ];
  const classAvg = rising("cavg", 6, n("cavg-base", 68, 76), 3);
  const subjectRadar = [list("sr-0", 5, 58, 88), list("sr-1", 5, 58, 88)];
  const scatter = Array.from({ length: 40 }, (_, i) => [
    n(`sc-${i}-a`, 38, 98),
    n(`sc-${i}-b`, 40, 98),
    n(`sc-${i}-c`, 8, 38),
  ]);
  const names = [
    "张明远",
    "吴婉婷",
    "陈静茹",
    "李华清",
    "王芳菲",
    "刘浩然",
    "赵鹏程",
    "周子轩",
  ];
  const students = names
    .map((name, i) => {
      const score = i === 0 ? n("stu-hi", 90, 96) : n(`stu-${i}`, 56, 90);
      const t = n(`stu-trend-${i}`, 0, 2);
      return {
        name,
        score,
        trend: t === 0 ? "down" : t === 1 ? "stable" : "up",
        status:
          score >= 90
            ? "优秀"
            : score >= 80
              ? "良好"
              : score >= 70
                ? "中等"
                : "待提高",
      };
    })
    .sort((a, b) => b.score - a.score);

  // 模板：使用排行 / 类型占比 / 近六月趋势
  const templUse = list("tu", 5, 4, 20).sort((a, b) => b - a);
  const templMix = [n("tm-0", 50, 64), n("tm-1", 20, 30), n("tm-2", 10, 20)];
  const templTrend = [
    list("tt-0", 6, 4, 18),
    list("tt-1", 6, 3, 12),
    list("tt-2", 6, 2, 10),
  ];

  // 设置：存储占用 / 每月操作次数
  const storage = [
    n("st-0", 42, 54),
    n("st-1", 18, 26),
    n("st-2", 14, 22),
    n("st-3", 8, 16),
  ];
  const monthlyOps = list("ops", 6, 260, 540);

  return {
    clsNames,
    weekly,
    kind,
    subject,
    heat,
    gradeHours,
    progress,
    dayTypes,
    util,
    radar3,
    scoreDist3,
    examTrend3,
    gradeDist,
    classAvg,
    subjectRadar,
    scatter,
    students,
    templUse,
    templMix,
    templTrend,
    storage,
    monthlyOps,
  };
})();

// 兜底与统计小工具（供图表与「洞察」文案共用，保证二者永远一致）
const WEEK_LABELS = ["一", "二", "三", "四", "五", "六", "日"];
const SUBJECT_LABELS = ["语文", "数学", "英语", "物理", "化学", "生物"];
const sumOf = (arr) => arr.reduce((a, b) => a + b, 0);
const argMax = (arr) => arr.reduce((mi, v, i) => (v > arr[mi] ? i : mi), 0);
const argMin = (arr) => arr.reduce((mi, v, i) => (v < arr[mi] ? i : mi), 0);

const router = useRouter();
const user = useUserStore();
const userName = ref(user.getName() || "管理员");

const activeMenu = ref("dashboard");
// 语义化 SVG 图标 path（Material Icons 风格，24x24 viewBox）
const icons = {
  dashboard: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z",
  generate: "M13 2 3 14h7l-1 8 10-12h-7l1-8z",
  resource:
    "M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
  template: "M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z",
  schedule:
    "M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM5 8V6h14v2H5z",
  analytics: "M10 20h4V4h-4v16zm-6 0h4v-8H4v8zM16 9v11h4V9h-4z",
  settings:
    "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z",
};
const menuGroups = [
  { id: "dashboard", label: "数据看板", icon: "dashboard", standalone: true },
  {
    id: "lesson",
    label: "备课中心",
    icon: "resource",
    children: [
      { id: "tasks", label: "智能生成", icon: "generate" },
      { id: "courseware", label: "课件资源库", icon: "resource" },
      { id: "templates", label: "课件模板库", icon: "template" },
    ],
  },
  {
    id: "academic",
    label: "教务管理",
    icon: "analytics",
    children: [
      { id: "schedule", label: "课程安排", icon: "schedule" },
      { id: "analytics", label: "学情分析", icon: "analytics" },
    ],
  },
  { id: "settings", label: "系统设置", icon: "settings", standalone: true },
];
const openGroups = ref(new Set(["lesson"]));
function toggleGroup(id) {
  const next = new Set(openGroups.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  openGroups.value = next;
}

// ── 顶栏 ─────────────────────────────────
const currentCrumb = computed(() => {
  const flat = [];
  for (const g of menuGroups) {
    if (g.standalone) flat.push({ group: null, item: g });
    else g.children.forEach((c) => flat.push({ group: g, item: c }));
  }
  return flat.find((x) => x.item.id === activeMenu.value) || null;
});
const avatarText = computed(() => (userName.value || "管").charAt(0));
const showNotif = ref(false);
const showUserMenu = ref(false);
const notifications = [
  {
    id: 1,
    title: "课件审核通过",
    desc: "《牛顿第二定律》PPT 已完成审核，可下载使用",
    time: "10 分钟前",
    unread: true,
  },
  {
    id: 2,
    title: "新模板上线",
    desc: "「开学第一课」模板已加入课件模板库",
    time: "1 小时前",
    unread: true,
  },
  {
    id: 3,
    title: "生成任务完成",
    desc: "物理 3-2 章节测验试卷已生成",
    time: "昨天",
    unread: false,
  },
];

// ── ECharts ───────────────────────────────
let charts = [];
function disposeAll() {
  charts.forEach((c) => c?.dispose());
  charts = [];
}
function ec(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  const c = echarts.init(el, null, { renderer: "svg" });
  charts.push(c);
  return c;
}
const tx = { color: "#6B7C93", fontSize: 11, fontFamily: "system-ui" };
function noAxis() {
  return {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: tx,
  };
}
function splitY() {
  return {
    splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
    axisLabel: tx,
  };
}
const tip = {
  backgroundColor: "#fff",
  borderColor: "#E5E8EF",
  textStyle: { color: "#111", fontSize: 13, fontFamily: "system-ui" },
  extraCssText:
    "border-radius:6px;padding:4px 10px;box-shadow:0 1px 3px rgba(0,0,0,0.04);",
};

function initCharts() {
  disposeAll();
  // 每个模块独立色盘，避免颜色语义冲突
  const C = {
    work: ["#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EC4899"],
    sched: ["#0D9488", "#06B6D4", "#059669", "#64748B", "#F97316"],
    cls: ["#0077E6", "#00C2D4", "#10B981", "#6366F1", "#0EA5E9"],
    grade: ["#059669", "#0891B2", "#65A30D", "#0D9488", "#84CC16"],
    templ: ["#D97706", "#EA580C", "#CA8A04", "#78716C", "#A8A29E"],
  };
  const g = (t = 8, b = 16, l = 36, r = 6) => ({
    top: t,
    bottom: b,
    left: l,
    right: r,
  });

  // 工作台
  ec("ch-d1")?.setOption({
    grid: { top: 28, bottom: 32, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["一", "二", "三", "四", "五", "六", "日"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 0,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "line",
        smooth: true,
        data: demo.weekly,
        symbol: "circle",
        symbolSize: 7,
        lineStyle: { color: C.work[0], width: 2.5 },
        areaStyle: { color: "rgba(59,130,246,0.08)" },
        label: {
          show: true,
          position: "top",
          fontSize: 11,
          color: "#6B7C93",
        },
      },
    ],
  });
  ec("ch-d2")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["40%", "75%"],
        avoidLabelOverlap: true,
        label: {
          show: true,
          color: "#6B7C93",
          fontSize: 13,
          formatter: "{b}\n{d}%",
        },
        data: [
          { value: demo.kind[0], name: "PPT课件", itemStyle: { color: C.work[0] } },
          { value: demo.kind[1], name: "教案文档", itemStyle: { color: C.work[1] } },
          { value: demo.kind[2], name: "考试试卷", itemStyle: { color: C.work[2] } },
          { value: demo.kind[3], name: "课堂练习", itemStyle: { color: C.work[3] } },
        ],
      },
    ],
  });
  ec("ch-d3")?.setOption({
    grid: { top: 28, bottom: 34, left: 56, right: 24 },
    xAxis: {
      type: "category",
      data: ["语文", "数学", "英语", "物理", "化学", "生物"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "bar",
        data: demo.subject,
        barWidth: 28,
        label: {
          show: true,
          position: "top",
          fontSize: 12,
          color: "#6B7C93",
          fontWeight: 600,
        },
        itemStyle: { color: C.work[0], borderRadius: [4, 4, 0, 0] },
      },
    ],
  });

  // 课程表
  const days = ["周一", "周二", "周三", "周四", "周五"],
    slots = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节"];
  const hd = demo.heat;
  ec("ch-s1")?.setOption({
    grid: { top: 24, bottom: 70, left: 60, right: 16 },
    xAxis: {
      type: "category",
      data: days,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "category",
      data: slots,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    visualMap: {
      min: 0,
      max: 10,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: 14,
      itemWidth: 10,
      itemHeight: 120,
      inRange: { color: ["#EEF1F5", "#CCFBF1", "#5EEAD4", "#0D9488"] },
      textStyle: { color: "#94A3B8", fontSize: 11 },
    },
    graphic: [
      {
        type: "text",
        left: "center",
        bottom: 0,
        silent: true,
        style: {
          text: "颜色越深 = 该时段排课越密集",
          fill: "#94A3B8",
          fontSize: 10,
          align: "center",
        },
      },
    ],
    series: [
      {
        type: "heatmap",
        data: hd,
        label: { show: false },
        itemStyle: { borderColor: "#fff", borderWidth: 3, borderRadius: 2 },
      },
    ],
    tooltip: { ...tip, position: "top" },
  });
  ec("ch-s2")?.setOption({
    grid: { top: 28, bottom: 28, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["高一", "高二", "高三"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      name: "课时/周",
      nameTextStyle: { color: "#94A3B8", fontSize: 10 },
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: "bar",
        data: demo.gradeHours.map((v, i) => ({
          value: v,
          itemStyle: { color: C.sched[i] },
        })),
        barWidth: 30,
        borderRadius: [4, 4, 0, 0],
        label: { show: true, position: "top", fontSize: 11, color: "#6B7C93" },
      },
    ],
    tooltip: { ...tip, trigger: "axis" },
  });
  ec("ch-s3")?.setOption({
    series: [
      {
        type: "gauge",
        center: ["50%", "58%"],
        startAngle: 210,
        endAngle: -30,
        axisLine: {
          lineStyle: {
            width: 14,
            color: [
              [0.65, "#059669"],
              [0.88, "#F59E0B"],
              [1, "#EF4444"],
            ],
          },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          fontSize: 24,
          fontWeight: 700,
          color: "#111",
          offsetCenter: [0, "36%"],
          formatter: `${demo.progress}%`,
        },
        data: [{ value: demo.progress }],
      },
    ],
    tooltip: { ...tip, formatter: `学期进度: ${demo.progress}%` },
  });
  ec("ch-s4")?.setOption({
    tooltip: { ...tip, trigger: "axis" },
    legend: {
      show: true,
      bottom: 2,
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    grid: { top: 28, bottom: 58, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["周一", "周二", "周三", "周四", "周五"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 0,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        name: "新授课",
        type: "bar",
        stack: "total",
        barWidth: 26,
        data: demo.dayTypes[0],
        itemStyle: { color: C.sched[0], borderRadius: [0, 0, 0, 0] },
      },
      {
        name: "复习课",
        type: "bar",
        stack: "total",
        data: demo.dayTypes[1],
        itemStyle: { color: C.sched[1] },
      },
      {
        name: "实验课",
        type: "bar",
        stack: "total",
        data: demo.dayTypes[2],
        itemStyle: { color: C.sched[2] },
      },
      {
        name: "其他",
        type: "bar",
        stack: "total",
        data: demo.dayTypes[3],
        itemStyle: { color: C.sched[3] },
        label: {
          show: true,
          position: "top",
          fontSize: 11,
          fontWeight: 600,
          color: "#6B7C93",
          formatter: (p) => {
            // 每日总课时由四类相加得出，不再写死 [6,6,6,4,6]
            const totals = [0, 1, 2, 3, 4].map((d) =>
              demo.dayTypes.reduce((s, t) => s + t[d], 0),
            );
            return totals[p.dataIndex] + "节";
          },
        },
      },
    ],
  });
  // 班级
  ec("ch-c1")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    radar: {
      indicator: [
        { name: "基础知识", max: 100 },
        { name: "公式运用", max: 100 },
        { name: "实验探究", max: 100 },
        { name: "综合解题", max: 100 },
        { name: "创新思维", max: 100 },
      ],
      axisName: { color: "#6B7C93", fontSize: 10 },
      splitArea: {
        areaStyle: {
          color: ["rgba(0,119,230,0.02)", "rgba(0,119,230,0.04)"],
        },
      },
      splitLine: { lineStyle: { color: "#EEF1F5" } },
    },
    series: [
      {
        type: "radar",
        data: demo.clsNames.map((name, i) => ({
          value: demo.radar3[i],
          name,
          lineStyle: { color: C.cls[i] },
          areaStyle: {
            color: [
              "rgba(31,108,159,0.1)",
              "rgba(0,194,212,0.1)",
              "rgba(16,185,129,0.1)",
            ][i],
          },
        })),
      },
    ],
  });
  ec("ch-c2")?.setOption({
    grid: { top: 28, bottom: 36, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["<60", "60-69", "70-79", "80-89", "90-100"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    legend: {
      show: true,
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        name: "高一(3)",
        type: "bar",
        barWidth: 12,
        barGap: "30%",
        data: demo.scoreDist3[0],
        itemStyle: { color: C.cls[0], borderRadius: [4, 4, 0, 0] },
      },
      {
        name: "高二(1)",
        type: "bar",
        barWidth: 12,
        data: demo.scoreDist3[1],
        itemStyle: { color: C.cls[1], borderRadius: [4, 4, 0, 0] },
      },
      {
        name: "高三(2)",
        type: "bar",
        barWidth: 12,
        data: demo.scoreDist3[2],
        itemStyle: { color: C.cls[2], borderRadius: [4, 4, 0, 0] },
      },
    ],
  });
  const sct = demo.scatter;
  ec("ch-c3")?.setOption({
    grid: { top: 28, bottom: 32, left: 56, right: 24 },
    xAxis: {
      type: "value",
      name: "参与度 (%)",
      nameTextStyle: { color: "#94A3B8", fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      name: "成绩",
      nameTextStyle: { color: "#94A3B8", fontSize: 10 },
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: "scatter",
        symbolSize: (v) => Math.max(7, Math.min(22, v[2] / 2)),
        data: sct,
        itemStyle: { color: "rgba(0,119,230,0.5)" },
      },
    ],
    tooltip: {
      ...tip,
      trigger: "item",
      formatter: "参与度: {c0}%<br/>成绩: {c1}<br/>练习: {c2}次",
    },
  });
  ec("ch-c4")?.setOption({
    grid: { top: 28, bottom: 36, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["第1次", "第2次", "第3次", "第4次", "第5次", "第6次"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 60,
      max: 100,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    legend: {
      show: true,
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        name: "高一(3)",
        type: "line",
        smooth: true,
        data: demo.examTrend3[0],
        lineStyle: { color: C.cls[0], width: 2 },
        symbol: "circle",
        symbolSize: 6,
        areaStyle: { color: "rgba(0,119,230,0.05)" },
      },
      {
        name: "高二(1)",
        type: "line",
        smooth: true,
        data: demo.examTrend3[1],
        lineStyle: { color: C.cls[1], width: 2 },
        symbol: "diamond",
        symbolSize: 6,
        areaStyle: { color: "rgba(0,194,212,0.05)" },
      },
      {
        name: "高三(2)",
        type: "line",
        smooth: true,
        data: demo.examTrend3[2],
        lineStyle: { color: C.cls[2], width: 2 },
        symbol: "triangle",
        symbolSize: 6,
        areaStyle: { color: "rgba(236,72,153,0.05)" },
      },
    ],
  });

  // 成绩
  ec("ch-g1")?.setOption({
    grid: { top: 28, bottom: 32, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["<60", "60-69", "70-79", "80-89", "90-100"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "bar",
        data: demo.gradeDist,
        barWidth: 28,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: C.grade[0] },
            { offset: 1, color: "rgba(5,150,105,0.35)" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: { show: true, position: "top", fontSize: 11, color: "#6B7C93" },
      },
    ],
  });
  const gradeLine = Math.round(sumOf(demo.classAvg) / demo.classAvg.length);
  ec("ch-g2")?.setOption({
    grid: { top: 28, bottom: 32, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["第1周", "第2周", "第3周", "第4周", "第5周", "第6周"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 60,
      max: 100,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "line",
        smooth: true,
        data: demo.classAvg,
        lineStyle: { color: C.grade[0], width: 2.5 },
        areaStyle: { color: "rgba(5,150,105,0.08)" },
        symbol: "diamond",
        symbolSize: 8,
        itemStyle: { color: C.grade[0] },
        markLine: {
          silent: true,
          data: [
            {
              yAxis: gradeLine,
              label: {
                formatter: `年级平均 ${gradeLine}`,
                color: "#94A3B8",
                fontSize: 10,
              },
            },
          ],
          lineStyle: { color: "#D4D1CC", type: "dashed" },
        },
      },
    ],
  });
  ec("ch-g3")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    radar: {
      indicator: [
        { name: "概念理解", max: 100 },
        { name: "公式应用", max: 100 },
        { name: "实验探究", max: 100 },
        { name: "计算能力", max: 100 },
        { name: "分析推理", max: 100 },
      ],
      axisName: { color: "#6B7C93", fontSize: 10 },
      splitArea: {
        areaStyle: { color: ["rgba(5,150,105,0.02)", "rgba(5,150,105,0.04)"] },
      },
      splitLine: { lineStyle: { color: "#EEF1F5" } },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: demo.subjectRadar[0],
            name: "物理",
            lineStyle: { color: C.grade[0] },
            areaStyle: { color: "rgba(5,150,105,0.08)" },
          },
          {
            value: demo.subjectRadar[1],
            name: "数学",
            lineStyle: { color: C.grade[1] },
            areaStyle: { color: "rgba(8,145,178,0.08)" },
          },
        ],
      },
    ],
  });
  const stuAvg = Math.round(
    sumOf(demo.students.map((s) => s.score)) / demo.students.length,
  );
  ec("ch-g4")?.setOption({
    tooltip: { ...tip, trigger: "axis" },
    grid: { top: 20, bottom: 30, left: 68, right: 40 },
    xAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
    },
    yAxis: {
      type: "category",
      data: demo.students.map((s) => s.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        name: "当前成绩",
        type: "bar",
        data: demo.students.map((s) => s.score),
        barWidth: 18,
        label: {
          show: true,
          position: "right",
          fontSize: 11,
          color: "#6B7C93",
        },
        itemStyle: { color: C.grade[0], borderRadius: [0, 4, 4, 0] },
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { color: "#64748B", type: "dashed", width: 1 },
          label: {
            show: true,
            position: "end",
            formatter: `班级均分 ${stuAvg}`,
            fontSize: 10,
            color: "#64748B",
          },
          data: [{ xAxis: stuAvg }],
        },
      },
    ],
  });

  // 模板
  ec("ch-t1")?.setOption({
    grid: { top: 24, bottom: 28, left: 88, right: 32 },
    xAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
    },
    yAxis: {
      type: "category",
      data: [
        "数学复习课",
        "物理新授课",
        "化学实验课",
        "语文精读课",
        "英语听力课",
      ],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        type: "bar",
        data: demo.templUse,
        barWidth: 16,
        label: {
          show: true,
          position: "right",
          fontSize: 11,
          color: "#6B7C93",
        },
        itemStyle: { color: C.templ[0], borderRadius: [0, 3, 3, 0] },
      },
    ],
    tooltip: { ...tip, trigger: "axis" },
  });
  ec("ch-t2")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["42%", "76%"],
        label: {
          show: true,
          color: "#6B7C93",
          fontSize: 12,
          formatter: "{b}\n{d}%",
        },
        data: [
          { value: demo.templMix[0], name: "PPT模板", itemStyle: { color: C.templ[0] } },
          { value: demo.templMix[1], name: "教案模板", itemStyle: { color: C.templ[1] } },
          { value: demo.templMix[2], name: "试卷模板", itemStyle: { color: C.templ[2] } },
        ],
      },
    ],
  });
  ec("ch-t3")?.setOption({
    grid: { top: 28, bottom: 36, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["3月", "4月", "5月", "6月", "7月", "8月"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    legend: {
      show: true,
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: demo.templTrend[0],
        name: "物理新授课",
        lineStyle: { color: C.templ[0], width: 2 },
        symbol: "none",
        areaStyle: { color: "rgba(217,7,6,0.06)" },
      },
      {
        type: "line",
        smooth: true,
        data: demo.templTrend[1],
        name: "数学复习课",
        lineStyle: { color: C.templ[1], width: 2 },
        symbol: "none",
        areaStyle: { color: "rgba(234,88,12,0.06)" },
      },
      {
        type: "line",
        smooth: true,
        data: demo.templTrend[2],
        name: "化学实验课",
        lineStyle: { color: C.templ[2], width: 2 },
        symbol: "none",
        areaStyle: { color: "rgba(202,138,4,0.06)" },
      },
    ],
  });

  // 设置
  ec("ch-ss")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    series: [
      {
        type: "pie",
        radius: ["42%", "76%"],
        avoidLabelOverlap: true,
        label: {
          show: true,
          color: "#6B7C93",
          fontSize: 11,
          formatter: "{b}\n{d}%",
        },
        data: [
          { value: demo.storage[0], name: "课件文件", itemStyle: { color: "#64748B" } },
          { value: demo.storage[1], name: "学生数据", itemStyle: { color: "#6B7280" } },
          { value: demo.storage[2], name: "模板资源", itemStyle: { color: "#71717A" } },
          { value: demo.storage[3], name: "系统缓存", itemStyle: { color: "#A3A3A3" } },
        ],
      },
    ],
  });
  ec("ch-ss2")?.setOption({
    grid: { top: 28, bottom: 32, left: 52, right: 24 },
    xAxis: {
      type: "category",
      data: ["1月", "2月", "3月", "4月", "5月", "6月"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "bar",
        data: demo.monthlyOps,
        barWidth: 24,
        label: { show: true, position: "top", fontSize: 10, color: "#6B7C93" },
        itemStyle: { color: "#64748B", borderRadius: [4, 4, 0, 0] },
      },
    ],
  });

  // ── 生成任务面板 ─────────────────────────
  const typeCount = { ppt: 0, doc: 0, quiz: 0, exam: 0 };
  tasks.value.forEach((t) => {
    if (typeCount[t.type] !== undefined) typeCount[t.type]++;
  });
  const typePieData = Object.keys(typeCount)
    .filter((k) => typeCount[k] > 0)
    .map((k) => ({
      value: typeCount[k],
      name: typeMap[k].label,
      itemStyle: { color: typeMap[k].color },
    }));
  ec("ch-task1")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    legend: {
      show: true,
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        type: "pie",
        radius: ["42%", "72%"],
        center: ["50%", "44%"],
        avoidLabelOverlap: true,
        label: {
          show: true,
          color: "#6B7C93",
          fontSize: 12,
          formatter: "{b}\n{d}%",
        },
        data: typePieData.length
          ? typePieData
          : [{ value: 1, name: "暂无数据", itemStyle: { color: "#E5E8EF" } }],
      },
    ],
  });

  const last7 = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    last7.push({ label: `${d.getMonth() + 1}/${d.getDate()}`, count: 0 });
  }
  tasks.value.forEach((t) => {
    if (!t.created_at) return;
    const parts = t.created_at.split(" ")[0].split("-");
    if (parts.length < 3) return;
    const label = `${parseInt(parts[1], 10)}/${parseInt(parts[2], 10)}`;
    const hit = last7.find((x) => x.label === label);
    if (hit) hit.count++;
  });
  ec("ch-task2")?.setOption({
    grid: { top: 28, bottom: 30, left: 44, right: 16 },
    xAxis: {
      type: "category",
      data: last7.map((x) => x.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "bar",
        data: last7.map((x) => x.count),
        barWidth: 18,
        label: { show: true, position: "top", fontSize: 11, color: "#6B7C93" },
        itemStyle: { color: "#0077E6", borderRadius: [4, 4, 0, 0] },
      },
    ],
  });

  // ── 课件资源面板 ─────────────────────────
  const subjCount = {};
  tasks.value.forEach((t) => {
    if (t.status !== "completed") return;
    const s = t.subject || "未分类";
    subjCount[s] = (subjCount[s] || 0) + 1;
  });
  const subjKeys = Object.keys(subjCount);
  const subjVals = subjKeys.map((k) => subjCount[k]);
  ec("ch-cw1")?.setOption({
    grid: { top: 28, bottom: 34, left: 44, right: 16 },
    xAxis: {
      type: "category",
      data: subjKeys.length ? subjKeys : ["暂无"],
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      splitLine: { lineStyle: { color: "#EEF1F5", type: "dashed" } },
      axisLabel: { color: "#6B7C93", fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    tooltip: { ...tip, trigger: "axis" },
    series: [
      {
        type: "bar",
        data: subjKeys.length ? subjVals : [0],
        barWidth: 22,
        label: { show: true, position: "top", fontSize: 11, color: "#6B7C93" },
        itemStyle: { color: "#00C2D4", borderRadius: [4, 4, 0, 0] },
      },
    ],
  });

  const statusCount = { queued: 0, processing: 0, completed: 0, failed: 0 };
  tasks.value.forEach((t) => {
    if (statusCount[t.status] !== undefined) statusCount[t.status]++;
  });
  const statusPieData = Object.keys(statusCount)
    .filter((k) => statusCount[k] > 0)
    .map((k) => ({
      value: statusCount[k],
      name: statusMap[k].label,
      itemStyle: { color: statusMap[k].color },
    }));
  ec("ch-cw2")?.setOption({
    tooltip: { ...tip, trigger: "item" },
    legend: {
      show: true,
      bottom: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: "#6B7C93", fontSize: 11 },
    },
    series: [
      {
        type: "pie",
        radius: ["42%", "72%"],
        center: ["50%", "44%"],
        avoidLabelOverlap: true,
        label: {
          show: true,
          color: "#6B7C93",
          fontSize: 12,
          formatter: "{b}\n{d}%",
        },
        data: statusPieData.length
          ? statusPieData
          : [{ value: 1, name: "暂无数据", itemStyle: { color: "#E5E8EF" } }],
      },
    ],
  });
}

const onResize = () => charts.forEach((c) => c?.resize());

// ── 生成任务 / 课件资源数据 ───────────────
const tasks = ref([]);
const tasksLoading = ref(false);
const tasksError = ref("");

const typeMap = {
  ppt: { label: "PPT课件", color: "#0077E6", bg: "rgba(0,119,230,0.1)" },
  doc: { label: "教案文档", color: "#10B981", bg: "rgba(16,185,129,0.1)" },
  quiz: { label: "课堂练习", color: "#00C2D4", bg: "rgba(0,194,212,0.1)" },
  exam: { label: "考试试卷", color: "#6366F1", bg: "rgba(99,102,241,0.1)" },
};
const statusMap = {
  queued: { label: "排队中", color: "#94A3B8", bg: "rgba(148,163,184,0.12)" },
  processing: { label: "生成中", color: "#0077E6", bg: "rgba(0,119,230,0.1)" },
  completed: { label: "已完成", color: "#10B981", bg: "rgba(16,185,129,0.1)" },
  failed: { label: "失败", color: "#EF4444", bg: "rgba(239,68,68,0.1)" },
};

function typeLabel(t) {
  return typeMap[t]?.label || t || "未知";
}
function statusLabel(s) {
  return statusMap[s]?.label || s || "未知";
}

const completedTasks = computed(() =>
  tasks.value.filter((t) => t.status === "completed"),
);
const activeTasks = computed(() =>
  tasks.value.filter((t) => t.status === "processing" || t.status === "queued"),
);
const successRate = computed(() => {
  const done = tasks.value.filter(
    (t) => t.status === "completed" || t.status === "failed",
  );
  if (!done.length) return "—";
  const ok = tasks.value.filter((t) => t.status === "completed").length;
  return `${Math.round((ok / done.length) * 100)}%`;
});

async function loadTasks() {
  tasksLoading.value = true;
  tasksError.value = "";
  try {
    tasks.value = await getCoursewareHistory();
  } catch (e) {
    tasksError.value = e.message || "加载失败";
  } finally {
    tasksLoading.value = false;
    nextTick(initCharts);
  }
}

function handleDelete(t) {
  if (!window.confirm(`确认删除「${t.topic || t.filename || t.id}」？`)) return;
  deleteCoursewareTask(t.id)
    .then(() => loadTasks())
    .catch((e) => (tasksError.value = e.message || "删除失败"));
}

function handleDownload(t) {
  if (t.filename) downloadFile(t.id, t.filename);
}

onMounted(() => {
  nextTick(initCharts);
  loadTasks();
  window.addEventListener("resize", onResize);
});
onUnmounted(() => {
  window.removeEventListener("resize", onResize);
  disposeAll();
});

// 切换菜单时：自动展开所在分组，等 v-if 渲染出新的 DOM 后再初始化图表
watch(activeMenu, (id) => {
  const group = menuGroups.find((g) => g.children?.some((c) => c.id === id));
  if (group && !openGroups.value.has(group.id)) {
    const next = new Set(openGroups.value);
    next.add(group.id);
    openGroups.value = next;
  }
  nextTick(initCharts);
});

// ── 数据 ──────────────────────────────────
const weekDays = ["周一", "周二", "周三", "周四", "周五"];
const periods = ["第1节", "第2节", "第3节", "第4节", "第5节", "第6节", "第7节"];
const scheduleData = {
  周一: { 第1节: "高一(3)班 物理", 第3节: "高二(1)班 物理" },
  周二: { 第2节: "高一(3)班 物理", 第4节: "高三(2)班 物理" },
  周三: { 第1节: "高一(3)班 物理", 第5节: "教研活动" },
  周四: { 第3节: "高二(1)班 物理", 第6节: "高一(3)班 物理" },
  周五: { 第2节: "高二(1)班 物理", 第4节: "高三(2)班 物理", 第7节: "班会" },
};
const classList = ["高一(3)班", "高二(1)班", "高三(2)班"];
const activeClass = ref("高一(3)班");
// 学生名单与成绩取自统一演示数据源（同一天刷新结果恒定，跨天缓慢变化）
const studentData = demo.students;
const templates = [
  {
    id: "chinese_style",
    name: "中国风模版",
    desc: "水墨古典风格 · 适合语文/政治/文化课",
    type: "PPT",
  },
  {
    id: "spring",
    name: "春天主题模版",
    desc: "清新自然风格 · 适合生物/地理/科学课",
    type: "PPT",
  },
  {
    id: "history",
    name: "历史教育模版",
    desc: "古朴厚重风格 · 适合历史/文化类课程",
    type: "PPT",
  },
  {
    id: "first_class",
    name: "开学第一课模版",
    desc: "通用简洁风格 · 适合数学/英语/理化课",
    type: "PPT",
  },
  {
    id: "chapter4",
    name: "章节教学模版",
    desc: "结构分明风格 · 适合系统化章节教学",
    type: "PPT",
  },
  {
    id: "chinese_style",
    name: "语文精读课模版",
    desc: "背景→朗读→分析→拓展·深阅读",
    type: "教案",
  },
].map((t, i) => ({
  ...t,
  used: seededInt(`zqls-admin:${dateKey()}:tpl-used-${i}`, 8, 26),
}));

// ── 图表解读配置（全部由演示数据推导）─────────────────
// 每条 insight / suggest 都从 demo 实时算出，所以不可能出现"文案写 15 个、
// 图上却画 8 个"的矛盾。desc 是定性说明、与数值无关，保持固定。
const KIND_LABELS = ["PPT 课件", "教案文档", "考试试卷", "课堂练习"];
const DIM_LABELS = ["基础知识", "公式运用", "实验探究", "综合解题", "创新思维"];
const GDIM_LABELS = ["概念理解", "公式应用", "实验探究", "计算能力", "分析推理"];
const DIST_LABELS = ["60 分以下", "60-69", "70-79", "80-89", "90-100"];
const TPL_LABELS = [
  "数学复习课",
  "物理新授课",
  "化学实验课",
  "语文精读课",
  "英语听力课",
];
const GRADE_LABELS = ["高一", "高二", "高三"];
const WEEK_FULL = ["周一", "周二", "周三", "周四", "周五"];
const TREND_MONTHS = ["3月", "4月", "5月", "6月", "7月", "8月"];
const OPS_MONTHS = ["1月", "2月", "3月", "4月", "5月", "6月"];

/** 返回按数值从大到小排列的下标序列 */
const byDesc = (arr) => arr.map((_, i) => i).sort((a, b) => arr[b] - arr[a]);
/** 一组数各占多大百分比（四舍五入） */
const pctOf = (arr) => {
  const total = sumOf(arr) || 1;
  return arr.map((v) => Math.round((v / total) * 100));
};

const chartInfo = computed(() => {
  const d = demo;
  const wRank = byDesc(d.weekly);
  const kPct = pctOf(d.kind);
  const sRank = byDesc(d.subject);
  const gRank = byDesc(d.gradeHours);
  const uRank = byDesc(d.util);
  const heatTop = d.heat.reduce((m, c) => (c[2] > m[2] ? c : m), d.heat[0]);
  const utilAvg = Math.round(sumOf(d.util) / d.util.length);
  const c1 = d.radar3[0];
  const c1Hi = argMax(c1);
  const c1Lo = argMin(c1);
  const c2Top = byDesc(d.scoreDist3.map((a) => a[4]))[0];
  const c4Gain = d.examTrend3.map((a) => a[a.length - 1] - a[0]);
  const c4Top = byDesc(c4Gain)[0];
  const g1Hi = argMax(d.gradeDist);
  const g1Total = sumOf(d.gradeDist) || 1;
  const g1Pass = Math.round(((g1Total - d.gradeDist[0]) / g1Total) * 100);
  const phys = d.subjectRadar[0];
  const g3Hi = argMax(phys);
  const g3Lo = argMin(phys);
  const stuAvg = Math.round(
    sumOf(d.students.map((s) => s.score)) / d.students.length,
  );
  const stuTop = d.students[0];
  const stuLow = d.students[d.students.length - 1];
  const t2Pct = pctOf(d.templMix);
  const t3Total = [0, 1, 2, 3, 4, 5].map((i) =>
    d.templTrend.reduce((s, a) => s + a[i], 0),
  );
  const t3Rank = byDesc(t3Total);
  const stPct = pctOf(d.storage);
  const opsRank = byDesc(d.monthlyOps);

  return {
    "ch-d1": {
      desc: "统计本周每日课件生成数量，用于观察备课节奏与工作高峰。",
      insight: `周${WEEK_LABELS[wRank[0]]}生成量最高（${d.weekly[wRank[0]]} 个），周${WEEK_LABELS[wRank[6]]}最少（${d.weekly[wRank[6]]} 个），符合教学周节奏。`,
      suggest: `可将需打磨的课件安排在周${WEEK_LABELS[wRank[6]]}低峰期制作，错峰提升质量。`,
    },
    "ch-d2": {
      desc: "各类课件的产出占比，反映备课资源的分配结构。",
      insight: `${KIND_LABELS[0]}占 ${kPct[0]}%，是当前主力产出，教案与试卷合计约 ${kPct[1] + kPct[2]}%。`,
      suggest: `教案类占比 ${kPct[1]}%，可尝试用 AI 一键生成配套教案补齐缺口。`,
    },
    "ch-d3": {
      desc: "各学科课件生成数量对比，用于发现备课资源覆盖的强弱学科。",
      insight: `${SUBJECT_LABELS[sRank[0]]}（${d.subject[sRank[0]]} 个）与${SUBJECT_LABELS[sRank[1]]}（${d.subject[sRank[1]]} 个）产出最高，${SUBJECT_LABELS[sRank[5]]}（${d.subject[sRank[5]]} 个）偏少。`,
      suggest: `${SUBJECT_LABELS[sRank[5]]}、${SUBJECT_LABELS[sRank[4]]}资源缺口明显，建议优先补充对应学科的专题模板。`,
    },
    "ch-s1": {
      desc: "以热力图呈现一周各节次课程安排的密度，辅助排课与教研调度。",
      insight: `${WEEK_FULL[heatTop[0]]}第 ${heatTop[1] + 1} 节课时最集中，整体排课密度适中。`,
      suggest: "可将教研活动、公开课试讲安排在课时较少的时段。",
    },
    "ch-s2": {
      desc: "各年级每周课时总量对比，用于评估各年级教学任务的轻重。",
      insight: `${GRADE_LABELS[gRank[0]]}周课时最多（${d.gradeHours[gRank[0]]} 节），${GRADE_LABELS[gRank[2]]}最少（${d.gradeHours[gRank[2]]} 节），总量分布合理。`,
      suggest: `${GRADE_LABELS[gRank[2]]}课时偏少，复习资料与习题可提前规划补足。`,
    },
    "ch-s3": {
      desc: "学期教学进度完成情况，对比计划进度判断教学是否滞后。",
      insight: `当前完成 ${d.progress}%，${d.progress >= 65 ? "略高于" : "基本持平于"}学期时间进度，教学节奏平稳。`,
      suggest: "保持当前进度，可将富余时间用于章节复习与查漏补缺。",
    },
    "ch-s4": {
      desc: "每日课程类型构成（新授 / 复习 / 实验 / 其他）及周课时利用率。",
      insight: `周一至周三以新授课为主，周课时利用率约 ${utilAvg}%。`,
      suggest: "实验课改到上午效果更佳，可提升学生课堂参与度。",
    },
    "ch-s5": {
      desc: "各天实际课时占计划课时的比例，用于发现利用率偏低的教学日。",
      insight: `周${WEEK_LABELS[uRank[0]]}利用率最高（${d.util[uRank[0]]}%），周${WEEK_LABELS[uRank[4]]}最低（${d.util[uRank[4]]}%），存在课时空档。`,
      suggest: "可将课时空档用于答疑或教研活动，提升整体课时利用率。",
    },
    "ch-c1": {
      desc: "以雷达图对比各班级五项核心能力维度，快速定位班级优劣势。",
      insight: `${d.clsNames[0]}${DIM_LABELS[c1Hi]}最强（${c1[c1Hi]}），${DIM_LABELS[c1Lo]}偏弱（${c1[c1Lo]}），维度不均衡。`,
      suggest: `建议${d.clsNames[0]}增加${DIM_LABELS[c1Lo]}专项训练，补齐短板。`,
    },
    "ch-c2": {
      desc: "各班级成绩分段人数分布，直观反映班级整体水平与分层情况。",
      insight: `${d.clsNames[c2Top]} 90 分以上人数最多（${d.scoreDist3[c2Top][4]} 人），分层结构清晰。`,
      suggest: `可总结${d.clsNames[c2Top]}的高分经验，在年级内推广教学方法。`,
    },
    "ch-c3": {
      desc: "学生成绩与课堂参与度的散点图，用于发现需要重点关注的学生。",
      insight: "成绩与参与度整体正相关，左下角少数学生参与度低且成绩偏低。",
      suggest: "对参与度低的学生进行个别沟通，必要时安排导师结对帮扶。",
    },
    "ch-c4": {
      desc: "历次考试各班级平均分走势，用于跟踪各班成绩变化与提升幅度。",
      insight: `三个班级成绩均呈上升趋势，${d.clsNames[c4Top]}提升幅度最大（+${c4Gain[c4Top]} 分）。`,
      suggest: `可提炼${d.clsNames[c4Top]}的教学方法，作为教研组的借鉴案例。`,
    },
    "ch-g1": {
      desc: "本次考试各分数段人数分布，用于评估整体成绩形态（正态程度）。",
      insight: `${DIST_LABELS[g1Hi]} 段人数最多（${d.gradeDist[g1Hi]} 人），整体呈正态分布，及格率 ${g1Pass}%。`,
      suggest: "中段学生提分空间最大，可重点进行中档题强化训练。",
    },
    "ch-g2": {
      desc: "班级平均分近六周的变化趋势，并与年级平均分对比。",
      insight: `班级均分由 ${d.classAvg[0]} 分升至 ${d.classAvg[5]} 分，${d.classAvg[5] >= 80 ? "已稳定超过" : "正在接近"}年级平均线。`,
      suggest: "关注上升放缓的节点，避免成绩波动回撤。",
    },
    "ch-g3": {
      desc: "各学科能力维度的雷达对比，用于发现学科内部的薄弱环节。",
      insight: `物理${GDIM_LABELS[g3Hi]}维度（${phys[g3Hi]}）明显强于${GDIM_LABELS[g3Lo]}（${phys[g3Lo]}），差距最大。`,
      suggest: `增加物理${GDIM_LABELS[g3Lo]}类作业，强化动手实践能力。`,
    },
    "ch-g4": {
      desc: `学生个人成绩与班级平均分（${stuAvg} 分）的对比，用于个别学生诊断。`,
      insight: `${stuTop.name}（${stuTop.score} 分）领先均分 ${stuTop.score - stuAvg} 分，${stuLow.name}（${stuLow.score} 分）低于均分 ${stuAvg - stuLow.score} 分。`,
      suggest: "对落后学生制定一对一提升计划，重点关注弱项学科。",
    },
    "ch-t1": {
      desc: "各课件模板的使用次数排行，反映教师对不同模板的偏好程度。",
      insight: `${TPL_LABELS[0]}模板使用最多（${d.templUse[0]} 次），是教师最常用模板。`,
      suggest: "可将热门模板设为默认推荐，减少教师的搜索成本。",
    },
    "ch-t2": {
      desc: "不同类型模板的占比，用于判断模板资源的供需是否匹配。",
      insight: `PPT 模板占 ${t2Pct[0]}%，是核心需求；教案模板占 ${t2Pct[1]}%。`,
      suggest: "补充教案类模板，可覆盖更多备课场景，提升利用率。",
    },
    "ch-t3": {
      desc: "三类模板近六月的使用趋势，用于观察需求的季节性波动。",
      insight: `${TREND_MONTHS[t3Rank[0]]}使用量最高（合计 ${t3Total[t3Rank[0]]} 次），${TREND_MONTHS[t3Rank[5]]}最低。`,
      suggest: "可在开学季前提前上新并预热模板，抓住需求高峰。",
    },
    "ch-ss": {
      desc: "存储空间占用分布，用于排查存储瓶颈并规划清理策略。",
      insight: `课件文件占 ${stPct[0]}%，是主要存储消耗；系统缓存占 ${stPct[3]}%。`,
      suggest: "建议每月清理系统缓存与旧版本课件，释放存储空间。",
    },
    "ch-ss2": {
      desc: "每月系统操作次数，用于观察平台使用活跃度与高峰期。",
      insight: `${OPS_MONTHS[opsRank[0]]}操作最频繁（${d.monthlyOps[opsRank[0]]} 次），处于教学活跃期。`,
      suggest: "在活跃高峰期前完成系统维护与扩容，保障使用体验。",
    },
  };
});

// ── 设置 ─────────────────────────────────
const profile = ref({
  name: userName.value,
  email: "admin@school.edu.cn",
  phone: "138****5678",
  notifyReview: true,
  notifyGrade: false,
  notifySystem: true,
});

function useTemplate(t) {
  if (t.type === "PPT") {
    // 跳转到课件制作页面，并预选模版
    router.push({ path: "/features", query: { template: t.id, panel: "ppt" } });
  } else {
    router.push({ path: "/features", query: { panel: "doc" } });
  }
}
</script>

<template>
  <div class="admin-shell min-h-screen bg-[#f7f9fc] flex flex-col antialiased">
    <a
      href="#main-content"
      class="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:bg-white focus:text-[#0077e6] focus:px-3 focus:py-2 focus:rounded-lg focus:shadow-md focus:text-sm"
      >跳到主内容</a
    >
    <!-- 顶栏 -->
    <header
      class="fixed top-0 left-0 right-0 z-50 h-12 bg-white/90 backdrop-blur border-b border-gray-100 flex items-center justify-between gap-4 px-5"
    >
      <!-- 品牌 + 面包屑 -->
      <div class="flex items-center gap-3 min-w-0">
        <div class="flex items-center gap-2">
          <span class="admin-brand-icon">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path
                d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"
              />
            </svg>
          </span>
          <h1
            class="text-sm font-bold tracking-wide text-gray-900 whitespace-nowrap"
          >
            教学管理
          </h1>
        </div>
        <div
          v-if="currentCrumb"
          class="hidden sm:flex items-center gap-1.5 text-[13px] text-gray-400 min-w-0"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="w-3.5 h-3.5 shrink-0"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M9 6l6 6-6 6" />
          </svg>
          <span v-if="currentCrumb.group" class="whitespace-nowrap">{{
            currentCrumb.group.label
          }}</span>
          <svg
            v-if="currentCrumb.group"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="w-3 h-3 shrink-0"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M9 6l6 6-6 6" />
          </svg>
          <span
            class="font-semibold text-gray-600 whitespace-nowrap truncate"
            >{{ currentCrumb.item.label }}</span
          >
        </div>
      </div>

      <!-- 右侧操作区 -->
      <div class="flex items-center gap-2">
        <RouterLink to="/features" class="admin-header-cta">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            class="w-3.5 h-3.5"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12h14" />
          </svg>
          <span>新建课件</span>
        </RouterLink>

        <!-- 通知 -->
        <div class="relative">
          <button
            class="admin-header-icon-btn"
            :aria-expanded="showNotif"
            aria-label="通知"
            @click="
              showNotif = !showNotif;
              showUserMenu = false;
            "
          >
            <svg
              viewBox="0 0 24 24"
              fill="currentColor"
              class="w-4 h-4"
              aria-hidden="true"
            >
              <path
                d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"
              />
            </svg>
            <span class="admin-header-dot" aria-hidden="true"></span>
          </button>
          <div
            v-if="showNotif"
            class="admin-dropdown admin-notif-panel"
            role="menu"
            aria-label="通知列表"
          >
            <div class="admin-dropdown-head">通知</div>
            <div
              v-for="n in notifications"
              :key="n.id"
              class="admin-notif-item"
              :class="{ 'is-unread': n.unread }"
            >
              <div class="flex items-center gap-2">
                <span class="text-[13px] font-semibold text-gray-900">{{
                  n.title
                }}</span>
                <span
                  v-if="n.unread"
                  class="w-1.5 h-1.5 rounded-full bg-[#0077e6] shrink-0"
                  aria-hidden="true"
                ></span>
              </div>
              <p class="text-[12px] text-gray-500 mt-0.5 leading-snug">
                {{ n.desc }}
              </p>
              <span class="text-[11px] text-gray-400 mt-1 block">{{
                n.time
              }}</span>
            </div>
          </div>
        </div>

        <!-- 用户 -->
        <div class="relative">
          <button
            class="admin-user-btn"
            :aria-expanded="showUserMenu"
            @click="
              showUserMenu = !showUserMenu;
              showNotif = false;
            "
          >
            <span class="admin-avatar">{{ avatarText }}</span>
            <span
              class="hidden md:inline text-[13px] text-gray-600 font-medium"
              >{{ userName }}</span
            >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              class="w-3 h-3 text-gray-400 transition-transform"
              :class="{ 'rotate-180': showUserMenu }"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          <div
            v-if="showUserMenu"
            class="admin-dropdown admin-user-menu"
            role="menu"
          >
            <div class="admin-user-menu-head">
              <span class="admin-avatar admin-avatar--lg">{{
                avatarText
              }}</span>
              <div class="min-w-0">
                <div class="text-sm font-semibold text-gray-900 truncate">
                  {{ userName }}
                </div>
                <div class="text-[11px] text-gray-400">教师账号</div>
              </div>
            </div>
            <RouterLink
              to="/profile"
              class="admin-menu-item"
              @click="showUserMenu = false"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path
                  d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
                />
              </svg>
              <span>个人中心</span>
            </RouterLink>
            <RouterLink
              to="/"
              class="admin-menu-item"
              @click="showUserMenu = false"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z" />
              </svg>
              <span>返回首页</span>
            </RouterLink>
          </div>
        </div>
      </div>
    </header>

    <!-- 点击外部关闭下拉 -->
    <div
      v-if="showNotif || showUserMenu"
      class="fixed inset-0 z-40"
      @click="
        showNotif = false;
        showUserMenu = false;
      "
    ></div>

    <div class="flex pt-12">
      <!-- 侧栏 -->
      <aside
        class="admin-sidebar w-48 shrink-0 bg-white border-r border-gray-100 sticky top-12 h-[calc(100vh-48px)] overflow-y-auto p-3"
      >
        <div class="admin-nav-head">管理导航</div>
        <nav class="flex flex-col gap-1">
          <template v-for="g in menuGroups" :key="g.id">
            <!-- 独立项 -->
            <button
              v-if="g.standalone"
              class="admin-nav-btn"
              :class="{ 'is-active': activeMenu === g.id }"
              @click="activeMenu = g.id"
            >
              <span class="admin-nav-icon">
                <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                  <path :d="icons[g.icon]" />
                </svg>
              </span>
              <span class="admin-nav-label">{{ g.label }}</span>
            </button>
            <!-- 折叠分组 -->
            <div v-else class="admin-nav-group">
              <button
                class="admin-nav-group-btn"
                :class="{ 'is-open': openGroups.has(g.id) }"
                :aria-expanded="openGroups.has(g.id)"
                @click="toggleGroup(g.id)"
              >
                <span class="admin-nav-icon">
                  <svg
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path :d="icons[g.icon]" />
                  </svg>
                </span>
                <span class="admin-nav-label">{{ g.label }}</span>
                <span class="admin-nav-count">{{ g.children.length }}</span>
                <span
                  class="admin-nav-chevron"
                  :class="{ 'is-open': openGroups.has(g.id) }"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    aria-hidden="true"
                  >
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </span>
              </button>
              <div v-if="openGroups.has(g.id)" class="admin-nav-sub">
                <button
                  v-for="m in g.children"
                  :key="m.id"
                  class="admin-nav-btn admin-nav-sub-btn"
                  :class="{ 'is-active': activeMenu === m.id }"
                  @click="activeMenu = m.id"
                >
                  <span class="admin-nav-icon admin-nav-icon--sub">
                    <svg
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path :d="icons[m.icon]" />
                    </svg>
                  </span>
                  <span class="admin-nav-label">{{ m.label }}</span>
                </button>
              </div>
            </div>
          </template>
        </nav>
      </aside>

      <!-- 主区 -->
      <main
        class="flex-1 overflow-y-auto p-5 lg:p-6 flex flex-col gap-4"
        id="main-content"
        aria-labelledby="main-heading"
      >
        <h2 id="main-heading" class="sr-only">管理后台</h2>
        <!-- ═══ 工作台 ═══ -->
        <template v-if="activeMenu === 'dashboard'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div
              class="admin-card stat-card p-4"
              v-for="(k, i) in [
                { v: '106', l: '总课件数' },
                { v: '42', l: '本月新增' },
                { v: '86.3', l: '平均评分' },
                { v: '12', l: '在教班级' },
              ]"
              :key="i"
            >
              <div class="stat-value">
                {{ k.v }}
              </div>
              <div class="text-[13px] text-gray-500 mt-0.5">{{ k.l }}</div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="admin-card p-5 md:col-span-2">
              <div class="chart-head">
                <h3 class="chart-title">周生成趋势</h3>
                <p class="chart-desc">{{ chartInfo["ch-d1"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-d1"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-d1"].suggest }}</span>
                </p>
              </div>
              <div id="ch-d1" class="h-72"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">课件类型占比</h3>
                <p class="chart-desc">{{ chartInfo["ch-d2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-d2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-d2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-d2" class="h-72"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">学科分布</h3>
                <p class="chart-desc">{{ chartInfo["ch-d3"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-d3"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-d3"].suggest }}</span>
                </p>
              </div>
              <div id="ch-d3" class="h-72"></div>
            </div>
          </div>
        </template>

        <!-- ═══ 生成任务 ═══ -->
        <template v-if="activeMenu === 'tasks'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-4">
              <div class="stat-value">{{ tasks.length }}</div>
              <div class="text-[13px] text-gray-500 mt-0.5">任务总数</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">{{ activeTasks.length }}</div>
              <div class="text-[13px] text-gray-500 mt-0.5">进行中</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">{{ completedTasks.length }}</div>
              <div class="text-[13px] text-gray-500 mt-0.5">累计完成</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">{{ successRate }}</div>
              <div class="text-[13px] text-gray-500 mt-0.5">成功率</div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">生成类型分布</h3>
                <p class="chart-desc">各类型课件的生成数量占比。</p>
              </div>
              <div id="ch-task1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">近7日生成趋势</h3>
                <p class="chart-desc">近一周每日生成的课件数量。</p>
              </div>
              <div id="ch-task2" class="h-64"></div>
            </div>
          </div>

          <div class="admin-card p-5">
            <div class="flex items-center justify-between mb-3">
              <h3 class="chart-title">生成任务队列</h3>
              <button
                class="admin-refresh-btn"
                :disabled="tasksLoading"
                @click="loadTasks"
              >
                {{ tasksLoading ? "刷新中…" : "刷新" }}
              </button>
            </div>
            <p
              v-if="tasksError"
              class="text-[13px] text-[#EF4444] mb-2"
              role="alert"
            >
              {{ tasksError }}
            </p>
            <div
              v-if="tasksLoading && !tasks.length"
              class="py-8 text-center text-[13px] text-gray-500"
            >
              正在加载任务…
            </div>
            <div
              v-else-if="!tasks.length"
              class="py-8 text-center text-[13px] text-gray-500"
            >
              暂无生成任务，去「课件制作」页提交一次生成吧
            </div>
            <div v-else class="overflow-x-auto">
              <table class="admin-table w-full">
                <thead>
                  <tr>
                    <th>类型</th>
                    <th>学科 / 课题</th>
                    <th>状态</th>
                    <th>进度</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in tasks" :key="t.id">
                    <td>
                      <span
                        class="type-badge"
                        :style="{
                          color: typeMap[t.type]?.color,
                          background: typeMap[t.type]?.bg,
                        }"
                        >{{ typeLabel(t.type) }}</span
                      >
                    </td>
                    <td>
                      <div class="font-semibold text-[#111]">
                        {{ t.topic || "—" }}
                      </div>
                      <div class="text-[12px] text-gray-500">
                        {{ t.subject || "未分类"
                        }}{{ t.grade ? " · " + t.grade : "" }}
                      </div>
                    </td>
                    <td>
                      <span
                        class="status-badge"
                        :style="{
                          color: statusMap[t.status]?.color,
                          background: statusMap[t.status]?.bg,
                        }"
                        >{{ statusLabel(t.status) }}</span
                      >
                    </td>
                    <td>
                      <div class="flex items-center gap-2 min-w-[120px]">
                        <div class="progress-track">
                          <div
                            class="progress-fill"
                            :class="{
                              'is-done': t.status === 'completed',
                              'is-failed': t.status === 'failed',
                            }"
                            :style="{
                              transform:
                                'scaleX(' +
                                (t.status === 'failed' ? 100 : t.progress) /
                                  100 +
                                ')',
                            }"
                          ></div>
                        </div>
                        <span class="text-[12px] text-gray-500 tabular-nums">{{
                          t.status === "failed" ? "—" : t.progress + "%"
                        }}</span>
                      </div>
                    </td>
                    <td class="text-[13px] text-gray-500 whitespace-nowrap">
                      {{ t.created_at || "—" }}
                    </td>
                    <td>
                      <div class="flex items-center gap-2">
                        <button
                          v-if="t.status === 'completed' && t.filename"
                          class="admin-action-btn"
                          @click="handleDownload(t)"
                        >
                          下载
                        </button>
                        <button
                          class="admin-action-btn admin-action-btn--danger"
                          @click="handleDelete(t)"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- ═══ 课件资源 ═══ -->
        <template v-if="activeMenu === 'courseware'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-4">
              <div class="stat-value">{{ completedTasks.length }}</div>
              <div class="text-[13px] text-gray-500 mt-0.5">课件总数</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">
                {{ completedTasks.filter((t) => t.type === "ppt").length }}
              </div>
              <div class="text-[13px] text-gray-500 mt-0.5">PPT课件</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">
                {{ completedTasks.filter((t) => t.type === "doc").length }}
              </div>
              <div class="text-[13px] text-gray-500 mt-0.5">教案文档</div>
            </div>
            <div class="admin-card stat-card p-4">
              <div class="stat-value">
                {{
                  completedTasks.filter(
                    (t) => t.type === "quiz" || t.type === "exam",
                  ).length
                }}
              </div>
              <div class="text-[13px] text-gray-500 mt-0.5">试卷练习</div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">学科分布</h3>
                <p class="chart-desc">已生成课件的学科覆盖情况。</p>
              </div>
              <div id="ch-cw1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">状态分布</h3>
                <p class="chart-desc">所有任务的状态构成。</p>
              </div>
              <div id="ch-cw2" class="h-64"></div>
            </div>
          </div>

          <div class="admin-card p-5">
            <h3 class="chart-title mb-3">课件资源列表</h3>
            <div
              v-if="!completedTasks.length"
              class="py-8 text-center text-[13px] text-gray-500"
            >
              暂无已生成的课件资源
            </div>
            <div v-else class="overflow-x-auto">
              <table class="admin-table w-full">
                <thead>
                  <tr>
                    <th>文件名</th>
                    <th>类型</th>
                    <th>学科</th>
                    <th>课题</th>
                    <th>年级</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="t in completedTasks" :key="t.id">
                    <td class="font-semibold text-[#111]">
                      {{ t.filename || "—" }}
                    </td>
                    <td>
                      <span
                        class="type-badge"
                        :style="{
                          color: typeMap[t.type]?.color,
                          background: typeMap[t.type]?.bg,
                        }"
                        >{{ typeLabel(t.type) }}</span
                      >
                    </td>
                    <td class="text-[13px] text-gray-500">
                      {{ t.subject || "未分类" }}
                    </td>
                    <td class="text-[13px] text-gray-500">
                      {{ t.topic || "—" }}
                    </td>
                    <td class="text-[13px] text-gray-500">
                      {{ t.grade || "—" }}
                    </td>
                    <td class="text-[13px] text-gray-500 whitespace-nowrap">
                      {{ t.created_at || "—" }}
                    </td>
                    <td>
                      <div class="flex items-center gap-2">
                        <button
                          v-if="t.filename"
                          class="admin-action-btn"
                          @click="handleDownload(t)"
                        >
                          下载
                        </button>
                        <button
                          class="admin-action-btn admin-action-btn--danger"
                          @click="handleDelete(t)"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- ═══ 课程表 ═══ -->
        <template v-if="activeMenu === 'schedule'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-5">
              <div class="stat-value">35</div>
              <div class="text-[13px] text-gray-500 mt-0.5">周总课时</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">3</div>
              <div class="text-[13px] text-gray-500 mt-0.5">任教班级</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">65%</div>
              <div class="text-[13px] text-gray-500 mt-0.5">学期进度</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">92%</div>
              <div class="text-[13px] text-gray-500 mt-0.5">出勤率</div>
            </div>
          </div>
          <div class="admin-card p-5">
            <h3 class="text-sm font-semibold text-gray-500 mb-3 text-pretty">
              课程表
            </h3>
            <div class="overflow-x-auto">
              <div
                class="grid"
                style="
                  grid-template-columns: 44px repeat(5, 1fr);
                  gap: 2px;
                  min-width: 400px;
                "
              >
                <div></div>
                <div
                  v-for="d in weekDays"
                  :key="d"
                  class="text-xs font-semibold text-gray-500 text-center py-1"
                >
                  {{ d }}
                </div>
                <template v-for="p in periods" :key="p">
                  <div
                    class="text-xs text-gray-500 flex items-center justify-center"
                  >
                    {{ p }}
                  </div>
                  <div
                    v-for="d in weekDays"
                    :key="d + p"
                    class="min-h-[30px] bg-gray-50 rounded p-1"
                  >
                    <div
                      v-if="scheduleData[d]?.[p]"
                      class="bg-[#0077e6]/10 text-[#0077e6] text-xs font-medium rounded px-1.5 py-0.5 leading-tight"
                    >
                      {{ scheduleData[d][p] }}
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">每日课程分布</h3>
                <p class="chart-desc">{{ chartInfo["ch-s4"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-s4"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-s4"].suggest }}</span>
                </p>
              </div>
              <div id="ch-s4" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">周课时利用率</h3>
                <p class="chart-desc">{{ chartInfo["ch-s5"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-s5"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-s5"].suggest }}</span>
                </p>
              </div>
              <div class="relative h-[240px]">
                <!-- 背景参考线 -->
                <div
                  class="absolute inset-0 flex flex-col justify-between pointer-events-none"
                >
                  <div class="border-t border-gray-100" style="height: 0"></div>
                  <div class="border-t border-gray-100" style="height: 0"></div>
                  <div class="border-t border-gray-100" style="height: 0"></div>
                  <div class="border-t border-gray-100" style="height: 0"></div>
                  <div
                    class="border-t border-dashed border-gray-200"
                    style="height: 0"
                  ></div>
                </div>
                <!-- 柱子 -->
                <div
                  class="absolute inset-x-0 bottom-0 flex items-end justify-around px-6"
                  style="top: 20px"
                >
                  <div
                    v-for="(v, i) in demo.util"
                    :key="i"
                    class="flex flex-col items-center"
                    style="width: 40px"
                  >
                    <span
                      class="text-sm font-semibold mb-1.5"
                      :class="
                        v >= 85
                          ? 'text-teal-700'
                          : v >= 75
                            ? 'text-cyan-700'
                            : 'text-amber-700'
                      "
                      >{{ v }}%</span
                    >
                    <div
                      class="w-full rounded-t transition-opacity duration-300 hover:opacity-80"
                      :style="{
                        height: v * 1.8 + 'px',
                        background: [
                          '#0D9488',
                          '#06B6D4',
                          '#0D9488',
                          '#F59E0B',
                          '#0D9488',
                        ][i],
                      }"
                    ></div>
                  </div>
                </div>
              </div>
              <div
                class="flex justify-around mt-3 pt-2 border-t border-gray-50"
              >
                <span
                  v-for="(day, i) in ['周一', '周二', '周三', '周四', '周五']"
                  :key="i"
                  class="text-xs text-gray-500"
                  style="width: 40px; text-align: center"
                  >{{ day }}</span
                >
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">课时热度</h3>
                <p class="chart-desc">{{ chartInfo["ch-s1"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-s1"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-s1"].suggest }}</span>
                </p>
              </div>
              <div id="ch-s1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">年级课时分布</h3>
                <p class="chart-desc">{{ chartInfo["ch-s2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-s2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-s2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-s2" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">教学完成度</h3>
                <p class="chart-desc">{{ chartInfo["ch-s3"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-s3"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-s3"].suggest }}</span>
                </p>
              </div>
              <div id="ch-s3" class="h-64"></div>
            </div>
          </div>
        </template>

        <!-- ═══ 学情分析 ═══ -->
        <template v-if="activeMenu === 'analytics'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-5">
              <div class="stat-value">3</div>
              <div class="text-[13px] text-gray-500 mt-0.5">班级数</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">120</div>
              <div class="text-[13px] text-gray-500 mt-0.5">学生总数</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">72.4</div>
              <div class="text-[13px] text-gray-500 mt-0.5">平均分</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">86%</div>
              <div class="text-[13px] text-gray-500 mt-0.5">及格率</div>
            </div>
          </div>
          <div
            class="flex gap-1.5 bg-white border border-gray-100 rounded-xl p-1.5 w-fit"
          >
            <button
              v-for="c in classList"
              :key="c"
              class="px-3.5 py-1.5 text-sm rounded-lg text-gray-500 hover:text-gray-700 transition-colors focus-visible:ring-2 focus-visible:ring-[#0077e6]/30 focus-visible:outline-none"
              :class="{
                '!text-gray-900 !bg-gray-100 font-semibold': activeClass === c,
              }"
              @click="activeClass = c"
            >
              {{ c }}
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">能力对比</h3>
                <p class="chart-desc">{{ chartInfo["ch-c1"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-c1"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-c1"].suggest }}</span>
                </p>
              </div>
              <div id="ch-c1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">分数分布</h3>
                <p class="chart-desc">{{ chartInfo["ch-g1"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-g1"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-g1"].suggest }}</span>
                </p>
              </div>
              <div id="ch-g1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">成绩·参与度</h3>
                <p class="chart-desc">{{ chartInfo["ch-c3"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-c3"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-c3"].suggest }}</span>
                </p>
              </div>
              <div id="ch-c3" class="h-64"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">6周趋势</h3>
                <p class="chart-desc">{{ chartInfo["ch-g2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-g2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-g2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-g2" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">学科能力</h3>
                <p class="chart-desc">{{ chartInfo["ch-g3"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-g3"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-g3"].suggest }}</span>
                </p>
              </div>
              <div id="ch-g3" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">班级分数段对比</h3>
                <p class="chart-desc">{{ chartInfo["ch-c2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-c2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-c2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-c2" class="h-64"></div>
            </div>
          </div>
          <div class="admin-card p-5">
            <h3 class="text-sm font-semibold text-gray-500 mb-3 text-pretty">
              {{ activeClass }} · 学生成绩明细
            </h3>
            <div class="text-sm">
              <div
                class="grid grid-cols-[1fr_50px_40px_60px_80px] gap-2 px-2.5 py-2 text-xs font-semibold text-gray-500 border-b border-gray-50 items-center"
              >
                <span>姓名</span><span>分数</span><span>趋势</span
                ><span>等级</span><span>薄弱项</span>
              </div>
              <div
                v-for="s in studentData"
                :key="s.name"
                class="grid grid-cols-[1fr_50px_40px_60px_80px] gap-2 px-2.5 py-1.5 hover:bg-gray-50 rounded items-center"
              >
                <span class="text-gray-900 font-medium">{{ s.name }}</span>
                <span
                  class="font-bold"
                  :class="{
                    'text-green-600': s.trend === 'up',
                    'text-amber-600': s.trend === 'stable',
                    'text-red-500': s.trend === 'down',
                  }"
                  >{{ s.score }}</span
                >
                <span class="text-sm">{{
                  { up: "↑", stable: "→", down: "↓" }[s.trend]
                }}</span>
                <span
                  class="text-xs font-semibold px-1.5 py-0.5 rounded-full w-fit"
                  :class="{
                    'bg-green-50 text-green-700':
                      s.status === '优秀' || s.status === '良好',
                    'bg-amber-50 text-amber-700': s.status === '中等',
                    'bg-red-50 text-red-600': s.status === '待提高',
                  }"
                  >{{ s.status }}</span
                >
                <span class="text-gray-500 text-xs">{{
                  s.score < 70 ? "需重点关注" : "—"
                }}</span>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">各班级成绩趋势</h3>
                <p class="chart-desc">{{ chartInfo["ch-c4"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-c4"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-c4"].suggest }}</span>
                </p>
              </div>
              <div id="ch-c4" class="h-64"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 gap-4">
            <div class="admin-card p-4 max-w-md mx-auto">
              <div class="chart-head">
                <h3 class="chart-title">学生成绩对比</h3>
                <p class="chart-desc">{{ chartInfo["ch-g4"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-g4"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-g4"].suggest }}</span>
                </p>
              </div>
              <div id="ch-g4" class="h-64"></div>
            </div>
          </div>
        </template>
        <template v-if="activeMenu === 'templates'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-5">
              <div class="stat-value">6</div>
              <div class="text-[13px] text-gray-500 mt-0.5">模板数</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">67</div>
              <div class="text-[13px] text-gray-500 mt-0.5">总使用</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">11.2</div>
              <div class="text-[13px] text-gray-500 mt-0.5">平均使用</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">5</div>
              <div class="text-[13px] text-gray-500 mt-0.5">PPT模板</div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">使用排行</h3>
                <p class="chart-desc">{{ chartInfo["ch-t1"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-t1"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-t1"].suggest }}</span>
                </p>
              </div>
              <div id="ch-t1" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">模板类型</h3>
                <p class="chart-desc">{{ chartInfo["ch-t2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-t2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-t2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-t2" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">月度趋势</h3>
                <p class="chart-desc">{{ chartInfo["ch-t3"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-t3"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-t3"].suggest }}</span>
                </p>
              </div>
              <div id="ch-t3" class="h-64"></div>
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <button
              v-for="t in templates"
              :key="t.id"
              class="bg-white border border-gray-100 rounded-xl p-3.5 flex items-center gap-4 hover:border-[#c9d5e3] hover:shadow-[0_4px_16px_rgba(10,15,26,0.06)] transition focus-visible:ring-2 focus-visible:ring-[#0077e6]/30 focus-visible:outline-none text-left"
              @click="useTemplate(t)"
            >
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center text-[13px] font-bold shrink-0"
                :class="
                  t.type === 'PPT'
                    ? 'bg-[#0077e6]/10 text-[#0077e6]'
                    : 'bg-[#059669]/10 text-[#047857]'
                "
              >
                {{ t.type === "PPT" ? "P" : "D" }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-semibold text-gray-900">
                  {{ t.name }}
                </div>
                <div class="text-xs text-gray-500 mt-0.5 truncate">
                  {{ t.desc }}
                </div>
                <div class="text-xs text-gray-500 mt-0.5">
                  使用 {{ t.used }} 次 · {{ t.type }}
                </div>
              </div>
            </button>
          </div>
        </template>

        <!-- ═══ 设置 ═══ -->
        <template v-if="activeMenu === 'settings'">
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div class="admin-card stat-card p-5">
              <div class="stat-value">106</div>
              <div class="text-[13px] text-gray-500 mt-0.5">课件文件</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">42</div>
              <div class="text-[13px] text-gray-500 mt-0.5">学生数据</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">18</div>
              <div class="text-[13px] text-gray-500 mt-0.5">模板资源</div>
            </div>
            <div class="admin-card stat-card p-5">
              <div class="stat-value">2.4 GB</div>
              <div class="text-[13px] text-gray-500 mt-0.5">总存储</div>
            </div>
          </div>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div class="admin-card p-5">
              <h3 class="text-sm font-semibold text-gray-500 mb-3 text-pretty">
                个人信息
              </h3>
              <div class="flex flex-col gap-2">
                <label
                  class="flex items-center gap-4 py-1.5 border-b border-gray-50 focus-within:border-blue-200 transition-colors"
                >
                  <span class="text-[13px] text-gray-500 w-10 shrink-0"
                    >姓名</span
                  ><input
                    v-model="profile.name"
                    name="display_name"
                    autocomplete="name"
                    spellcheck="false"
                    class="flex-1 text-sm text-gray-900 border-0 outline-none bg-transparent focus-visible:outline-none py-0.5"
                  />
                </label>
                <label
                  class="flex items-center gap-4 py-1.5 border-b border-gray-50 focus-within:border-blue-200 transition-colors"
                >
                  <span class="text-[13px] text-gray-500 w-10 shrink-0"
                    >邮箱</span
                  ><input
                    v-model="profile.email"
                    type="email"
                    name="email"
                    autocomplete="email"
                    spellcheck="false"
                    class="flex-1 text-sm text-gray-900 border-0 outline-none bg-transparent focus-visible:outline-none py-0.5"
                  />
                </label>
                <label
                  class="flex items-center gap-4 py-1.5 border-b border-gray-50 focus-within:border-blue-200 transition-colors"
                >
                  <span class="text-[13px] text-gray-500 w-10 shrink-0"
                    >手机</span
                  ><input
                    v-model="profile.phone"
                    type="tel"
                    name="phone"
                    autocomplete="tel"
                    inputmode="numeric"
                    class="flex-1 text-sm text-gray-900 border-0 outline-none bg-transparent focus-visible:outline-none py-0.5"
                  />
                </label>
              </div>
            </div>
            <div class="admin-card p-5">
              <h3 class="text-sm font-semibold text-gray-500 mb-3 text-pretty">
                通知偏好
              </h3>
              <div class="flex flex-col gap-2">
                <label
                  class="flex items-center justify-between py-1.5 cursor-pointer"
                  ><span class="text-sm text-gray-900">课件审核通知</span
                  ><input
                    type="checkbox"
                    v-model="profile.notifyReview"
                    aria-label="课件审核通知"
                    class="peer sr-only" /><span
                    class="w-7 h-4 bg-gray-200 rounded-full relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-3 after:h-3 after:bg-white after:rounded-full after:transition-transform peer-checked:bg-[#0077e6] peer-checked:after:translate-x-3"
                  ></span
                ></label>
                <label
                  class="flex items-center justify-between py-1.5 cursor-pointer"
                  ><span class="text-sm text-gray-900">成绩更新通知</span
                  ><input
                    type="checkbox"
                    v-model="profile.notifyGrade"
                    aria-label="成绩更新通知"
                    class="peer sr-only" /><span
                    class="w-7 h-4 bg-gray-200 rounded-full relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-3 after:h-3 after:bg-white after:rounded-full after:transition-transform peer-checked:bg-[#0077e6] peer-checked:after:translate-x-3"
                  ></span
                ></label>
                <label
                  class="flex items-center justify-between py-1.5 cursor-pointer"
                  ><span class="text-sm text-gray-900">系统公告</span
                  ><input
                    type="checkbox"
                    v-model="profile.notifySystem"
                    aria-label="系统公告"
                    class="peer sr-only" /><span
                    class="w-7 h-4 bg-gray-200 rounded-full relative after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-3 after:h-3 after:bg-white after:rounded-full after:transition-transform peer-checked:bg-[#0077e6] peer-checked:after:translate-x-3"
                  ></span
                ></label>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">存储使用</h3>
                <p class="chart-desc">{{ chartInfo["ch-ss"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-ss"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-ss"].suggest }}</span>
                </p>
              </div>
              <div id="ch-ss" class="h-64"></div>
            </div>
            <div class="admin-card p-5">
              <div class="chart-head">
                <h3 class="chart-title">月操作频次</h3>
                <p class="chart-desc">{{ chartInfo["ch-ss2"].desc }}</p>
                <p class="chart-insight">
                  <span class="chart-tag">洞察</span>
                  <span>{{ chartInfo["ch-ss2"].insight }}</span>
                </p>
                <p class="chart-suggest">
                  <span class="chart-tag chart-tag--suggest">建议</span>
                  <span>{{ chartInfo["ch-ss2"].suggest }}</span>
                </p>
              </div>
              <div id="ch-ss2" class="h-64"></div>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.admin-shell {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--ink);
  line-height: 1.5;
}

/* ── 顶栏 ─────────────────────────────── */
.admin-brand-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent), var(--cyan));
  color: #fff;
  flex-shrink: 0;
}

.admin-brand-icon svg {
  width: 15px;
  height: 15px;
}

.admin-header-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12.5px;
  font-weight: 600;
  color: #fff;
  background: var(--accent);
  border-radius: 8px;
  padding: 6px 12px;
  box-shadow: 0 1px 3px rgba(0, 119, 230, 0.35);
  transition:
    background 0.2s,
    box-shadow 0.2s;
}

.admin-header-cta:hover {
  background: #0062c4;
  box-shadow: 0 2px 6px rgba(0, 119, 230, 0.4);
}

.admin-header-cta:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-header-icon-btn {
  position: relative;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: var(--ink-muted);
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s,
    border-color 0.2s;
}

.admin-header-icon-btn:hover {
  color: var(--ink);
  background: #f4f6fa;
}

.admin-header-icon-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-header-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: #ef4444;
  border: 1.5px solid #fff;
}

.admin-user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: #fff;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s;
}

.admin-user-btn:hover {
  background: #f4f6fa;
  border-color: var(--border-strong);
}

.admin-user-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-avatar {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, var(--accent), var(--cyan));
  flex-shrink: 0;
  user-select: none;
}

.admin-avatar--lg {
  width: 38px;
  height: 38px;
  font-size: 15px;
}

.admin-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 220px;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(10, 15, 26, 0.1);
  padding: 6px;
  z-index: 60;
}

.admin-dropdown-head {
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-muted);
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}

.admin-notif-panel {
  width: 300px;
}

.admin-notif-item {
  padding: 9px 10px;
  border-radius: 8px;
}

.admin-notif-item:hover {
  background: #f7f9fc;
}

.admin-notif-item + .admin-notif-item {
  border-top: 1px solid rgba(10, 15, 26, 0.05);
}

.admin-notif-item.is-unread {
  background: rgba(0, 119, 230, 0.04);
}

.admin-user-menu {
  min-width: 200px;
}

.admin-user-menu-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 10px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}

.admin-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--ink);
  transition: background 0.15s;
}

.admin-menu-item:hover {
  background: #f4f6fa;
}

.admin-menu-item svg {
  width: 15px;
  height: 15px;
  color: var(--ink-muted);
  flex-shrink: 0;
}

/* ── 侧边栏 ─────────────────────────── */
.admin-sidebar {
  scrollbar-gutter: stable;
}

.admin-nav-head {
  padding: 2px 10px 10px;
  margin-bottom: 6px;
  border-bottom: 1px solid rgba(10, 15, 26, 0.08);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-muted);
}

.admin-nav-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  position: relative;
  transition:
    background 0.2s,
    color 0.2s;
}

.admin-nav-btn,
.admin-nav-group-btn {
  white-space: nowrap;
}

.admin-nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 0;
}

.admin-nav-btn:hover {
  color: var(--ink);
  background: #f4f6fa;
}

.admin-nav-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-nav-btn.is-active {
  color: var(--accent);
  background: linear-gradient(
    90deg,
    rgba(0, 119, 230, 0.1),
    rgba(0, 194, 212, 0.05)
  );
  font-weight: 700;
}

.admin-nav-btn.is-active::before {
  content: "";
  position: absolute;
  left: -3px;
  top: 9px;
  bottom: 9px;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg, var(--accent), var(--cyan));
}

.admin-nav-icon {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  background: #f1f5f9;
  color: var(--ink-muted);
  transition:
    background 0.2s,
    color 0.2s;
}

.admin-nav-btn.is-active .admin-nav-icon {
  background: var(--accent);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 119, 230, 0.3);
}

.admin-nav-icon svg {
  width: 14px;
  height: 14px;
}

/* ── 分组导航 ─────────────────────────── */
.admin-nav-group-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s;
}

.admin-nav-group-btn:hover {
  color: var(--ink);
  background: #f4f6fa;
}

.admin-nav-group-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-nav-count {
  margin-left: auto;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.5;
  padding: 1px 7px;
  border-radius: 999px;
  color: var(--ink-muted);
  background: #eef1f5;
  flex-shrink: 0;
}

.admin-nav-group-btn.is-open .admin-nav-count {
  color: var(--accent);
  background: rgba(0, 119, 230, 0.1);
}

.admin-nav-chevron {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--ink-muted);
  transition: transform 0.25s ease;
}

.admin-nav-chevron svg {
  width: 14px;
  height: 14px;
}

.admin-nav-chevron.is-open {
  transform: rotate(180deg);
}

.admin-nav-sub {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin: 2px 0 2px 12px;
  padding-left: 8px;
  border-left: 1px solid rgba(10, 15, 26, 0.08);
}

.admin-nav-sub-btn {
  padding: 6px 10px;
  font-weight: 500;
}

.admin-nav-sub-btn.is-active::before {
  display: none;
}

.admin-nav-sub-btn .admin-nav-label {
  font-size: 12.5px;
}

.admin-nav-icon--sub {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f6f8fb;
}

/* ── 卡片 ───────────────────────────── */
.admin-card {
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.admin-card:hover {
  border-color: var(--border-strong);
}

/* ── 统计卡装饰 ─────────────────────── */
.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card::after {
  content: "";
  position: absolute;
  top: -20px;
  right: -20px;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 119, 230, 0.1), transparent 70%);
  pointer-events: none;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 1.625rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}

/* ── 图表解读头 ─────────────────────── */
.chart-head {
  margin-bottom: 14px;
}

.chart-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}

.chart-desc {
  font-size: 12px;
  line-height: 1.55;
  color: var(--ink-muted);
  margin-bottom: 8px;
}

.chart-insight,
.chart-suggest {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  line-height: 1.55;
  color: var(--ink-soft);
  padding: 6px 9px;
  border-radius: 8px;
  margin-bottom: 6px;
}

.chart-insight {
  background: rgba(0, 119, 230, 0.06);
  border: 1px solid rgba(0, 119, 230, 0.12);
}

.chart-suggest {
  background: rgba(0, 194, 212, 0.05);
  border: 1px solid rgba(0, 194, 212, 0.14);
  margin-bottom: 0;
}

.chart-tag {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.4;
  padding: 1px 6px;
  border-radius: 4px;
  margin-top: 1px;
  color: var(--accent);
  background: rgba(0, 119, 230, 0.12);
}

.chart-tag--suggest {
  color: #0e7f8e;
  background: rgba(0, 194, 212, 0.14);
}

/* ── 任务表格 ─────────────────────────── */
.admin-table {
  border-collapse: collapse;
  font-size: 13px;
}

.admin-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--ink-muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.admin-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(10, 15, 26, 0.05);
  color: var(--ink);
  vertical-align: middle;
}

.admin-table tbody tr:last-child td {
  border-bottom: none;
}

.admin-table tbody tr {
  transition: background 0.15s;
}

.admin-table tbody tr:hover {
  background: #f7f9fc;
}

/* ── 徽章 ─────────────────────────────── */
.type-badge,
.status-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
  padding: 5px 9px;
  border-radius: 999px;
  white-space: nowrap;
}

/* ── 进度条 ───────────────────────────── */
.progress-track {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #eef1f5;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  width: 100%;
  border-radius: 999px;
  background: var(--accent);
  transform-origin: left center;
  transition: transform 0.3s;
}

.progress-fill.is-done {
  background: #10b981;
}

.progress-fill.is-failed {
  background: #ef4444;
}

/* ── 操作按钮 ─────────────────────────── */
.admin-refresh-btn {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  background: rgba(0, 119, 230, 0.08);
  border: 1px solid rgba(0, 119, 230, 0.18);
  border-radius: var(--radius-sm);
  padding: 5px 12px;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s;
}

.admin-refresh-btn:hover:not(:disabled) {
  background: rgba(0, 119, 230, 0.14);
}

.admin-refresh-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.admin-refresh-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.admin-action-btn {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  background: transparent;
  border: 1px solid rgba(0, 119, 230, 0.25);
  border-radius: var(--radius-sm);
  padding: 4px 11px;
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s;
}

.admin-action-btn:hover {
  background: rgba(0, 119, 230, 0.08);
}

.admin-action-btn--danger {
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.25);
}

.admin-action-btn--danger:hover {
  background: rgba(239, 68, 68, 0.08);
}

.admin-action-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition: none !important;
  }
}
</style>
