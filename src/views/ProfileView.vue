<script setup>
import {
  ref,
  reactive,
  computed,
  onMounted,
  onUnmounted,
  nextTick,
  watch,
} from "vue";
import { RouterLink } from "vue-router";
import { useCommunity, formatTime } from "../composables/useCommunity.js";
import * as echarts from "echarts";
import SiteNav from "../components/layout/SiteNav.vue";
import { seededInt } from "../utils/demoData.js";

// 用户信息
import { useUserStore } from "../stores/userStore.js";
const userStore = useUserStore();
// 全部可编辑字段都从本地存储读取，刷新后不丢
const userInfo = reactive({
  name: userStore.getName() || "测试用户",
  avatar: userStore.getAvatar(),
  email: userStore.state.email || "",
  birthday: userStore.state.birthday || "",
  qq: userStore.state.qq || "",
  wechat: userStore.state.wechat || "",
  motto: userStore.state.motto || "",
});

// 保存成功提示
const saveToast = ref(false);
let saveToastTimer = null;
function showSaveToast() {
  saveToast.value = true;
  clearTimeout(saveToastTimer);
  saveToastTimer = setTimeout(() => {
    saveToast.value = false;
  }, 2000);
}

// 发布想法
const postContent = ref("");
const selectedFiles = ref([]);

// 已发布的想法列表
const posts = ref([
  {
    id: 1,
    content: "今天分享一个很有趣的教学方法，让学生更容易理解抽象概念！",
    time: "2小时前",
    likes: 12,
    comments: 3,
  },
]);

// 当前选中的菜单
const activeMenu = ref("profile");

// 菜单列表
const menuItems = [
  { id: "profile", label: "个人资料" },
  { id: "usage", label: "使用记录" },
  { id: "favorites", label: "我的收藏" },
  { id: "posts", label: "发布想法" },
  { id: "settings", label: "账号设置" },
];

// 使用记录数据
const usageTimeRange = ref("week"); // 'week' | 'year'
const hoveredDataPoint = ref(null);
const selectedDate = ref(null);
const selectedType = ref("all"); // 'all' | 'ppt' | 'doc' | 'interactive'

// 图表颜色配置
const CHART_COLORS = {
  all: {
    primary: "#667eea",
    secondary: "#764ba2",
    gradient: ["rgba(102, 126, 234, 0.3)", "rgba(102, 126, 234, 0.05)"],
    shadow: "rgba(102, 126, 234, 0.4)",
  },
  ppt: {
    primary: "#4c7dff",
    secondary: "#6b8cff",
    gradient: ["rgba(76, 125, 255, 0.3)", "rgba(76, 125, 255, 0.05)"],
    shadow: "rgba(76, 125, 255, 0.4)",
  },
  doc: {
    primary: "#23c3b2",
    secondary: "#4dd9c9",
    gradient: ["rgba(35, 195, 178, 0.3)", "rgba(35, 195, 178, 0.05)"],
    shadow: "rgba(35, 195, 178, 0.4)",
  },
  interactive: {
    primary: "#f97316",
    secondary: "#fb923c",
    gradient: ["rgba(249, 115, 22, 0.3)", "rgba(249, 115, 22, 0.05)"],
    shadow: "rgba(249, 115, 22, 0.4)",
  },
};

// 社区收藏功能
const community = useCommunity();

// 获取收藏的文章列表
const favoritePosts = computed(() => {
  return community.getPosts("favorite");
});

// 取消收藏
function removeFavorite(postId) {
  community.toggleFavorite(postId);
}

// 跳转到社区详情
function goToCommunityPost(postId) {
  window.location.href = `/community?post=${postId}`;
}

// ==================== 作品生成轨迹堆叠柱状图 ====================
const workChartRef = ref(null);
const workChartInstance = ref(null);
const selectedTimeRange = ref("week"); // 'week' | 'month'

// ==================== 创作趋势面积图 ====================
const trendChartRef = ref(null);
const trendChartInstance = ref(null);

// ==================== 创作类型分布环形图 ====================
const typeChartRef = ref(null);
const typeChartInstance = ref(null);

// 作品生成数据
const workGenerationData = ref({
  week: {
    dates: ["周三", "周四", "周五", "周六", "周日", "周一", "周二"],
    series: [
      { name: "课件制作", data: [4, 3, 5, 5, 2, 1, 4], color: "#3b82f6" },
      { name: "教案编写", data: [3, 3, 2, 2, 0, 1, 1], color: "#10b981" },
      { name: "课堂练习", data: [2, 2, 3, 1, 1, 1, 2], color: "#8b5cf6" },
    ],
  },
  month: {
    dates: ["第1周", "第2周", "第3周", "第4周"],
    series: [
      { name: "课件制作", data: [18, 22, 15, 20], color: "#3b82f6" },
      { name: "教案编写", data: [12, 15, 10, 14], color: "#10b981" },
      { name: "课堂练习", data: [8, 12, 9, 11], color: "#8b5cf6" },
    ],
  },
});

// 生成图表配置
function generateWorkChartOption(timeRange) {
  const data = workGenerationData.value[timeRange];

  return {
    title: {
      text: "最近生成与优化轨迹",
      left: "2%",
      top: "2%",
      textStyle: {
        fontSize: 16,
        fontWeight: 600,
        color: "#1e293b",
      },
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      padding: [12, 16],
      textStyle: { color: "#1e293b" },
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 12px;",
      formatter: function (params) {
        let total = 0;
        let html = `<div style="font-weight: 600; margin-bottom: 8px; font-size: 14px;">${params[0].axisValue}</div>`;
        params.forEach((item) => {
          total += item.value;
          html += `
            <div style="display: flex; align-items: center; margin: 6px 0;">
              <span style="display: inline-block; width: 10px; height: 10px; 
                background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
              <span style="flex: 1;">${item.seriesName}</span>
              <span style="font-weight: 600; margin-left: 12px;">${item.value} 个</span>
            </div>
          `;
        });
        html += `<div style="border-top: 1px solid #e2e8f0; margin-top: 8px; padding-top: 8px;">
          <span style="color: #64748b;">总计：</span>
          <span style="font-weight: 700; color: #3b82f6; font-size: 16px;">${total} 个</span>
        </div>`;
        return html;
      },
    },
    legend: {
      data: ["课件制作", "教案编写", "课堂练习"],
      right: "4%",
      top: "3%",
      itemGap: 20,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 12, color: "#475569" },
      icon: "circle",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "10%",
      top: "18%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: data.dates,
      axisLine: { lineStyle: { color: "#e2e8f0" } },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 12, margin: 12 },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#94a3b8", fontSize: 11 },
      splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
    },
    series: data.series.map((item, index) => ({
      name: item.name,
      type: "bar",
      data: item.data,
      barWidth: "20%",
      barGap: "20%",
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: item.color },
          { offset: 1, color: item.color + "cc" },
        ]),
        borderRadius: [6, 6, 0, 0],
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: item.color + "80",
        },
      },
    })),
    animationDuration: 800,
    animationEasing: "elasticOut",
  };
}

// 初始化作品生成图表
function initWorkChart() {
  console.log("初始化图表, ref:", workChartRef.value);
  if (!workChartRef.value) {
    console.warn("图表容器未找到，延迟重试");
    setTimeout(initWorkChart, 100);
    return;
  }

  try {
    if (workChartInstance.value) {
      workChartInstance.value.dispose();
      workChartInstance.value = null;
    }

    // 确保容器有尺寸
    const container = workChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      console.warn("容器尺寸为0，延迟重试");
      setTimeout(initWorkChart, 200);
      return;
    }

    workChartInstance.value = echarts.init(container);
    const option = generateWorkChartOption(selectedTimeRange.value);
    workChartInstance.value.setOption(option);
    console.log("图表初始化成功");

    // 点击事件 - 下钻查看详情
    workChartInstance.value.on("click", function (params) {
      const date = params.name;
      const type = params.seriesName;
      console.log("点击了:", date, type);
    });
  } catch (error) {
    console.error("图表初始化失败:", error);
  }
}

// 切换作品图表时间范围
function switchWorkTimeRange(range) {
  selectedTimeRange.value = range;
  if (workChartInstance.value) {
    const option = generateWorkChartOption(range);
    workChartInstance.value.setOption(option, true);
  }
}

// 监听窗口大小变化
function handleResize() {
  if (workChartInstance.value) {
    workChartInstance.value.resize();
  }
  if (trendChartInstance.value) {
    trendChartInstance.value.resize();
  }
  if (typeChartInstance.value) {
    typeChartInstance.value.resize();
  }
}

// 生成创作趋势图表配置
function generateTrendChartOption() {
  const data = usageData.value[usageTimeRange.value];
  const colors = CHART_COLORS[selectedType.value];

  return {
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      padding: [12, 16],
      textStyle: { color: "#1e293b" },
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 12px;",
      formatter: function (params) {
        const index = params[0].dataIndex;
        const label = data.labels[index];
        const value = params[0].value;
        const detail = data.details[label];

        let html = `<div style="font-weight: 600; margin-bottom: 8px; font-size: 14px;">${label}</div>`;
        html += `<div style="display: flex; align-items: center; margin: 6px 0;">`;
        html += `<span style="display: inline-block; width: 10px; height: 10px; background: ${params[0].color}; border-radius: 50%; margin-right: 8px;"></span>`;
        html += `<span>创作数量: <strong>${value}</strong></span>`;
        html += `</div>`;

        if (detail) {
          html += `<div style="border-top: 1px solid #e2e8f0; margin-top: 8px; padding-top: 8px; font-size: 12px; color: #64748b;">`;
          const icoBook =
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748b" '
            + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            + 'style="vertical-align:-2px;margin-right:5px">'
            + '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>'
            + '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'
            + '</svg>';
          const icoClock =
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#64748b" '
            + 'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
            + 'style="vertical-align:-2px;margin-right:5px">'
            + '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>'
            + '</svg>';
          html += `<div>${icoBook}${detail.subjects.join("、")}</div>`;
          html += `<div>${icoClock}高峰 ${detail.peakHour}</div>`;
          html += `</div>`;
        }
        return html;
      },
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      top: "10%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: data.labels,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 12 },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#94a3b8", fontSize: 11 },
      splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
    },
    series: [
      {
        name: "创作数量",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        sampling: "average",
        itemStyle: {
          color: colors.primary,
          borderWidth: 2,
          borderColor: "#fff",
        },
        lineStyle: {
          width: 3,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: colors.primary },
            { offset: 1, color: colors.secondary },
          ]),
          shadowColor: colors.shadow,
          shadowBlur: 10,
          shadowOffsetY: 5,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors.primary + "80" },
            { offset: 0.5, color: colors.secondary + "40" },
            { offset: 1, color: colors.secondary + "05" },
          ]),
        },
        data: data.data,
        emphasis: {
          focus: "series",
          itemStyle: {
            shadowBlur: 15,
            shadowColor: colors.shadow,
          },
        },
      },
    ],
    animationDuration: 1000,
    animationEasing: "cubicOut",
  };
}

// 初始化创作趋势图表
function initTrendChart() {
  console.log("初始化创作趋势图表, ref:", trendChartRef.value);
  if (!trendChartRef.value) {
    setTimeout(initTrendChart, 100);
    return;
  }

  try {
    if (trendChartInstance.value) {
      trendChartInstance.value.dispose();
      trendChartInstance.value = null;
    }

    const container = trendChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("创作趋势容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      setTimeout(initTrendChart, 200);
      return;
    }

    trendChartInstance.value = echarts.init(container);
    const option = generateTrendChartOption();
    trendChartInstance.value.setOption(option);
    console.log("创作趋势图表初始化成功");

    // 点击事件
    trendChartInstance.value.on("click", function (params) {
      const index = params.dataIndex;
      const label = usageData.value[usageTimeRange.value].labels[index];
      selectedDate.value = label;
      console.log("点击了日期:", label);
    });
  } catch (error) {
    console.error("创作趋势图表初始化失败:", error);
  }
}

// 更新创作趋势图表
function updateTrendChart() {
  if (trendChartInstance.value) {
    const option = generateTrendChartOption();
    trendChartInstance.value.setOption(option, true);
  }
}

// 生成创作类型分布图表配置
function generateTypeChartOption() {
  const pptCount = getTypeCount("ppt");
  const docCount = getTypeCount("doc");
  const interactiveCount = getTypeCount("interactive");
  const total = pptCount + docCount + interactiveCount;

  const data = [
    { value: pptCount, name: "课件 PPT", itemStyle: { color: "#8b5cf6" } },
    { value: docCount, name: "教案文档", itemStyle: { color: "#10b981" } },
    {
      value: interactiveCount,
      name: "教学题",
      itemStyle: { color: "#f59e0b" },
    },
  ];

  return {
    tooltip: {
      trigger: "item",
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      padding: [12, 16],
      textStyle: { color: "#1e293b" },
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 12px;",
      formatter: function (params) {
        const percent =
          total > 0 ? ((params.value / total) * 100).toFixed(1) : 0;
        return `<div style="font-weight: 600; margin-bottom: 4px;">${params.name}</div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 10px; height: 10px; background: ${params.color}; border-radius: 50%;"></span>
                  <span>${params.value} 个 (${percent}%)</span>
                </div>`;
      },
    },
    legend: {
      orient: "vertical",
      right: "5%",
      top: "center",
      itemGap: 16,
      itemWidth: 12,
      itemHeight: 12,
      textStyle: {
        fontSize: 13,
        color: "#475569",
      },
      icon: "circle",
      formatter: function (name) {
        const item = data.find((d) => d.name === name);
        const count = item ? item.value : 0;
        return `${name}  ${count}个`;
      },
    },
    series: [
      {
        name: "创作类型",
        type: "pie",
        radius: ["45%", "70%"],
        center: ["35%", "50%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: false,
          position: "center",
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: "bold",
            color: "#1e293b",
            formatter: function (params) {
              return `{name|${params.name}}\n{value|${params.value}}\n{unit|个}`;
            },
            rich: {
              name: {
                fontSize: 12,
                color: "#64748b",
                lineHeight: 20,
              },
              value: {
                fontSize: 24,
                fontWeight: "bold",
                color: "#1e293b",
                lineHeight: 32,
              },
              unit: {
                fontSize: 12,
                color: "#94a3b8",
              },
            },
          },
          itemStyle: {
            shadowBlur: 15,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.2)",
          },
        },
        labelLine: {
          show: false,
        },
        data: data,
      },
    ],
    animationDuration: 800,
    animationEasing: "cubicOut",
  };
}

// 初始化创作类型分布图表
function initTypeChart() {
  console.log("初始化类型分布图表, ref:", typeChartRef.value);
  if (!typeChartRef.value) {
    setTimeout(initTypeChart, 100);
    return;
  }

  try {
    if (typeChartInstance.value) {
      typeChartInstance.value.dispose();
      typeChartInstance.value = null;
    }

    const container = typeChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("类型分布容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      setTimeout(initTypeChart, 200);
      return;
    }

    typeChartInstance.value = echarts.init(container);
    const option = generateTypeChartOption();
    typeChartInstance.value.setOption(option);
    console.log("类型分布图表初始化成功");

    // 点击事件 - 筛选类型
    typeChartInstance.value.on("click", function (params) {
      const typeMap = {
        "课件 PPT": "ppt",
        教案文档: "doc",
        教学题: "interactive",
      };
      const type = typeMap[params.name];
      if (type) {
        filterByType(type);
        console.log("点击了类型:", params.name, type);
      }
    });
  } catch (error) {
    console.error("类型分布图表初始化失败:", error);
  }
}

// 更新创作类型分布图表
function updateTypeChart() {
  if (typeChartInstance.value) {
    const option = generateTypeChartOption();
    typeChartInstance.value.setOption(option, true);
  }
}

// 模拟使用数据 - 丰富的教育场景数据
const usageData = ref({
  week: {
    labels: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    data: [5, 8, 3, 12, 6, 9, 7],
    details: {
      周一: {
        total: 5,
        ppt: 2,
        doc: 2,
        interactive: 1,
        subjects: ["数学", "语文"],
        peakHour: "14:00",
        files: [
          {
            name: "二次函数图像.pptx",
            type: "ppt",
            subject: "数学",
            time: "09:30",
          },
          {
            name: "古诗词鉴赏.docx",
            type: "doc",
            subject: "语文",
            time: "10:15",
          },
          {
            name: "英语语法练习.xlsx",
            type: "interactive",
            subject: "英语",
            time: "14:00",
          },
          {
            name: "力学基础.pptx",
            type: "ppt",
            subject: "物理",
            time: "16:20",
          },
          {
            name: "实验报告模板.docx",
            type: "doc",
            subject: "化学",
            time: "17:45",
          },
        ],
      },
      周二: {
        total: 8,
        ppt: 4,
        doc: 3,
        interactive: 1,
        subjects: ["物理", "化学", "生物"],
        peakHour: "10:00",
        files: [
          {
            name: "牛顿定律.pptx",
            type: "ppt",
            subject: "物理",
            time: "08:30",
          },
          {
            name: "化学方程式.pptx",
            type: "ppt",
            subject: "化学",
            time: "09:15",
          },
          {
            name: "细胞结构.pptx",
            type: "ppt",
            subject: "生物",
            time: "10:00",
          },
          {
            name: "电路分析.pptx",
            type: "ppt",
            subject: "物理",
            time: "11:20",
          },
          {
            name: "有机化学教案.docx",
            type: "doc",
            subject: "化学",
            time: "14:30",
          },
          {
            name: "生物实验指导.docx",
            type: "doc",
            subject: "生物",
            time: "15:45",
          },
          {
            name: "物理习题集.docx",
            type: "doc",
            subject: "物理",
            time: "16:50",
          },
          {
            name: "元素周期表测试.xlsx",
            type: "interactive",
            subject: "化学",
            time: "17:30",
          },
        ],
      },
      周三: {
        total: 3,
        ppt: 1,
        doc: 1,
        interactive: 1,
        subjects: ["历史"],
        peakHour: "15:00",
        files: [
          {
            name: "辛亥革命.pptx",
            type: "ppt",
            subject: "历史",
            time: "10:00",
          },
          {
            name: "近代史教案.docx",
            type: "doc",
            subject: "历史",
            time: "14:20",
          },
          {
            name: "历史知识问答.xlsx",
            type: "interactive",
            subject: "历史",
            time: "15:00",
          },
        ],
      },
      周四: {
        total: 12,
        ppt: 5,
        doc: 4,
        interactive: 3,
        subjects: ["数学", "英语", "地理"],
        peakHour: "09:30",
        files: [
          {
            name: "三角函数.pptx",
            type: "ppt",
            subject: "数学",
            time: "08:00",
          },
          {
            name: "阅读理解技巧.pptx",
            type: "ppt",
            subject: "英语",
            time: "08:45",
          },
          {
            name: "世界地理.pptx",
            type: "ppt",
            subject: "地理",
            time: "09:30",
          },
          {
            name: "数列求和.pptx",
            type: "ppt",
            subject: "数学",
            time: "10:15",
          },
          {
            name: "写作指导.pptx",
            type: "ppt",
            subject: "英语",
            time: "11:00",
          },
          {
            name: "数学教案.docx",
            type: "doc",
            subject: "数学",
            time: "13:30",
          },
          {
            name: "英语教案.docx",
            type: "doc",
            subject: "英语",
            time: "14:20",
          },
          {
            name: "地理教案.docx",
            type: "doc",
            subject: "地理",
            time: "15:10",
          },
          {
            name: "期末复习计划.docx",
            type: "doc",
            subject: "数学",
            time: "16:00",
          },
          {
            name: "数学练习题.xlsx",
            type: "interactive",
            subject: "数学",
            time: "17:30",
          },
          {
            name: "英语单词测试.xlsx",
            type: "interactive",
            subject: "英语",
            time: "18:15",
          },
          {
            name: "地理知识竞赛.xlsx",
            type: "interactive",
            subject: "地理",
            time: "19:00",
          },
        ],
      },
      周五: {
        total: 6,
        ppt: 3,
        doc: 2,
        interactive: 1,
        subjects: ["政治", "音乐", "美术"],
        peakHour: "14:30",
        files: [
          {
            name: "公民权利.pptx",
            type: "ppt",
            subject: "政治",
            time: "09:00",
          },
          {
            name: "音乐欣赏.pptx",
            type: "ppt",
            subject: "音乐",
            time: "10:30",
          },
          {
            name: "色彩理论.pptx",
            type: "ppt",
            subject: "美术",
            time: "14:30",
          },
          {
            name: "政治教案.docx",
            type: "doc",
            subject: "政治",
            time: "15:45",
          },
          {
            name: "艺术活动方案.docx",
            type: "doc",
            subject: "美术",
            time: "16:30",
          },
          {
            name: "音乐理论测试.xlsx",
            type: "interactive",
            subject: "音乐",
            time: "17:15",
          },
        ],
      },
      周六: {
        total: 9,
        ppt: 3,
        doc: 4,
        interactive: 2,
        subjects: ["全科复习"],
        peakHour: "10:00",
        files: [
          {
            name: "周末作业-数学.pptx",
            type: "ppt",
            subject: "数学",
            time: "09:00",
          },
          {
            name: "周末作业-语文.pptx",
            type: "ppt",
            subject: "语文",
            time: "09:45",
          },
          {
            name: "周末作业-英语.pptx",
            type: "ppt",
            subject: "英语",
            time: "10:30",
          },
          {
            name: "复习提纲-物理.docx",
            type: "doc",
            subject: "物理",
            time: "11:15",
          },
          {
            name: "复习提纲-化学.docx",
            type: "doc",
            subject: "化学",
            time: "14:00",
          },
          {
            name: "复习提纲-生物.docx",
            type: "doc",
            subject: "生物",
            time: "15:30",
          },
          {
            name: "错题整理.docx",
            type: "doc",
            subject: "数学",
            time: "16:45",
          },
          {
            name: "周末测试-数学.xlsx",
            type: "interactive",
            subject: "数学",
            time: "17:30",
          },
          {
            name: "周末测试-英语.xlsx",
            type: "interactive",
            subject: "英语",
            time: "18:15",
          },
        ],
      },
      周日: {
        total: 7,
        ppt: 2,
        doc: 3,
        interactive: 2,
        subjects: ["备课", "总结"],
        peakHour: "15:00",
        files: [
          {
            name: "下周教学计划.pptx",
            type: "ppt",
            subject: "综合",
            time: "10:00",
          },
          {
            name: "课程安排.pptx",
            type: "ppt",
            subject: "综合",
            time: "11:30",
          },
          {
            name: "教学反思.docx",
            type: "doc",
            subject: "综合",
            time: "14:00",
          },
          {
            name: "学生评价表.docx",
            type: "doc",
            subject: "综合",
            time: "15:00",
          },
          {
            name: "家长会通知.docx",
            type: "doc",
            subject: "综合",
            time: "16:30",
          },
          {
            name: "学习进度统计.xlsx",
            type: "interactive",
            subject: "综合",
            time: "17:45",
          },
          {
            name: "成绩分析.xlsx",
            type: "interactive",
            subject: "综合",
            time: "18:30",
          },
        ],
      },
    },
  },
  year: {
    labels: [
      "1月",
      "2月",
      "3月",
      "4月",
      "5月",
      "6月",
      "7月",
      "8月",
      "9月",
      "10月",
      "11月",
      "12月",
    ],
    data: [45, 38, 52, 41, 48, 55, 42, 39, 46, 50, 44, 58],
    details: {
      "1月": {
        total: 45,
        ppt: 20,
        doc: 15,
        interactive: 10,
        subjects: ["期末复习"],
        peakHour: "全天",
      },
      "2月": {
        total: 38,
        ppt: 15,
        doc: 12,
        interactive: 11,
        subjects: ["寒假作业"],
        peakHour: "上午",
      },
      "3月": {
        total: 52,
        ppt: 25,
        doc: 18,
        interactive: 9,
        subjects: ["新学期"],
        peakHour: "下午",
      },
      "4月": {
        total: 41,
        ppt: 18,
        doc: 14,
        interactive: 9,
        subjects: ["期中准备"],
        peakHour: "晚上",
      },
      "5月": {
        total: 48,
        ppt: 22,
        doc: 16,
        interactive: 10,
        subjects: ["期中复习"],
        peakHour: "下午",
      },
      "6月": {
        total: 55,
        ppt: 28,
        doc: 17,
        interactive: 10,
        subjects: ["期末考试"],
        peakHour: "全天",
      },
      "7月": {
        total: 42,
        ppt: 16,
        doc: 15,
        interactive: 11,
        subjects: ["暑假作业"],
        peakHour: "上午",
      },
      "8月": {
        total: 39,
        ppt: 15,
        doc: 14,
        interactive: 10,
        subjects: ["暑期备课"],
        peakHour: "下午",
      },
      "9月": {
        total: 46,
        ppt: 21,
        doc: 16,
        interactive: 9,
        subjects: ["开学季"],
        peakHour: "晚上",
      },
      "10月": {
        total: 50,
        ppt: 24,
        doc: 17,
        interactive: 9,
        subjects: ["国庆活动"],
        peakHour: "全天",
      },
      "11月": {
        total: 44,
        ppt: 19,
        doc: 15,
        interactive: 10,
        subjects: ["期中考试"],
        peakHour: "下午",
      },
      "12月": {
        total: 58,
        ppt: 30,
        doc: 18,
        interactive: 10,
        subjects: ["年终总结"],
        peakHour: "全天",
      },
    },
  },
});

// 生成年度的模拟文件数据
const months = [
  "1月",
  "2月",
  "3月",
  "4月",
  "5月",
  "6月",
  "7月",
  "8月",
  "9月",
  "10月",
  "11月",
  "12月",
];
const fileTypes = [".pptx", ".docx", ".xlsx", ".pdf", ".txt"];
const prefixes = [
  "课件",
  "教案",
  "试卷",
  "统计",
  "计划",
  "总结",
  "报告",
  "笔记",
  "方案",
  "记录",
];

// 初始化年度文件数据
// 文件名用「月份 + 序号」作种子确定生成：同一份历史记录的名字恒定不变，
// 避免每次刷新整列文件名都换一遍（旧写法用 Math.random()，一眼就露馅）。
usageData.value.year.files = {};
months.forEach((month, index) => {
  const count = usageData.value.year.data[index];
  usageData.value.year.files[month] = Array.from({ length: count }, (_, j) => {
    const prefix =
      prefixes[seededInt(`${month}-f${j}-prefix`, 0, prefixes.length - 1)];
    const type =
      fileTypes[seededInt(`${month}-f${j}-type`, 0, fileTypes.length - 1)];
    const weekNum = Math.floor(j / 7) + 1;
    return `${month}${weekNum}周-${prefix}${j + 1}${type}`;
  });
});

// 计算折线图路径 - 根据选中类型动态更新
const chartPath = computed(() => {
  const currentData = usageData.value[usageTimeRange.value];
  const labels = currentData.labels;
  const details = currentData.details;

  // 根据选中类型获取数据
  let data;
  if (selectedType.value === "all") {
    data = currentData.data;
  } else {
    // 从details中提取对应类型的数据
    data = labels.map((label) => {
      const dayData = details[label];
      return dayData ? dayData[selectedType.value] || 0 : 0;
    });
  }

  const max = Math.max(...data, 1) || 1;
  const width = 700;
  const height = 200;
  const padding = 40;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * chartWidth;
    const y = height - padding - (value / max) * chartHeight;
    return { x, y, value, index };
  });

  if (points.length === 0) {
    return {
      path: "",
      points: [],
      max: 0,
      colors: CHART_COLORS[selectedType.value],
    };
  }

  // 生成平滑曲线
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    const cpx1 = prev.x + (curr.x - prev.x) / 3;
    const cpy1 = prev.y;
    const cpx2 = prev.x + (2 * (curr.x - prev.x)) / 3;
    const cpy2 = curr.y;
    path += ` C ${cpx1} ${cpy1}, ${cpx2} ${cpy2}, ${curr.x} ${curr.y}`;
  }

  return { path, points, max, colors: CHART_COLORS[selectedType.value] };
});

// 切换时间范围
function switchTimeRange(range) {
  usageTimeRange.value = range;
  selectedDate.value = null;
  selectedType.value = "all";
  // 更新创作趋势图表
  updateTrendChart();
}

// 切换类型筛选
function filterByType(type) {
  selectedType.value = type;
  // 更新创作趋势图表颜色
  updateTrendChart();
}

// 处理数据点悬停
function handlePointHover(point) {
  hoveredDataPoint.value = point;
}

// 处理数据点离开
function handlePointLeave() {
  hoveredDataPoint.value = null;
}

// 处理数据点点击
function handlePointClick(point) {
  const labels = usageData.value[usageTimeRange.value].labels;
  selectedDate.value = labels[point.index];
}

// 获取创作高峰时段
function getPeakHour() {
  const details = usageData.value[usageTimeRange.value].details;
  const hourCount = {};

  Object.values(details).forEach((day) => {
    if (day.files) {
      day.files.forEach((file) => {
        const hour = file.time.split(":")[0];
        hourCount[hour] = (hourCount[hour] || 0) + 1;
      });
    }
  });

  const peakHour = Object.entries(hourCount).sort((a, b) => b[1] - a[1])[0];
  return peakHour ? `${peakHour[0]}:00` : "14:00";
}

// 获取类型数量
function getTypeCount(type) {
  const details = usageData.value[usageTimeRange.value].details;
  return Object.values(details).reduce((sum, day) => sum + (day[type] || 0), 0);
}

// 获取类型百分比
function getTypePercentage(type) {
  const total =
    getTypeCount("ppt") + getTypeCount("doc") + getTypeCount("interactive");
  if (total === 0) return 0;
  return Math.round((getTypeCount(type) / total) * 100);
}

// 获取效率等级样式
function getEfficiencyClass(value) {
  const max = Math.max(...usageData.value[usageTimeRange.value].data);
  const ratio = value / max;
  if (ratio >= 0.8) return "efficiency-high";
  if (ratio >= 0.5) return "efficiency-medium";
  return "efficiency-low";
}

// 获取效率等级标签
function getEfficiencyLabel(value) {
  const max = Math.max(...usageData.value[usageTimeRange.value].data);
  const ratio = value / max;
  if (ratio >= 0.8) return "高效日";
  if (ratio >= 0.5) return "正常";
  return "轻松日";
}

// 获取日期详情
function getDayDetail(index) {
  const labels = usageData.value[usageTimeRange.value].labels;
  const label = labels[index];
  return usageData.value[usageTimeRange.value].details[label];
}

// 获取选中日期的详情
function getSelectedDateDetail() {
  if (!selectedDate.value) return null;
  return usageData.value[usageTimeRange.value].details[selectedDate.value];
}

// 获取筛选后的文件列表
const filteredFiles = computed(() => {
  const detail = getSelectedDateDetail();
  if (!detail || !detail.files) return [];
  if (selectedType.value === "all") return detail.files;
  return detail.files.filter((file) => file.type === selectedType.value);
});

// 计算属性：检测内容中的链接
const parsedContent = computed(() => {
  let content = postContent.value;
  // 检测 URL 并转换为可点击链接
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  return content.replace(
    urlRegex,
    '<a href="$1" target="_blank" class="link">$1</a>',
  );
});

// 头像上传
function handleAvatarUpload(event) {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      // 仅暂存到内存预览，统一由「保存资料」按钮落盘
      userInfo.avatar = e.target.result;
    };
    reader.readAsDataURL(file);
  }
}

// 文件上传
function handleFileUpload(event) {
  const files = Array.from(event.target.files);
  files.forEach((file) => {
    selectedFiles.value.push({
      name: file.name,
      size: (file.size / 1024).toFixed(1) + " KB",
      type: file.type,
    });
  });
}

// 移除文件
function removeFile(index) {
  selectedFiles.value.splice(index, 1);
}

// 发布想法
function publishPost() {
  if (!postContent.value.trim() && selectedFiles.value.length === 0) {
    alert("请输入内容或上传文件");
    return;
  }

  const newPost = {
    id: Date.now(),
    content: postContent.value,
    files: [...selectedFiles.value],
    time: "刚刚",
    likes: 0,
    comments: 0,
  };

  posts.value.unshift(newPost);
  postContent.value = "";
  selectedFiles.value = [];
  alert("发布成功！");
}

// 点赞
function likePost(post) {
  post.likes++;
}

// 保存个人资料：把页面上全部可编辑字段一次性写入 localStorage
function saveProfile() {
  userStore.updateProfile({
    name: (userInfo.name || "").trim() || "测试用户",
    avatar: userInfo.avatar,
    email: (userInfo.email || "").trim(),
    birthday: userInfo.birthday,
    qq: (userInfo.qq || "").trim(),
    wechat: (userInfo.wechat || "").trim(),
    motto: (userInfo.motto || "").trim(),
  });
  // 以存储层为准回填，保证界面与落盘结果一致
  userInfo.name = userStore.getName();
  userInfo.email = userStore.state.email || "";
  showSaveToast();
}

// 生命周期钩子
onMounted(() => {
  // 延迟初始化确保DOM完全渲染
  setTimeout(() => {
    nextTick(() => {
      initWorkChart();
      initTrendChart();
      initTypeChart();
    });
  }, 300);
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  clearTimeout(saveToastTimer);
  window.removeEventListener("resize", handleResize);
  if (workChartInstance.value) {
    workChartInstance.value.dispose();
    workChartInstance.value = null;
  }
  if (trendChartInstance.value) {
    trendChartInstance.value.dispose();
    trendChartInstance.value = null;
  }
  if (typeChartInstance.value) {
    typeChartInstance.value.dispose();
    typeChartInstance.value = null;
  }
});
</script>

<template>
  <div class="profile-page">
    <SiteNav />
    <div class="profile-container">
      <!-- 左侧菜单 -->
      <aside class="profile-sidebar">
        <div class="user-card">
          <div
            class="user-card__avatar"
            :class="{ 'has-avatar': userInfo.avatar }"
          >
            <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="头像" />
            <span v-else>{{ userInfo.name.charAt(0) }}</span>
          </div>
          <h3 class="user-card__name">{{ userInfo.name }}</h3>
          <p class="user-card__email">
            {{ userInfo.email || "未填写邮箱" }}
          </p>
        </div>

        <nav class="profile-menu">
          <button
            v-for="item in menuItems"
            :key="item.id"
            class="menu-item"
            :class="{ 'menu-item--active': activeMenu === item.id }"
            @click="activeMenu = item.id"
          >
            <span class="menu-item__icon">
              <svg
                v-if="item.id === 'profile'"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
              <svg
                v-if="item.id === 'usage'"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              <svg
                v-if="item.id === 'favorites'"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polygon
                  points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                />
              </svg>
              <svg
                v-if="item.id === 'posts'"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path
                  d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                />
              </svg>
              <svg
                v-if="item.id === 'settings'"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <circle cx="12" cy="12" r="3" />
                <path
                  d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                />
              </svg>
            </span>
            <span class="menu-item__label">{{ item.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- 右侧内容区 -->
      <main class="profile-main">
        <!-- 个人资料 -->
        <div v-if="activeMenu === 'profile'" class="content-panel">
          <h2 class="panel-title">个人资料</h2>

          <div class="form-section">
            <label class="form-label">头像</label>
            <div class="avatar-upload">
              <div
                class="avatar-preview"
                :class="{ 'has-avatar': userInfo.avatar }"
              >
                <img v-if="userInfo.avatar" :src="userInfo.avatar" alt="头像" />
                <span v-else>{{ userInfo.name.charAt(0) }}</span>
              </div>
              <label class="upload-btn">
                <input
                  type="file"
                  accept="image/*"
                  @change="handleAvatarUpload"
                  hidden
                />
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                上传头像
              </label>
            </div>
          </div>

          <div class="form-section">
            <label class="form-label">用户名</label>
            <input
              v-model="userInfo.name"
              type="text"
              class="form-input"
              placeholder="请输入用户名"
              maxlength="20"
            />
          </div>

          <div class="form-section">
            <label class="form-label">邮箱</label>
            <input
              v-model="userInfo.email"
              type="email"
              class="form-input"
              placeholder="请输入邮箱地址"
              maxlength="60"
            />
          </div>

          <!-- 生日 -->
          <div class="form-section">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none">
                <rect
                  x="3"
                  y="4"
                  width="18"
                  height="18"
                  rx="2"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <path
                  d="M16 2v4M8 2v4M3 10h18"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
              生日
            </label>
            <input v-model="userInfo.birthday" type="date" class="form-input" />
          </div>

          <!-- QQ -->
          <div class="form-section">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 2C8.5 2 6 4.5 6 7c0 1.5.5 2.5 1.5 3.5-1 1-2.5 2-3 3.5-.5 2 1 3.5 2.5 4-.5 1.5-.5 3 0 4.5 2-1 4.5-1.5 6-1.5s4 .5 6 1.5c.5-1.5.5-3 0-4.5 1.5-.5 3-2 2.5-4-.5-1.5-2-2.5-3-3.5 1-1 1.5-2 1.5-3.5 0-2.5-2.5-5-6-5z"
                  stroke="currentColor"
                  stroke-width="2"
                />
              </svg>
              QQ
            </label>
            <input
              v-model="userInfo.qq"
              type="text"
              class="form-input"
              placeholder="请输入QQ号码"
              maxlength="15"
            />
          </div>

          <!-- 微信 -->
          <div class="form-section">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 11a2 2 0 100-4 2 2 0 000 4zM15 11a2 2 0 100-4 2 2 0 000 4z"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <path
                  d="M8 16c0 2 2.5 4 6 4s6-2 6-4"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
                <path
                  d="M18 8c2.5 1.5 4 4 4 6.5 0 4-3.5 7.5-9 7.5-1.5 0-3-.5-4-1l-4 1 1.5-3C4 17 3 15 3 12.5 3 7.5 7 4 12 4c1 0 2 .5 2.5.5"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
              微信
            </label>
            <input
              v-model="userInfo.wechat"
              type="text"
              class="form-input"
              placeholder="请输入微信号"
              maxlength="20"
            />
          </div>

          <!-- 个人座右铭 -->
          <div class="form-section">
            <label class="form-label">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M12 3c-4.5 0-8 3-8 7 0 2 1 3.5 2.5 4.5L5 20l4-1.5c1 .5 2 .5 3 .5 4.5 0 8-3 8-7s-3.5-7-8-7z"
                  stroke="currentColor"
                  stroke-width="2"
                />
                <circle cx="9" cy="10" r="1" fill="currentColor" />
                <circle cx="15" cy="10" r="1" fill="currentColor" />
                <path
                  d="M9 13c1 1 2.5 1 4 0"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
              个人座右铭
            </label>
            <textarea
              v-model="userInfo.motto"
              class="form-textarea"
              placeholder="写下你的人生格言..."
              rows="3"
              maxlength="100"
            ></textarea>
            <span class="char-count">{{ userInfo.motto.length }}/100</span>
          </div>

          <!-- 保存按钮 -->
          <div class="form-section">
            <button class="btn-save" @click="saveProfile">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M17 21v-8H7v8M7 3v5h8"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              保存资料
            </button>
          </div>
        </div>

        <!-- 使用记录 -->
        <div v-if="activeMenu === 'usage'" class="content-panel">
          <div class="usage-header">
            <div class="usage-title-group">
              <h2 class="panel-title">使用记录</h2>
              <p class="panel-subtitle">追踪您的创作历程与教学效率</p>
            </div>
            <div class="time-range-switch">
              <button
                class="range-btn"
                :class="{ 'range-btn--active': usageTimeRange === 'week' }"
                @click="switchTimeRange('week')"
              >
                <svg viewBox="0 0 20 20" fill="none">
                  <path
                    d="M4 4h12v12H4V4z"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <path
                    d="M4 8h12M8 4v12"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                </svg>
                近一周
              </button>
              <button
                class="range-btn"
                :class="{ 'range-btn--active': usageTimeRange === 'year' }"
                @click="switchTimeRange('year')"
              >
                <svg viewBox="0 0 20 20" fill="none">
                  <circle
                    cx="10"
                    cy="10"
                    r="7"
                    stroke="currentColor"
                    stroke-width="1.5"
                  />
                  <path
                    d="M10 5v5l3 3"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
                近一年
              </button>
            </div>
          </div>

          <!-- 统计概览 - 更丰富的维度 -->
          <div class="usage-stats">
            <div class="stat-card stat-card--primary">
              <div class="stat-icon">
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
              <div class="stat-info">
                <div class="stat-value">
                  {{
                    usageData[usageTimeRange].data.reduce((a, b) => a + b, 0)
                  }}
                </div>
                <div class="stat-label">创作总数</div>
              </div>
            </div>
            <div class="stat-card stat-card--success">
              <div class="stat-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="8" r="6" />
                  <path d="M15.5 13.2 17 22l-5-3-5 3 1.5-8.8" />
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">
                  {{ Math.max(...usageData[usageTimeRange].data) }}
                </div>
                <div class="stat-label">单日最高</div>
              </div>
            </div>
            <div class="stat-card stat-card--info">
              <div class="stat-icon">
                <svg
                  width="20"
                  height="20"
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
              <div class="stat-info">
                <div class="stat-value">
                  {{
                    (
                      usageData[usageTimeRange].data.reduce(
                        (a, b) => a + b,
                        0,
                      ) / usageData[usageTimeRange].data.length
                    ).toFixed(1)
                  }}
                </div>
                <div class="stat-label">日均创作</div>
              </div>
            </div>
            <div class="stat-card stat-card--warning">
              <div class="stat-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ getPeakHour() }}</div>
                <div class="stat-label">创作高峰</div>
              </div>
            </div>
          </div>

          <!-- 创作类型分布 - ECharts环形图 -->
          <div class="type-distribution-chart">
            <div class="type-chart-header">
              <h4 class="section-title">创作类型分布</h4>
              <span v-if="selectedType !== 'all'" class="filter-tag">
                已筛选:
                {{
                  selectedType === "ppt"
                    ? "课件"
                    : selectedType === "doc"
                      ? "教案"
                      : "教学题"
                }}
                <button class="clear-filter" @click="filterByType('all')">
                  ✕
                </button>
              </span>
            </div>
            <div ref="typeChartRef" class="type-chart-container"></div>
          </div>

          <!-- 作品生成轨迹堆叠柱状图 -->
          <div class="work-chart-section">
            <div class="work-chart-header">
              <h4 class="section-title">最近任务</h4>
              <div class="work-chart-controls">
                <button
                  class="time-range-btn"
                  :class="{ active: selectedTimeRange === 'week' }"
                  @click="switchWorkTimeRange('week')"
                >
                  本周
                </button>
                <button
                  class="time-range-btn"
                  :class="{ active: selectedTimeRange === 'month' }"
                  @click="switchWorkTimeRange('month')"
                >
                  本月
                </button>
              </div>
            </div>
            <div ref="workChartRef" class="work-chart-container"></div>
          </div>

          <!-- 创作趋势 - ECharts平滑面积图 -->
          <div class="chart-section">
            <div class="chart-header">
              <h4 class="section-title">
                创作趋势
                <span v-if="selectedType !== 'all'" class="chart-filter-tag">
                  {{
                    selectedType === "ppt"
                      ? "课件"
                      : selectedType === "doc"
                        ? "教案"
                        : "教学题"
                  }}
                </span>
              </h4>
              <div class="chart-legend">
                <span class="legend-item">
                  <span
                    class="legend-dot"
                    :style="{
                      background: `linear-gradient(135deg, ${chartPath.colors.primary} 0%, ${chartPath.colors.secondary} 100%)`,
                    }"
                  ></span>
                  {{
                    selectedType === "all"
                      ? "创作数量"
                      : selectedType === "ppt"
                        ? "课件数量"
                        : selectedType === "doc"
                          ? "教案数量"
                          : "教学题数量"
                  }}
                </span>
              </div>
            </div>
            <div ref="trendChartRef" class="trend-chart-container"></div>
          </div>

          <!-- 选中日期详情 - 更丰富的展示 -->
          <div v-if="selectedDate" class="date-detail date-detail--enhanced">
            <div class="detail-header">
              <div class="detail-title-group">
                <h3>{{ selectedDate }} 创作详情</h3>
                <span class="detail-summary" v-if="getSelectedDateDetail()">
                  共 {{ getSelectedDateDetail()?.total }} 个 ·
                  {{ getSelectedDateDetail()?.subjects?.join("、") }}
                </span>
              </div>
              <button class="close-detail" @click="selectedDate = null">
                <svg viewBox="0 0 20 20" fill="none">
                  <path
                    d="M5 5l10 10M15 5L5 15"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                  />
                </svg>
              </button>
            </div>

            <!-- 类型统计 -->
            <div class="detail-stats" v-if="getSelectedDateDetail()">
              <div class="detail-stat-item">
                <span class="stat-dot ppt"></span>
                <span class="stat-label">课件</span>
                <span class="stat-num">{{
                  getSelectedDateDetail()?.ppt || 0
                }}</span>
              </div>
              <div class="detail-stat-item">
                <span class="stat-dot doc"></span>
                <span class="stat-label">教案</span>
                <span class="stat-num">{{
                  getSelectedDateDetail()?.doc || 0
                }}</span>
              </div>
              <div class="detail-stat-item">
                <span class="stat-dot interactive"></span>
                <span class="stat-label">教学题</span>
                <span class="stat-num">{{
                  getSelectedDateDetail()?.interactive || 0
                }}</span>
              </div>
            </div>

            <!-- 文件列表 -->
            <div class="file-list file-list--enhanced">
              <div
                v-for="(file, index) in filteredFiles"
                :key="index"
                class="file-item"
                :class="file.type"
              >
                <div class="file-icon" :class="file.type">
                  <svg
                    v-if="file.type === 'ppt'"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <rect
                      x="3"
                      y="4"
                      width="18"
                      height="16"
                      rx="2"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path d="M8 9v6l4-3-4-3z" fill="currentColor" />
                  </svg>
                  <svg
                    v-else-if="file.type === 'doc'"
                    viewBox="0 0 24 24"
                    fill="none"
                  >
                    <path
                      d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path
                      d="M14 2v6h6M8 13h8"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" fill="none">
                    <rect
                      x="4"
                      y="6"
                      width="16"
                      height="12"
                      rx="2"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                    <path
                      d="M8 10h2M8 14h2"
                      stroke="currentColor"
                      stroke-width="1.5"
                    />
                  </svg>
                </div>
                <div class="file-info">
                  <span class="file-name">{{ file.name }}</span>
                  <div class="file-meta">
                    <span class="file-subject">{{ file.subject }}</span>
                    <span class="file-time">{{ file.time }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 创作建议 -->
          <div class="usage-tips">
            <div class="tip-card">
              <div class="tip-icon">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M9 18h6" />
                  <path d="M10 22h4" />
                  <path
                    d="M12 2a6 6 0 0 0-3.5 10.9c.5.4.8 1 .8 1.6h5.4c0-.6.3-1.2.8-1.6A6 6 0 0 0 12 2z"
                  />
                </svg>
              </div>
              <div class="tip-content">
                <h4>创作建议</h4>
                <p>
                  根据您的使用记录，{{
                    usageTimeRange === "week" ? "周四" : "12月"
                  }}是您的创作高峰期。建议提前规划好备课内容，充分利用高效时段。
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- 我的收藏 -->
        <div v-if="activeMenu === 'favorites'" class="content-panel">
          <h2 class="panel-title">我的收藏</h2>
          <p class="panel-subtitle">来自社区的精选内容</p>

          <div v-if="favoritePosts.length === 0" class="favorites-empty">
            <div class="empty-icon">
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
                <polygon
                  points="12 2 15.1 8.5 22 9.3 17 14.1 18.1 21 12 17.8 5.9 21 7 14.1 2 9.3 8.9 8.5"
                />
              </svg>
            </div>
            <h3>暂无收藏</h3>
            <p>去社区浏览精彩内容，点击收藏按钮即可保存到这里</p>
            <RouterLink to="/community" class="btn-primary">
              去社区看看
            </RouterLink>
          </div>

          <div v-else class="favorites-list">
            <div
              v-for="post in favoritePosts"
              :key="post.id"
              class="favorite-card"
              @click="goToCommunityPost(post.id)"
            >
              <div class="favorite-card__header">
                <span class="favorite-tag">{{ post.tag }}</span>
                <button
                  class="favorite-remove"
                  @click.stop="removeFavorite(post.id)"
                  title="取消收藏"
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path
                      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                    />
                  </svg>
                </button>
              </div>

              <h3 class="favorite-title">{{ post.title }}</h3>
              <p class="favorite-content">{{ post.content }}</p>

              <div
                v-if="post.images && post.images.length"
                class="favorite-images"
              >
                <img
                  v-for="(img, idx) in post.images.slice(0, 3)"
                  :key="idx"
                  :src="img"
                  :alt="`图片 ${idx + 1}`"
                />
                <div v-if="post.images.length > 3" class="image-more">
                  +{{ post.images.length - 3 }}
                </div>
              </div>

              <div class="favorite-footer">
                <div class="favorite-author">
                  <span class="author-avatar">{{ post.author.charAt(0) }}</span>
                  <span>{{ post.author }}</span>
                </div>
                <div class="favorite-meta">
                  <span class="meta-item">
                    <svg viewBox="0 0 20 20" fill="none">
                      <path
                        d="M10 17s-6-4.35-6-8.5A3.5 3.5 0 0 1 10 6a3.5 3.5 0 0 1 6 2.5C16 12.65 10 17 10 17z"
                        stroke="currentColor"
                        stroke-width="1.5"
                      />
                    </svg>
                    {{ post.likes }}
                  </span>
                  <span class="meta-item">
                    <svg viewBox="0 0 20 20" fill="none">
                      <path
                        d="M4 6a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3H9l-3 3v-3H7a3 3 0 0 1-3-3V6z"
                        stroke="currentColor"
                        stroke-width="1.5"
                      />
                    </svg>
                    {{ post.comments.length }}
                  </span>
                  <time>{{ formatTime(post.createdAt) }}</time>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 发布想法 -->
        <div v-if="activeMenu === 'posts'" class="content-panel">
          <h2 class="panel-title">发布想法</h2>

          <!-- 发布框 -->
          <div class="post-composer">
            <div class="composer-textarea-wrapper">
              <textarea
                v-model="postContent"
                class="composer-textarea"
                placeholder="分享你的想法..."
                rows="4"
              ></textarea>

              <!-- 工具栏 -->
              <div class="composer-toolbar">
                <div class="toolbar-left">
                  <!-- 插入表情 -->
                  <button class="toolbar-btn" title="表情">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                      <line x1="9" y1="9" x2="9.01" y2="9" />
                      <line x1="15" y1="9" x2="15.01" y2="9" />
                    </svg>
                  </button>

                  <!-- 文件上传 -->
                  <label class="toolbar-btn">
                    <input
                      type="file"
                      multiple
                      @change="handleFileUpload"
                      hidden
                    />
                    <svg viewBox="0 0 24 24" fill="none">
                      <path
                        d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>
                    文件
                  </label>
                </div>

                <button
                  class="btn-publish"
                  :disabled="!postContent.trim() && selectedFiles.length === 0"
                  @click="publishPost"
                >
                  发布
                </button>
              </div>
            </div>

            <!-- 已选文件列表 -->
            <div v-if="selectedFiles.length > 0" class="selected-files">
              <div
                v-for="(file, index) in selectedFiles"
                :key="index"
                class="file-tag"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <path
                    d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                  <path
                    d="M14 2v6h6M16 13H8M16 17H8M10 9H8"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ file.size }}</span>
                <button class="file-remove" @click="removeFile(index)">
                  ×
                </button>
              </div>
            </div>
          </div>

          <!-- 已发布的想法列表 -->
          <div class="posts-list">
            <h3 class="posts-list__title">我的想法</h3>
            <div v-for="post in posts" :key="post.id" class="post-card">
              <div class="post-header">
                <div class="post-avatar">{{ userInfo.name.charAt(0) }}</div>
                <div class="post-meta">
                  <span class="post-author">{{ userInfo.name }}</span>
                  <span class="post-time">{{ post.time }}</span>
                </div>
              </div>
              <div class="post-content" v-html="post.content"></div>
              <div class="post-actions">
                <button class="post-action" @click="likePost(post)">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path
                      d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  {{ post.likes }}
                </button>
                <button class="post-action">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path
                      d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  {{ post.comments }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 账号设置 -->
        <div v-if="activeMenu === 'settings'" class="content-panel">
          <h2 class="panel-title">账号设置</h2>
          <p class="placeholder-text">设置功能开发中...</p>
        </div>
      </main>
    </div>

    <!-- 保存成功提示：由「保存资料」按钮统一触发 -->
    <Transition name="save-toast">
      <div v-if="saveToast" class="save-toast">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.4"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        资料已保存
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #f7f5f2;
}

.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 104px 24px 48px;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 32px;
  align-items: start;
}

/* 侧边栏 */
.profile-sidebar {
  position: sticky;
  top: 100px;
  height: fit-content;
}

.user-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 28px 20px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
}

.user-card__avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  margin: 0 auto 16px;
  overflow: hidden;
}

.user-card__avatar.has-avatar {
  background: var(--color-gray-100);
}

.user-card__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-card__name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 4px;
}

.user-card__email {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 12px;
}

.profile-menu {
  background: white;
  border-radius: 16px;
  padding: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9375rem;
  color: #475569;
}

.menu-item:hover {
  background: #f2f4f7;
}

.menu-item--active {
  background: #f2f4f7;
  color: #0f172a;
  font-weight: 600;
  border-left: 3px solid #4c7dff;
  border-radius: 12px 8px 8px 12px;
}

.menu-item__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: currentColor;
  flex-shrink: 0;
}

/* 主内容区 */
.profile-main {
  min-height: calc(100vh - 140px);
}

.content-panel {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.panel-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 24px;
}

.form-section {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.9375rem;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

/* 表单标签带图标 */
.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.form-label svg {
  width: 18px;
  height: 18px;
  color: #64748b;
}

/* 文本域 */
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  font-size: 0.9375rem;
  resize: vertical;
  min-height: 80px;
  transition: all 0.2s;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: #6b7280;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

.form-textarea::placeholder {
  color: #64748b;
}

.char-count {
  display: block;
  text-align: right;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 4px;
}

/* 保存按钮 */
.btn-save {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 24px;
  background: #374151;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-save:hover {
  background: #1f2937;
}

.btn-save svg {
  width: 20px;
  height: 20px;
}

/* 头像上传 */
.avatar-upload {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  overflow: hidden;
}

.avatar-preview.has-avatar {
  background: #f1f5f9;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #f2f4f7;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #475569;
  transition: all 0.2s;
}

.upload-btn:hover {
  background: #e5e7eb;
}

.upload-btn svg {
  width: 18px;
  height: 18px;
}

/* 使用记录 */
.usage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.time-range-switch {
  display: flex;
  gap: 8px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 10px;
}

.range-btn {
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.range-btn:hover {
  color: #0f172a;
}

.range-btn--active {
  background: white;
  color: #2563eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.usage-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: #f8fafc;
  border-radius: 14px;
  padding: 20px;
  text-align: center;
  border: 1px solid #eef2f6;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
}

.chart-container {
  position: relative;
  background: white;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.chart-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.chart-tooltip {
  position: absolute;
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  z-index: 10;
  min-width: 200px;
  transform: translateX(-50%);
}

.tooltip-date {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 4px;
}

.tooltip-value {
  font-size: 1rem;
  font-weight: 700;
  color: #2563eb;
  margin-bottom: 8px;
}

.tooltip-files {
  font-size: 0.75rem;
  color: #64748b;
  line-height: 1.4;
}

.date-detail {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.detail-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
}

.close-detail {
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-detail:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 10px;
  transition: background 0.2s;
}

.file-item:hover {
  background: #f1f5f9;
}

.file-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.file-name {
  font-size: 0.875rem;
  color: #334155;
}

/* 发布想法 */
.post-composer {
  margin-bottom: 32px;
}

.composer-textarea-wrapper {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  overflow: hidden;
  background: white;
}

.composer-textarea {
  width: 100%;
  padding: 20px;
  border: none;
  resize: none;
  font-size: 0.9375rem;
  line-height: 1.6;
  outline: none;
  min-height: 120px;
}

.composer-textarea::placeholder {
  color: #94a3b8;
}

.composer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid #f1f5f9;
  background: #fafafa;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #64748b;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.toolbar-btn svg {
  width: 18px;
  height: 18px;
}

.btn-publish {
  padding: 10px 24px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-publish:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-publish:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 已选文件 */
.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f1f5f9;
  border-radius: 10px;
  font-size: 0.8125rem;
}

.file-tag svg {
  width: 16px;
  height: 16px;
  color: #64748b;
}

.file-name {
  color: #374151;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  color: #94a3b8;
  font-size: 0.75rem;
}

.file-remove {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.file-remove:hover {
  background: #fecaca;
}

/* 想法列表 */
.posts-list {
  border-top: 1px solid #e2e8f0;
  padding-top: 24px;
}

.posts-list__title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 16px;
}

.post-card {
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  margin-bottom: 16px;
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.post-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #2563eb;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 600;
}

.post-meta {
  display: flex;
  flex-direction: column;
}

.post-author {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.9375rem;
}

.post-time {
  font-size: 0.8125rem;
  color: #94a3b8;
}

.post-content {
  font-size: 0.9375rem;
  line-height: 1.6;
  color: #374151;
  margin-bottom: 16px;
}

.post-content :deep(.link) {
  color: #2563eb;
  text-decoration: none;
}

.post-content :deep(.link:hover) {
  text-decoration: underline;
}

.post-actions {
  display: flex;
  gap: 16px;
}

.post-action {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.875rem;
  color: #64748b;
  transition: all 0.2s;
}

.post-action:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.post-action svg {
  width: 18px;
  height: 18px;
}

.placeholder-text {
  color: #94a3b8;
  text-align: center;
  padding: 48px;
}

/* 响应式 */
@media (max-width: 768px) {
  .profile-container {
    grid-template-columns: 1fr;
    padding: 88px 16px 32px;
  }

  .profile-sidebar {
    position: static;
  }

  .profile-menu {
    display: flex;
    overflow-x: auto;
    gap: 8px;
  }

  .menu-item {
    white-space: nowrap;
  }

  .menu-item--active {
    border-left: none;
    border-bottom: 2px solid #4c7dff;
    border-radius: 12px 12px 8px 8px;
  }
}

/* 我的收藏 */
.favorites-empty {
  text-align: center;
  padding: 64px 32px;
  background: #f2f4f7;
  border-radius: 20px;
  border: 2px dashed #d1d5db;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.favorites-empty h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
}

.favorites-empty p {
  color: #64748b;
  margin-bottom: 24px;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #2563eb;
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.favorites-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.favorite-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 144, 255, 0.2);
}

.favorite-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.favorite-tag {
  display: inline-flex;
  padding: 4px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #2563eb;
  background: rgba(0, 144, 255, 0.08);
  border-radius: 999px;
}

.favorite-remove {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #fbbf24;
  transition: all 0.2s ease;
}

.favorite-remove:hover {
  background: #fef3c7;
  color: #f59e0b;
  transform: scale(1.1);
}

.favorite-remove svg {
  width: 20px;
  height: 20px;
}

.favorite-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 8px;
  line-height: 1.4;
}

.favorite-content {
  font-size: 0.9375rem;
  color: #475569;
  line-height: 1.6;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.favorite-images {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.favorite-images img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
}

.favorite-images .image-more {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
}

.favorite-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.favorite-author {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: #64748b;
}

.author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #2563eb;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.favorite-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 0.8125rem;
  color: #94a3b8;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-item svg {
  width: 16px;
  height: 16px;
}

/* 使用记录样式增强 */
.usage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.usage-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.panel-subtitle {
  font-size: 0.875rem;
  color: #64748b;
}

.time-range-switch {
  display: flex;
  gap: 8px;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 12px;
}

.range-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.range-btn svg {
  width: 16px;
  height: 16px;
}

.range-btn:hover {
  color: #0f172a;
}

.range-btn--active {
  background: white;
  color: #2563eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 统计卡片增强 */
.usage-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.stat-card--primary {
  background: #eef2ff;
  color: #4c1d95;
}

.stat-card--success {
  background: #ecfdf5;
  color: #065f46;
}

.stat-card--info {
  background: #eff6ff;
  color: #1e40af;
}

.stat-card--warning {
  background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%);
  color: #9d174d;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.62);
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1;
}

.stat-card--primary .stat-value {
  color: #4c1d95;
}

.stat-card--success .stat-value {
  color: #065f46;
}

.stat-card--info .stat-value {
  color: #1e40af;
}

.stat-card--warning .stat-value {
  color: #9d174d;
}

.stat-label {
  font-size: 0.8125rem;
  opacity: 0.9;
  margin-top: 4px;
}

/* 类型分布 */
.type-distribution {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid #e2e8f0;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: 20px;
}

.clear-filter {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.3);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 0.625rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-filter:hover {
  background: rgba(255, 255, 255, 0.5);
}

.type-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.type-bar-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.type-bar-item:hover {
  background: #f1f5f9;
}

.type-bar-item.active {
  background: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.type-label {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 100px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
}

.type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.type-dot.all {
  background: linear-gradient(135deg, #64748b 0%, #94a3b8 100%);
}

.type-dot.ppt {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.type-dot.doc {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.type-dot.interactive {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.type-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bg {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.progress-fill.all {
  background: linear-gradient(90deg, #64748b 0%, #94a3b8 100%);
}

.progress-fill.ppt {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.progress-fill.doc {
  background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
}

.progress-fill.interactive {
  background: linear-gradient(90deg, #fa709a 0%, #fee140 100%);
}

.progress-value {
  min-width: 50px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-align: right;
}

/* 作品生成轨迹图表区域 */
.work-chart-section {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
  margin-bottom: 24px;
}

.work-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.work-chart-controls {
  display: flex;
  gap: 8px;
}

.time-range-btn {
  padding: 6px 16px;
  border: 1px solid #e2e8f0;
  background: white;
  border-radius: 20px;
  font-size: 0.85rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s ease;
}

.time-range-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.time-range-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border-color: #3b82f6;
}

.work-chart-container {
  width: 100%;
  height: 320px;
  min-height: 320px;
}

/* 创作趋势图表容器 */
.trend-chart-container {
  width: 100%;
  height: 280px;
  min-height: 280px;
}

/* 创作类型分布图表 */
.type-distribution-chart {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
  margin-bottom: 24px;
}

.type-chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.type-chart-container {
  width: 100%;
  height: 240px;
  min-height: 240px;
}

/* 图表区域 */
.chart-section {
  background: white;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #f1f5f9;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.chart-filter-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  margin-left: 12px;
  background: v-bind("chartPath.colors.primary");
  color: white;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 20px;
  vertical-align: middle;
}

.chart-legend {
  display: flex;
  align-items: center;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: #64748b;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.chart-container {
  position: relative;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
  border-radius: 16px;
  padding: 20px;
  overflow: visible;
}

.chart-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.chart-line {
  filter: drop-shadow(0 2px 8px rgba(102, 126, 234, 0.4));
}

.data-point {
  cursor: pointer;
  transition: all 0.3s ease;
  filter: drop-shadow(0 2px 4px rgba(102, 126, 234, 0.4));
}

.data-point:hover {
  r: 8;
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.6));
}

/* 增强悬停提示 */
.chart-tooltip--enhanced {
  background: white;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  min-width: 220px;
  border: 1px solid #f1f5f9;
  animation: tooltipFadeIn 0.2s ease;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.tooltip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.tooltip-date {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
}

.tooltip-badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.efficiency-high {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  color: white;
}

.efficiency-medium {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  color: white;
}

.efficiency-low {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  color: white;
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tooltip-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.tooltip-value small {
  font-size: 0.8125rem;
  color: #94a3b8;
  font-weight: 500;
}

.tooltip-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8125rem;
  color: #64748b;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 日期详情面板 */
.date-detail {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.detail-header h3 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.close-detail {
  width: 36px;
  height: 36px;
  border: none;
  background: #f1f5f9;
  border-radius: 10px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-detail:hover {
  background: #e2e8f0;
  color: #0f172a;
  transform: rotate(90deg);
}

/* 文件列表 */
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
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.file-item:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.file-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.file-icon.ppt {
  background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
}

.file-icon.doc {
  background: linear-gradient(135deg, #11998e20 0%, #38ef7d20 100%);
}

.file-icon.interactive {
  background: linear-gradient(135deg, #fa709a20 0%, #fee14020 100%);
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.file-meta {
  font-size: 0.75rem;
  color: #94a3b8;
}

.file-time {
  font-size: 0.8125rem;
  color: #64748b;
  font-weight: 500;
}

/* 创作建议卡片 */
.suggestion-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 20px;
  color: white;
  margin-top: 24px;
}

.suggestion-card h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.suggestion-card p {
  font-size: 0.875rem;
  opacity: 0.9;
  line-height: 1.6;
}

/* 日期详情增强样式 */
.date-detail--enhanced {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 20px;
  padding: 28px;
  margin-top: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.detail-title-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-summary {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.detail-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.detail-stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.stat-dot.ppt {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-dot.doc {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-dot.interactive {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.detail-stat-item .stat-label {
  font-size: 0.8125rem;
  color: #64748b;
  font-weight: 500;
}

.detail-stat-item .stat-num {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin-left: 4px;
}

.file-list--enhanced {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-list--enhanced .file-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
}

.file-list--enhanced .file-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateX(6px);
}

.file-list--enhanced .file-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.file-list--enhanced .file-icon.ppt {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  color: #667eea;
}

.file-list--enhanced .file-icon.doc {
  background: linear-gradient(135deg, #11998e15 0%, #38ef7d15 100%);
  color: #11998e;
}

.file-list--enhanced .file-icon.interactive {
  background: linear-gradient(135deg, #fa709a15 0%, #fee14015 100%);
  color: #fa709a;
}

.file-list--enhanced .file-icon svg {
  width: 22px;
  height: 22px;
}

.file-list--enhanced .file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-list--enhanced .file-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
}

.file-list--enhanced .file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.8125rem;
  color: #94a3b8;
}

.file-subject {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  background: #f1f5f9;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #64748b;
}

.file-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8125rem;
  color: #94a3b8;
  font-weight: 500;
}

/* 创作建议卡片 */
.usage-tips {
  margin-top: 24px;
}

.tip-card {
  display: flex;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
  border: 1px solid #d1fae5;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.tip-card:hover {
  border-color: #a7f3d0;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.12);
}

.tip-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: #ffffff;
  color: #059669;
}

.tip-content h4 {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 6px;
}

.tip-content p {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
}

/* 响应式优化 */
@media (max-width: 1024px) {
  .usage-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .detail-stats {
    flex-wrap: wrap;
  }

  .detail-stat-item {
    flex: 1;
    min-width: 100px;
  }
}

@media (max-width: 640px) {
  .usage-stats {
    grid-template-columns: 1fr;
  }

  .usage-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .tip-card {
    flex-direction: column;
    text-align: center;
  }
}

/* 保存成功提示 */
.save-toast {
  position: fixed;
  left: 50%;
  bottom: 48px;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  border-radius: 999px;
  background: #10b981;
  color: #ffffff;
  font-size: 0.9375rem;
  font-weight: 500;
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.32);
  z-index: 1200;
}

.save-toast-enter-active,
.save-toast-leave-active {
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.save-toast-enter-from,
.save-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* ==================== 无障碍支持 ==================== */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .favorite-card:hover,
  .post-card:hover {
    transform: none !important;
  }
}
</style>
