<script setup>
import { ref, onMounted, computed, nextTick } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts";
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
        color: "#3b82f6",
        description: "定律定义、物理意义理解",
      },
      {
        name: "公式应用",
        value: 30,
        color: "#06b6d4",
        description: "F=ma公式变形与计算",
      },
      {
        name: "图像分析",
        value: 15,
        color: "#8b5cf6",
        description: "a-F、a-m关系图像",
      },
      {
        name: "实验探究",
        value: 20,
        color: "#22c55e",
        description: "控制变量法实验设计",
      },
      {
        name: "综合解题",
        value: 10,
        color: "#f59e0b",
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
        color: "#ef4444",
        description: "时间、地点、人物记忆",
      },
      {
        name: "因果分析",
        value: 25,
        color: "#f97316",
        description: "战争爆发原因分析",
      },
      {
        name: "史料解读",
        value: 20,
        color: "#a855f7",
        description: "条约内容、史料分析",
      },
      {
        name: "影响评价",
        value: 25,
        color: "#3b82f6",
        description: "历史影响与意义评价",
      },
      {
        name: "时空观念",
        value: 10,
        color: "#14b8a6",
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
        color: "#3b82f6",
        description: "加速度定义与物理意义",
      },
      {
        name: "图像理解",
        value: 30,
        color: "#8b5cf6",
        description: "v-t图像斜率分析",
      },
      {
        name: "计算应用",
        value: 20,
        color: "#06b6d4",
        description: "a=Δv/Δt计算",
      },
      {
        name: "生活联系",
        value: 10,
        color: "#22c55e",
        description: "生活实例分析",
      },
      {
        name: "易错辨析",
        value: 5,
        color: "#f59e0b",
        description: "速度与加速度区分",
      },
    ],
    keyPoints: ["加速度定义式", "加速度与速度关系", "v-t图像斜率", "方向判断"],
    teachingMethods: ["生活实例", "图像教学", "概念辨析", "练习巩固"],
  },
];

// ==================== 能力模块图例说明 ====================
const abilityLegend = [
  {
    category: "认知理解类",
    items: ["概念理解", "概念建构", "史实记忆"],
    color: "#3b82f6",
  },
  {
    category: "应用分析类",
    items: ["公式应用", "计算应用", "因果分析", "图像分析", "图像理解"],
    color: "#06b6d4",
  },
  {
    category: "综合评价类",
    items: ["综合解题", "影响评价", "史料解读", "时空观念"],
    color: "#8b5cf6",
  },
  {
    category: "实验探究类",
    items: ["实验探究", "生活联系", "易错辨析"],
    color: "#22c55e",
  },
];

// ==================== 图表实例存储 ====================
const chartInstances = ref([]);
const reportRef = ref(null);

// ==================== 生成饼图配置 ====================
function generatePieOption(course, index) {
  const data = course.abilityModules.map((item) => ({
    value: item.value,
    name: item.name,
    itemStyle: { color: item.color },
    description: item.description,
  }));

  return {
    title: {
      text: `${course.title}`,
      subtext: `${course.subject} · ${course.gradeLevel} · ${course.duration}`,
      left: "center",
      top: 10,
      textStyle: {
        fontSize: 16,
        fontWeight: "bold",
        color: "#1e293b",
      },
      subtextStyle: {
        fontSize: 12,
        color: "#64748b",
      },
    },
    tooltip: {
      trigger: "item",
      formatter: function (params) {
        const module = course.abilityModules.find(
          (m) => m.name === params.name,
        );
        return `
          <div style="padding: 8px;">
            <div style="font-weight: bold; margin-bottom: 4px; color: ${params.color}">
              ${params.name}
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 4px;">
              ${module?.description || ""}
            </div>
            <div style="font-size: 14px; font-weight: 600;">
              占比: ${params.value}% (${params.percent}%)
            </div>
          </div>
        `;
      },
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      textStyle: {
        color: "#1e293b",
      },
      extraCssText:
        "box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;",
    },
    legend: {
      orient: "vertical",
      right: 10,
      top: "center",
      itemGap: 12,
      textStyle: {
        fontSize: 11,
        color: "#475569",
      },
      formatter: function (name) {
        const item = data.find((d) => d.name === name);
        return `${name}  ${item?.value}%`;
      },
    },
    series: [
      {
        name: "能力模块",
        type: "pie",
        radius: ["40%", "65%"],
        center: ["40%", "55%"],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: true,
          position: "outside",
          formatter: "{b}\n{c}%",
          fontSize: 11,
          color: "#475569",
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 8,
          smooth: true,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: "bold",
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.2)",
          },
        },
        data: data,
        animationType: "scale",
        animationEasing: "elasticOut",
        animationDelay: function (idx) {
          return Math.random() * 200;
        },
      },
    ],
  };
}

// ==================== 初始化图表 ====================
function initCharts() {
  courses.forEach((course, index) => {
    const chartDom = document.getElementById(`chart-${course.id}`);
    if (chartDom) {
      // 用 svg 渲染器：导出报告时整份图表能随 HTML 一起带走（canvas 不行）
      const chart = echarts.init(chartDom, null, { renderer: "svg" });
      const option = generatePieOption(course, index);
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

// ==================== 计算属性 ====================
const totalCourses = computed(() => courses.length);
const avgDuration = computed(() => {
  const total = courses.reduce((sum, c) => {
    const min = parseInt(c.duration);
    return sum + min;
  }, 0);
  return Math.round(total / courses.length);
});
const subjectDistribution = computed(() => {
  const dist = {};
  courses.forEach((c) => {
    dist[c.subject] = (dist[c.subject] || 0) + 1;
  });
  return dist;
});
</script>

<template>
  <div class="analysis-report" ref="reportRef">
    <!-- 报告头部 -->
    <header class="report-header">
      <div class="header-content">
        <div class="header-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="4" y="14" width="4" height="6" rx="1" />
            <rect x="10" y="8" width="4" height="12" rx="1" />
            <rect x="16" y="3" width="4" height="17" rx="1" />
          </svg>
        </div>
        <div class="header-text">
          <h1>课程内容可视化分析报告</h1>
          <p class="header-subtitle">
            AI智能分析 · 能力模块分布 · 教学重点洞察
          </p>
        </div>
      </div>
      <div class="header-actions">
        <button class="action-btn secondary" @click="router.back()">
          <span>←</span>
          <span>返回</span>
        </button>
        <button class="action-btn secondary" @click="printReport">
          <span>🖨️</span>
          <span>打印</span>
        </button>
        <button class="action-btn primary" @click="exportReport">
          <span>📥</span>
          <span>导出报告</span>
        </button>
      </div>
    </header>

    <!-- 报告概览 -->
    <section class="report-overview">
      <div class="overview-card">
        <div class="overview-icon">📚</div>
        <div class="overview-data">
          <span class="overview-number">{{ totalCourses }}</span>
          <span class="overview-label">分析课程</span>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon">⏱️</div>
        <div class="overview-data">
          <span class="overview-number">{{ avgDuration }}</span>
          <span class="overview-label">平均时长(分钟)</span>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="6" />
            <circle cx="12" cy="12" r="2" fill="currentColor" />
          </svg>
        </div>
        <div class="overview-data">
          <span class="overview-number">15+</span>
          <span class="overview-label">能力维度</span>
        </div>
      </div>
      <div class="overview-card">
        <div class="overview-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
        </div>
        <div class="overview-data">
          <span class="overview-number">100%</span>
          <span class="overview-label">数据覆盖</span>
        </div>
      </div>
    </section>

    <!-- 能力模块图例 -->
    <section class="legend-section">
      <h2 class="section-title">
        <span class="title-icon"
          ><svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M21 21l-4.3-4.3" /></svg
        ></span>
        能力模块分类说明
      </h2>
      <div class="legend-grid">
        <div
          v-for="(item, index) in abilityLegend"
          :key="index"
          class="legend-card"
        >
          <div class="legend-header" :style="{ background: item.color }">
            <span class="legend-category">{{ item.category }}</span>
          </div>
          <div class="legend-items">
            <span
              v-for="(subItem, subIndex) in item.items"
              :key="subIndex"
              class="legend-item"
            >
              {{ subItem }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- 课程分析图表区 -->
    <section class="charts-section">
      <h2 class="section-title">
        <span class="title-icon"
          ><svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="4" y="14" width="4" height="6" rx="1" />
            <rect x="10" y="8" width="4" height="12" rx="1" />
            <rect x="16" y="3" width="4" height="17" rx="1" /></svg
        ></span>
        课程能力模块分布分析
      </h2>
      <p class="section-desc">
        以下图表展示了每门课程的能力模块占比分布，悬停可查看详细信息
      </p>

      <div class="charts-grid">
        <div v-for="course in courses" :key="course.id" class="chart-card">
          <!-- 图表容器 -->
          <div :id="`chart-${course.id}`" class="chart-container"></div>

          <!-- 课程信息 -->
          <div class="course-detail">
            <div class="detail-section">
              <h4>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <circle cx="12" cy="12" r="6" />
                  <circle cx="12" cy="12" r="2" fill="currentColor" />
                </svg>
                核心知识点
              </h4>
              <div class="tag-list">
                <span
                  v-for="(point, idx) in course.keyPoints"
                  :key="idx"
                  class="detail-tag"
                >
                  {{ point }}
                </span>
              </div>
            </div>

            <div class="detail-section">
              <h4>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M17 3a2.85 2.85 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"
                  />
                </svg>
                教学方法
              </h4>
              <div class="tag-list">
                <span
                  v-for="(method, idx) in course.teachingMethods"
                  :key="idx"
                  class="detail-tag method"
                >
                  {{ method }}
                </span>
              </div>
            </div>

            <div class="detail-section">
              <h4>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="4" y="14" width="4" height="6" rx="1" />
                  <rect x="10" y="8" width="4" height="12" rx="1" />
                  <rect x="16" y="3" width="4" height="17" rx="1" />
                </svg>
                难度分析
              </h4>
              <div class="difficulty-bar">
                <div
                  class="difficulty-fill"
                  :style="{
                    width:
                      course.difficulty === '基础'
                        ? '33%'
                        : course.difficulty === '中等偏难'
                          ? '66%'
                          : '100%',
                    background:
                      course.difficulty === '基础'
                        ? '#22c55e'
                        : course.difficulty === '中等偏难'
                          ? '#f59e0b'
                          : '#ef4444',
                  }"
                ></div>
                <span class="difficulty-text">{{ course.difficulty }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 分析总结 -->
    <section class="summary-section">
      <h2 class="section-title">
        <span class="title-icon"
          ><svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M10 18h4" />
            <path d="M12 2v2" />
            <path d="M7 7l1.4 1.4" />
            <path d="M17 7l-1.4 1.4" />
            <circle cx="12" cy="10" r="5" />
            <path d="M10 14c0 .7.5 1 2 1s2-.3 2-1" /></svg
        ></span>
        分析洞察与建议
      </h2>
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-icon">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" fill="currentColor" />
            </svg>
          </div>
          <h3>重点能力培养</h3>
          <p>
            物理课程侧重"概念理解"与"公式应用"，占比达55%-65%；历史课程强调"因果分析"与"影响评价"，体现学科核心素养差异。
          </p>
        </div>
        <div class="summary-card">
          <div class="summary-icon">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
          </div>
          <h3>能力分布特点</h3>
          <p>
            基础课程（加速度）概念建构占比35%，而进阶课程（牛顿定律）综合解题占比提升，体现能力培养的递进性。
          </p>
        </div>
        <div class="summary-card">
          <div class="summary-icon">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.8-3.8a1 1 0 000-1.4L19.9 2a1 1 0 00-1.4 0L14.7 6.3z"
              />
              <path
                d="M6.3 14.7l-4.6 4.6a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l4.6-4.6"
              />
              <path d="M8 9l5 5-4 4-5-5 4-4z" />
            </svg>
          </div>
          <h3>教学方法匹配</h3>
          <p>
            实验探究类模块配合"实验演示"方法，图像分析类配合"图像教学"，实现内容与方法的精准匹配。
          </p>
        </div>
        <div class="summary-card">
          <div class="summary-icon">⚖️</div>
          <h3>难度梯度设计</h3>
          <p>
            课程难度从基础到中等偏难合理分布，符合学生认知发展规律，建议增加高难度拓展课程。
          </p>
        </div>
      </div>
    </section>

    <!-- 报告页脚 -->
    <footer class="report-footer">
      <div class="footer-info">
        <p>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="4" y="14" width="4" height="6" rx="1" />
            <rect x="10" y="8" width="4" height="12" rx="1" />
            <rect x="16" y="3" width="4" height="17" rx="1" />
          </svg>
          报告生成时间：{{ new Date().toLocaleString("zh-CN") }}
        </p>
        <p>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.8-3.8a1 1 0 000-1.4L19.9 2a1 1 0 00-1.4 0L14.7 6.3z"
            />
            <path
              d="M6.3 14.7l-4.6 4.6a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l4.6-4.6"
            />
            <path d="M8 9l5 5-4 4-5-5 4-4z" />
          </svg>
          分析工具：ECharts 5.x | Vue 3 | AI智能分析引擎
        </p>
      </div>
      <div class="footer-links">
        <a href="https://echarts.apache.org/" target="_blank" rel="noopener"
          >ECharts 官网</a
        >
        <span>|</span>
        <a href="#" @click.prevent="printReport">打印报告</a>
        <span>|</span>
        <a href="#" @click.prevent="exportReport">导出PDF</a>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ==================== 报告整体样式 ==================== */
.analysis-report {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
  padding: 40px;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
    Arial, sans-serif;
}

/* ==================== 报告头部 ==================== */
.report-header {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.report-header::before {
  content: "";
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(
    circle,
    rgba(59, 130, 246, 0.15) 0%,
    transparent 70%
  );
  pointer-events: none;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 24px;
  position: relative;
  z-index: 1;
}

.header-icon {
  font-size: 4rem;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.2));
}

.header-text h1 {
  font-size: 2.2rem;
  font-weight: 700;
  color: white;
  margin: 0 0 8px 0;
  letter-spacing: -0.5px;
}

.header-subtitle {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.action-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.4);
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.5);
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* ==================== 概览卡片 ==================== */
.report-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 40px;
}

.overview-card {
  background: white;
  border-radius: 16px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.overview-icon {
  font-size: 2.5rem;
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 16px;
}

.overview-data {
  display: flex;
  flex-direction: column;
}

.overview-number {
  font-size: 2rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1;
}

.overview-label {
  font-size: 0.9rem;
  color: #64748b;
  margin-top: 4px;
}

/* ==================== 章节标题 ==================== */
.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 20px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 1.3rem;
}

.section-desc {
  font-size: 0.95rem;
  color: #64748b;
  margin: -12px 0 24px 0;
}

/* ==================== 图例说明区 ==================== */
.legend-section {
  margin-bottom: 40px;
}

.legend-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.legend-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.3s ease;
}

.legend-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.legend-header {
  padding: 16px 20px;
  color: white;
  font-weight: 600;
}

.legend-category {
  font-size: 1rem;
}

.legend-items {
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.legend-item {
  padding: 6px 12px;
  background: #f1f5f9;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #475569;
}

/* ==================== 图表区 ==================== */
.charts-section {
  margin-bottom: 40px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 28px;
}

.chart-card {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.3s ease;
}

.chart-card:hover {
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.chart-container {
  width: 100%;
  height: 400px;
  margin-bottom: 20px;
}

/* ==================== 课程详情 ==================== */
.course-detail {
  border-top: 1px solid #e2e8f0;
  padding-top: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #475569;
  margin: 0 0 10px 0;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-tag {
  padding: 6px 14px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 20px;
  font-size: 0.8rem;
  color: #3b82f6;
  font-weight: 500;
}

.detail-tag.method {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  color: #22c55e;
}

.difficulty-bar {
  height: 28px;
  background: #f1f5f9;
  border-radius: 14px;
  position: relative;
  overflow: hidden;
}

.difficulty-fill {
  height: 100%;
  border-radius: 14px;
  transition: width 1s ease;
}

.difficulty-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}

/* ==================== 总结区 ==================== */
.summary-section {
  margin-bottom: 40px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.summary-card {
  background: white;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
  transition: all 0.3s ease;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.summary-icon {
  font-size: 2rem;
  margin-bottom: 12px;
}

.summary-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 10px 0;
}

.summary-card p {
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.7;
  margin: 0;
}

/* ==================== 页脚 ==================== */
.report-footer {
  background: white;
  border-radius: 16px;
  padding: 24px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.footer-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.footer-info p {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-links a {
  font-size: 0.9rem;
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.footer-links a:hover {
  color: #2563eb;
  text-decoration: underline;
}

.footer-links span {
  color: #cbd5e1;
}

/* ==================== 打印样式 ==================== */
@media print {
  .analysis-report {
    padding: 20px;
    background: white;
  }

  .report-header {
    background: #1e293b;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .header-actions {
    display: none;
  }

  .chart-card {
    break-inside: avoid;
    page-break-inside: avoid;
  }

  .action-btn {
    display: none;
  }
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 1200px) {
  .report-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .legend-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .analysis-report {
    padding: 20px;
  }

  .report-header {
    flex-direction: column;
    text-align: center;
    gap: 24px;
  }

  .header-content {
    flex-direction: column;
  }

  .report-overview {
    grid-template-columns: 1fr;
  }

  .legend-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 300px;
  }

  .report-footer {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
}
</style>
