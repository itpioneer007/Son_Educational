<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import SiteNav from "../components/layout/SiteNav.vue";
import * as echarts from "echarts";

const router = useRouter();

// ==================== 状态管理 ====================
// 当前激活的菜单项
const activeMenu = ref("home");
// 菜单切换动画状态
const isTransitioning = ref(false);

// ==================== 菜单配置 ====================
const menuItems = [
  {
    id: "course-resource",
    label: "课程资源",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    desc: "浏览所有课程",
  },
  {
    id: "course-analysis",
    label: "课程分析",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="14" width="3" height="7" rx="1.5"/><rect x="10.5" y="8" width="3" height="13" rx="1.5"/><rect x="15" y="3" width="3" height="18" rx="1.5"/></svg>',
    desc: "数据可视化分析",
  },
  {
    id: "classroom-activity",
    label: "课堂互动",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="12" rx="3"/><circle cx="12" cy="11" r="2"/><path d="M8 17v2h8v-2"/></svg>',
    desc: "随堂活动管理",
  },
  {
    id: "qa-session",
    label: "边问边答",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 01-9 9H3l3-3.5A9 9 0 1121 12z"/></svg>',
    desc: "互动问答学习",
  },
  {
    id: "after-class",
    label: "课后追问",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
    desc: "深入探讨问题",
  },
  {
    id: "ai-summary",
    label: "AI总结助手",
    icon: '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l1.5 5L18 8l-5 1.5L12 14l-1.5-5L6 8l5-1.5L12 2z"/><path d="M19 17l.5 1.5L21 19l-1.5.5-.5 1.5-.5-1.5L17 19l1.5-.5.5-1.5z"/></svg>',
    desc: "智能学习总结",
  },
];

// 主页卡片详细描述
function getHomeDesc(id) {
  const map = {
    "course-resource":
      "浏览所有课程资源，查看课程详情与学习进度，点击即可开始学习。",
    "course-analysis": "选择课程查看能力雷达图与时间分配，获取课件制作建议。",
    "classroom-activity":
      "四大课堂活动工具：随堂抢答、实时投票、随机抽选、小组积分，提升课堂趣味与参与度。",
    "qa-session": "课堂互动问答，支持学生提问、教师解答，促进课堂参与。",
    "after-class": "课后深入探讨课程疑难点，巩固学习效果，拓展知识边界。",
    "ai-summary": "AI 自动生成课程学习总结，提炼核心知识点，评估掌握程度。",
  };
  return map[id] || "";
}

// 主页卡片角标
function getHomeBadge(id) {
  const map = {
    "course-resource": "资源库",
    "course-analysis": "数据看板",
    "classroom-activity": "课堂活动",
    "qa-session": "互动",
    "after-class": "拓展",
    "ai-summary": "AI",
  };
  return map[id] || "";
}

// 主页卡片关键词标签
function getHomeKeywords(id) {
  const map = {
    "course-resource": ["课程浏览", "进度跟踪"],
    "course-analysis": ["雷达图", "能力画像"],
    "classroom-activity": ["随堂抢答", "实时投票", "随机点名", "小组竞赛"],
    "qa-session": ["实时问答", "课堂参与"],
    "after-class": ["深度探讨", "知识拓展"],
    "ai-summary": ["智能总结", "掌握评估"],
  };
  return map[id] || [];
}

// ==================== 课程数据 ====================
const courses = ref([
  {
    id: 1,
    title: "牛顿第二定律实验课",
    subject: "物理",
    grade: "高一必修一",
    teacher: "张老师",
    duration: "45分钟",
    cover: "https://images.unsplash.com/photo-1636466497217-26a8cbeaf0aa?w=400",
    description: "通过实验探究力、质量和加速度的关系",
    tags: ["实验课", "核心概念"],
    progress: 85,
    // 课程能力画像（6维度 0-100）
    capabilities: {
      知识覆盖面: 78,
      实验实践性: 92,
      思维启发性: 85,
      互动参与度: 80,
      难度梯度: 65,
      知识系统性: 75,
    },
    // 课程要点
    keyPoints: [
      "控制变量法在实验中的应用",
      "F=ma 公式的推导与理解",
      "加速度与力、质量的关系",
      "实验数据采集与误差分析",
    ],
    // 课件制作建议
    designTips: {
      strengths: "实验环节设计出色，学生动手参与度高",
      improvements: "可增加生活实例导入，降低抽象概念理解门槛",
      suggestions: [
        "增加打点计时器实验动画演示",
        "设计阶梯式练习题巩固公式应用",
      ],
    },
    // 教学时间分配占比
    timeAllocation: [
      { value: 25, name: "理论讲解" },
      { value: 35, name: "实验操作" },
      { value: 20, name: "数据分析" },
      { value: 15, name: "互动讨论" },
      { value: 5, name: "课堂测评" },
    ],
  },
  {
    id: 2,
    title: "化学反应速率",
    subject: "化学",
    grade: "高二必修二",
    teacher: "李老师",
    duration: "40分钟",
    cover: "https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=400",
    description: "探究影响化学反应速率的因素",
    tags: ["理论课", "实验探究"],
    progress: 60,
    capabilities: {
      知识覆盖面: 72,
      实验实践性: 88,
      思维启发性: 70,
      互动参与度: 65,
      难度梯度: 72,
      知识系统性: 80,
    },
    keyPoints: [
      "浓度对反应速率的影响",
      "温度对反应速率的定量关系",
      "催化剂的作用机理",
      "压强对气体反应的影响",
    ],
    designTips: {
      strengths: "实验素材丰富，变量控制清晰",
      improvements: "理论讲解偏多，建议增加学生自主实验时间",
      suggestions: ["添加微观粒子碰撞动画模拟", "设计探究式实验报告模板"],
    },
    timeAllocation: [
      { value: 20, name: "理论讲解" },
      { value: 30, name: "实验操作" },
      { value: 25, name: "数据分析" },
      { value: 15, name: "互动讨论" },
      { value: 10, name: "课堂测评" },
    ],
  },
  {
    id: 3,
    title: "函数单调性",
    subject: "数学",
    grade: "高一必修一",
    teacher: "王老师",
    duration: "45分钟",
    cover: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=400",
    description: "从图像到定义的完整学习",
    tags: ["概念课", "数形结合"],
    progress: 100,
    capabilities: {
      知识覆盖面: 65,
      实验实践性: 30,
      思维启发性: 90,
      互动参与度: 55,
      难度梯度: 78,
      知识系统性: 85,
    },
    keyPoints: [
      "函数单调性的直观图像理解",
      "单调递增/递减的严格定义",
      "定义法证明函数单调性",
      "复合函数单调性判断",
    ],
    designTips: {
      strengths: "数形结合方法恰当，逻辑推导严谨",
      improvements: "可增加动态几何软件演示，提升直观性",
      suggestions: [
        "用GeoGebra制作函数图像动态演示",
        "增加生活场景中的单调性案例",
      ],
    },
    timeAllocation: [
      { value: 35, name: "概念讲解" },
      { value: 25, name: "例题演示" },
      { value: 20, name: "练习巩固" },
      { value: 12, name: "互动讨论" },
      { value: 8, name: "课堂测评" },
    ],
  },
  {
    id: 4,
    title: "细胞结构",
    subject: "生物",
    grade: "高一必修一",
    teacher: "赵老师",
    duration: "50分钟",
    cover: "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=400",
    description: "显微镜下的细胞世界",
    tags: ["观察课", "微观世界"],
    progress: 30,
    capabilities: {
      知识覆盖面: 80,
      实验实践性: 95,
      思维启发性: 60,
      互动参与度: 70,
      难度梯度: 50,
      知识系统性: 78,
    },
    keyPoints: [
      "细胞膜的结构与功能",
      "线粒体与叶绿体的比较",
      "显微观察操作规范",
      "细胞器协调工作机制",
    ],
    designTips: {
      strengths: "观察课设计直观，学生兴趣浓厚",
      improvements: "知识点记忆量大，需设计更多互动环节",
      suggestions: ["制作3D细胞器模型图", "设计细胞工厂角色扮演活动"],
    },
    timeAllocation: [
      { value: 20, name: "理论讲解" },
      { value: 40, name: "观察实践" },
      { value: 15, name: "绘图记录" },
      { value: 18, name: "互动讨论" },
      { value: 7, name: "课堂测评" },
    ],
  },
  {
    id: 5,
    title: "鸦片战争",
    subject: "历史",
    grade: "高一必修一",
    teacher: "陈老师",
    duration: "45分钟",
    cover: "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400",
    description: "近代中国历史的转折点",
    tags: ["历史事件", "思辨分析"],
    progress: 0,
    capabilities: {
      知识覆盖面: 70,
      实验实践性: 15,
      思维启发性: 92,
      互动参与度: 75,
      难度梯度: 55,
      知识系统性: 82,
    },
    keyPoints: [
      "鸦片贸易的背景与危害",
      "林则徐虎门销烟的经过",
      "《南京条约》的内容与影响",
      "鸦片战争的历史意义",
    ],
    designTips: {
      strengths: "史料丰富，思辨性强，启发性好",
      improvements: "文字材料较多，建议增加可视化元素",
      suggestions: ["制作事件时间轴思维导图", "引入一手史料图片增强历史感"],
    },
    timeAllocation: [
      { value: 30, name: "史料讲解" },
      { value: 25, name: "思辨讨论" },
      { value: 20, name: "案例分析" },
      { value: 15, name: "互动问答" },
      { value: 10, name: "课堂测评" },
    ],
  },
  {
    id: 6,
    title: "大气环流",
    subject: "地理",
    grade: "高一必修一",
    teacher: "刘老师",
    duration: "40分钟",
    cover: "https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=400",
    description: "全球气候形成的基础",
    tags: ["自然地理", "系统思维"],
    progress: 45,
    capabilities: {
      知识覆盖面: 75,
      实验实践性: 35,
      思维启发性: 80,
      互动参与度: 50,
      难度梯度: 70,
      知识系统性: 88,
    },
    keyPoints: [
      "三圈环流的形成机制",
      "气压带与风带的分布规律",
      "季风环流的成因与特点",
      "大气环流对气候的影响",
    ],
    designTips: {
      strengths: "系统性思维培养到位，逻辑链条清晰",
      improvements: "抽象概念多，建议增加3D动画辅助理解",
      suggestions: ["制作三圈环流3D动画演示", "设计全球气候类型连线图"],
    },
    timeAllocation: [
      { value: 25, name: "理论讲解" },
      { value: 15, name: "图表识读" },
      { value: 30, name: "案例分析" },
      { value: 20, name: "互动讨论" },
      { value: 10, name: "课堂测评" },
    ],
  },
]);

// 学科视觉配置：颜色 + 图标 + 背景纹理
const subjectStyleMap = {
  物理: {
    color: "#6c5ce7",
    bg: "linear-gradient(135deg, #f3f0ff 0%, #e8e5ff 50%, #dcd6ff 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(30 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-30 12 12)"/></svg>',
    symbol: "φ",
    label: "PHYSICS",
    image: "/image/物理.png",
  },
  化学: {
    color: "#00b894",
    bg: "linear-gradient(135deg, #e6fff5 0%, #d4f8e8 50%, #bdf0d9 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2h6"/><path d="M12 2v7"/><path d="M6 21h12a2 2 0 002-2v-2l-7-11"/><path d="M4 19l7-11"/></svg>',
    symbol: "⚗",
    label: "CHEMISTRY",
    image: "/image/化学.png",
  },
  数学: {
    color: "#0984e3",
    bg: "linear-gradient(135deg, #e8f4fd 0%, #d6ecfb 50%, #c4e2f8 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V4a2 2 0 012-2h12a2 2 0 012 2v16"/><path d="M8 8v4"/><path d="M12 8v4"/><path d="M16 8v4"/></svg>',
    symbol: "∑",
    label: "MATH",
    image: "/image/数学.png",
  },
  生物: {
    color: "#00cec9",
    bg: "linear-gradient(135deg, #e8faf8 0%, #d4f5f1 50%, #bdf0ea 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 22h8"/><path d="M12 17v5"/><circle cx="12" cy="10" r="5"/><path d="M16 14l4 4"/></svg>',
    symbol: "🧬",
    label: "BIOLOGY",
    image: "/image/生物.png",
  },
  历史: {
    color: "#d63031",
    bg: "linear-gradient(135deg, #fff0f0 0%, #ffe8e8 50%, #ffdbdb 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h12a2 2 0 002-2V5a2 2 0 00-2-2H8"/><path d="M4 21h4V3H4"/><path d="M8 9h8"/><path d="M8 13h6"/><path d="M8 17h4"/></svg>',
    symbol: "㊦",
    label: "HISTORY",
    image: "/image/历史.png",
  },
  地理: {
    color: "#e17055",
    bg: "linear-gradient(135deg, #fff5f0 0%, #ffede5 50%, #ffe4d9 100%)",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>',
    symbol: "◈",
    label: "GEOGRAPHY",
    image: "/image/地理.png",
  },
};

function getSubjectStyle(subject) {
  return (
    subjectStyleMap[subject] || {
      color: "#4c7dff",
      bg: "linear-gradient(135deg, #f0f4ff 0%, #e4e9ff 50%, #d8deff 100%)",
      icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
      symbol: "✦",
      label: "COURSE",
      image: "/image/物理.png",
    }
  );
}

// ==================== 问答数据 ====================
const qaList = ref([
  {
    id: 1,
    question: "牛顿第二定律中，加速度与力的关系是什么？",
    answer:
      "根据牛顿第二定律 F = ma，加速度与作用力成正比，与物体质量成反比。当质量不变时，力越大，加速度越大。",
    isExpanded: false,
    relatedCourse: "牛顿第二定律实验课",
  },
  {
    id: 2,
    question: "如何理解化学反应速率的影响因素？",
    answer:
      "影响化学反应速率的主要因素包括：浓度、温度、压强（气体反应）、催化剂和接触面积。温度每升高10℃，反应速率通常增加2-4倍。",
    isExpanded: false,
    relatedCourse: "化学反应速率",
  },
  {
    id: 3,
    question: "函数单调性的定义是什么？",
    answer:
      "设函数f(x)的定义域为I，如果对于定义域I内某个区间D上的任意两个自变量的值x₁、x₂，当x₁ < x₂时，都有f(x₁) < f(x₂)，那么就说函数f(x)在区间D上是增函数。",
    isExpanded: false,
    relatedCourse: "函数单调性",
  },
  {
    id: 4,
    question: "线粒体和叶绿体的功能区别是什么？",
    answer:
      '线粒体是细胞的"动力车间"，进行有氧呼吸产生ATP；叶绿体是植物细胞进行光合作用的场所，将光能转化为化学能储存起来。',
    isExpanded: false,
    relatedCourse: "细胞结构",
  },
]);

// ==================== 课后追问数据 ====================
const topicsList = ref([
  {
    id: 1,
    title: "牛顿定律在实际生活中的应用",
    content:
      "除了课本中的例子，牛顿定律在体育运动、交通工具设计等领域有哪些具体应用？",
    replies: 12,
    views: 156,
    author: "物理爱好者",
    time: "2小时前",
  },
  {
    id: 2,
    title: "化学反应速率的工业意义",
    content: "在化工生产中，如何通过控制反应条件来提高生产效率？",
    replies: 8,
    views: 98,
    author: "化学探索者",
    time: "5小时前",
  },
  {
    id: 3,
    title: "函数单调性与导数的关系",
    content: "学习了导数之后，如何用导数来判断函数的单调性？",
    replies: 15,
    views: 203,
    author: "数学思考者",
    time: "1天前",
  },
  {
    id: 4,
    title: "细胞器的协同工作",
    content: "细胞内的各种细胞器是如何协调配合完成生命活动的？",
    replies: 6,
    views: 87,
    author: "生物迷",
    time: "2天前",
  },
]);

// ==================== AI总结数据 ====================
const aiSummaries = ref([
  {
    id: 1,
    course: "牛顿第二定律实验课",
    summary:
      "本节课通过实验探究了力、质量和加速度的关系。重点掌握了控制变量法的应用，理解了牛顿第二定律 F=ma 的物理意义。",
    keyPoints: ["控制变量法", "F=ma公式", "实验数据分析"],
    mastery: 85,
    suggestions: ["建议复习矢量运算", "多做斜面问题练习"],
  },
  {
    id: 2,
    course: "化学反应速率",
    summary:
      "学习了影响化学反应速率的五大因素，通过实验观察了浓度、温度对反应速率的影响。",
    keyPoints: ["浓度影响", "温度影响", "催化剂作用"],
    mastery: 72,
    suggestions: ["理解活化能概念", "练习速率方程计算"],
  },
  {
    id: 3,
    course: "函数单调性",
    summary:
      "从图像直观感知到严格数学定义，完整学习了函数单调性的概念及其判断方法。",
    keyPoints: ["单调性定义", "图像特征", "证明方法"],
    mastery: 95,
    suggestions: ["已掌握良好，可继续学习极值问题"],
  },
]);

// ==================== AI总结助手（课程分析中心） ====================

// 视图状态
const aiHubCourse = ref(null);
const aiHubActiveTab = ref("analysis");
const aiHubTabs = [
  {
    id: "analysis",
    step: 1,
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="14" width="3" height="7" rx="1.5"/><rect x="10.5" y="8" width="3" height="13" rx="1.5"/><rect x="15" y="3" width="3" height="18" rx="1.5"/></svg>',
    label: "课程分析",
    desc: "AI能力画像评估",
  },
  {
    id: "activity",
    step: 2,
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="12" rx="3"/><circle cx="12" cy="11" r="2"/><path d="M8 17v2h8v-2"/></svg>',
    label: "课堂互动",
    desc: "随堂活动与抢答",
  },
  {
    id: "qa",
    step: 3,
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 01-9 9H3l3-3.5A9 9 0 1121 12z"/></svg>',
    label: "边问边答",
    desc: "互动问答巩固",
  },
  {
    id: "afterclass",
    step: 4,
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>',
    label: "课后追问",
    desc: "深入拓展探讨",
  },
];

// 选择课程
function selectAiHubCourse(course) {
  aiHubCourse.value = course;
  aiHubActiveTab.value = "analysis";
  resetQAState();
  nextTick(() => {
    initAiHubCharts();
  });
}

// 切换子标签
function switchAiHubTab(tabId) {
  aiHubActiveTab.value = tabId;
  if (tabId === "analysis") {
    nextTick(() => {
      initAiHubCharts();
    });
  }
}

// 判断步骤是否已完成
function getAiHubStepDone(tabId) {
  const currentIdx = aiHubTabs.findIndex((t) => t.id === aiHubActiveTab.value);
  const targetIdx = aiHubTabs.findIndex((t) => t.id === tabId);
  return targetIdx <= currentIdx;
}

// ===== ECharts 图表 =====
function initAiHubCharts() {
  if (!aiHubCourse.value) return;

  const course = aiHubCourse.value;
  const radarDom = document.getElementById("ai-hub-radar");
  const pieDom = document.getElementById("ai-hub-pie");
  if (!radarDom || !pieDom) return;

  // 雷达图
  const dims = Object.keys(course.capabilities || {});
  const vals = Object.values(course.capabilities || {});
  if (charts.aiHubRadar) charts.aiHubRadar.dispose();
  const radarChart = echarts.init(radarDom);
  radarChart.setOption({
    tooltip: { trigger: "item" },
    radar: {
      indicator: dims.map((d) => ({ name: d, max: 100 })),
      radius: "65%",
      center: ["50%", "50%"],
      axisName: { color: "#64748b", fontSize: 11 },
      splitArea: {
        areaStyle: {
          color: ["rgba(76,125,255,0.02)", "rgba(76,125,255,0.06)"],
        },
      },
    },
    series: [
      {
        type: "radar",
        data: [
          {
            value: vals,
            name: course.title,
            areaStyle: { color: "rgba(76,125,255,0.2)" },
            lineStyle: { color: "#4c7dff", width: 2 },
            itemStyle: { color: "#4c7dff" },
          },
        ],
      },
    ],
  });

  // 饼图
  const pieChart = echarts.init(pieDom);
  const timeData = (course.timeAllocation || []).map((t) => ({
    name: t.name,
    value: t.value,
  }));
  pieChart.setOption({
    tooltip: { trigger: "item", formatter: "{b}: {c}%" },
    series: [
      {
        type: "pie",
        radius: ["45%", "70%"],
        center: ["50%", "50%"],
        data: timeData,
        label: { color: "#475569", fontSize: 11, formatter: "{b}\n{d}%" },
        labelLine: { length: 8, length2: 10 },
        itemStyle: { borderRadius: 4, borderColor: "white", borderWidth: 2 },
        color: ["#4c7dff", "#6366f1", "#a78bfa", "#f472b6", "#fb923c"],
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.1)" },
        },
      },
    ],
  });

  charts.aiHubRadar = radarChart;
  charts.aiHubPie = pieChart;
  window.addEventListener("resize", () => {
    radarChart.resize();
    pieChart.resize();
  });
}

// AI Hub 问答数据
const aiHubCourseQA = ref([
  {
    id: 1,
    question: "牛顿第二定律的适用条件是什么？",
    answer:
      "牛顿第二定律适用于惯性参考系中的宏观低速物体，研究对象可视为质点。当物体速度接近光速或进入微观领域时需使用相对论或量子力学。",
    expanded: false,
  },
  {
    id: 2,
    question: "如何理解加速度与力的瞬时对应关系？",
    answer:
      "力是产生加速度的原因，力和加速度具有瞬时对应关系——有力即有加速度，力消失则加速度同时消失。这与速度不同，速度的改变需要时间积累。",
    expanded: false,
  },
  {
    id: 3,
    question: "实验中如何减小误差？",
    answer:
      "可通过多次测量取平均值、使用更精密的仪器、控制变量保持实验条件一致等方法来减小实验误差。",
    expanded: false,
  },
  {
    id: 4,
    question: "实验数据处理有哪些常用方法？",
    answer:
      "常用方法包括列表法、图像法（如v-t图像求加速度）、逐差法等。其中图像法能直观反映物理量关系并有效剔除异常数据点。",
    expanded: false,
  },
]);

// AI Hub 投票数据
const currentVote = ref({
  title: "本节课的教学节奏如何？",
  options: [
    { text: "偏快", count: 12 },
    { text: "适中", count: 28 },
    { text: "偏慢", count: 8 },
    { text: "需要调整", count: 5 },
  ],
});
const voteSelected = ref(null);
const voteEnded = ref(false);
function submitVote() {
  if (voteSelected.value !== null) {
    currentVote.value.options[voteSelected.value].count++;
    voteEnded.value = true;
  }
}

// 课堂互动区 QA 别名（兼容 AI Hub 子标签页调用）
function qaSelectAnswer(idx) {
  if (
    !qaTimerRunning.value ||
    quickAnswerQuestions.value[qaCurrentQuestion.value].answered
  )
    return;
  qaSelectedAnswer.value = qaSelectedAnswer.value === idx ? -1 : idx;
  quickAnswerQuestions.value[qaCurrentQuestion.value].selected =
    qaSelectedAnswer.value === -1 ? undefined : qaSelectedAnswer.value;
}
function qaConfirmAnswer() {
  if (qaSelectedAnswer.value === null) return;
  if (quickAnswerQuestions.value[qaCurrentQuestion.value].answered) {
    if (qaCurrentQuestion.value < quickAnswerQuestions.value.length - 1) {
      qaSelectedAnswer.value = -1;
      qaCurrentQuestion.value++;
    }
  } else {
    quickAnswerQuestions.value[qaCurrentQuestion.value].answered = true;
    qaSelectedAnswer.value = -1;
  }
}

// ==================== 课堂互动数据 ====================

const activityTab = ref("quick-answer");

const lessonActivityTabs = [
  {
    id: "quick-answer",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 4 14 10 14 10 22 20 10 14 10 14 2"/></svg>',
    label: "随堂抢答",
    desc: "限时竞答",
  },
  {
    id: "poll",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="14" width="4" height="6" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="16" y="3" width="4" height="17" rx="1"/></svg>',
    label: "实时投票",
    desc: "数据决策",
  },
  {
    id: "random-pick",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="3"/><circle cx="9" cy="9" r="1.5" fill="currentColor"/><circle cx="15" cy="15" r="1.5" fill="currentColor"/></svg>',
    label: "随机抽选",
    desc: "公平互动",
  },
  {
    id: "group-score",
    icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2 2 0 01-2-2V5a2 2 0 012-2H6"/><path d="M18 9h1.5a2 2 0 002-2V5a2 2 0 00-2-2H18"/><path d="M6 3h12v4a6 6 0 01-12 0V3z"/><path d="M12 15v4"/><path d="M8 21h8"/></svg>',
    label: "小组积分",
    desc: "团队竞赛",
  },
];

const students = ref([
  { id: 1, name: "张三", avatar: "张" },
  { id: 2, name: "李四", avatar: "李" },
  { id: 3, name: "王五", avatar: "王" },
  { id: 4, name: "赵六", avatar: "赵" },
  { id: 5, name: "陈七", avatar: "陈" },
  { id: 6, name: "刘八", avatar: "刘" },
  { id: 7, name: "孙九", avatar: "孙" },
  { id: 8, name: "周十", avatar: "周" },
  { id: 9, name: "吴十一", avatar: "吴" },
  { id: 10, name: "郑十二", avatar: "郑" },
]);

// 1. 随堂抢答 - 按学科分类的题库
const subjectQuestionBank = {
  default: [
    {
      id: 1,
      question: "本节课的核心概念是什么？",
      options: ["概念A", "概念B", "概念C", "概念D"],
      correct: 0,
      explanation: "核心概念是需要重点掌握的基础知识。",
      answered: false,
      timer: 30,
    },
    {
      id: 2,
      question: "以下哪项是本课的重点内容？",
      options: ["内容一", "内容二", "内容三", "内容四"],
      correct: 1,
      explanation: "重点内容需要反复练习来巩固。",
      answered: false,
      timer: 30,
    },
    {
      id: 3,
      question: "学习本课程后，最应该掌握的能力是？",
      options: ["记忆能力", "理解应用", "分析推理", "创新创造"],
      correct: 1,
      explanation: "理解应用是学习的关键环节。",
      answered: false,
      timer: 25,
    },
  ],
  物理: [
    {
      id: 1,
      question: "牛顿第二定律的公式是？",
      options: ["F=ma", "P=MV", "E=mc²", "W=Fs"],
      correct: 0,
      explanation: "牛顿第二定律：物体加速度与合外力成正比，F=ma。",
      answered: false,
      timer: 30,
    },
    {
      id: 2,
      question: "自由落体运动中，物体下落速度如何变化？",
      options: ["匀速增大", "匀加速增大", "先快后慢", "保持不变"],
      correct: 1,
      explanation: "自由落体是匀加速直线运动，速度随时间均匀增大。",
      answered: false,
      timer: 25,
    },
    {
      id: 3,
      question: "在实验中，控制变量法的目的是什么？",
      options: ["减少实验次数", "确保单一变量", "增加实验精度", "简化计算过程"],
      correct: 1,
      explanation: "控制变量法保证每次只改变一个变量，便于分析因果关系。",
      answered: false,
      timer: 25,
    },
  ],
  化学: [
    {
      id: 1,
      question: "影响化学反应速率的主要因素不包括？",
      options: ["温度", "浓度", "颜色", "催化剂"],
      correct: 2,
      explanation: "颜色是物理性质，一般不直接改变反应速率。",
      answered: false,
      timer: 25,
    },
    {
      id: 2,
      question: "催化剂在化学反应中的作用是？",
      options: ["改变反应平衡", "降低活化能", "增加产物量", "消耗反应物"],
      correct: 1,
      explanation: "催化剂通过降低反应的活化能来加快反应速率。",
      answered: false,
      timer: 30,
    },
    {
      id: 3,
      question: "升高温度对反应速率的影响是？",
      options: ["加快", "减慢", "不变", "不确定"],
      correct: 0,
      explanation: "温度升高，分子运动加剧，有效碰撞增多，反应速率加快。",
      answered: false,
      timer: 20,
    },
  ],
  数学: [
    {
      id: 1,
      question: "函数单调递增的充要条件是？",
      options: ["导数为正", "导数为负", "导数为零", "二阶导为正"],
      correct: 0,
      explanation: "可导函数单调递增的充要条件是在区间内导数大于等于零。",
      answered: false,
      timer: 25,
    },
    {
      id: 2,
      question: "判断函数单调性的最基本方法是？",
      options: ["图像法", "定义法", "导数法", "复合函数法"],
      correct: 1,
      explanation: "定义法（作差比较）是判断函数单调性的最基本方法。",
      answered: false,
      timer: 25,
    },
    {
      id: 3,
      question: "复合函数求导的法则是什么？",
      options: ["链式法则", "乘积法则", "商法则", "加法法则"],
      correct: 0,
      explanation: "链式法则是复合函数求导的核心法则。",
      answered: false,
      timer: 20,
    },
  ],
  生物: [
    {
      id: 1,
      question: "细胞膜的主要功能是？",
      options: ["提供能量", "控制物质进出", "储存遗传信息", "合成蛋白质"],
      correct: 1,
      explanation: "细胞膜具有选择透过性，控制物质进出细胞。",
      answered: false,
      timer: 25,
    },
    {
      id: 2,
      question: "有丝分裂过程中染色体数目加倍发生在？",
      options: ["前期", "中期", "后期", "末期"],
      correct: 2,
      explanation: "有丝分裂后期着丝粒分裂，姐妹染色单体分开，染色体数目加倍。",
      answered: false,
      timer: 30,
    },
    {
      id: 3,
      question: "线粒体被称为细胞的什么？",
      options: ["遗传控制中心", "动力车间", "合成车间", "消化车间"],
      correct: 1,
      explanation: "线粒体是有氧呼吸的主要场所，被称为细胞的动力车间。",
      answered: false,
      timer: 20,
    },
  ],
  历史: [
    {
      id: 1,
      question: "关于虎门销烟，下列说法正确的是？",
      options: [
        "发生在鸦片战争之后",
        "由林则徐领导",
        "标志着近代史开端",
        "属于洋务运动",
      ],
      correct: 1,
      explanation: "1839年林则徐在广东虎门主持销烟，体现了中国人民的抗英决心。",
      answered: false,
      timer: 25,
    },
    {
      id: 2,
      question: "辛亥革命的历史意义主要是？",
      options: [
        "建立了社会主义制度",
        "推翻了封建帝制",
        "完成了反帝反封建任务",
        "实现了民族独立",
      ],
      correct: 1,
      explanation: "辛亥革命推翻了统治中国两千多年的封建君主专制制度。",
      answered: false,
      timer: 30,
    },
    {
      id: 3,
      question: "关于五四运动，以下哪项描述正确？",
      options: [
        "由工人阶层领导",
        "爆发于1921年",
        "是新民主主义革命的开端",
        "以失败告终",
      ],
      correct: 2,
      explanation: "五四运动标志着中国新民主主义革命的开端。",
      answered: false,
      timer: 25,
    },
  ],
  地理: [
    {
      id: 1,
      question: "大气环流的根本动力是？",
      options: ["地球自转", "太阳辐射", "海陆分布", "地形起伏"],
      correct: 1,
      explanation: "太阳辐射的纬度差异是大气环流形成的根本原因。",
      answered: false,
      timer: 25,
    },
    {
      id: 2,
      question: "关于三圈环流，以下说法正确的是？",
      options: [
        "包含热力环流",
        "只存在于北半球",
        "形成信风带和西风带",
        "不受地转偏向力影响",
      ],
      correct: 2,
      explanation: "三圈环流形成了信风带、西风带和极地东风带。",
      answered: false,
      timer: 30,
    },
    {
      id: 3,
      question: "世界主要气候类型分布规律主要受什么影响？",
      options: ["纬度位置", "海拔高度", "距海远近", "综合因素"],
      correct: 3,
      explanation: "气候类型分布受纬度、海陆位置、地形等多种因素综合影响。",
      answered: false,
      timer: 25,
    },
  ],
};

const quickAnswerQuestions = ref(
  subjectQuestionBank.default.map((q) => ({ ...q })),
);

// 切换课程时更新题库并重置状态
function resetQAState() {
  const subject = aiHubCourse?.value?.subject || "default";
  const bank = subjectQuestionBank[subject] || subjectQuestionBank.default;
  quickAnswerQuestions.value = bank.map((q) => ({ ...q }));
  qaCurrentQuestion.value = 0;
  qaStarted.value = false;
  qaTimerRunning.value = false;
  if (qaTimerInterval) {
    clearInterval(qaTimerInterval);
    qaTimerInterval = null;
  }
  qaTotalTime.value = 0;
  qaTotalTimeLeft.value = 0;
  qaSelectedAnswer.value = -1;
}
const qaCurrentQuestion = ref(0);
const qaTimerRunning = ref(false);
const qaStarted = ref(false);
const qaTotalTime = ref(0);
const qaTotalTimeLeft = ref(0);
const qaSelectedAnswer = ref(-1);
let qaTimerInterval = null;

const qaLeaderboard = ref([
  { name: "李四", score: 5, time: 2.3 },
  { name: "王五", score: 5, time: 3.1 },
  { name: "张三", score: 4, time: 1.8 },
  { name: "赵六", score: 3, time: 4.2 },
  { name: "陈七", score: 3, time: 5.0 },
]);

const qaAllAnswered = () => quickAnswerQuestions.value.every((q) => q.answered);

function startQATimer() {
  qaStarted.value = true;
  qaTimerRunning.value = true;
  const total = quickAnswerQuestions.value.reduce((sum, q) => sum + q.timer, 0);
  qaTotalTime.value = total;
  qaTotalTimeLeft.value = total;
  qaTimerInterval = setInterval(() => {
    qaTotalTimeLeft.value--;
    if (qaTotalTimeLeft.value <= 0) {
      // time's up — auto-reveal all unanswered questions
      quickAnswerQuestions.value.forEach((q) => {
        if (!q.answered) q.answered = true;
      });
      stopQATimer();
    }
  }, 1000);
}

function stopQATimer() {
  qaTimerRunning.value = false;
  if (qaTimerInterval) {
    clearInterval(qaTimerInterval);
    qaTimerInterval = null;
  }
}

function nextQAQuestion() {
  // auto-reveal current answer before moving
  if (!quickAnswerQuestions.value[qaCurrentQuestion.value].answered) {
    quickAnswerQuestions.value[qaCurrentQuestion.value].answered = true;
  }
  if (qaAllAnswered()) {
    stopQATimer();
    return;
  }
  if (qaCurrentQuestion.value < quickAnswerQuestions.value.length - 1) {
    qaSelectedAnswer.value =
      quickAnswerQuestions.value[qaCurrentQuestion.value + 1].selected ?? -1;
    qaCurrentQuestion.value++;
  }
}
function submitQA() {
  if (!quickAnswerQuestions.value[qaCurrentQuestion.value].answered) {
    quickAnswerQuestions.value[qaCurrentQuestion.value].answered = true;
  }
  stopQATimer();
}

function prevQAQuestion() {
  if (qaCurrentQuestion.value > 0) {
    qaSelectedAnswer.value =
      quickAnswerQuestions.value[qaCurrentQuestion.value - 1].selected ?? -1;
    qaCurrentQuestion.value--;
  }
}

function selectQAAnswer(idx) {
  if (
    !qaTimerRunning.value ||
    quickAnswerQuestions.value[qaCurrentQuestion.value].answered
  )
    return;
  qaSelectedAnswer.value = qaSelectedAnswer.value === idx ? -1 : idx;
  quickAnswerQuestions.value[qaCurrentQuestion.value].selected =
    qaSelectedAnswer.value === -1 ? undefined : qaSelectedAnswer.value;
}

function resetQAQuestion() {
  stopQATimer();
  qaStarted.value = false;
  quickAnswerQuestions.value.forEach((q) => {
    q.answered = false;
    q.selected = undefined;
  });
  qaSelectedAnswer.value = -1;
  qaCurrentQuestion.value = 0;
}

// 2. 实时投票
const polls = ref([
  {
    id: 1,
    title: "你认为本节课最难理解的概念是什么？",
    options: [
      { label: "控制变量法", votes: 12, color: "#667eea" },
      { label: "牛顿第二定律公式", votes: 8, color: "#10b981" },
      { label: "实验误差分析", votes: 5, color: "#f59e0b" },
      { label: "力的合成与分解", votes: 3, color: "#06b6d4" },
    ],
    total: 28,
    active: true,
  },
  {
    id: 2,
    title: "你更喜欢哪种教学方式？",
    options: [
      { label: "传统讲授", votes: 5, color: "#667eea" },
      { label: "小组合作探究", votes: 15, color: "#10b981" },
      { label: "动手实验", votes: 18, color: "#f59e0b" },
      { label: "多媒体互动", votes: 10, color: "#06b6d4" },
    ],
    total: 48,
    active: true,
  },
]);
const activePollId = ref(1);

// 3. 随机抽选
const pickHistory = ref([]);
const pickingStudent = ref(null);
const isPicking = ref(false);
const pickMode = ref("single");

function startRandomPick() {
  if (isPicking.value) return;
  isPicking.value = true;
  pickingStudent.value = null;
  const totalFrames = 30;
  let frame = 0;
  const interval = setInterval(() => {
    const randomIndex = Math.floor(Math.random() * students.value.length);
    pickingStudent.value = students.value[randomIndex];
    frame++;
    if (frame >= totalFrames) {
      clearInterval(interval);
      isPicking.value = false;
      pickHistory.value.unshift({
        name: pickingStudent.value.name,
        avatar: pickingStudent.value.avatar,
        time: new Date().toLocaleTimeString(),
      });
    }
  }, 60);
}

// 4. 小组积分
const groups = ref([
  {
    id: 1,
    name: "第一组",
    color: "#667eea",
    score: 85,
    members: ["张三", "李四", "王五"],
  },
  {
    id: 2,
    name: "第二组",
    color: "#10b981",
    score: 72,
    members: ["赵六", "陈七"],
  },
  {
    id: 3,
    name: "第三组",
    color: "#f59e0b",
    score: 63,
    members: ["刘八", "孙九"],
  },
  {
    id: 4,
    name: "第四组",
    color: "#06b6d4",
    score: 91,
    members: ["周十", "吴十一", "郑十二"],
  },
]);

function addGroupScore(groupId, points) {
  const group = groups.value.find((g) => g.id === groupId);
  if (group) group.score += points;
}

function removeStudent(id) {
  students.value = students.value.filter((s) => s.id !== id);
}

// ==================== 课程分析

// ==================== 课程分析——选中课程的能力画像 ====================
const selectedCourseId = ref(1);

// 筛选条件
const filterSubject = ref("");
const filterGrade = ref("");
const filterTag = ref("");
const filterStatus = ref("");

// 可供选择的筛选项（从课程数据动态提取）
const filterOptions = computed(() => ({
  subjects: [...new Set(courses.value.map((c) => c.subject))],
  grades: [...new Set(courses.value.map((c) => c.grade))],
  tags: [...new Set(courses.value.flatMap((c) => c.tags))],
}));

// 根据筛选条件过滤课程
const filteredCourses = computed(() => {
  let result = courses.value;
  if (filterSubject.value) {
    result = result.filter((c) => c.subject === filterSubject.value);
  }
  if (filterGrade.value) {
    result = result.filter((c) => c.grade === filterGrade.value);
  }
  if (filterTag.value) {
    result = result.filter((c) => c.tags.includes(filterTag.value));
  }
  if (filterStatus.value === "completed") {
    result = result.filter((c) => c.progress === 100);
  } else if (filterStatus.value === "in-progress") {
    result = result.filter((c) => c.progress > 0 && c.progress < 100);
  } else if (filterStatus.value === "not-started") {
    result = result.filter((c) => c.progress === 0);
  }
  return result;
});

// 过滤后自动选中第一个匹配课程
watch(filteredCourses, (list) => {
  if (list.length > 0 && !list.find((c) => c.id === selectedCourseId.value)) {
    selectedCourseId.value = list[0].id;
    nextTick(() => reInitCharts());
  }
});

// 重置所有筛选条件
function resetFilters() {
  filterSubject.value = "";
  filterGrade.value = "";
  filterTag.value = "";
  filterStatus.value = "";
}

// 是否有活跃筛选条件
const hasActiveFilter = computed(
  () =>
    filterSubject.value ||
    filterGrade.value ||
    filterTag.value ||
    filterStatus.value,
);

const selectedCourse = computed(() =>
  courses.value.find((c) => c.id === selectedCourseId.value),
);

// ==================== 课程资源——视频详情页 ====================
const currentCourseId = ref(null); // null = 课程列表，数字 = 某课程的视频详情

// 每个课程的视频资源数据
const courseVideos = {
  1: [
    {
      id: "v1",
      title: "牛顿第二定律实验演示",
      duration: "12:30",
      cover: "physics-1",
      desc: "通过演示实验直观感受力、质量与加速度三者的关系，建立对 F=ma 的初步认识。",
      focus: ["实验演示", "F=ma 初步认识", "控制变量"],
    },
    {
      id: "v2",
      title: "控制变量法详解",
      duration: "08:45",
      cover: "physics-2",
      desc: "讲解实验设计中如何控制变量，理清自变量、因变量与无关变量的关系。",
      focus: ["控制变量法", "实验设计", "变量分析"],
    },
    {
      id: "v3",
      title: "打点计时器使用教程",
      duration: "15:20",
      cover: "physics-3",
      desc: "手把手演示打点计时器的安装与纸带处理，学会用打点纸带测量加速度。",
      focus: ["打点计时器", "纸带分析", "数据处理"],
    },
    {
      id: "v4",
      title: "F=ma 公式推导与例题",
      duration: "18:10",
      cover: "physics-4",
      desc: "从实验结论出发推导牛顿第二定律表达式，并通过典型例题巩固应用。",
      focus: ["公式推导", "典型例题", "定量计算"],
    },
  ],
  2: [
    {
      id: "v6",
      title: "浓度对反应速率的影响",
      duration: "14:20",
      cover: "chem-1",
      desc: "通过对比实验观察浓度变化如何影响反应快慢，理解碰撞理论的初步解释。",
      focus: ["浓度影响", "对比实验", "碰撞理论"],
    },
    {
      id: "v7",
      title: "温度与反应速率的定量关系",
      duration: "11:30",
      cover: "chem-2",
      desc: "测量不同温度下的反应速率，认识温度变化对反应速率的定量影响规律。",
      focus: ["温度影响", "定量关系", "速率测量"],
    },
    {
      id: "v8",
      title: "催化剂作用机理动画",
      duration: "09:15",
      cover: "chem-3",
      desc: "以动画直观展示催化剂降低活化能的微观过程，理解其加快反应的原理。",
      focus: ["催化剂", "活化能", "微观机理"],
    },
  ],
  3: [
    {
      id: "v10",
      title: "函数单调性图像直观理解",
      duration: "10:20",
      cover: "math-1",
      desc: "从函数图像入手，直观感受曲线的上升与下降趋势，建立单调性的直观印象。",
      focus: ["图像直观", "增减趋势", "概念入门"],
    },
    {
      id: "v12",
      title: "定义法证明函数单调性",
      duration: "16:00",
      cover: "math-2",
      desc: "严格使用单调性定义，通过取值、作差、定号的完整步骤完成代数证明。",
      focus: ["定义法", "作差比较", "代数证明"],
    },
    {
      id: "v13",
      title: "复合函数单调性判断技巧",
      duration: "12:35",
      cover: "math-3",
      desc: "总结“同增异减”的判断口诀，快速确定复合函数的单调区间。",
      focus: ["复合函数", "同增异减", "判断技巧"],
    },
  ],
  4: [
    {
      id: "v15",
      title: "细胞膜结构与功能",
      duration: "11:40",
      cover: "biology-1",
      desc: "解析细胞膜流动镶嵌模型的组成，对应理解其物质运输、信息交流等功能。",
      focus: ["流动镶嵌模型", "膜的功能", "物质运输"],
    },
    {
      id: "v16",
      title: "有丝分裂过程详解",
      duration: "10:50",
      cover: "biology-2",
      desc: "按前期、中期、后期、末期逐步拆解有丝分裂各阶段的染色体变化。",
      focus: ["分裂各时期", "染色体变化", "过程记忆"],
    },
    {
      id: "v18",
      title: "细胞器协调工作机制",
      duration: "13:15",
      cover: "biology-3",
      desc: "以内质网、高尔基体等为例，串联分泌蛋白合成与运输的细胞器协作过程。",
      focus: ["分泌蛋白", "细胞器协作", "合成运输"],
    },
  ],
  5: [
    {
      id: "v20",
      title: "林则徐虎门销烟",
      duration: "12:20",
      cover: "history-1",
      desc: "回顾虎门销烟的背景与经过，认识其作为近代民族抗争标志的历史意义。",
      focus: ["虎门销烟", "禁烟运动", "历史意义"],
    },
    {
      id: "v21",
      title: "辛亥革命与帝制终结",
      duration: "14:30",
      cover: "history-2",
      desc: "梳理辛亥革命的爆发与成果，理解其推翻封建帝制的划时代意义。",
      focus: ["辛亥革命", "推翻帝制", "划时代意义"],
    },
    {
      id: "v22",
      title: "五四运动与新民主主义开端",
      duration: "15:10",
      cover: "history-3",
      desc: "分析五四运动的导火索与影响，理解其作为新民主主义革命开端的地位。",
      focus: ["五四运动", "导火索", "革命开端"],
    },
  ],
  6: [
    {
      id: "v23",
      title: "大气环流基本概念",
      duration: "10:30",
      cover: "geography-1",
      desc: "建立大气环流的整体概念，理解气压带与风带的形成基础。",
      focus: ["大气环流", "气压带风带", "概念基础"],
    },
    {
      id: "v24",
      title: "三圈环流模型解析",
      duration: "14:15",
      cover: "geography-2",
      desc: "用三圈环流模型解释全球气压带与风带的分布规律及其成因。",
      focus: ["三圈环流", "气压带分布", "风带规律"],
    },
    {
      id: "v26",
      title: "世界气候类型分布与判读",
      duration: "16:40",
      cover: "geography-3",
      desc: "结合气候资料图，掌握主要气候类型的分布规律与判读方法。",
      focus: ["气候类型", "分布规律", "图表判读"],
    },
  ],
};

const currentCourse = computed(() =>
  currentCourseId.value
    ? courses.value.find((c) => c.id === currentCourseId.value)
    : null,
);

// 已落地的视频资源清单（对应 public/video/courses/）。未列出的 slug 视为
// 「暂未上传」，列表渲染时过滤掉，避免出现点开即报错的空卡片。
// 新增资源时：把 mp4 放到 public/video/courses/、封面放到
// public/video/courses/covers/，再把 slug 补进这个集合即可。
const AVAILABLE_COVERS = new Set([
  // 物理
  "physics-1", "physics-2", "physics-3", "physics-4",
  // 化学
  "chem-1", "chem-2", "chem-3",
  // 数学
  "math-1", "math-2", "math-3",
  // 生物
  "biology-1", "biology-2", "biology-3",
  // 历史
  "history-1", "history-2", "history-3",
  // 地理
  "geography-1", "geography-2", "geography-3",
]);
function hasVideo(video) {
  return AVAILABLE_COVERS.has(video.cover);
}

const currentVideos = computed(() => {
  const all = currentCourseId.value
    ? courseVideos[currentCourseId.value] || []
    : [];
  return all.filter(hasVideo);
});

function openCourseDetail(id) {
  currentCourseId.value = id;
  playingVideo.value = null;
  // 预加载该课程下所有视频的真实时长
  const videos = courseVideos[id] || [];
  preloadVideoDurations(videos);
}

function backToVideoList() {
  playingVideo.value = null;
  biliIsPlaying.value = false;
  if (biliVideoRef.value) {
    biliVideoRef.value.pause();
  }
  if (biliHideTimer) clearTimeout(biliHideTimer);
  if (biliCenterBtnTimer) clearTimeout(biliCenterBtnTimer);
}

function closeCourseDetail() {
  currentCourseId.value = null;
  playingVideo.value = null;
}

// 视频页「配套备课资源」：一键跳转核心功能页，并预填本节视频课题
function goGenerateKit(type) {
  const video = playingVideo.value || currentVideos.value[0];
  if (!video) return;
  router.push({ path: "/features", query: { type, topic: video.title } });
}

// 当前播放视频在课程中的集数（第几集 / 共几集）
const playingIndex = computed(() => {
  const list = currentVideos.value;
  const vid = playingVideo.value;
  if (!vid || !list.length) return 0;
  const i = list.findIndex((v) => v.id === vid.id);
  return i >= 0 ? i + 1 : 0;
});

function getVideoUrl(cover) {
  return `/video/courses/${cover}.mp4`;
}
function getCoverUrl(cover) {
  return `/video/courses/covers/${cover}.jpg`;
}
function onCoverError(e) {
  e.target.style.display = "none";
  e.target.parentElement.style.background = "#e2e8f0";
}

// ===== 预加载视频真实时长 =====
const realDurations = ref({});

function preloadVideoDurations(videos) {
  if (!videos || videos.length === 0) return;
  for (const video of videos) {
    const tempVideo = document.createElement("video");
    tempVideo.preload = "metadata";
    tempVideo.muted = true;
    tempVideo.src = getVideoUrl(video.cover);
    tempVideo.onloadedmetadata = () => {
      if (tempVideo.duration && isFinite(tempVideo.duration)) {
        realDurations.value = {
          ...realDurations.value,
          [video.id]: tempVideo.duration,
        };
      }
      tempVideo.remove();
    };
    tempVideo.onerror = () => {
      tempVideo.remove();
    };
  }
}

// ===== B站风格播放器 =====
const playingVideo = ref(null);
const biliVideoRef = ref(null);
const biliBgRef = ref(null); // 模糊填充背景视频
const biliProgressRef = ref(null);
const biliMoreRef = ref(null);
const biliIsPlaying = ref(false);
const biliIsFullscreen = ref(false);
const biliCurrentTime = ref("0:00");
const biliDuration = ref("0:00");
const biliPlayedPercent = ref(0);
const biliBufferPercent = ref(0);
const biliVolume = ref(1);
const biliPlaybackRate = ref(1);
const biliControlsHidden = ref(false);
const biliShowVolume = ref(false);
const biliShowMore = ref(false);
const biliShowCenterBtn = ref(true);
const biliSpeedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2];
let biliHideTimer = null;
let biliCenterBtnTimer = null;

function playVideo(video) {
  playingVideo.value = video;
  biliIsPlaying.value = false;
  biliCurrentTime.value = "0:00";
  biliDuration.value = "0:00";
  biliPlayedPercent.value = 0;
  biliBufferPercent.value = 0;
  biliControlsHidden.value = false;
  biliShowMore.value = false;
  biliShowCenterBtn.value = true;
  biliCenterBtnTimer = setTimeout(() => {
    biliShowCenterBtn.value = false;
  }, 3000);
}

function closePlayer() {
  playingVideo.value = null;
  biliIsPlaying.value = false;
  if (biliVideoRef.value) {
    biliVideoRef.value.pause();
  }
  if (biliHideTimer) clearTimeout(biliHideTimer);
  if (biliCenterBtnTimer) clearTimeout(biliCenterBtnTimer);
}

function biliTogglePlay() {
  const video = biliVideoRef.value;
  if (!video) return;
  if (video.paused) {
    video.play();
  } else {
    video.pause();
  }
}

function biliOnPlay() {
  biliIsPlaying.value = true;
  biliShowCenterBtn.value = false;
  if (biliCenterBtnTimer) clearTimeout(biliCenterBtnTimer);
  biliSyncBg();
}

function biliOnPause() {
  biliIsPlaying.value = false;
  biliShowCenterBtn.value = true;
  biliSyncBg();
}

function biliOnEnded() {
  biliIsPlaying.value = false;
  biliShowCenterBtn.value = true;
}

function biliOnMetaLoaded() {
  const video = biliVideoRef.value;
  if (!video) return;
  biliDuration.value = biliFormatTime(video.duration);
  // 同步更新到 realDurations，和视频卡片显示一致
  if (playingVideo.value && video.duration && isFinite(video.duration)) {
    realDurations.value = {
      ...realDurations.value,
      [playingVideo.value.id]: video.duration,
    };
  }
  video.playbackRate = biliPlaybackRate.value;
}

// 模糊填充背景跟随主视频的播放状态与进度
function biliSyncBg() {
  const bg = biliBgRef.value;
  const video = biliVideoRef.value;
  if (!bg || !video) return;
  if (!video.paused) {
    bg.play().catch(() => {});
  } else {
    bg.pause();
  }
  if (Math.abs(bg.currentTime - video.currentTime) > 1) {
    bg.currentTime = video.currentTime;
  }
}

function biliOnTimeUpdate() {
  const video = biliVideoRef.value;
  if (!video || !video.duration) return;
  biliCurrentTime.value = biliFormatTime(video.currentTime);
  biliPlayedPercent.value = (video.currentTime / video.duration) * 100;
  // buffer
  if (video.buffered.length > 0) {
    biliBufferPercent.value =
      (video.buffered.end(video.buffered.length - 1) / video.duration) * 100;
  }
  biliSyncBg();
}

function biliFormatTime(s) {
  const min = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return min + ":" + (sec < 10 ? "0" : "") + sec;
}

// 视频卡片显示时长：优先用加载到的真实时长（秒），回退到存储值
function displayDuration(video) {
  const realSec = realDurations.value[video.id];
  if (realSec) return biliFormatTime(realSec);
  return video.duration;
}

function biliSeek(e) {
  const video = biliVideoRef.value;
  const bar = biliProgressRef.value;
  if (!video || !bar || !video.duration) return;
  const rect = bar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  video.currentTime = pct * video.duration;
}

function biliSetVolume(e) {
  const v = parseFloat(e.target.value);
  biliVolume.value = v;
  const video = biliVideoRef.value;
  if (video) video.volume = v;
}

function biliSetSpeed(rate) {
  biliPlaybackRate.value = rate;
  const video = biliVideoRef.value;
  if (video) video.playbackRate = rate;
}

function biliToggleFullscreen() {
  const container = document.querySelector(".bili-page-player");
  if (!container) return;
  if (!document.fullscreenElement) {
    container
      .requestFullscreen()
      .then(() => {
        biliIsFullscreen.value = true;
      })
      .catch(() => {});
  } else {
    document
      .exitFullscreen()
      .then(() => {
        biliIsFullscreen.value = false;
      })
      .catch(() => {});
  }
  biliShowMore.value = false;
}

function biliDownload() {
  if (!playingVideo.value) return;
  const a = document.createElement("a");
  a.href = getVideoUrl(playingVideo.value.cover);
  a.download = playingVideo.value.title + ".mp4";
  a.click();
  biliShowMore.value = false;
}

function biliSwitchVideo(video) {
  if (playingVideo.value?.id === video.id) return;
  const wasPlaying = biliIsPlaying.value;
  playingVideo.value = video;
  biliShowMore.value = false;
  biliShowCenterBtn.value = true;
  // 重置播放状态
  biliIsPlaying.value = false;
  biliCurrentTime.value = "0:00";
  biliPlayedPercent.value = 0;
  biliBufferPercent.value = 0;
  biliControlsHidden.value = false;
  if (biliCenterBtnTimer) clearTimeout(biliCenterBtnTimer);
  biliCenterBtnTimer = setTimeout(() => {
    biliShowCenterBtn.value = false;
  }, 3000);
  // 如果之前正在播放，等 metadata 加载后自动播放
  nextTick(() => {
    const videoEl = biliVideoRef.value;
    if (videoEl && wasPlaying) {
      videoEl.play().catch(() => {});
    }
  });
}

function biliShowControls() {
  biliControlsHidden.value = false;
  biliCancelHideTimer();
  if (biliIsPlaying.value) {
    biliStartHideTimer();
  }
}

function biliStartHideTimer() {
  biliCancelHideTimer();
  if (!biliIsPlaying.value) return;
  biliHideTimer = setTimeout(() => {
    if (!biliShowMore.value) {
      biliControlsHidden.value = true;
    }
  }, 3000);
}

function biliCancelHideTimer() {
  if (biliHideTimer) {
    clearTimeout(biliHideTimer);
    biliHideTimer = null;
  }
}

const radarDimensions = [
  "知识覆盖面",
  "实验实践性",
  "思维启发性",
  "互动参与度",
  "难度梯度",
  "知识系统性",
];

// 雷达图系列数据
const radarData = computed(() => {
  const course = selectedCourse.value;
  if (!course) return [];
  return [
    {
      value: radarDimensions.map((d) => course.capabilities[d]),
      name: course.title,
    },
  ];
});

// 获取维度评级
function getDimensionLabel(value) {
  if (value >= 85) return { text: "强项", color: "#22c55e" };
  if (value >= 65) return { text: "良好", color: "#4c7dff" };
  if (value >= 40) return { text: "待提升", color: "#f59e0b" };
  return { text: "薄弱", color: "#ef4444" };
}

// ==================== 菜单切换 ====================
function switchMenu(menuId) {
  if (menuId === activeMenu.value) return;

  isTransitioning.value = true;
  currentCourseId.value = null; // 切换菜单时回到课程列表
  setTimeout(() => {
    activeMenu.value = menuId;
    nextTick(() => {
      if (menuId === "course-analysis") {
        initCharts();
      }
      setTimeout(() => {
        isTransitioning.value = false;
      }, 50);
    });
  }, 200);
}

// ==================== ECharts 初始化 ====================
let charts = {};

function initCharts() {
  const chartDom = document.getElementById("radar-chart");
  if (!chartDom) return;

  if (charts.radar) charts.radar.dispose();

  const course = selectedCourse.value;
  if (!course) return;

  const radarChart = echarts.init(chartDom);
  charts.radar = radarChart;

  const indicator = radarDimensions.map((name) => ({ name, max: 100 }));

  radarChart.setOption({
    title: {
      text: `${course.title}\n能力画像`,
      left: "center",
      top: 10,
      textStyle: { fontSize: 16, fontWeight: "bold", color: "#1e293b" },
    },
    legend: {
      bottom: 5,
      data: [course.title],
      textStyle: { fontSize: 12, color: "#64748b" },
    },
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        if (params.name) {
          const value = params.value;
          const label = getDimensionLabel(value);
          return `<b>${params.name}</b><br/>分值: <span style="color:${label.color};font-weight:bold">${value}</span> <span style="color:${label.color}">(${label.text})</span>`;
        }
        return "";
      },
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      textStyle: { color: "#334155" },
    },
    radar: {
      indicator,
      center: ["50%", "55%"],
      radius: "60%",
      shape: "polygon",
      splitNumber: 5,
      axisName: {
        color: "#475569",
        fontSize: 12,
        borderRadius: 3,
        padding: [3, 5],
      },
      splitArea: {
        areaStyle: {
          color: [
            "rgba(76,125,255,0.02)",
            "rgba(76,125,255,0.02)",
            "rgba(76,125,255,0.04)",
            "rgba(76,125,255,0.06)",
            "rgba(76,125,255,0.08)",
          ],
        },
      },
      splitLine: { lineStyle: { color: "rgba(76,125,255,0.15)" } },
      axisLine: { lineStyle: { color: "rgba(76,125,255,0.3)" } },
    },
    series: [
      {
        type: "radar",
        data: radarData.value,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: "#4c7dff", width: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(76,125,255,0.35)" },
              { offset: 1, color: "rgba(99,102,241,0.08)" },
            ],
          },
        },
        itemStyle: { color: "#4c7dff", borderColor: "#fff", borderWidth: 2 },
        label: {
          show: true,
          formatter: (p) => p.value,
          color: "#475569",
          fontSize: 10,
        },
        emphasis: {
          areaStyle: { color: "rgba(76,125,255,0.5)" },
          label: { fontSize: 13, fontWeight: "bold" },
        },
        animationDuration: 1500,
        animationEasing: "elasticOut",
      },
    ],
  });

  window.addEventListener("resize", () => {
    charts.radar?.resize?.();
    charts.factorPie?.resize?.();
    charts.bar?.resize?.();
  });

  // 教学时间分配饼图
  const pieDom = document.getElementById("factor-chart");
  if (pieDom && course.timeAllocation) {
    const pieChart = echarts.init(pieDom);
    charts.factorPie = pieChart;

    const pieColors = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de"];
    pieChart.setOption({
      title: {
        text: "教学时间分配",
        left: "center",
        top: 10,
        textStyle: { fontSize: 15, fontWeight: "bold", color: "#1e293b" },
      },
      tooltip: {
        trigger: "item",
        formatter: "<b>{b}</b><br/>占比: {c}% ({d}%)",
        backgroundColor: "rgba(255, 255, 255, 0.95)",
        borderColor: "#e2e8f0",
        borderWidth: 1,
        textStyle: { color: "#334155" },
      },
      legend: {
        bottom: 5,
        textStyle: { fontSize: 11, color: "#64748b" },
      },
      series: [
        {
          type: "pie",
          radius: ["45%", "75%"],
          center: ["50%", "50%"],
          itemStyle: {
            borderRadius: 6,
            borderColor: "#fff",
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: "{b}\n{d}%",
            color: "#475569",
            fontSize: 10,
          },
          emphasis: {
            label: { fontSize: 14, fontWeight: "bold" },
            itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.15)" },
          },
          data: course.timeAllocation.map((d, i) => ({
            ...d,
            itemStyle: { color: pieColors[i % pieColors.length] },
          })),
          animationType: "scale",
          animationEasing: "elasticOut",
        },
      ],
    });
  }

  // 能力维度水平柱状图
  const barDom = document.getElementById("bar-chart");
  if (barDom) {
    const barChart = echarts.init(barDom);
    charts.bar = barChart;

    // 反转维度顺序（从上到下显示），配合反转的 Y 轴
    const items = radarDimensions
      .map((dim) => {
        const score = course.capabilities[dim] || 0;
        const label = getDimensionLabel(score);
        return {
          name: dim,
          value: score,
          color: label.color,
          label: label.text,
        };
      })
      .reverse();

    barChart.setOption({
      title: {
        text: "能力维度解读",
        left: "center",
        top: 10,
        textStyle: { fontSize: 15, fontWeight: "bold", color: "#1e293b" },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        formatter: (params) => {
          const p = params[0];
          return `<b>${p.name}</b><br/>分值: <span style="color:${p.color};font-weight:bold">${p.value}</span>`;
        },
        backgroundColor: "rgba(255, 255, 255, 0.95)",
        borderColor: "#e2e8f0",
        borderWidth: 1,
        textStyle: { color: "#334155" },
      },
      grid: {
        left: "5%",
        right: "12%",
        top: "18%",
        bottom: "5%",
        containLabel: true,
      },
      xAxis: {
        type: "value",
        max: 100,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
        axisLabel: { color: "#94a3b8", fontSize: 10, formatter: "{value}" },
      },
      yAxis: {
        type: "category",
        data: items.map((d) => d.name),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: "#475569", fontSize: 11, fontWeight: 500 },
        inverse: true,
      },
      series: [
        {
          type: "bar",
          data: items.map((d) => ({
            value: d.value,
            itemStyle: {
              color: d.color,
              borderRadius: [0, 6, 6, 0],
            },
          })),
          barWidth: 18,
          label: {
            show: true,
            position: "right",
            formatter: (p) => `${p.value}`,
            color: "#475569",
            fontSize: 10,
            fontWeight: 600,
          },
          emphasis: {
            itemStyle: { shadowBlur: 8, shadowColor: "rgba(0,0,0,0.12)" },
          },
          animationDuration: 1200,
          animationEasing: "cubicOut",
        },
      ],
    });
  }
}

// 重置图表
function reInitCharts() {
  if (charts.radar) {
    charts.radar.dispose();
    charts.radar = null;
  }
  if (charts.factorPie) {
    charts.factorPie.dispose();
    charts.factorPie = null;
  }
  if (charts.bar) {
    charts.bar.dispose();
    charts.bar = null;
  }
  nextTick(() => initCharts());
}

// ==================== 辅助函数 ====================
function getMasteryLevel(mastery) {
  if (mastery >= 90) return "excellent";
  if (mastery >= 70) return "good";
  if (mastery >= 50) return "average";
  return "needs-work";
}

// ==================== 问答交互 ====================
function toggleQA(id) {
  const qa = qaList.value.find((q) => q.id === id);
  if (qa) {
    qa.isExpanded = !qa.isExpanded;
  }
}

// ==================== 生命周期 ====================
onMounted(() => {
  // 初始加载时如果是课程分析页面，初始化图表
  if (activeMenu.value === "course-analysis") {
    nextTick(() => {
      initCharts();
    });
  }
});

// 监听菜单变化，清理图表
watch(activeMenu, (newVal) => {
  if (newVal !== "course-analysis") {
    if (charts.radar) {
      charts.radar.dispose();
      charts.radar = null;
    }
    if (charts.factorPie) {
      charts.factorPie.dispose();
      charts.factorPie = null;
    }
    if (charts.bar) {
      charts.bar.dispose();
      charts.bar = null;
    }
  }
});
</script>

<template>
  <div class="lessons-page">
    <div class="lessons-bg" aria-hidden="true" />
    <SiteNav />

    <main class="lessons-main">
      <div
        class="lessons-container"
        :class="{ 'lessons-container--home': activeMenu === 'home' }"
      >
        <!-- 左侧功能菜单（主页时隐藏） -->
        <aside v-if="activeMenu !== 'home'" class="sidebar-menu">
          <div
            class="menu-header"
            @click="switchMenu('home')"
            style="cursor: pointer"
          >
            <div class="menu-icon">🎓</div>
            <h2>课堂教程</h2>
            <p>点击返回主页</p>
          </div>

          <nav class="menu-list">
            <button
              v-for="item in menuItems"
              :key="item.id"
              class="menu-item"
              :class="{ 'menu-item--active': activeMenu === item.id }"
              @click="switchMenu(item.id)"
            >
              <span class="menu-item__icon" v-html="item.icon"></span>
              <div class="menu-item__content">
                <span class="menu-item__label">{{ item.label }}</span>
                <span class="menu-item__desc">{{ item.desc }}</span>
              </div>
              <span class="menu-item__arrow">→</span>
            </button>
          </nav>

          <div class="menu-footer">
            <div class="stats-card">
              <div class="stat-item">
                <span class="stat-value">12</span>
                <span class="stat-label">已学课程</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">86%</span>
                <span class="stat-label">平均进度</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- 右侧内容区域 -->
        <section class="content-area">
          <div
            class="content-wrapper"
            :class="{
              'content-wrapper--transitioning': isTransitioning,
              'content-wrapper--home': activeMenu === 'home',
            }"
          >
            <!-- 主页 -->
            <div
              v-if="activeMenu === 'home'"
              class="content-panel content-panel--home"
            >
              <!-- Hero 区域 -->
              <div class="home-hero">
                <div class="home-hero-badge">教学工具集</div>
                <h1 class="home-hero-title">
                  <span class="float-cap">🎓</span>
                  课堂教程
                </h1>
                <p class="home-hero-subtitle">
                  课程资源、能力分析、课堂互动与AI总结，<br />覆盖课前备课到课后追踪的全流程。
                </p>
                <div class="home-stats-row">
                  <div class="home-stat">
                    <span class="home-stat-num">{{ courses.length }}</span>
                    <span class="home-stat-label">课程资源</span>
                  </div>
                  <div class="home-stat">
                    <span class="home-stat-num">6</span>
                    <span class="home-stat-label">学科覆盖</span>
                  </div>
                  <div class="home-stat">
                    <span class="home-stat-num">5</span>
                    <span class="home-stat-label">功能模块</span>
                  </div>
                  <div class="home-stat">
                    <span class="home-stat-num">86%</span>
                    <span class="home-stat-label">平均完成率</span>
                  </div>
                </div>
              </div>

              <!-- 模块卡片 -->
              <div class="home-section">
                <h2 class="home-section-title">功能模块</h2>
                <p class="home-section-desc">选择一个模块开始使用</p>
                <div class="home-cards">
                  <div
                    v-for="item in menuItems"
                    :key="item.id"
                    class="home-card"
                    :class="[`home-card--${item.id}`]"
                    @click="switchMenu(item.id)"
                  >
                    <div class="home-card-top">
                      <div class="home-card-icon-wrap">
                        <span class="home-card-emoji" v-html="item.icon"></span>
                      </div>
                      <div class="home-card-top-right">
                        <span class="home-card-badge">{{
                          getHomeBadge(item.id)
                        }}</span>
                      </div>
                    </div>
                    <div class="home-card-body">
                      <h3 class="home-card-title">{{ item.label }}</h3>
                      <p class="home-card-desc">{{ getHomeDesc(item.id) }}</p>
                      <div class="home-card-keywords">
                        <span
                          v-for="kw in getHomeKeywords(item.id)"
                          :key="kw"
                          class="home-keyword"
                          >{{ kw }}</span
                        >
                      </div>
                    </div>
                    <div class="home-card-footer">
                      <span class="home-card-action">
                        进入模块
                        <span class="home-card-arrow">→</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 底部提示 -->
              <div class="home-footer-hint">
                <span>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#6B7280"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    style="vertical-align: middle; margin-right: 4px"
                  >
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                  也可以使用左侧菜单栏在各模块间快速切换
                </span>
              </div>
            </div>

            <!-- 1. 课程资源 -->
            <div v-if="activeMenu === 'course-resource'" class="content-panel">
              <!-- ===== 课程列表视图 ===== -->
              <template v-if="!currentCourseId">
                <div class="panel-header">
                  <h1>
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#4c7dff"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      style="vertical-align: middle; margin-right: 8px"
                    >
                      <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
                      <path
                        d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"
                      />
                    </svg>
                    课程资源
                  </h1>
                  <p>浏览所有可用的课程资源，点击课程查看该课程下的教学视频</p>
                </div>

                <div class="course-grid">
                  <div
                    v-for="course in courses"
                    :key="course.id"
                    class="course-card"
                    @click="openCourseDetail(course.id)"
                  >
                    <div class="course-cover">
                      <img
                        :src="getSubjectStyle(course.subject).image"
                        :alt="course.subject"
                        class="cover-img"
                        @error="onCoverError"
                        :style="{
                          objectPosition:
                            course.subject === '化学'
                              ? '50% 37%'
                              : course.subject === '生物'
                                ? '50% 35%'
                                : course.subject === '物理'
                                  ? '50% 22%'
                                  : 'center',
                          transform:
                            course.subject === '物理' ||
                            course.subject === '化学'
                              ? 'scale(1)'
                              : undefined,
                        }"
                      />
                      <!-- 底部渐变遮罩 -->
                      <div class="cover-gradient"></div>
                      <!-- 学科标签 -->
                      <div
                        class="cover-subject-tag"
                        :style="{
                          background: getSubjectStyle(course.subject).color,
                        }"
                      >
                        {{ getSubjectStyle(course.subject).symbol }}
                        {{ course.subject }}
                      </div>
                      <!-- 悬停浮层（底部） -->
                      <div class="course-overlay">
                        <span class="detail-hint">查看视频</span>
                      </div>
                      <span class="course-video-count"
                        >{{
                          (courseVideos[course.id] || []).length
                        }}个视频</span
                      >
                    </div>
                    <div class="course-info">
                      <div class="course-tags">
                        <span
                          v-for="tag in course.tags"
                          :key="tag"
                          class="tag"
                          >{{ tag }}</span
                        >
                      </div>
                      <h3 class="course-title">{{ course.title }}</h3>
                      <p class="course-desc">{{ course.description }}</p>
                      <div class="course-meta">
                        <span class="subject-badge">{{ course.subject }}</span>
                        <span class="grade-text">{{ course.grade }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- ===== 课程视频列表（点击课程后显示） ===== -->
              <template v-else-if="currentCourseId && !playingVideo">
                <div class="video-list-page">
                  <div class="video-list-header">
                    <button class="back-btn" @click="closeCourseDetail">
                      <span class="back-arrow">←</span>
                      <span>返回课程资源</span>
                    </button>
                    <div class="bili-page-course-info">
                      <span
                        v-html="getSubjectStyle(currentCourse?.subject).icon"
                      ></span>
                      <div>
                        <strong>{{ currentCourse?.title }}</strong>
                        <span
                          >{{ currentCourse?.subject }} ·
                          {{ currentCourse?.grade }} ·
                          {{ currentVideos.length }}个视频</span
                        >
                      </div>
                    </div>
                  </div>

                  <div class="video-grid">
                    <div
                      v-for="video in currentVideos"
                      :key="video.id"
                      class="video-card"
                      @click="playVideo(video)"
                    >
                      <div class="video-cover">
                        <img
                          :src="getCoverUrl(video.cover)"
                          :alt="video.title"
                          class="video-cover-img"
                          loading="lazy"
                        />
                        <div class="video-overlay">
                          <div class="video-play-btn">▶</div>
                        </div>
                        <span class="video-duration-badge">{{
                          displayDuration(video)
                        }}</span>
                      </div>
                      <div class="video-info">
                        <h4 class="video-title-text">{{ video.title }}</h4>
                        <div class="video-sub-info">
                          <span class="video-subject-label">{{
                            currentCourse?.subject
                          }}</span>
                          <span class="video-grade-label">{{
                            currentCourse?.grade
                          }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>

              <!-- ===== B站风格视频播放器 ===== -->
              <template v-else>
                <div class="bili-page">
                  <!-- 顶部导航 -->
                  <div class="bili-page-header">
                    <button class="back-btn" @click="backToVideoList">
                      <span class="back-arrow">←</span>
                      <span>返回视频列表</span>
                    </button>
                    <div class="bili-page-course-info">
                      <span
                        v-html="getSubjectStyle(currentCourse?.subject).icon"
                      ></span>
                      <div>
                        <strong>{{ currentCourse?.title }}</strong>
                        <span
                          >{{ currentCourse?.subject }} ·
                          {{ currentCourse?.grade }} ·
                          {{ currentVideos.length }}个视频</span
                        >
                      </div>
                    </div>
                  </div>

                  <div class="bili-page-layout">
                    <!-- 左侧：播放器 + 视频信息/配套资源 -->
                    <div class="bili-page-left">
                      <div class="bili-page-player">
                        <!-- 视频区域 -->
                        <div
                          class="bili-player-video-wrap"
                          @click="biliTogglePlay"
                          @mousemove="biliShowControls"
                          @mouseleave="biliStartHideTimer"
                        >
                          <!-- 模糊填充背景：竖屏/异形视频也能铺满统一 16:9 画面 -->
                          <video
                            ref="biliBgRef"
                            :src="
                              getVideoUrl(
                                playingVideo?.cover || currentVideos[0]?.cover,
                              )
                            "
                            class="bili-player-bg"
                            muted
                            loop
                            playsinline
                            aria-hidden="true"
                            tabindex="-1"
                            @loadedmetadata="biliSyncBg"
                          ></video>
                          <video
                            ref="biliVideoRef"
                            :src="
                              getVideoUrl(
                                playingVideo?.cover || currentVideos[0]?.cover,
                              )
                            "
                            class="bili-player-video"
                            @loadedmetadata="biliOnMetaLoaded"
                            @timeupdate="biliOnTimeUpdate"
                            @ended="biliOnEnded"
                            @play="biliOnPlay"
                            @pause="biliOnPause"
                            playsinline
                          ></video>

                          <!-- 中央播放按钮 -->
                          <div
                            class="bili-center-play"
                            :class="{ 'is-hidden': !biliShowCenterBtn }"
                            @click.stop="biliTogglePlay"
                          >
                            <svg
                              width="48"
                              height="48"
                              viewBox="0 0 24 24"
                              fill="white"
                            >
                              <polygon points="8,5 19,12 8,19" />
                            </svg>
                          </div>
                          <!-- 底部控制栏（覆盖在视频底部） -->
                          <div
                            class="bili-controls"
                            :class="{ 'is-hidden': biliControlsHidden }"
                            @click.stop
                            @mouseenter="biliCancelHideTimer"
                            @mouseleave="biliStartHideTimer"
                          >
                            <!-- 进度条 -->
                            <div
                              class="bili-progress-bar"
                              @click="biliSeek"
                              ref="biliProgressRef"
                            >
                              <div
                                class="bili-progress-buffer"
                                :style="{ width: biliBufferPercent + '%' }"
                              ></div>
                              <div
                                class="bili-progress-played"
                                :style="{ width: biliPlayedPercent + '%' }"
                              >
                                <div class="bili-progress-thumb"></div>
                              </div>
                            </div>

                            <!-- 控制按钮行 -->
                            <div class="bili-controls-row">
                              <div class="bili-controls-left">
                                <button
                                  class="bili-btn"
                                  @click="biliTogglePlay"
                                  title="播放/暂停"
                                >
                                  <svg
                                    v-if="!biliIsPlaying"
                                    width="20"
                                    height="20"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                  >
                                    <polygon points="8,5 19,12 8,19" />
                                  </svg>
                                  <svg
                                    v-else
                                    width="20"
                                    height="20"
                                    viewBox="0 0 24 24"
                                    fill="currentColor"
                                  >
                                    <rect
                                      x="6"
                                      y="4"
                                      width="4"
                                      height="16"
                                      rx="1"
                                    />
                                    <rect
                                      x="14"
                                      y="4"
                                      width="4"
                                      height="16"
                                      rx="1"
                                    />
                                  </svg>
                                </button>
                                <span class="bili-time"
                                  >{{ biliCurrentTime }} /
                                  {{ biliDuration }}</span
                                >
                              </div>

                              <div class="bili-controls-right">
                                <!-- 音量 -->
                                <div
                                  class="bili-volume-wrap"
                                  @mouseenter="biliShowVolume = true"
                                  @mouseleave="biliShowVolume = false"
                                >
                                  <button class="bili-btn" title="音量">
                                    <svg
                                      width="20"
                                      height="20"
                                      viewBox="0 0 24 24"
                                      fill="currentColor"
                                    >
                                      <polygon
                                        points="11,5 6,9 2,9 2,15 6,15 11,19"
                                      />
                                      <path
                                        v-if="biliVolume > 0"
                                        d="M15.54 8.46a5 5 0 010 7.07"
                                        stroke="currentColor"
                                        fill="none"
                                        stroke-width="2"
                                        stroke-linecap="round"
                                      />
                                      <path
                                        v-if="biliVolume > 0.5"
                                        d="M19.07 4.93a10 10 0 010 14.14"
                                        stroke="currentColor"
                                        fill="none"
                                        stroke-width="2"
                                        stroke-linecap="round"
                                      />
                                    </svg>
                                  </button>
                                  <div
                                    v-show="biliShowVolume"
                                    class="bili-volume-slider"
                                  >
                                    <input
                                      type="range"
                                      min="0"
                                      max="1"
                                      step="0.05"
                                      :value="biliVolume"
                                      @input="biliSetVolume"
                                    />
                                  </div>
                                </div>

                                <!-- 三个点菜单 -->
                                <div class="bili-more-wrap" ref="biliMoreRef">
                                  <button
                                    class="bili-btn"
                                    @click="biliShowMore = !biliShowMore"
                                    title="更多"
                                  >
                                    <svg
                                      width="20"
                                      height="20"
                                      viewBox="0 0 24 24"
                                      fill="currentColor"
                                    >
                                      <circle cx="12" cy="5" r="1.5" />
                                      <circle cx="12" cy="12" r="1.5" />
                                      <circle cx="12" cy="19" r="1.5" />
                                    </svg>
                                  </button>
                                  <Transition name="more-menu">
                                    <div
                                      v-if="biliShowMore"
                                      class="bili-more-menu"
                                      @click.stop
                                    >
                                      <div class="bili-menu-section">
                                        <div class="bili-menu-label">
                                          播放速度
                                        </div>
                                        <div class="bili-speed-list">
                                          <button
                                            v-for="rate in biliSpeedOptions"
                                            :key="rate"
                                            class="bili-speed-btn"
                                            :class="{
                                              active: biliPlaybackRate === rate,
                                            }"
                                            @click="biliSetSpeed(rate)"
                                          >
                                            {{ rate }}x
                                          </button>
                                        </div>
                                      </div>
                                      <div class="bili-menu-divider"></div>
                                      <button
                                        class="bili-menu-item"
                                        @click="biliToggleFullscreen"
                                      >
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
                                            d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"
                                          />
                                        </svg>
                                        <span>{{
                                          biliIsFullscreen ? "退出全屏" : "全屏"
                                        }}</span>
                                      </button>
                                      <button
                                        class="bili-menu-item"
                                        @click="biliDownload"
                                      >
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
                                            d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"
                                          />
                                          <polyline points="7 10 12 15 17 10" />
                                          <line
                                            x1="12"
                                            y1="15"
                                            x2="12"
                                            y2="3"
                                          />
                                        </svg>
                                        <span>下载视频</span>
                                      </button>
                                    </div>
                                  </Transition>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- 视频信息 + 配套备课资源 -->
                      <div class="video-info-card">
                        <h3 class="video-info-title">
                          {{ playingVideo?.title || currentVideos[0]?.title }}
                        </h3>
                        <div class="video-info-meta">
                          <span class="video-info-tag">{{
                            currentCourse?.subject
                          }}</span>
                          <span class="video-info-meta-item">{{
                            currentCourse?.grade
                          }}</span>
                          <span class="video-info-meta-item">{{
                            displayDuration(playingVideo || currentVideos[0])
                          }}</span>
                          <span class="video-info-meta-item" v-if="playingIndex"
                            >第 {{ playingIndex }} 集 / 共
                            {{ currentVideos.length }} 集</span
                          >
                        </div>
                        <p class="video-info-desc">
                          {{
                            (playingVideo || currentVideos[0])?.desc ||
                            currentCourse?.description
                          }}
                        </p>
                        <div
                          class="video-focus"
                          v-if="
                            (playingVideo || currentVideos[0])?.focus?.length
                          "
                        >
                          <span class="video-focus-label">
                            <svg
                              width="13"
                              height="13"
                              viewBox="0 0 24 24"
                              fill="currentColor"
                            >
                              <path
                                d="M12 2l1.9 5.7 5.7 1.9-5.7 1.9L12 17l-1.9-5.5-5.7-1.9 5.7-1.9L12 2z"
                              />
                            </svg>
                            本节要点
                          </span>
                          <span
                            class="video-focus-tag"
                            v-for="tag in (playingVideo || currentVideos[0])
                              ?.focus"
                            :key="tag"
                            >{{ tag }}</span
                          >
                        </div>
                        <div class="video-info-divider"></div>
                        <div class="video-kit-head">
                          <span class="video-kit-title">
                            <svg
                              width="15"
                              height="15"
                              viewBox="0 0 24 24"
                              fill="currentColor"
                            >
                              <path
                                d="M12 2l1.9 5.7 5.7 1.9-5.7 1.9L12 17l-1.9-5.5-5.7-1.9 5.7-1.9L12 2z"
                              />
                            </svg>
                            配套备课资源
                          </span>
                          <span class="video-kit-hint"
                            >由知启灵枢 AI 生成 · 稍作修改即可使用</span
                          >
                        </div>
                        <div class="video-kit-btns">
                          <button
                            class="video-kit-btn"
                            @click="goGenerateKit('ppt')"
                          >
                            <svg
                              width="15"
                              height="15"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                            >
                              <rect x="3" y="4" width="18" height="13" rx="2" />
                              <path d="M12 17v4M8 21h8" />
                            </svg>
                            <span>生成本节课件</span>
                          </button>
                          <button
                            class="video-kit-btn"
                            @click="goGenerateKit('doc')"
                          >
                            <svg
                              width="15"
                              height="15"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                            >
                              <path
                                d="M4 19.5A2.5 2.5 0 016.5 17H20V2H6.5A2.5 2.5 0 004 4.5v15z"
                              />
                              <path d="M4 19.5A2.5 2.5 0 006.5 22H20v-5" />
                            </svg>
                            <span>生成本节教案</span>
                          </button>
                          <button
                            class="video-kit-btn"
                            @click="goGenerateKit('quiz')"
                          >
                            <svg
                              width="15"
                              height="15"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                              stroke-linecap="round"
                              stroke-linejoin="round"
                            >
                              <path d="M17 3l4 4L8 20l-5 1 1-5L17 3z" />
                            </svg>
                            <span>生成本节练习</span>
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- 右侧：播放列表 -->
                    <div class="bili-page-playlist">
                      <div class="bili-playlist-header">
                        <span class="bili-playlist-title">播放列表</span>
                        <span class="bili-playlist-count"
                          >{{ currentVideos.length }}个视频</span
                        >
                      </div>
                      <div class="bili-playlist-list">
                        <div
                          v-for="(video, idx) in currentVideos"
                          :key="video.id"
                          class="bili-playlist-item"
                          :class="{ active: playingVideo?.id === video.id }"
                          @click="biliSwitchVideo(video)"
                        >
                          <div class="bili-playlist-num">{{ idx + 1 }}</div>
                          <div class="bili-playlist-cover">
                            <img
                              :src="getCoverUrl(video.cover)"
                              :alt="video.title"
                              loading="lazy"
                            />
                            <div class="bili-playlist-play-icon">▶</div>
                          </div>
                          <div class="bili-playlist-info">
                            <span class="bili-playlist-name">{{
                              video.title
                            }}</span>
                            <span class="bili-playlist-meta">{{
                              displayDuration(video)
                            }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- 2. 课程分析 -->
            <div v-if="activeMenu === 'course-analysis'" class="content-panel">
              <div class="panel-header">
                <h1>📊 课程分析</h1>
                <p>选择一个课程，查看该课程的能力画像与课件制作建议</p>
              </div>

              <div class="analysis-dashboard">
                <!-- 下拉筛选栏 -->
                <div class="filter-search-bar">
                  <div class="filter-row">
                    <div class="filter-group">
                      <label class="filter-label">学科</label>
                      <select v-model="filterSubject" class="filter-select">
                        <option value="">全部学科</option>
                        <option
                          v-for="sub in filterOptions.subjects"
                          :key="sub"
                          :value="sub"
                        >
                          {{ sub }}
                        </option>
                      </select>
                    </div>
                    <div class="filter-group">
                      <label class="filter-label">年级</label>
                      <select v-model="filterGrade" class="filter-select">
                        <option value="">全部年级</option>
                        <option
                          v-for="g in filterOptions.grades"
                          :key="g"
                          :value="g"
                        >
                          {{ g }}
                        </option>
                      </select>
                    </div>
                    <div class="filter-group">
                      <label class="filter-label">标签</label>
                      <select v-model="filterTag" class="filter-select">
                        <option value="">全部标签</option>
                        <option
                          v-for="t in filterOptions.tags"
                          :key="t"
                          :value="t"
                        >
                          {{ t }}
                        </option>
                      </select>
                    </div>
                    <div class="filter-group">
                      <label class="filter-label">进度</label>
                      <select v-model="filterStatus" class="filter-select">
                        <option value="">全部状态</option>
                        <option value="completed">已完成</option>
                        <option value="in-progress">进行中</option>
                        <option value="not-started">未开始</option>
                      </select>
                    </div>
                  </div>
                  <div class="filter-actions">
                    <button
                      class="filter-btn filter-btn-go"
                      @click="reInitCharts()"
                    >
                      筛选
                    </button>
                    <button
                      class="filter-btn filter-btn-reset"
                      :disabled="!hasActiveFilter"
                      @click="resetFilters()"
                    >
                      重置
                    </button>
                  </div>
                </div>

                <!-- 筛选结果提示 -->
                <div v-if="hasActiveFilter" class="result-count">
                  找到 {{ filteredCourses.length }} 门匹配课程
                </div>

                <!-- 课程选择器 -->
                <div class="course-selector-bar">
                  <div
                    v-for="course in filteredCourses"
                    :key="course.id"
                    class="course-chip"
                    :class="{ active: selectedCourseId === course.id }"
                    @click="
                      selectedCourseId = course.id;
                      reInitCharts();
                    "
                  >
                    <span class="chip-subject">{{ course.subject }}</span>
                    <span class="chip-title">{{ course.title }}</span>
                  </div>
                </div>

                <!-- 选中课程信息卡片 -->
                <div v-if="selectedCourse" class="course-info-card">
                  <div class="info-card-left">
                    <h2>{{ selectedCourse.title }}</h2>
                    <div class="info-card-tags">
                      <span class="info-tag">{{ selectedCourse.subject }}</span>
                      <span class="info-tag">{{ selectedCourse.grade }}</span>
                      <span class="info-tag">{{ selectedCourse.teacher }}</span>
                      <span class="info-tag">{{
                        selectedCourse.duration
                      }}</span>
                    </div>
                    <p class="info-card-desc">
                      {{ selectedCourse.description }}
                    </p>
                  </div>
                  <div class="info-card-right">
                    <span
                      class="info-badge"
                      :style="{
                        background:
                          selectedCourse.progress === 100
                            ? '#22c55e'
                            : selectedCourse.progress > 0
                              ? '#f59e0b'
                              : '#94a3b8',
                      }"
                    >
                      {{
                        selectedCourse.progress === 100
                          ? "已完成"
                          : selectedCourse.progress > 0
                            ? "进行中"
                            : "未开始"
                      }}
                    </span>
                  </div>
                </div>

                <!-- 雷达图 + 饼图 + 维度解读 -->
                <div class="radar-section">
                  <div class="radar-chart-container">
                    <div id="radar-chart" class="chart"></div>
                  </div>
                  <div class="radar-chart-container">
                    <div id="factor-chart" class="chart"></div>
                  </div>
                  <div class="radar-chart-container">
                    <div id="bar-chart" class="chart"></div>
                  </div>
                </div>

                <!-- 课程要点 + 课件建议 -->
                <div class="tips-row">
                  <!-- 课程要点 -->
                  <div class="tips-card">
                    <h3>📋 核心知识点</h3>
                    <ul class="keypoints-list">
                      <li
                        v-for="(point, idx) in selectedCourse?.keyPoints"
                        :key="idx"
                      >
                        <span class="kp-index">{{ idx + 1 }}</span>
                        <span>{{ point }}</span>
                      </li>
                    </ul>
                  </div>

                  <!-- 课件制作建议 -->
                  <div class="tips-card">
                    <h3>
                      <svg
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#f59e0b"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        style="vertical-align: middle; margin-right: 6px"
                      >
                        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                      </svg>
                      课件制作建议
                    </h3>
                    <div class="design-section">
                      <div class="design-item strength">
                        <span class="design-label">✅ 优势</span>
                        <p>{{ selectedCourse?.designTips?.strengths }}</p>
                      </div>
                      <div class="design-item improvement">
                        <span class="design-label">⚠️ 改进方向</span>
                        <p>{{ selectedCourse?.designTips?.improvements }}</p>
                      </div>
                      <div class="design-item suggestions">
                        <span class="design-label">🔧 具体建议</span>
                        <ul>
                          <li
                            v-for="(tip, idx) in selectedCourse?.designTips
                              ?.suggestions"
                            :key="idx"
                          >
                            {{ tip }}
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. 边问边答 -->
            <div v-if="activeMenu === 'qa-session'" class="content-panel">
              <div class="panel-header">
                <h1>💬 边问边答</h1>
                <p>互动式学习问答，巩固知识点</p>
              </div>

              <div class="qa-list">
                <div
                  v-for="qa in qaList"
                  :key="qa.id"
                  class="qa-item"
                  :class="{ 'qa-item--expanded': qa.isExpanded }"
                  @click="toggleQA(qa.id)"
                >
                  <div class="qa-question">
                    <span class="qa-icon">Q</span>
                    <p>{{ qa.question }}</p>
                    <span class="qa-toggle">{{
                      qa.isExpanded ? "−" : "+"
                    }}</span>
                  </div>
                  <div v-if="qa.isExpanded" class="qa-answer">
                    <span class="qa-icon qa-icon--answer">A</span>
                    <div class="qa-answer-content">
                      <p>{{ qa.answer }}</p>
                      <span class="qa-related"
                        >相关课程：{{ qa.relatedCourse }}</span
                      >
                    </div>
                  </div>
                </div>
              </div>

              <div class="qa-input-section">
                <h3>🤔 有问题？立即提问</h3>
                <div class="qa-input-box">
                  <input type="text" placeholder="输入你的问题..." />
                  <button class="submit-btn">提问</button>
                </div>
              </div>
            </div>

            <!-- 4. 课后追问 -->
            <div v-if="activeMenu === 'after-class'" class="content-panel">
              <div class="panel-header">
                <h1>🔍 课后追问</h1>
                <p>深入探讨，拓展思维边界</p>
              </div>

              <div class="topics-list">
                <div
                  v-for="topic in topicsList"
                  :key="topic.id"
                  class="topic-card"
                >
                  <div class="topic-header">
                    <h3>{{ topic.title }}</h3>
                    <span class="topic-time">{{ topic.time }}</span>
                  </div>
                  <p class="topic-content">{{ topic.content }}</p>
                  <div class="topic-meta">
                    <div class="topic-author">
                      <span class="author-avatar" aria-hidden="true">{{
                        topic.author.charAt(0)
                      }}</span>
                      <span>{{ topic.author }}</span>
                    </div>
                    <div class="topic-stats">
                      <span aria-hidden="true">👁</span> {{ topic.views }}
                      <span aria-hidden="true">💬</span> {{ topic.replies }}
                    </div>
                  </div>
                </div>
              </div>

              <button class="new-topic-btn">
                <span>+</span>
                发起新讨论
              </button>
            </div>

            <!-- 6. 课堂互动 -->
            <div
              v-if="activeMenu === 'classroom-activity'"
              class="content-panel classroom-activity-panel"
            >
              <div class="panel-header panel-header--activity">
                <h1>
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
                    <rect x="3" y="7" width="18" height="10" rx="3" />
                    <circle cx="8" cy="12" r="1.5" fill="currentColor" />
                    <circle cx="16" cy="12" r="1.5" fill="currentColor" />
                    <path d="M10 12h0" />
                    <path d="M12 10v4" />
                  </svg>
                  课堂互动
                </h1>
                <p>随堂抢答 · 实时投票 · 随机抽选 · 小组积分</p>
              </div>

              <div class="activity-tabs">
                <button
                  v-for="tab in lessonActivityTabs"
                  :key="tab.id"
                  class="activity-tab"
                  :class="{ 'activity-tab--active': activityTab === tab.id }"
                  @click="activityTab = tab.id"
                >
                  <span class="activity-tab__icon" v-html="tab.icon"></span>
                  <div class="activity-tab__text">
                    <span class="activity-tab__label">{{ tab.label }}</span>
                    <span class="activity-tab__desc">{{ tab.desc }}</span>
                  </div>
                </button>
              </div>

              <!-- 随堂抢答 -->
              <div
                v-if="activityTab === 'quick-answer'"
                class="activity-section"
              >
                <div class="qa-control-bar">
                  <div class="qa-progress">
                    <span class="qa-progress__label"
                      >题目 {{ qaCurrentQuestion + 1 }} /
                      {{ quickAnswerQuestions.length }}</span
                    >
                    <div class="qa-progress__bar">
                      <div
                        class="qa-progress__fill"
                        :style="{
                          width:
                            ((qaCurrentQuestion + 1) /
                              quickAnswerQuestions.length) *
                              100 +
                            '%',
                        }"
                      />
                    </div>
                  </div>
                  <div
                    class="qa-timer"
                    :class="{
                      'qa-timer--running': qaTimerRunning,
                      'qa-timer--expired': qaTotalTimeLeft <= 0,
                    }"
                  >
                    <span class="qa-timer__icon">⏳</span>
                    <span class="qa-timer__value">{{ qaTotalTimeLeft }}s</span>
                  </div>
                </div>
                <div class="qa-question-card">
                  <div class="qa-question-card__header">
                    <span class="qa-question-card__num"
                      >Q{{ qaCurrentQuestion + 1 }}</span
                    >
                    <span class="qa-question-card__type">⚡ 限时抢答</span>
                  </div>
                  <h3 class="qa-question-card__text">
                    {{ quickAnswerQuestions[qaCurrentQuestion].question }}
                  </h3>
                  <div class="qa-question-card__options">
                    <div
                      v-for="(opt, idx) in quickAnswerQuestions[
                        qaCurrentQuestion
                      ].options"
                      :key="idx"
                      class="qa-option"
                      :class="{
                        'qa-option--selected': qaSelectedAnswer === idx,
                        'qa-option--correct':
                          quickAnswerQuestions[qaCurrentQuestion].answered &&
                          idx ===
                            quickAnswerQuestions[qaCurrentQuestion].correct,
                        'qa-option--wrong':
                          quickAnswerQuestions[qaCurrentQuestion].answered &&
                          quickAnswerQuestions[qaCurrentQuestion].selected >=
                            0 &&
                          idx ===
                            quickAnswerQuestions[qaCurrentQuestion].selected &&
                          idx !==
                            quickAnswerQuestions[qaCurrentQuestion].correct,
                      }"
                      @click="selectQAAnswer(idx)"
                    >
                      <span class="qa-option__letter">{{
                        ["A", "B", "C", "D"][idx]
                      }}</span>
                      <span class="qa-option__text">{{ opt }}</span>
                    </div>
                  </div>
                  <div
                    v-if="quickAnswerQuestions[qaCurrentQuestion].answered"
                    class="qa-explanation"
                  >
                    <span class="qa-explanation__icon">ℹ️</span>
                    <p>
                      {{ quickAnswerQuestions[qaCurrentQuestion].explanation }}
                    </p>
                  </div>
                </div>
                <div class="qa-actions">
                  <button
                    v-if="!qaStarted"
                    class="qa-action-btn qa-action-btn--primary"
                    @click="startQATimer"
                  >
                    ▶ 开始计时
                  </button>
                  <template v-if="qaStarted &amp;&amp; qaTimerRunning">
                    <button
                      class="qa-action-btn qa-action-btn--secondary"
                      @click="prevQAQuestion"
                      :disabled="qaCurrentQuestion === 0"
                    >
                      ← 上一题
                    </button>
                    <button
                      v-if="qaCurrentQuestion < quickAnswerQuestions.length - 1"
                      class="qa-action-btn qa-action-btn--secondary"
                      @click="nextQAQuestion"
                    >
                      下一题 →
                    </button>
                    <button
                      v-if="
                        qaCurrentQuestion >= quickAnswerQuestions.length - 1
                      "
                      class="qa-action-btn qa-action-btn--reveal"
                      @click="submitQA"
                    >
                      ✅ 提交
                    </button>
                    <button
                      class="qa-action-btn qa-action-btn--reset"
                      @click="resetQAQuestion"
                    >
                      🔄 重新开始
                    </button>
                  </template>
                  <template v-if="qaStarted &amp;&amp; !qaTimerRunning">
                    <button
                      class="qa-action-btn qa-action-btn--secondary"
                      @click="prevQAQuestion"
                      :disabled="qaCurrentQuestion === 0"
                    >
                      ← 上一题
                    </button>
                    <button
                      class="qa-action-btn qa-action-btn--reset"
                      @click="resetQAQuestion"
                    >
                      🔄 重新开始
                    </button>
                  </template>
                </div>
                <div class="qa-leaderboard">
                  <h3>🏅 抢答排行榜</h3>
                  <div class="qa-leaderboard-list">
                    <div
                      v-for="(entry, idx) in qaLeaderboard"
                      :key="entry.name"
                      class="qa-leaderboard-item"
                      :class="{ 'qa-leaderboard-item--top': idx < 3 }"
                    >
                      <span class="qa-leaderboard-item__rank">{{
                        idx + 1
                      }}</span>
                      <span class="qa-leaderboard-item__name">{{
                        entry.name
                      }}</span>
                      <span class="qa-leaderboard-item__score"
                        >{{ entry.score }}分</span
                      >
                      <span class="qa-leaderboard-item__time"
                        >{{ entry.time }}s</span
                      >
                    </div>
                  </div>
                </div>
              </div>

              <!-- 实时投票 -->
              <div v-if="activityTab === 'poll'" class="activity-section">
                <div class="poll-selector">
                  <label>选择投票主题：</label>
                  <select v-model="activePollId">
                    <option v-for="p in polls" :key="p.id" :value="p.id">
                      {{ p.title }}
                    </option>
                  </select>
                </div>
                <div
                  v-if="polls.find((p) => p.id === activePollId)"
                  class="poll-card"
                >
                  <h3 class="poll-card__title">
                    {{ polls.find((p) => p.id === activePollId).title }}
                  </h3>
                  <div class="poll-card__stats">
                    <span class="poll-stat"
                      >👥 已参与
                      {{ polls.find((p) => p.id === activePollId).total }}
                      人</span
                    >
                  </div>
                  <div class="poll-results">
                    <div
                      v-for="(opt, idx) in polls.find(
                        (p) => p.id === activePollId,
                      ).options"
                      :key="idx"
                      class="poll-bar-item"
                    >
                      <div class="poll-bar-item__label">{{ opt.label }}</div>
                      <div class="poll-bar-item__track">
                        <div
                          class="poll-bar-item__fill"
                          :style="{
                            width:
                              (opt.votes /
                                polls.find((p) => p.id === activePollId)
                                  .total) *
                                100 +
                              '%',
                            background: opt.color,
                          }"
                        />
                      </div>
                      <div class="poll-bar-item__meta">
                        <span class="poll-bar-item__count"
                          >{{ opt.votes }}票</span
                        >
                        <span class="poll-bar-item__percent"
                          >{{
                            Math.round(
                              (opt.votes /
                                polls.find((p) => p.id === activePollId)
                                  .total) *
                                100,
                            )
                          }}%</span
                        >
                      </div>
                    </div>
                  </div>
                </div>
                <button class="poll-action-btn">
                  <span>✏️</span> 创建新投票
                </button>
              </div>

              <!-- 随机抽选 -->
              <div
                v-if="activityTab === 'random-pick'"
                class="activity-section"
              >
                <div class="pick-mode-switch">
                  <button
                    :class="{ 'pick-mode-btn--active': pickMode === 'single' }"
                    class="pick-mode-btn"
                    @click="pickMode = 'single'"
                  >
                    单人抽取
                  </button>
                  <button
                    :class="{ 'pick-mode-btn--active': pickMode === 'group' }"
                    class="pick-mode-btn"
                    @click="pickMode = 'group'"
                  >
                    小组抽取
                  </button>
                </div>
                <div class="pick-roulette">
                  <div
                    v-if="pickingStudent || pickHistory.length > 0"
                    class="pick-result"
                    :class="{ 'pick-result--spinning': isPicking }"
                  >
                    <span class="pick-result__avatar">{{
                      (pickingStudent && pickingStudent.avatar) ||
                      (pickHistory.length > 0 && pickHistory[0].avatar)
                    }}</span>
                    <span class="pick-result__name">{{
                      (pickingStudent && pickingStudent.name) ||
                      (pickHistory.length > 0 && pickHistory[0].name)
                    }}</span>
                  </div>
                  <div
                    v-if="!isPicking && pickHistory.length === 0"
                    class="pick-placeholder"
                  >
                    <span class="pick-placeholder__icon">🎲</span>
                    <span class="pick-placeholder__text"
                      >点击下方按钮开始抽选</span
                    >
                  </div>
                </div>
                <button
                  class="pick-button"
                  :class="{ 'pick-button--running': isPicking }"
                  @click="startRandomPick"
                  :disabled="isPicking"
                >
                  <span>{{ isPicking ? "🎰" : "🎯" }}</span>
                  {{ isPicking ? "抽取中..." : "随机抽选" }}
                </button>
                <div class="student-roster">
                  <h3>📋 学生名单（{{ students.length }}人）</h3>
                  <div class="roster-grid">
                    <div
                      v-for="student in students"
                      :key="student.id"
                      class="roster-item"
                    >
                      <span class="roster-item__avatar">{{
                        student.avatar
                      }}</span>
                      <span class="roster-item__name">{{ student.name }}</span>
                      <button
                        class="roster-item__remove"
                        @click="removeStudent(student.id)"
                        title="移除"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
                <div v-if="pickHistory.length > 0" class="pick-history">
                  <h3>📝 抽选记录</h3>
                  <div class="pick-history-list">
                    <div
                      v-for="(record, idx) in pickHistory.slice(0, 10)"
                      :key="idx"
                      class="pick-history-item"
                    >
                      <span class="pick-history-item__idx">{{ idx + 1 }}</span>
                      <span class="pick-history-item__avatar">{{
                        record.avatar
                      }}</span>
                      <span class="pick-history-item__name">{{
                        record.name
                      }}</span>
                      <span class="pick-history-item__time">{{
                        record.time
                      }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 小组积分 -->
              <div
                v-if="activityTab === 'group-score'"
                class="activity-section"
              >
                <div class="group-scoreboard">
                  <div
                    v-for="group in [...groups].sort(
                      (a, b) => b.score - a.score,
                    )"
                    :key="group.id"
                    class="group-card"
                  >
                    <div
                      class="group-card__rank"
                      :style="{ color: group.color }"
                    >
                      {{
                        [...groups]
                          .sort((a, b) => b.score - a.score)
                          .indexOf(group) + 1
                      }}
                    </div>
                    <div class="group-card__info">
                      <h3
                        class="group-card__name"
                        :style="{ color: group.color }"
                      >
                        {{ group.name }}
                      </h3>
                      <div class="group-card__members">
                        <span
                          v-for="(member, idx) in group.members"
                          :key="idx"
                          class="group-card__member"
                          >{{ member }}</span
                        >
                      </div>
                    </div>
                    <div class="group-card__score-area">
                      <div
                        class="group-card__score"
                        :style="{ color: group.color }"
                      >
                        {{ group.score
                        }}<span class="group-card__score-unit">分</span>
                      </div>
                      <div class="group-card__bar">
                        <div
                          class="group-card__bar-fill"
                          :style="{
                            width: (group.score / 100) * 100 + '%',
                            background: group.color,
                          }"
                        />
                      </div>
                    </div>
                    <div class="group-card__actions">
                      <button
                        class="group-score-btn group-score-btn--add"
                        @click="addGroupScore(group.id, 5)"
                      >
                        +5
                      </button>
                      <button
                        class="group-score-btn group-score-btn--add"
                        @click="addGroupScore(group.id, 1)"
                      >
                        +1
                      </button>
                      <button
                        class="group-score-btn group-score-btn--sub"
                        @click="addGroupScore(group.id, -1)"
                      >
                        −1
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 5. AI总结助手 -->
            <div v-if="activeMenu === 'ai-summary'" class="content-panel">
              <div class="panel-header">
                <h1>
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#8b5cf6"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    style="vertical-align: middle; margin-right: 8px"
                  >
                    <path
                      d="M12 2l1.5 5L18 8l-5 1.5L12 14l-1.5-5L6 8l5-1.5L12 2z"
                    />
                    <path
                      d="M19 17l.5 1.5L21 19l-1.5.5-.5 1.5-.5-1.5L17 19l1.5-.5.5-1.5z"
                    />
                  </svg>
                  AI总结助手
                </h1>
                <p>智能分析学习情况，生成个性化总结</p>
              </div>

              <div class="ai-summaries">
                <div
                  v-for="summary in aiSummaries"
                  :key="summary.id"
                  class="ai-summary-card"
                >
                  <div class="summary-header">
                    <h3>{{ summary.course }}</h3>
                    <div
                      class="mastery-badge"
                      :class="'mastery--' + getMasteryLevel(summary.mastery)"
                    >
                      掌握度 {{ summary.mastery }}%
                    </div>
                  </div>
                  <p class="summary-text">{{ summary.summary }}</p>
                  <div class="key-points">
                    <h4>📌 核心要点</h4>
                    <div class="points-tags">
                      <span
                        v-for="point in summary.keyPoints"
                        :key="point"
                        class="point-tag"
                      >
                        {{ point }}
                      </span>
                    </div>
                  </div>
                  <div class="suggestions-box">
                    <h4>💡 学习建议</h4>
                    <ul>
                      <li
                        v-for="(suggestion, idx) in summary.suggestions"
                        :key="idx"
                      >
                        {{ suggestion }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <div class="ai-actions">
                <button class="ai-btn ai-btn--primary">
                  <span>✨</span>
                  生成新的学习总结
                </button>
                <button class="ai-btn">
                  <span>📊</span>
                  查看完整学习报告
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- 页面底部装饰 -->
    <footer class="lessons-footer">
      <!-- 波浪分隔线 -->
      <div class="footer-wave">
        <svg
          viewBox="0 0 1200 80"
          preserveAspectRatio="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M0 40 C150 10, 300 70, 600 40 C900 10, 1050 70, 1200 40 L1200 80 L0 80 Z"
            class="footer-wave-path footer-wave--front"
          />
          <path
            d="M0 55 C200 25, 400 80, 600 55 C800 30, 1000 80, 1200 55 L1200 80 L0 80 Z"
            class="footer-wave-path footer-wave--back"
          />
        </svg>
      </div>

      <div class="footer-content">
        <!-- 底部装饰光球 -->
        <div class="footer-glow footer-glow--1"></div>
        <div class="footer-glow footer-glow--2"></div>
        <div class="footer-glow footer-glow--3"></div>

        <div class="footer-inner">
          <!-- 品牌区 -->
          <div class="footer-brand">
            <div class="footer-logo">🎓</div>
            <h3>课堂教程</h3>
            <p>
              集成课程资源、数据分析、互动问答<br />与AI总结的一站式智能教学平台
            </p>
          </div>

          <!-- 快速导航 -->
          <div class="footer-nav">
            <h4>功能模块</h4>
            <ul>
              <li
                v-for="item in menuItems"
                :key="item.id"
                @click="switchMenu(item.id)"
              >
                <span v-html="item.icon"></span> {{ item.label }}
              </li>
            </ul>
          </div>

          <!-- 数据概览 -->
          <div class="footer-stats">
            <h4>教学数据</h4>
            <div class="footer-stat-row">
              <div class="footer-stat-item">
                <span class="footer-stat-num">{{ courses.length }}</span>
                <span class="footer-stat-desc">课程资源</span>
              </div>
              <div class="footer-stat-item">
                <span class="footer-stat-num">6</span>
                <span class="footer-stat-desc">学科覆盖</span>
              </div>
              <div class="footer-stat-item">
                <span class="footer-stat-num">5</span>
                <span class="footer-stat-desc">功能模块</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部线 -->
        <div class="footer-bottom">
          <span class="footer-copy">© 2026 课堂教程 · 智能教学平台</span>
          <div class="footer-dots">
            <span class="footer-dot"></span>
            <span class="footer-dot"></span>
            <span class="footer-dot"></span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ==================== 基础布局 ==================== */
.lessons-page {
  min-height: 100vh;
  background: #f7f5f2;
  position: relative;
  font-family:
    system-ui,
    -apple-system,
    "Segoe UI",
    Roboto,
    "Helvetica Neue",
    sans-serif;
}

.lessons-bg {
  position: fixed;
  inset: 0;
  background: radial-gradient(
    800px 400px at 80% -10%,
    rgba(76, 125, 255, 0.05),
    transparent
  );
  pointer-events: none;
  z-index: 0;
}

.lessons-main {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  padding: 100px 24px 24px;
}

.lessons-container {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  min-height: calc(100vh - 120px);
}

/* ==================== 左侧菜单 ==================== */
.sidebar-menu {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: sticky;
  top: 24px;
  height: fit-content;
  max-height: calc(100vh - 48px);
}

.menu-header {
  padding: 28px 24px;
  background: #2d3a50;
  color: white;
  text-align: center;
}

.menu-header h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 8px 0;
}

.menu-header p {
  font-size: 0.85rem;
  opacity: 0.9;
  margin: 0;
}

.menu-list {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  margin-bottom: 8px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.menu-item:focus-visible {
  outline: 2px solid #4c7dff;
  outline-offset: 2px;
}

.menu-item:hover {
  background: rgba(76, 125, 255, 0.05);
  border-color: rgba(76, 125, 255, 0.15);
  transform: translateX(4px);
}

.menu-item--active {
  background: #f2f4f7;
  border-color: transparent;
  border-left: 3px solid #4c7dff;
  border-radius: 12px 8px 8px 12px;
}

.menu-item--active .menu-item__label {
  color: #1e293b;
  font-weight: 600;
}

.menu-item--active .menu-item__arrow {
  opacity: 1;
  transform: translateX(0);
}

.menu-item__icon {
  font-size: 1.5rem;
  transition: transform 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
}
.menu-item__icon svg {
  width: 26px;
  height: 26px;
  transition:
    stroke 0.3s ease,
    filter 0.3s ease;
}
.menu-item--active .menu-item__icon svg {
  filter: drop-shadow(0 1px 4px rgba(76, 125, 255, 0.35));
}

.menu-item__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.menu-item__label {
  font-size: 0.95rem;
  font-weight: 500;
  color: #1e293b;
  transition: color 0.3s ease;
}

.menu-item__desc {
  font-size: 0.75rem;
  color: #6b7280;
}

.menu-item__arrow {
  font-size: 1.2rem;
  color: #94a3b8;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.menu-item:hover .menu-item__arrow {
  opacity: 1;
  color: #4c7dff;
  transform: translateX(4px);
}

.menu-footer {
  padding: 16px;
  border-top: 1px solid rgba(76, 125, 255, 0.1);
}

.stats-card {
  display: flex;
  justify-content: space-around;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #4c7dff;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
}

/* ==================== 右侧内容区域 ==================== */
.content-area {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  min-height: calc(100vh - 120px);
}

.content-wrapper {
  padding: 32px;
  opacity: 1;
  transform: translateY(0);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.content-wrapper--transitioning {
  opacity: 0;
  transform: translateY(10px);
}

.content-wrapper--home {
  padding: 0;
}

.panel-header {
  margin-bottom: 28px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(76, 125, 255, 0.1);
}

.panel-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.panel-header p {
  font-size: 0.95rem;
  color: #475569;
  margin: 0;
}

/* ==================== 主页 ==================== */
.lessons-container--home {
  grid-template-columns: 1fr;
  max-width: 1200px;
  margin: 0 auto;
}

.content-panel--home {
  background: transparent;
  box-shadow: none;
  border: none;
  padding: 0;
  position: relative;
  overflow: hidden;
}

/* Hero 区域 */
.home-hero {
  text-align: center;
  padding: 48px 20px 40px;
  position: relative;
  z-index: 1;
}

.home-hero-badge {
  display: inline-block;
  padding: 4px 14px;
  border-radius: 6px;
  background: #f2f4f7;
  color: #475569;
  font-size: 0.78rem;
  font-weight: 500;
  margin-bottom: 16px;
}

.home-hero-title {
  font-size: 3rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0 0 16px 0;
  letter-spacing: -1px;
}

.float-cap {
  display: inline-block;
  font-size: 0.92em;
  line-height: 1;
  vertical-align: -0.06em;
  margin-right: 10px;
}

.home-hero-subtitle {
  font-size: 1rem;
  color: #475569;
  line-height: 1.7;
  margin: 0 auto 36px;
  max-width: 560px;
}

/* Hero 统计数据 */
.home-stats-row {
  display: flex;
  justify-content: center;
  gap: 32px;
  flex-wrap: wrap;
}

.home-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.home-stat-num {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}

.home-stat-label {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 500;
}

/* 模块卡片区域 */
.home-section {
  padding: 60px 40px 50px;
  position: relative;
  z-index: 1;
}

.home-section-title {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
}

.home-section-desc {
  text-align: center;
  font-size: 0.9rem;
  color: #64748b;
  margin: 0 0 48px 0;
}

/* 3 列等宽网格 */
.home-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1100px;
  margin: 0 auto;
}

.home-card {
  background: white;
  border-radius: 12px;
  padding: 28px 24px 24px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  position: relative;
}

.home-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  border-color: #d1d5db;
}

/* 按模块类型着色 - 统一使用极简标记 */
.home-card .home-card-icon-wrap {
  background: #f2f4f7;
}
.home-card .home-card-badge {
  background: #6b7280;
}
.home-card:hover .home-card-badge {
  background: #4b5563;
}

.home-card .home-card-emoji svg {
  stroke: #6b7280;
}

.home-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.home-card-top-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.home-card-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.home-card:hover .home-card-icon-wrap {
  transform: scale(1.06);
}

.home-card-emoji {
  font-size: 1.8rem;
}
.home-card-emoji svg,
.home-card-icon-wrap svg {
  width: 34px;
  height: 34px;
  stroke-width: 1.6;
  transition:
    stroke 0.3s ease,
    filter 0.3s ease,
    transform 0.3s ease;
}
.home-card:hover .home-card-emoji svg,
.home-card:hover .home-card-icon-wrap svg {
  transform: scale(1.04);
}

.home-card-badge {
  font-size: 0.7rem;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: background 0.3s ease;
}

.home-card-count {
  font-size: 0.72rem;
  color: #6b7280;
  font-weight: 500;
}

.home-card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.home-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.3px;
}

.home-card-desc {
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.65;
  margin: 0;
}

/* 关键词标签 */
.home-card-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.home-keyword {
  font-size: 0.7rem;
  padding: 3px 10px;
  border-radius: 6px;
  background: rgba(76, 125, 255, 0.06);
  color: #4c7dff;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.home-card-footer {
  margin-top: 22px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.home-card-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #4c7dff;
  transition: color 0.25s ease;
}

.home-card:hover .home-card-action {
  color: #1e40af;
}

.home-card-arrow {
  transition: transform 0.3s ease;
  display: inline-block;
  font-size: 0.9rem;
}

.home-card:hover .home-card-arrow {
  transform: translateX(4px);
}

/* 底部提示 */
.home-footer-hint {
  text-align: center;
  padding: 32px 0 12px;
  position: relative;
  z-index: 1;
}

.home-footer-hint span {
  font-size: 0.85rem;
  color: #6b7280;
  background: rgba(107, 114, 128, 0.08);
  padding: 8px 20px;
  border-radius: 20px;
}

@media (max-width: 768px) {
  .home-hero {
    padding: 40px 16px 36px;
  }

  .home-hero-title {
    font-size: 2.2rem;
  }

  .home-stats-row {
    gap: 20px;
  }

  .home-stat-num {
    font-size: 1.5rem;
  }

  .home-section {
    padding: 40px 16px 32px;
  }

  .home-cards {
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .home-card {
    padding: 24px 18px 20px;
  }
}

@media (max-width: 500px) {
  .home-section {
    padding: 32px 12px 24px;
  }

  .home-cards {
    grid-template-columns: 1fr;
    gap: 20px;
    max-width: 380px;
    margin: 0 auto;
  }

  .home-hero-title {
    font-size: 1.8rem;
  }

  .home-stats-row {
    gap: 12px;
  }
}

/* ==================== 课程资源样式 ==================== */
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.course-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(76, 125, 255, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(76, 125, 255, 0.15);
}

.course-cover {
  position: relative;
  height: 160px;
  overflow: hidden;
  background: #f1f5f9;
}

/* 封面图片 */
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.35s ease;
}

.course-card:hover .cover-img {
  transform: scale(1.06);
}

/* 底部渐变遮罩，让标签可读 */
.cover-gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.45) 0%, transparent 100%);
  pointer-events: none;
  z-index: 1;
}

/* 底部学科标签 */
.cover-subject-tag {
  position: absolute;
  bottom: 10px;
  left: 12px;
  padding: 3px 10px;
  border-radius: 5px;
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  z-index: 2;
}

.course-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 52px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
  z-index: 2;
}

.course-card:hover .course-overlay {
  opacity: 1;
}

@media (hover: none) {
  .course-overlay {
    opacity: 0;
  }
}

.detail-hint {
  padding: 8px 22px;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 20px;
  transition: transform 0.3s ease;
  box-shadow: 0 4px 15px rgba(76, 125, 255, 0.4);
}

.course-card:hover .detail-hint {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(76, 125, 255, 0.5);
}

.course-video-count {
  position: absolute;
  bottom: 10px;
  right: 12px;
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.55);
  color: white;
  font-size: 0.72rem;
  border-radius: 5px;
  font-weight: 500;
  z-index: 2;
}

.course-info {
  padding: 16px;
}

.course-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.tag {
  padding: 4px 10px;
  background: rgba(76, 125, 255, 0.1);
  color: #4c7dff;
  font-size: 0.75rem;
  border-radius: 20px;
  font-weight: 500;
}

.course-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.course-desc {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.course-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.subject-badge {
  padding: 4px 10px;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  font-size: 0.75rem;
  border-radius: 4px;
  font-weight: 500;
}

.grade-text {
  font-size: 0.8rem;
  color: #94a3b8;
}

/* ==================== 视频详情页样式 ==================== */
.video-detail-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

/* 顶部栏 */
.video-detail-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #475569;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  width: fit-content;
}

.back-btn:hover {
  background: #f8fafc;
  border-color: #4c7dff;
  color: #4c7dff;
}

.back-arrow {
  font-size: 1rem;
  font-weight: 700;
}

.video-detail-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-radius: 16px;
  padding: 24px 28px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  border-left: 5px solid;
}

.video-detail-title-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}

.video-detail-icon {
  font-size: 2.5rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-detail-icon svg {
  width: 40px;
  height: 40px;
  filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.1));
}

.video-detail-course-name {
  font-size: 1.35rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px 0;
  line-height: 1.3;
}

.video-detail-meta {
  font-size: 0.82rem;
  color: #64748b;
  font-weight: 400;
}

.video-detail-subject-badge {
  padding: 6px 14px;
  border-radius: 8px;
  color: white;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

/* 视频网格 */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 22px;
}

.video-card {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(76, 125, 255, 0.08);
  cursor: pointer;
  transition: all 0.3s ease;
}

.video-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(76, 125, 255, 0.12);
  border-color: rgba(76, 125, 255, 0.2);
}

.video-cover {
  position: relative;
  height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.video-cover-icon {
  font-size: 2.8rem;
  opacity: 0.85;
  position: relative;
  z-index: 2;
  transition: transform 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-cover-icon svg {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
}
.video-cover-icon svg line,
.video-cover-icon svg path,
.video-cover-icon svg circle,
.video-cover-icon svg rect,
.video-cover-icon svg ellipse,
.video-cover-icon svg polyline,
.video-cover-icon svg polygon {
  stroke: white;
}

.video-card:hover .video-cover-icon {
  transform: scale(1.1);
}

.video-cover-deco {
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%) rotate(-15deg);
  font-size: 1.8rem;
  font-weight: 800;
  opacity: 0.08;
  letter-spacing: 2px;
  pointer-events: none;
  z-index: 1;
}

.video-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: absolute;
  inset: 0;
}

.video-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 3;
}

.video-card:hover .video-overlay {
  opacity: 1;
}

.video-play-btn {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
  transition: transform 0.3s ease;
  box-shadow: 0 4px 15px rgba(76, 125, 255, 0.4);
}

.video-card:hover .video-play-btn {
  transform: scale(1.1);
}

.video-duration-badge {
  position: absolute;
  bottom: 8px;
  right: 10px;
  padding: 3px 9px;
  background: rgba(0, 0, 0, 0.65);
  color: white;
  font-size: 0.7rem;
  border-radius: 4px;
  font-weight: 500;
  z-index: 4;
}

.video-info {
  padding: 14px 16px;
}

.video-title-text {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 10px 0;
  line-height: 1.45;
}

.video-sub-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-subject-label {
  padding: 3px 9px;
  background: rgba(76, 125, 255, 0.08);
  color: #4c7dff;
  font-size: 0.7rem;
  border-radius: 6px;
  font-weight: 500;
}

.video-grade-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 400;
}

/* ===== 视频列表页面（课程→选择视频） ===== */
.video-list-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-list-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(76, 125, 255, 0.06);
}

.video-list-header .back-btn,
.bili-page-header .back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid rgba(76, 125, 255, 0.15);
  border-radius: 10px;
  background: white;
  color: #4c7dff;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.video-list-header .back-btn:hover,
.bili-page-header .back-btn:hover {
  background: rgba(76, 125, 255, 0.06);
  border-color: #4c7dff;
}

.video-list-header .back-arrow,
.bili-page-header .back-arrow {
  font-size: 1.1rem;
  line-height: 1;
}

/* 响应式 */
@media (max-width: 768px) {
  .video-detail-title-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 18px 20px;
  }

  .video-detail-subject-badge {
    align-self: flex-start;
  }

  .video-grid {
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }
}

@media (max-width: 500px) {
  .video-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .video-detail-course-name {
    font-size: 1.15rem;
  }
}

/* ==================== B站风格视频详情页 ==================== */
.bili-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 顶部导航 */
.bili-page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(76, 125, 255, 0.06);
}
.bili-page-course-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #475569;
}
.bili-page-course-info strong {
  color: #1e293b;
  font-weight: 600;
  margin-right: 6px;
}
.bili-page-course-info span {
  color: #6b7280;
  font-size: 0.78rem;
}

/* 左右布局 */
.bili-page-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  align-items: start;
}

/* 左侧播放器 */
.bili-page-player {
  background: #000;
  border-radius: 14px;
  overflow: hidden;
  position: sticky;
  top: 16px;
}
.bili-page-player .bili-player-video-wrap {
  aspect-ratio: 16 / 9;
  background: #000;
  cursor: pointer;
  position: relative;
  max-height: 60vh;
}
/* 模糊填充背景：撑满统一画面，竖屏视频不再显得小 */
.bili-page-player .bili-player-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.15);
  filter: blur(28px) saturate(1.3) brightness(0.85);
  opacity: 0.9;
  pointer-events: none;
  z-index: 0;
}
.bili-page-player .bili-player-video {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

/* 右侧播放列表 */
.bili-page-playlist {
  background: white;
  border: 1px solid rgba(76, 125, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.bili-playlist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(76, 125, 255, 0.06);
  flex-shrink: 0;
}
.bili-playlist-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}
.bili-playlist-count {
  font-size: 0.72rem;
  color: #94a3b8;
}
.bili-playlist-list {
  overflow-y: auto;
  max-height: 480px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.bili-playlist-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  border: 1.5px solid transparent;
}
.bili-playlist-item:hover {
  background: rgba(76, 125, 255, 0.04);
}
.bili-playlist-item.active {
  background: rgba(76, 125, 255, 0.07);
  border-color: rgba(76, 125, 255, 0.18);
}
.bili-playlist-num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(76, 125, 255, 0.06);
  color: #94a3b8;
  font-size: 0.72rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 8px;
}
.bili-playlist-item.active .bili-playlist-num {
  background: #4c7dff;
  color: white;
}
.bili-playlist-cover {
  width: 120px;
  height: 67px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f1f5f9;
  position: relative;
}
.bili-playlist-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.bili-playlist-play-icon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  color: white;
  font-size: 1.2rem;
  opacity: 0;
  transition: opacity 0.15s;
  pointer-events: none;
}
.bili-playlist-item:hover .bili-playlist-play-icon {
  opacity: 1;
}
.bili-playlist-item.active .bili-playlist-play-icon {
  opacity: 0;
}
.bili-playlist-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding-top: 4px;
}
.bili-playlist-name {
  font-size: 0.78rem;
  font-weight: 500;
  color: #334155;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.bili-playlist-item.active .bili-playlist-name {
  color: #4c7dff;
}
.bili-playlist-meta {
  font-size: 0.68rem;
  color: #94a3b8;
}

/* 播放器弹窗过渡（保留但不使用） */
.player-enter-active {
  transition: opacity 0.25s;
}
.player-leave-active {
  transition: opacity 0.2s;
}
.player-enter-from {
  opacity: 0;
}
.player-leave-to {
  opacity: 0;
}

/* ===== 播放器控制栏样式 ===== */

/* 控制按钮行 - 左右分布 */
.bili-controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.bili-controls-left,
.bili-controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 通用按钮 */
.bili-btn {
  background: none;
  border: none;
  color: #ddd;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: color 0.12s;
}
.bili-btn:hover {
  color: #fff;
}

/* 时间显示 */
.bili-time {
  font-size: 0.78rem;
  color: #bbb;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.3px;
  user-select: none;
}

/* 进度条 */
.bili-progress-bar {
  position: relative;
  height: 6px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  cursor: pointer;
  margin: 0 0 10px;
  top: -4px;
  transition: height 0.12s;
}
.bili-progress-bar:hover {
  height: 8px;
}
.bili-progress-buffer {
  position: absolute;
  inset: 0;
  width: 0%;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  transition: width 0.3s;
}
.bili-progress-played {
  position: absolute;
  inset: 0;
  width: 0%;
  background: linear-gradient(90deg, #4c7dff, #7c9fff);
  border-radius: 3px;
  transition: width 0.1s linear;
}
.bili-progress-thumb {
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.12s;
}
.bili-progress-bar:hover .bili-progress-thumb {
  opacity: 1;
}

/* 中央播放按钮 */
.bili-center-play {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.18);
  transition: opacity 0.35s;
  z-index: 2;
}
.bili-center-play.is-hidden {
  opacity: 0;
  pointer-events: none;
}
.bili-center-play svg {
  width: 56px;
  height: 56px;
  filter: drop-shadow(0 4px 16px rgba(0, 0, 0, 0.4));
  opacity: 0.85;
}

/* 音量控件 */
.bili-volume-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.bili-volume-slider {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(30, 30, 30, 0.95);
  padding: 8px 4px;
  border-radius: 8px;
  margin-bottom: 6px;
}
.bili-volume-slider input[type="range"] {
  writing-mode: vertical-lr;
  direction: rtl;
  height: 70px;
  width: 4px;
  cursor: pointer;
  appearance: slider-vertical;
  accent-color: #4c7dff;
}

/* 三点菜单 */
.bili-more-wrap {
  position: relative;
}
.bili-more-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  background: rgba(30, 30, 30, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 8px;
  min-width: 180px;
  margin-bottom: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
}
.bili-menu-section {
  padding: 4px 0;
}
.bili-menu-label {
  font-size: 0.7rem;
  color: #999;
  padding: 4px 10px 6px;
  font-weight: 500;
}
.bili-speed-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  padding: 0 4px;
}
.bili-speed-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #ccc;
  padding: 5px 0;
  border-radius: 6px;
  font-size: 0.76rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.1s;
}
.bili-speed-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
.bili-speed-btn.active {
  background: #4c7dff;
  border-color: #4c7dff;
  color: #fff;
}
.bili-menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 6px 0;
}
.bili-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  background: none;
  border: none;
  color: #ccc;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.1s;
}
.bili-menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

/* 菜单动画 */
.more-menu-enter-active {
  transition:
    opacity 0.12s,
    transform 0.12s;
}
.more-menu-leave-active {
  transition:
    opacity 0.1s,
    transform 0.1s;
}
.more-menu-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.more-menu-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

/* 播放器控制栏 - 绝对覆盖在视频底部 */
.bili-page-player .bili-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.92) 0%,
    rgba(0, 0, 0, 0.75) 60%,
    transparent 100%
  );
  padding: 32px 16px 10px;
  transition: opacity 0.3s;
  z-index: 10;
}
.bili-page-player .bili-controls.is-hidden {
  opacity: 0;
  pointer-events: none;
}

/* 响应式 - 播放器布局 */
/* 左侧播放器 + 信息/配套资源列 */
.bili-page-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* 视频信息 + 配套备课资源卡片 */
.video-info-card {
  background: #fff;
  border: 1px solid rgba(76, 125, 255, 0.08);
  border-radius: 14px;
  padding: 18px 20px 20px;
}
.video-info-title {
  font-size: 1.02rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.45;
}
.video-info-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}
.video-info-tag {
  font-size: 0.72rem;
  color: #4c7dff;
  background: rgba(76, 125, 255, 0.08);
  padding: 2px 10px;
  border-radius: 999px;
}
.video-info-meta-item {
  font-size: 0.76rem;
  color: #64748b;
}
.video-info-desc {
  margin: 12px 0 0;
  font-size: 0.85rem;
  line-height: 1.75;
  color: #475569;
}
.video-focus {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}
.video-focus-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.76rem;
  font-weight: 600;
  color: #4c7dff;
  margin-right: 2px;
}
.video-focus-tag {
  font-size: 0.74rem;
  color: #334155;
  background: rgba(76, 125, 255, 0.07);
  border: 1px solid rgba(76, 125, 255, 0.14);
  padding: 3px 10px;
  border-radius: 999px;
}
.video-info-divider {
  height: 1px;
  background: rgba(76, 125, 255, 0.07);
  margin: 16px 0;
}
.video-kit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.video-kit-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.86rem;
  font-weight: 600;
  color: #1e293b;
}
.video-kit-title svg {
  color: #4c7dff;
}
.video-kit-hint {
  font-size: 0.72rem;
  color: #94a3b8;
}
.video-kit-btns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 12px;
}
.video-kit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 6px;
  font-size: 0.8rem;
  color: #4c7dff;
  background: rgba(76, 125, 255, 0.07);
  border: 1px solid rgba(76, 125, 255, 0.16);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.video-kit-btn:hover {
  background: #4c7dff;
  color: #fff;
  border-color: #4c7dff;
}

@media (max-width: 1100px) {
  .bili-page-layout {
    grid-template-columns: 1fr 240px;
    gap: 16px;
  }
}

@media (max-width: 900px) {
  .bili-page-layout {
    grid-template-columns: 1fr;
  }
  .bili-page-player {
    position: static;
  }
  .bili-playlist-list {
    max-height: 300px;
  }
  .bili-playlist-cover {
    width: 100px;
    height: 56px;
  }
  /* 视频列表页面的网格适配 */
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
}

@media (max-width: 500px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
  .video-kit-btns {
    grid-template-columns: 1fr;
  }
  .video-list-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}

/* ==================== 课程分析样式 ==================== */
.analysis-dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 下拉筛选栏 */
.filter-search-bar {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  flex: 1;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 130px;
  flex: 1;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.filter-select {
  padding: 10px 14px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #1e293b;
  background: white;
  outline: none;
  cursor: pointer;
  transition: all 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}

.filter-select:focus {
  border-color: #4c7dff;
  box-shadow: 0 0 0 3px rgba(76, 125, 255, 0.1);
}

.filter-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.filter-btn {
  padding: 10px 22px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.filter-btn-go {
  background: linear-gradient(135deg, #4c7dff, #6366f1);
  color: white;
}

.filter-btn-go:hover {
  box-shadow: 0 4px 12px rgba(76, 125, 255, 0.3);
  transform: translateY(-1px);
}

.filter-btn-reset {
  background: #f1f5f9;
  color: #64748b;
}

.filter-btn-reset:hover:not(:disabled) {
  background: #e2e8f0;
  color: #475569;
}

.filter-btn-reset:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.result-count {
  font-size: 0.8rem;
  color: #4c7dff;
  font-weight: 500;
}

/* 筛选结果提示 + 课程选择器 */
.course-selector-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.course-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: white;
  border: 1.5px solid #e5e7eb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
}

.course-chip:hover {
  border-color: #4c7dff;
  box-shadow: 0 2px 8px rgba(76, 125, 255, 0.1);
}

.course-chip.active {
  background: linear-gradient(135deg, #4c7dff, #6366f1);
  border-color: transparent;
}

.course-chip.active .chip-subject,
.course-chip.active .chip-title {
  color: white;
}

.chip-subject {
  font-size: 0.7rem;
  padding: 2px 8px;
  background: rgba(76, 125, 255, 0.1);
  border-radius: 4px;
  font-weight: 600;
  color: #4c7dff;
  white-space: nowrap;
}

.course-chip.active .chip-subject {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.chip-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
}

/* 课程信息卡片 */
.course-info-card {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
}

.info-card-left h2 {
  font-size: 1.3rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.info-card-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.info-tag {
  font-size: 0.75rem;
  padding: 4px 10px;
  background: rgba(76, 125, 255, 0.08);
  border-radius: 6px;
  color: #4c7dff;
  font-weight: 500;
}

.info-card-desc {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0;
}

.info-badge {
  font-size: 0.75rem;
  padding: 6px 14px;
  border-radius: 20px;
  color: white;
  font-weight: 600;
  white-space: nowrap;
}

/* 雷达图区域 */
.radar-section {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.radar-chart-container {
  background: white;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(76, 125, 255, 0.1);
}

/* 要点 + 建议行 */
.tips-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.tips-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
}

.tips-card h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px 0;
}

.keypoints-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keypoints-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.5;
}

.kp-index {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #4c7dff, #6366f1);
  color: white;
  border-radius: 50%;
  font-size: 0.7rem;
  font-weight: 700;
}

.design-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.design-item {
  padding: 14px;
  border-radius: 10px;
}

.design-item.strength {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.design-item.improvement {
  background: #fffbeb;
  border: 1px solid #fde68a;
}

.design-item.suggestions {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.design-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 6px;
  color: #475569;
}

.design-item p {
  font-size: 0.82rem;
  color: #475569;
  margin: 0;
  line-height: 1.5;
}

.design-item ul {
  list-style: disc;
  padding-left: 18px;
  margin: 0;
}

.design-item ul li {
  font-size: 0.8rem;
  color: #475569;
  margin-bottom: 4px;
  line-height: 1.4;
}

.chart {
  width: 100%;
  height: 380px;
}

@media (max-width: 900px) {
  .radar-section,
  .tips-row {
    grid-template-columns: 1fr;
  }

  .course-selector-bar {
    flex-direction: column;
  }

  .course-chip {
    width: 100%;
  }
}

/* ==================== 边问边答样式 ==================== */
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.qa-item {
  background: white;
  border-radius: 16px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.qa-item:hover {
  box-shadow: 0 4px 12px rgba(76, 125, 255, 0.1);
}

.qa-item--expanded {
  border-color: rgba(76, 125, 255, 0.3);
}

.qa-question {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.qa-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.qa-icon--answer {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
}

.qa-question p {
  flex: 1;
  font-size: 1rem;
  font-weight: 500;
  color: #1e293b;
  margin: 0;
}

.qa-toggle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(76, 125, 255, 0.1);
  color: #4c7dff;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.qa-item--expanded .qa-toggle {
  background: #4c7dff;
  color: white;
  transform: rotate(180deg);
}

.qa-answer {
  display: flex;
  gap: 16px;
  padding: 0 20px 20px 20px;
  border-top: 1px solid rgba(76, 125, 255, 0.1);
  margin-top: -10px;
  padding-top: 20px;
}

.qa-answer-content {
  flex: 1;
}

.qa-answer-content p {
  font-size: 0.95rem;
  color: #475569;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.qa-related {
  font-size: 0.8rem;
  color: #4c7dff;
  background: rgba(76, 125, 255, 0.1);
  padding: 4px 12px;
  border-radius: 20px;
}

.qa-input-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
}

.qa-input-section h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px 0;
}

.qa-input-box {
  display: flex;
  gap: 12px;
}

.qa-input-box input {
  flex: 1;
  padding: 14px 20px;
  border: 1px solid rgba(76, 125, 255, 0.2);
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.qa-input-box input:focus {
  border-color: #4c7dff;
  box-shadow: 0 0 0 3px rgba(76, 125, 255, 0.1);
}

.submit-btn {
  padding: 14px 28px;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(76, 125, 255, 0.3);
}

/* ==================== 课后追问样式 ==================== */
.topics-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.topic-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  transition: all 0.3s ease;
}

.topic-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(76, 125, 255, 0.1);
}

.topic-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.topic-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.topic-time {
  font-size: 0.8rem;
  color: #94a3b8;
}

.topic-content {
  font-size: 0.95rem;
  color: #64748b;
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.topic-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topic-author {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #64748b;
}

.author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e8e4ff;
  color: #5b4ad0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.topic-stats {
  display: flex;
  gap: 16px;
  font-size: 0.85rem;
  color: #94a3b8;
}

.new-topic-btn {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.new-topic-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(76, 125, 255, 0.3);
}

.new-topic-btn span {
  font-size: 1.5rem;
}

/* ==================== AI总结助手样式 ==================== */
.ai-summaries {
  display: flex;
  flex-direction: column;
  gap: 24px;
  margin-bottom: 32px;
}

.ai-summary-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(76, 125, 255, 0.1);
  transition: all 0.3s ease;
}

.ai-summary-card:hover {
  box-shadow: 0 8px 24px rgba(76, 125, 255, 0.1);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.summary-header h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.mastery-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.mastery--excellent {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.mastery--good {
  background: rgba(76, 125, 255, 0.1);
  color: #4c7dff;
}

.mastery--average {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}

.mastery--needs-work {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.summary-text {
  font-size: 0.95rem;
  color: #475569;
  margin: 0 0 20px 0;
  line-height: 1.6;
}

.key-points {
  margin-bottom: 20px;
}

.key-points h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.points-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.point-tag {
  padding: 6px 14px;
  background: rgba(76, 125, 255, 0.1);
  color: #4c7dff;
  font-size: 0.8rem;
  border-radius: 20px;
  font-weight: 500;
}

.suggestions-box {
  padding: 16px;
  background: linear-gradient(135deg, #fefce8 0%, #fef9c3 100%);
  border-radius: 12px;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.suggestions-box h4 {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.suggestions-box ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions-box li {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 6px;
  line-height: 1.5;
}

.ai-actions {
  display: flex;
  gap: 16px;
}

.ai-btn {
  flex: 1;
  padding: 16px 24px;
  background: white;
  border: 1px solid rgba(76, 125, 255, 0.2);
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.ai-btn:hover {
  border-color: #4c7dff;
  color: #4c7dff;
  transform: translateY(-2px);
}

.ai-btn--primary {
  background: linear-gradient(135deg, #4c7dff 0%, #6366f1 100%);
  color: white;
  border-color: transparent;
}

.ai-btn--primary:hover {
  color: white;
  box-shadow: 0 8px 16px rgba(76, 125, 255, 0.3);
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 1200px) {
  .lessons-container {
    grid-template-columns: 260px 1fr;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .suggestion-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .lessons-main {
    padding: 88px 16px 16px;
  }

  .lessons-container {
    grid-template-columns: 1fr;
  }

  .sidebar-menu {
    position: relative;
    top: 0;
    max-height: none;
  }

  .menu-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px;
  }

  .menu-item {
    flex: 1;
    min-width: 140px;
    margin-bottom: 0;
  }

  .menu-item__desc {
    display: none;
  }

  .content-wrapper {
    padding: 20px;
  }

  .panel-header h1 {
    font-size: 1.4rem;
  }

  .course-grid {
    grid-template-columns: 1fr;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 44px;
    height: 44px;
    font-size: 1.5rem;
  }

  .stat-number {
    font-size: 1.4rem;
  }

  .ai-actions {
    flex-direction: column;
  }
}

/* ==================== 页面底部装饰 ==================== */
.lessons-footer {
  position: relative;
  z-index: 1;
  margin-top: 60px;
}

/* 波浪分隔线 */
.footer-wave {
  position: relative;
  width: 100%;
  height: 80px;
  overflow: hidden;
  line-height: 0;
}

.footer-wave svg {
  width: 100%;
  height: 100%;
}

.footer-wave-path {
  fill: #f8fafc;
}

.footer-wave--front {
  fill: rgba(76, 125, 255, 0.04);
}

.footer-wave--back {
  fill: rgba(99, 102, 241, 0.02);
}

/* 底部内容区 */
.footer-content {
  position: relative;
  background: linear-gradient(
    180deg,
    rgba(76, 125, 255, 0.03) 0%,
    rgba(99, 102, 241, 0.05) 40%,
    rgba(15, 23, 42, 0.03) 100%
  );
  border-top: 1px solid rgba(76, 125, 255, 0.06);
  padding: 60px 24px 32px;
  overflow: hidden;
}

/* 底部光球装饰 */
.footer-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.12;
  pointer-events: none;
}

.footer-glow--1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(76, 125, 255, 0.5), transparent);
  top: -80px;
  left: 10%;
  animation: footerGlow1 12s ease-in-out infinite alternate;
}

.footer-glow--2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.4), transparent);
  bottom: -40px;
  right: 5%;
  animation: footerGlow2 15s ease-in-out infinite alternate;
}

.footer-glow--3 {
  width: 250px;
  height: 250px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.25), transparent);
  top: 30%;
  right: 40%;
  animation: footerGlow3 10s ease-in-out infinite alternate;
}

@keyframes footerGlow1 {
  0% {
    transform: translate(0, 0) scale(1);
  }
  100% {
    transform: translate(40px, -25px) scale(1.1);
  }
}

@keyframes footerGlow2 {
  0% {
    transform: translate(0, 0) scale(1);
  }
  100% {
    transform: translate(-30px, 20px) scale(1.12);
  }
}

@keyframes footerGlow3 {
  0% {
    transform: translate(0, 0) scale(1);
  }
  100% {
    transform: translate(15px, -15px) scale(1.08);
  }
}

.footer-inner {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 48px;
}

/* 品牌区 */
.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-logo {
  font-size: 2.4rem;
  margin-bottom: 4px;
}

.footer-brand h3 {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.footer-brand p {
  font-size: 0.82rem;
  color: #64748b;
  line-height: 1.7;
  margin: 0;
}

/* 导航 */
.footer-nav h4,
.footer-stats h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
  margin: 0 0 16px 0;
  letter-spacing: 0.5px;
}

.footer-nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-nav li {
  font-size: 0.82rem;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  padding: 4px 0;
}

.footer-nav li:hover {
  color: #4c7dff;
  transform: translateX(4px);
}

/* 数据概览 */
.footer-stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.footer-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 8px;
  background: rgba(76, 125, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(76, 125, 255, 0.06);
}

.footer-stat-num {
  font-size: 1.3rem;
  font-weight: 700;
  color: #4c7dff;
  line-height: 1;
}

.footer-stat-desc {
  font-size: 0.7rem;
  color: #94a3b8;
}

/* 底部线 */
.footer-bottom {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 40px auto 0;
  padding-top: 20px;
  border-top: 1px solid rgba(76, 125, 255, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-copy {
  font-size: 0.78rem;
  color: #94a3b8;
}

.footer-dots {
  display: flex;
  gap: 6px;
}

.footer-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #c7d2fe;
  animation: dotPulse 2s ease-in-out infinite;
}

.footer-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.footer-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dotPulse {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.5);
  }
}

@media (max-width: 768px) {
  .lessons-footer {
    margin-top: 40px;
  }

  .footer-content {
    padding: 40px 16px 24px;
  }

  .footer-inner {
    grid-template-columns: 1fr;
    gap: 28px;
  }

  .footer-stat-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .footer-bottom {
    flex-direction: column;
    gap: 12px;
    text-align: center;
  }
}
/* ==================== 课堂互动样式 ==================== */
.classroom-activity-panel {
}

.panel-header--activity h1 {
  background: linear-gradient(135deg, #667eea, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.activity-tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}

.activity-tab {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 12px 16px;
  background: rgba(255, 255, 255, 0.6);
  border: 2px solid transparent;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
}

.activity-tab:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.12);
}

.activity-tab--active {
  background: rgba(255, 255, 255, 0.95);
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
}

.activity-tab__icon {
  font-size: 1.6rem;
}
.activity-tab__text {
  text-align: center;
}
.activity-tab__label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e293b;
}
.activity-tab__desc {
  display: block;
  font-size: 0.7rem;
  color: #94a3b8;
  margin-top: 2px;
}

.activity-section {
  animation: fadeSlideIn 0.35s ease;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 随堂抢答 */
.qa-control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
}
.qa-progress {
  flex: 1;
}
.qa-progress__label {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 6px;
  display: block;
}
.qa-progress__bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}
.qa-progress__fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #10b981);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.qa-timer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  transition: all 0.3s ease;
}
.qa-timer--running {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
}
.qa-timer--expired {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
  animation: timer-pulse 0.6s ease infinite;
}
@keyframes timer-pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}
.qa-timer__icon {
  font-size: 1.2rem;
}
.qa-timer__value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  font-variant-numeric: tabular-nums;
}

.qa-question-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.6);
  margin-bottom: 20px;
}
.qa-question-card__header {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
}
.qa-question-card__num {
  font-size: 1.1rem;
  font-weight: 700;
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  padding: 4px 12px;
  border-radius: 8px;
}
.qa-question-card__type {
  font-size: 0.8rem;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
}
.qa-question-card__text {
  font-size: 1.15rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.6;
  margin: 0 0 20px 0;
}
.qa-question-card__options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.qa-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.6);
  transition: all 0.25s ease;
  cursor: pointer;
}
.qa-option:hover:not(.qa-option--correct):not(.qa-option--wrong) {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}
.qa-option--selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}
.qa-option--correct {
  border-color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
}
.qa-option--wrong {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
  opacity: 0.6;
}
.qa-option__letter {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: #f1f5f9;
  font-weight: 700;
  font-size: 0.8rem;
  color: #64748b;
  flex-shrink: 0;
}
.qa-option--correct .qa-option__letter {
  background: #8b5cf6;
  color: #fff;
}
.qa-option__text {
  font-size: 0.9rem;
  color: #334155;
}

.qa-explanation {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-top: 16px;
  padding: 14px 16px;
  background: rgba(102, 126, 234, 0.06);
  border-radius: 10px;
  border-left: 3px solid #667eea;
}
.qa-explanation__icon {
  font-size: 1rem;
  flex-shrink: 0;
  margin-top: 1px;
}
.qa-explanation p {
  font-size: 0.85rem;
  color: #475569;
  margin: 0;
  line-height: 1.5;
}

.qa-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.qa-action-btn {
  padding: 10px 20px;
  border-radius: 12px;
  border: none;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}
.qa-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.qa-action-btn--primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}
.qa-action-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(102, 126, 234, 0.4);
}
.qa-action-btn--secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #475569;
  border: 1px solid #e2e8f0;
}
.qa-action-btn--secondary:hover:not(:disabled) {
  background: #f8fafc;
}
.qa-action-btn--danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
}
.qa-action-btn--reveal {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.qa-action-btn--reset {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
  color: #fff;
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
}
.qa-action-btn--reset:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(6, 182, 212, 0.4);
}

.qa-leaderboard {
  margin-top: 8px;
}
.qa-leaderboard h3 {
  font-size: 0.95rem;
  color: #1e293b;
  margin-bottom: 12px;
}
.qa-leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.qa-leaderboard-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid #e2e8f0;
  transition: all 0.25s ease;
}
.qa-leaderboard-item--top {
  background: linear-gradient(
    135deg,
    rgba(255, 215, 0, 0.08),
    rgba(255, 255, 255, 0.6)
  );
  border-color: rgba(245, 158, 11, 0.3);
}
.qa-leaderboard-item__rank {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.85rem;
  background: #f1f5f9;
  color: #64748b;
}
.qa-leaderboard-item--top:nth-child(1) .qa-leaderboard-item__rank {
  background: #fbbf24;
  color: #fff;
}
.qa-leaderboard-item--top:nth-child(2) .qa-leaderboard-item__rank {
  background: #94a3b8;
  color: #fff;
}
.qa-leaderboard-item--top:nth-child(3) .qa-leaderboard-item__rank {
  background: #d97706;
  color: #fff;
}
.qa-leaderboard-item__name {
  flex: 1;
  font-weight: 600;
  font-size: 0.9rem;
  color: #1e293b;
}
.qa-leaderboard-item__score {
  font-weight: 700;
  font-size: 0.9rem;
  color: #667eea;
}
.qa-leaderboard-item__time {
  font-size: 0.8rem;
  color: #94a3b8;
  font-variant-numeric: tabular-nums;
}

/* 实时投票 */
.poll-selector {
  margin-bottom: 24px;
}
.poll-selector label {
  font-size: 0.85rem;
  color: #64748b;
  margin-right: 10px;
}
.poll-selector select {
  padding: 10px 16px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  color: #1e293b;
  min-width: 320px;
  cursor: pointer;
}

.poll-card {
  background: rgba(255, 255, 255, 0.85);
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(226, 232, 240, 0.6);
  margin-bottom: 20px;
}
.poll-card__title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px 0;
}
.poll-card__stats {
  margin-bottom: 20px;
}
.poll-stat {
  font-size: 0.8rem;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 4px 12px;
  border-radius: 20px;
}

.poll-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.poll-bar-item {
  display: flex;
  align-items: center;
  gap: 14px;
}
.poll-bar-item__label {
  width: 140px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #334155;
  flex-shrink: 0;
}
.poll-bar-item__track {
  flex: 1;
  height: 12px;
  background: #f1f5f9;
  border-radius: 6px;
  overflow: hidden;
}
.poll-bar-item__fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  min-width: 4px;
}
.poll-bar-item__meta {
  display: flex;
  gap: 10px;
  align-items: center;
  width: 80px;
  flex-shrink: 0;
}
.poll-bar-item__count {
  font-size: 0.8rem;
  color: #64748b;
}
.poll-bar-item__percent {
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
}

.poll-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.25s ease;
}
.poll-action-btn:hover {
  border-color: #667eea;
  color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

/* 随机抽选 */
.pick-mode-switch {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  justify-content: center;
}
.pick-mode-btn {
  padding: 10px 24px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.25s ease;
}
.pick-mode-btn--active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.08);
  color: #667eea;
}

.pick-roulette {
  min-height: 180px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 20px;
  border: 2px dashed #e2e8f0;
  margin-bottom: 20px;
}
.pick-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.pick-result--spinning {
  animation: pick-spin 0.06s linear infinite;
}
@keyframes pick-spin {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.06);
  }
  100% {
    transform: scale(1);
  }
}
.pick-result__avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
}
.pick-result__name {
  font-size: 1.3rem;
  font-weight: 700;
  color: #2d3748;
}
.pick-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.pick-placeholder__icon {
  font-size: 3rem;
  opacity: 0.4;
}
.pick-placeholder__text {
  font-size: 0.9rem;
  color: #94a3b8;
}

.pick-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 0 auto 28px;
  padding: 14px 40px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  font-size: 1.05rem;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 6px 24px rgba(245, 158, 11, 0.35);
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
}
.pick-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 32px rgba(245, 158, 11, 0.5);
}
.pick-button--running {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 6px 24px rgba(239, 68, 68, 0.35);
}

.student-roster {
  margin-bottom: 24px;
}
.student-roster h3 {
  font-size: 0.9rem;
  color: #475569;
  margin-bottom: 12px;
}
.roster-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}
.roster-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}
.roster-item:hover {
  border-color: #667eea;
}
.roster-item__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #e8e4ff;
  color: #5b4ad0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}
.roster-item__name {
  font-size: 0.85rem;
  font-weight: 500;
  color: #1e293b;
  flex: 1;
}
.roster-item__remove {
  opacity: 0;
  transition: opacity 0.2s;
  border: none;
  background: none;
  color: #ef4444;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 2px 4px;
}
.roster-item:hover .roster-item__remove {
  opacity: 1;
}

.pick-history h3 {
  font-size: 0.9rem;
  color: #475569;
  margin-bottom: 10px;
}
.pick-history-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pick-history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
}
.pick-history-item__idx {
  color: #94a3b8;
  width: 20px;
}
.pick-history-item__avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e8e4ff;
  color: #5b4ad0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.65rem;
  font-weight: 600;
  flex-shrink: 0;
}
.pick-history-item__name {
  flex: 1;
  font-weight: 500;
  color: #1e293b;
}
.pick-history-item__time {
  color: #94a3b8;
  font-size: 0.8rem;
}

/* 小组积分 */
.group-scoreboard {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.group-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(226, 232, 240, 0.6);
  transition: all 0.3s ease;
}
.group-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  transform: translateX(4px);
}
.group-card__rank {
  font-size: 1.8rem;
  font-weight: 800;
  width: 44px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.group-card__info {
  min-width: 140px;
}
.group-card__name {
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 6px 0;
}
.group-card__members {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.group-card__member {
  font-size: 0.72rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 6px;
}
.group-card__score-area {
  flex: 1;
}
.group-card__score {
  font-size: 1.6rem;
  font-weight: 800;
  margin-bottom: 6px;
}
.group-card__score-unit {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.7;
}
.group-card__bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}
.group-card__bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.group-card__actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.group-score-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.group-score-btn:hover {
  transform: scale(1.08);
}
.group-score-btn--add {
  color: #10b981;
  border-color: #10b981;
}
.group-score-btn--add:hover {
  background: rgba(16, 185, 129, 0.1);
}
.group-score-btn--sub {
  color: #ef4444;
  border-color: #ef4444;
}
.group-score-btn--sub:hover {
  background: rgba(239, 68, 68, 0.1);
}

@media (max-width: 768px) {
  .activity-tabs {
    grid-template-columns: repeat(2, 1fr);
  }
  .qa-question-card__options {
    grid-template-columns: 1fr;
  }
  .group-card {
    flex-direction: column;
    gap: 12px;
  }
  .group-card__info {
    min-width: auto;
  }
  .poll-bar-item {
    flex-wrap: wrap;
    gap: 6px;
  }
  .poll-bar-item__label {
    width: 100%;
  }
  .poll-bar-item__meta {
    width: 100%;
  }
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

  .home-card:hover,
  .course-card:hover,
  .video-card:hover,
  .menu-item:hover,
  .qa-question-card:hover,
  .group-card:hover,
  .roster-item:hover {
    transform: none !important;
  }

  .pick-result--spinning {
    animation: none !important;
  }
}
</style>
