<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from "vue";
import { RouterLink, useRoute } from "vue-router";
import * as echarts from "echarts";
import {
  useFeatures,
  formatFeatureTime,
  getTypeIcon,
} from "../composables/useFeatures.js";
import {
  submitCoursewareTask,
  refineCoursewareTask,
  exportCoursewareTask,
  subscribeProgress,
  downloadFile,
  getCoursewareHistory as fetchApiHistory,
  deleteCoursewareTask as deleteApiTask,
} from "../composables/useCoursewareApi.js";
import ContentRevisePanel from "../components/ContentRevisePanel.vue";
import FormWizard from "../components/FormWizard.vue";
import TemplateMarket from "../components/TemplateMarket.vue";
import { SPARK_TEMPLATES_API, apiUrl } from "../config/api.js";
import { dateKey, shortDate, seededInt } from "../utils/demoData.js";

const route = useRoute();

const {
  getHistory,
  getStats,
  addRecord,
  updateRecord,
  deleteRecord,
  TYPE_LABELS,
  STATUS_LABELS,
} = useFeatures();

const activePanel = ref("overview");
const sidebarOpen = ref(false);
const history = ref(getHistory());
const stats = ref(getStats());
const uploadFiles = ref([]);
const isGenerating = ref(false);
const toast = ref("");

// 真实 API 生成任务状态
const currentTaskId = ref(null);
const currentTaskProgress = ref(0);
const currentTaskStage = ref("");
const showProgress = ref(false);
const generatedFilename = ref(""); // 导出完成后的文件名
const contentReady = ref(false); // 正文已生成（可在右侧阅读 / 修改 / 导出）
const exporting = ref(false); // 正在导出最终文件

// ── 内容制作「内容调整」问答区 ─────────────────────────────────
// 左侧表单收集创作要素并提交流式生成；生成内容直接展示在右侧问答区，
// 用户像对话一样阅读并提出修改意见，满意后点击「导出最终内容」再生成文件。
const REVISE_TITLE = {
  ppt: "课件内容调整",
  doc: "教案内容调整",
  interactive: "练习内容调整",
  exam: "试卷内容调整",
};

const REVISE_PLACEHOLDER = {
  ppt: "说明课件要调整的地方…",
  doc: "说明教案要调整的地方…",
  interactive: "说明题目要调整的地方…",
  exam: "说明试卷要调整的地方…",
};

const panelByApiType = {
  ppt: "ppt",
  doc: "doc",
  quiz: "interactive",
  exam: "exam",
};

// 各面板独立的调整记录，切换面板时保留各自上下文
const reviseMessages = ref({ ppt: [], doc: [], interactive: [], exam: [] });
let reviseSeq = 0;
const nextReviseId = () => `revise-${++reviseSeq}`;

const currentReviseTitle = computed(
  () => REVISE_TITLE[activePanel.value] || "内容调整",
);
const currentRevisePlaceholder = computed(
  () => REVISE_PLACEHOLDER[activePanel.value] || "说明要调整的地方…",
);
const currentReviseMessages = computed(
  () => reviseMessages.value[activePanel.value] || [],
);
// 正文已生成后，才允许提交修改意见 / 导出
const reviseReady = computed(() => contentReady.value);

// 新建一条流式正文消息（AI 回复），随 delta 增量填充 content
function startStreamMessage(panel) {
  const msg = {
    id: nextReviseId(),
    role: "assistant",
    content: "",
    streaming: true,
  };
  reviseMessages.value[panel].push(msg);
  return msg;
}

// 订阅流式生成：正文增量写入消息，完成置为可修改 / 可导出
function subscribeStream(streamMsg) {
  return {
    onDelta: (text) => {
      streamMsg.content += text;
    },
    onProgress: (data) => {
      currentTaskProgress.value = data.progress;
      currentTaskStage.value = data.stage;
    },
    onDone: () => {
      isGenerating.value = false;
      streamMsg.streaming = false;
      contentReady.value = true;
    },
    onError: (err) => {
      isGenerating.value = false;
      streamMsg.streaming = false;
      if (!streamMsg.content) streamMsg.text = `生成失败：${err.message}`;
      showToast(`生成失败：${err.message}`);
    },
  };
}

// 提交修改意见：按意见重新流式生成，产出新版正文
async function handleReviseSend(text) {
  const panel = activePanel.value;
  const taskId = currentTaskId.value;
  const list = reviseMessages.value[panel];
  if (!taskId || !list) {
    showToast("请先生成初版内容");
    return;
  }

  list.push({ id: nextReviseId(), role: "user", text });

  isGenerating.value = true;
  exporting.value = false;
  currentTaskProgress.value = 0;
  currentTaskStage.value = "正在按修改意见调整…";
  contentReady.value = false;
  generatedFilename.value = "";

  const streamMsg = startStreamMessage(panel);

  try {
    await refineCoursewareTask(taskId, text);
    subscribeProgress(taskId, subscribeStream(streamMsg));
  } catch (err) {
    isGenerating.value = false;
    streamMsg.streaming = false;
    if (!streamMsg.content) streamMsg.text = `调整失败：${err.message}`;
    showToast(`调整失败：${err.message}`);
  }
}

// 导出最终内容：把已确认的正文渲染为文件，完成后自动下载
async function handleContentExport() {
  const taskId = currentTaskId.value;
  if (!taskId || !contentReady.value || isGenerating.value) return;

  isGenerating.value = true;
  exporting.value = true;
  currentTaskProgress.value = 0;
  currentTaskStage.value = "正在排版导出…";

  try {
    await exportCoursewareTask(taskId);
    subscribeProgress(taskId, {
      onProgress: (data) => {
        currentTaskProgress.value = data.progress;
        currentTaskStage.value = data.stage;
      },
      onDone: (data) => {
        isGenerating.value = false;
        exporting.value = false;
        if (data.status === "completed" && data.filename) {
          generatedFilename.value = data.filename;
          downloadFile(taskId, data.filename);
          showToast(`已导出：${data.filename}`);
        } else {
          showToast("导出未完成，请重试");
        }
      },
      onError: (err) => {
        isGenerating.value = false;
        exporting.value = false;
        showToast(`导出失败：${err.message}`);
      },
    });
  } catch (err) {
    isGenerating.value = false;
    exporting.value = false;
    showToast(`导出失败：${err.message}`);
  }
}

// 预览弹窗
const showPreview = ref(false);
const previewItem = ref(null);

const historyQuery = ref("");
const historyPage = ref(1);
const iterateFeedback = ref({});
const feedbackType = ref("");
const feedbackTitle = ref("");
const feedbackDesc = ref("");
const feedbackContact = ref("");
const feedbackFileName = ref("");
const fileInputRef = ref(null);
const expandedRecord = ref(null);

// ==================== 讯飞智文模板数据 ====================
// 讯飞模板接口不支持翻页/筛选，一次性返回全部可用模板
const sparkTemplates = ref([]);
const sparkTemplateLoading = ref(false);
const sparkTemplateError = ref("");

async function fetchSparkTemplates() {
  sparkTemplateLoading.value = true;
  sparkTemplateError.value = "";
  try {
    const res = await fetch(SPARK_TEMPLATES_API);
    const data = await res.json();
    sparkTemplates.value = data.templates || [];
    if (data.error) sparkTemplateError.value = data.error;
  } catch (e) {
    console.warn("获取讯飞模板列表失败:", e);
    sparkTemplates.value = [];
    sparkTemplateError.value = "无法连接后端服务，可稍后重试";
  } finally {
    sparkTemplateLoading.value = false;
  }
}

// 各面板最终产出内容的 AI 引擎（仅用于右侧对话区的 AI 头像，不在界面标注"生成引擎"）：
// 课件 = DeepSeek 出大纲 + 讯飞智文 排版出稿，头像取最终出稿方；教案/练习/试卷 = DeepSeek。
const currentPipeline = computed(() =>
  activePanel.value === "ppt" ? ["deepseek", "zhiwen"] : ["deepseek"],
);

// 拼完整预览图地址：后端返回 /api/... 相对路径。
// 若 preview 不是真实图片路径（早期模板误把风格描述放进预览字段），
// 返回空，模板卡不渲染破损的 <img>。
function previewUrl(path) {
  if (!path) return "";
  if (/^https?:\/\//.test(path)) return path;
  const looksLikeImage = /\.(png|jpe?g|svg|gif|webp)([\?#].*)?$/i.test(path);
  if (!looksLikeImage) return "";
  return apiUrl(path);
}

// 归一化选择值：选中"自定义"时取自定义输入内容，否则取所选预设
function resolveText(selected, custom) {
  return selected === CUSTOM_OPTION ? custom : selected;
}

// 归一化学科名：自定义学科取输入内容
function resolveSubjectName(form) {
  return form.subject === CUSTOM_OPTION ? form.subjectCustom : form.subject;
}

// 学科差异化：课堂互动与评估维度（无预设时回退通用选项）
function subjectTraits(form) {
  return subjectPresets[resolveSubjectName(form)] || {};
}
const pptInteractions = computed(
  () => subjectTraits(pptForm.value).interactions || DEFAULT_INTERACTIONS,
);
const pptAssessments = computed(
  () => subjectTraits(pptForm.value).assessment || ASSESSMENT_OPTIONS,
);
const docAssessments = computed(
  () => subjectTraits(docForm.value).assessment || ASSESSMENT_OPTIONS,
);
const quizAssessments = computed(
  () => subjectTraits(questionForm.value).assessment || ASSESSMENT_OPTIONS,
);
const examAssessments = computed(
  () => subjectTraits(examForm.value).assessment || ASSESSMENT_OPTIONS,
);

// 当前所选学科对应的教学目标 / 重点难点预设
const pptGoals = computed(
  () => subjectPresets[resolveSubjectName(pptForm.value)]?.goals || [],
);
const pptKeys = computed(
  () => subjectPresets[resolveSubjectName(pptForm.value)]?.keyPoints || [],
);
const docGoals = computed(
  () => subjectPresets[resolveSubjectName(docForm.value)]?.goals || [],
);
const docKeys = computed(
  () => subjectPresets[resolveSubjectName(docForm.value)]?.keyPoints || [],
);

// ==================== 教学档案筛选条件（新版）====================
const isArchiveFilterExpanded = ref(false);
const activeArchiveFilterGroups = ref(["basic", "type"]);

// 基础筛选
const archiveFilters = ref({
  type: "", // 课件类型
  subject: "", // 学科
  grade: "", // 年级
  status: "", // 状态
  timeRange: "", // 时间范围
  format: "", // 文件格式
  difficulty: "", // 难度
  searchQuery: "", // 搜索关键词
});

// 排序方式
const archiveSortBy = ref("newest");

// 保存的筛选方案
const savedArchiveFilters = ref([
  { name: "最近课件", filters: { type: "ppt", timeRange: "week" } },
  { name: "待优化教案", filters: { type: "doc", status: "iterating" } },
]);

// 筛选选项数据
const archiveFilterOptions = {
  grades: ["七年级", "八年级", "九年级", "高一", "高二", "高三"],
  formats: [
    { value: "pptx", label: "PPTX", icon: "ppt", color: "#f59e0b" },
    { value: "docx", label: "DOCX", icon: "doc", color: "#3b82f6" },
    { value: "html", label: "HTML", icon: "interactive", color: "#8b5cf6" },
  ],
  difficulties: [
    { value: "basic", label: "基础", color: "#22c55e", bgColor: "#dcfce7" },
    { value: "medium", label: "中等", color: "#f59e0b", bgColor: "#fef3c7" },
    { value: "advanced", label: "进阶", color: "#ef4444", bgColor: "#fee2e2" },
  ],
  timeRanges: [
    { value: "today", label: "今天", desc: "今日创建" },
    { value: "week", label: "近7天", desc: "最近一周" },
    { value: "month", label: "近30天", desc: "最近一月" },
    { value: "quarter", label: "本季度", desc: "三个月内" },
  ],
};

// 知识点标签
const knowledgeTags = [
  "牛顿定律",
  "电磁感应",
  "化学反应",
  "细胞结构",
  "函数与方程",
  "几何证明",
  "文言文阅读",
  "英语语法",
  "实验探究",
  "数据分析",
  "历史事件",
  "地理地貌",
];

// 意见反馈筛选条件
const feedbackFilters = ref({
  subject: "",
  type: "",
  timeRange: "",
  searchQuery: "",
});

// 可选的学科列表
const availableSubjects = computed(() => {
  const subjects = new Set(history.value.map((item) => item.subject));
  return Array.from(subjects).filter(Boolean);
});

// 时间范围选项
const timeRangeOptions = [
  { value: "", label: "全部时间" },
  { value: "today", label: "今天" },
  { value: "week", label: "最近7天" },
  { value: "month", label: "最近30天" },
];

// 课件类型选项
const contentTypeOptions = [
  { value: "", label: "全部类型" },
  { value: "ppt", label: "课件" },
  { value: "doc", label: "教案" },
  { value: "interactive", label: "教学题" },
  { value: "exam", label: "试卷" },
];

// 自定义选项标记：选中后显示输入框让用户自行填写
const CUSTOM_OPTION = "__custom__";

// 课件篇幅 → 章节数约束提示（传递给 AI，控制生成结构与模版容量匹配）
const PAGES_SECTION_HINT = {
  精炼: "建议 2-3 个章节，每章 1-2 个内容点，适合导入/短课",
  标准: "建议 3-4 个章节，每章 2 个内容点，适合常规教学",
  充实: "建议 4 个章节，每章 2-3 个内容点，适合公开课/示范课",
};

// 学段选项（影响内容深度与模版匹配）
const GRADE_OPTIONS = ["小学低年级", "小学高年级", "初中", "高中"];

// 分步向导：各面板独立记忆当前步骤
const formStep = ref({ ppt: 0, doc: 0, interactive: 0, exam: 0 });
const currentFormStep = computed({
  get: () => formStep.value[activePanel.value] ?? 0,
  set: (v) => {
    formStep.value[activePanel.value] = v;
  },
});

const PPT_STEPS = [
  { key: "base", title: "基础信息", desc: "学科 / 课题 / 学段" },
  { key: "goals", title: "教学目标与学情", desc: "目标 / 重难点 / 学情" },
  {
    key: "content",
    title: "内容结构与呈现",
    desc: "课时 / 篇幅 / 大纲 / 风格",
  },
  { key: "apply", title: "应用与输出", desc: "场景 / 评估 / 生成" },
];
const DOC_STEPS = [
  { key: "base", title: "基础信息", desc: "学科 / 课题 / 学段" },
  { key: "goals", title: "教学目标与学情", desc: "目标 / 重难点 / 学情" },
  { key: "process", title: "教学过程设计", desc: "格式 / 风格 / 环节" },
  { key: "apply", title: "应用与输出", desc: "场景 / 评估 / 生成" },
];
const QUIZ_STEPS = [
  { key: "base", title: "基础信息", desc: "学科 / 知识点 / 学段" },
  { key: "goals", title: "考查目标与学情", desc: "考查点 / 学情" },
  { key: "design", title: "题目设计", desc: "难度 / 题量 / 题型" },
  { key: "apply", title: "应用与输出", desc: "场景 / 评估 / 生成" },
];
const EXAM_STEPS = [
  { key: "base", title: "基础信息", desc: "学科 / 范围 / 学段" },
  { key: "goals", title: "命题目标与学情", desc: "考查目标 / 学情" },
  { key: "paper", title: "卷面设计", desc: "难度 / 分值 / 题量" },
  { key: "apply", title: "应用与输出", desc: "场景 / 评估 / 生成" },
];

// 教学要素通用选项
const DURATION_OPTIONS = ["40分钟", "45分钟", "50分钟"];
const STUDENT_PROFILE_OPTIONS = [
  "基础薄弱（多支架、多实例、小步走）",
  "中等水平（讲练结合、落实考点）",
  "优秀拔高（加变式与思维拓展）",
];
const ASSESSMENT_OPTIONS = ["知识点掌握", "思维过程", "应用能力", "综合素养"];
const USAGE_SCENE = {
  ppt: ["新授课", "复习课", "公开课", "微课", "示范课"],
  doc: ["常规备课", "公开课", "评优课", "校本教研"],
  interactive: ["随堂检测", "课后练习", "单元复习", "分层作业"],
  exam: ["单元测试", "期中考试", "期末考试", "月考", "模拟考"],
};
const LESSON_FOCUS_OPTIONS = ["导入设计", "活动组织", "板书设计", "作业分层"];
const QUESTION_TYPE_OPTIONS = [
  "选择 + 填空 + 解答（混合）",
  "仅选择题",
  "仅解答题",
  "计算题为主",
];
const DEFAULT_INTERACTIONS = ["提问互动", "小组讨论", "随堂练习", "板书推演"];

/**
 * 各学科预设的教学目标与重点难点模板
 * 用户选择学科后，教学目标/重点难点下拉自动加载对应学科的常用选项，
 * 也可选择"自定义"自行填写。
 */
const subjectPresets = {
  语文: {
    goals: [
      "知识与技能：正确、流利、有感情地朗读课文，读懂并积累重点词句",
      "过程与方法：抓关键词句、借助参考资料，概括内容、体会表达方法",
      "情感态度与价值观：感受语言文字之美，培育人文情怀与文化自信",
    ],
    keyPoints: [
      "教学重点：理解重点语句含义，学习作者观察与表达的方法",
      "教学难点：体会言外之意、把握文章主旨与情感升华",
    ],
    interactions: ["朗读品味", "小组讨论", "情境表演", "读写结合"],
    assessment: ["语言积累", "文本理解", "表达运用", "文化感悟"],
  },
  数学: {
    goals: [
      "知识与技能：理解并掌握本课核心概念、公式与运算法则，能正确应用",
      "过程与方法：经历观察、猜想、验证、归纳等数学活动，发展逻辑思维",
      "情感态度与价值观：体会数学与生活的联系，养成严谨求实的科学态度",
    ],
    keyPoints: [
      "教学重点：掌握例题所涉及的概念、定理及其基本应用",
      "教学难点：理解抽象概念间的联系，灵活运用所学方法解决问题",
    ],
    interactions: ["问题串引导", "板演推演", "变式训练", "小组探究"],
    assessment: ["概念理解", "运算能力", "推理能力", "建模应用"],
  },
  英语: {
    goals: [
      "知识与技能：掌握本课重点词汇、句型与语法，能进行准确表达",
      "过程与方法：通过听说读写等语言实践，提升综合语言运用能力",
      "情感态度与价值观：拓宽国际视野，增强跨文化交际意识",
    ],
    keyPoints: [
      "教学重点：掌握核心词汇与目标句型，能完成基本会话任务",
      "教学难点：在真实语境中正确、得体地运用目标语言",
    ],
    interactions: ["情景对话", "听读输入", "角色扮演", "任务型输出"],
    assessment: ["词汇句型", "语篇理解", "口语表达", "跨文化意识"],
  },
  物理: {
    goals: [
      "知识与技能：理解并掌握本课物理概念、规律与公式，能正确运用",
      "过程与方法：通过实验观察、数据分析与推理，培养科学探究能力",
      "情感态度与价值观：体会物理与生活的密切联系，激发探究兴趣",
    ],
    keyPoints: [
      "教学重点：理解核心概念与规律的建立过程及适用条件",
      "教学难点：物理量间的逻辑关系与综合分析、计算能力",
    ],
    interactions: ["演示实验", "问题探究", "模型建构", "数据推理"],
    assessment: ["概念规律理解", "实验探究能力", "模型应用", "科学思维"],
  },
  化学: {
    goals: [
      "知识与技能：掌握本课物质的性质、变化及化学反应原理",
      "过程与方法：通过实验探究，学会观察、对比与分析现象",
      "情感态度与价值观：树立安全与环保意识，感受化学的实用价值",
    ],
    keyPoints: [
      "教学重点：掌握核心化学概念与化学方程式的书写、应用",
      "教学难点：从微观本质理解宏观现象，正确分析实验结论",
    ],
    interactions: ["实验探究", "现象观察", "微观解释", "方程式书写"],
    assessment: ["概念原理", "实验操作", "微观表征", "证据推理"],
  },
  生物: {
    goals: [
      "知识与技能：掌握本课生物结构、功能与生命活动规律",
      "过程与方法：运用观察、比较等方法，建立生命观念",
      "情感态度与价值观：尊重生命、热爱自然，树立生态保护意识",
    ],
    keyPoints: [
      "教学重点：掌握核心概念与结构功能相适应的观点",
      "教学难点：理解生命活动过程的内在机制与相互关系",
    ],
    interactions: ["观察比较", "结构功能分析", "实验探究", "图示建模"],
    assessment: ["概念理解", "结构与功能观", "实验探究", "生命观念"],
  },
  历史: {
    goals: [
      "知识与技能：掌握本课重要史实、人物与历史事件脉络",
      "过程与方法：学会史料研读与历史解释，培养时序与因果思维",
      "情感态度与价值观：树立正确历史观，增强家国情怀与责任感",
    ],
    keyPoints: [
      "教学重点：梳理历史事件的基本线索与关键史实",
      "教学难点：辩证分析历史事件的背景、影响与启示",
    ],
    interactions: ["史料研读", "时间轴梳理", "事件比较", "情境还原"],
    assessment: ["史实掌握", "史料实证", "历史解释", "家国情怀"],
  },
  地理: {
    goals: [
      "知识与技能：掌握本课地理分布、成因与区域特征",
      "过程与方法：运用地图与图表资料，培养区域认知与综合思维",
      "情感态度与价值观：树立人地协调观，增强环境保护意识",
    ],
    keyPoints: [
      "教学重点：掌握核心地理现象、分布规律及成因",
      "教学难点：综合分析自然与人文要素的相互影响",
    ],
    interactions: ["地图判读", "图表分析", "要素综合", "案例分析"],
    assessment: ["区域认知", "综合思维", "地理实践力", "人地协调观"],
  },
  政治: {
    goals: [
      "知识与技能：理解并掌握本课基本概念、观点与价值导向",
      "过程与方法：结合生活情境，学会运用所学知识分析社会现象",
      "情感态度与价值观：坚定理想信念，提升道德与法治素养",
    ],
    keyPoints: [
      "教学重点：理解本课核心观点与基本价值导向",
      "教学难点：运用正确立场、观点和方法分析现实问题",
    ],
    interactions: ["时政案例", "情境辨析", "观点论证", "价值澄清"],
    assessment: ["概念观点理解", "材料分析", "价值判断", "政治认同"],
  },
};

const pptForm = ref({
  subject: "",
  subjectCustom: "",
  topic: "",
  grade: "", // 学段：小学低年级 / 小学高年级 / 初中 / 高中
  duration: "45分钟",
  style: "实验探究型",
  pages: "标准", // 课件篇幅：精炼 / 标准 / 充实
  teachingGoals: "",
  goalCustom: "",
  keyPoints: "",
  keyCustom: "",
  outlineCustom: "", // 自定义章节大纲（可选，每行一个章节）
  studentProfile: "",
  studentProfileCustom: "",
  interactionDesign: "",
  interactionCustom: "",
  usageScene: "",
  usageSceneCustom: "",
  assessment: "",
  assessmentCustom: "",
  referenceFile: null,
  sparkTemplateId: "", // 讯飞模板 ID，为空用后端默认模板
  isCardNote: true, // 讯飞：是否生成演讲备注
  isFigure: true, // 讯飞：是否自动配图
});

const docForm = ref({
  subject: "",
  subjectCustom: "",
  topic: "",
  grade: "",
  duration: "45分钟",
  format: "标准教案",
  style: "实验探究型",
  teachingGoals: "",
  goalCustom: "",
  keyPoints: "",
  keyCustom: "",
  studentProfile: "",
  studentProfileCustom: "",
  lessonFocus: "",
  lessonFocusCustom: "",
  usageScene: "",
  usageSceneCustom: "",
  assessment: "",
  assessmentCustom: "",
  referenceFile: null,
});

// 学科变化时自动带入该学科默认教学目标与重难点，减少手动选择；无预设则清空
watch(
  () => [pptForm.value.subject, docForm.value.subject],
  ([pptSubj, docSubj]) => {
    if (pptSubj !== undefined) {
      const preset = subjectPresets[resolveSubjectName(pptForm.value)];
      pptForm.value.teachingGoals = preset?.goals?.[0] || "";
      pptForm.value.goalCustom = "";
      pptForm.value.keyPoints = preset?.keyPoints?.[0] || "";
      pptForm.value.keyCustom = "";
    }
    if (docSubj !== undefined) {
      const preset = subjectPresets[resolveSubjectName(docForm.value)];
      docForm.value.teachingGoals = preset?.goals?.[0] || "";
      docForm.value.goalCustom = "";
      docForm.value.keyPoints = preset?.keyPoints?.[0] || "";
      docForm.value.keyCustom = "";
    }
  },
);

const questionForm = ref({
  subject: "",
  subjectCustom: "",
  topic: "",
  stage: "高中",
  difficulty: "综合提升",
  count: 8,
  scenario: "随堂检测",
  scenarioCustom: "",
  target: "",
  targetCustom: "",
  studentProfile: "",
  studentProfileCustom: "",
  questionTypes: "",
  questionTypesCustom: "",
  assessment: "",
  assessmentCustom: "",
});

const commonSubjects = [
  "语文",
  "数学",
  "英语",
  "物理",
  "化学",
  "生物",
  "历史",
  "地理",
  "政治",
];

const examForm = ref({
  subject: "",
  subjectCustom: "",
  topic: "",
  grade: "高中",
  difficulty: "中等",
  totalScore: 100,
  choiceCount: 10,
  fillCount: 6,
  essayCount: 4,
  generateAB: false,
  target: "",
  targetCustom: "",
  studentProfile: "",
  studentProfileCustom: "",
  usageScene: "",
  usageSceneCustom: "",
  assessment: "",
  assessmentCustom: "",
});

const examPreviewStructure = {
  基础: [
    { type: "选择题", count: 12, score: 3, desc: "基础概念辨析" },
    { type: "填空题", count: 6, score: 4, desc: "核心公式与术语" },
    { type: "解答题", count: 3, score: 10, desc: "简单应用与计算" },
  ],
  中等: [
    { type: "选择题", count: 10, score: 3, desc: "概念应用与情境判断" },
    { type: "填空题", count: 6, score: 4, desc: "综合填空与推理" },
    { type: "解答题", count: 4, score: 10, desc: "多步综合应用" },
  ],
  提高: [
    { type: "选择题", count: 8, score: 3, desc: "高阶思维与综合辨析" },
    { type: "填空题", count: 5, score: 4, desc: "复杂推导与计算" },
    { type: "解答题", count: 5, score: 10, desc: "探究创新与拓展" },
  ],
};

const navGroups = [
  {
    label: "内容生成",
    featured: true,
    items: [
      {
        id: "ppt",
        label: "课件制作",
        icon: "ppt",
        desc: "套用精美模版，自动填充课件内容",
      },
      {
        id: "doc",
        label: "教案编写",
        icon: "doc",
        desc: "生成完整教学设计，含流程与脚本",
      },
      {
        id: "interactive",
        label: "课堂练习",
        icon: "interactive",
        desc: "按难度分层生成练习题与检测卷",
      },
      {
        id: "exam",
        label: "试卷生成",
        icon: "exam",
        desc: "混合题型组卷，支持A/B卷与答题卡",
      },
    ],
  },
  {
    label: "复盘优化",
    items: [
      {
        id: "history",
        label: "教学档案",
        icon: "history",
        desc: "按学科和时间检索历史生成内容",
      },
      {
        id: "iterate",
        label: "教学反思",
        icon: "iterate",
        desc: "记录教学心得，持续优化内容质量",
      },
    ],
  },
];

const panelTitles = {
  overview: "核心功能概览",
  ppt: "课件制作",
  doc: "教案编写",
  interactive: "课堂练习",
  exam: "试卷生成",
  history: "教学档案",
  iterate: "教学反思",
};

const panelSubtitles = {
  overview: "概览任务状态与创作节奏，快速进入工作流",
  ppt: "选择预设风格模版，自动套用精美版式生成课件",
  doc: "描述教学目标，编写完整教案",
  interactive: "根据知识点出题，支持分层练习",
  exam: "选择题+填空题+解答题混合组卷，一键生成A/B卷",
  history: "查看历史生成记录，支持复用与迭代",
  iterate: "记录教学心得，持续优化内容质量",
};

const panelChips = {
  overview: "知启灵枢 · 教学创作台",
  ppt: "知启灵枢 · 课件制作",
  doc: "知启灵枢 · 教案编写",
  interactive: "知启灵枢 · 课堂练习",
  exam: "知启灵枢 · 试卷生成",
  history: "知启灵枢 · 教学档案",
  iterate: "知启灵枢 · 教学反思",
};

const featureIcons = {
  ppt: ["M4 4.5h12v8H4v-8z", "M7 15.5h6M10 12.5v3"],
  doc: ["M6 3.5h6l3 3v10H6v-13z", "M12 3.5v4h4M8.5 10h5M8.5 13h5"],
  interactive: [
    "M4.5 5.5h11v8h-11z",
    "M7.5 8.5h5M7.5 11.5h3",
    "M13.5 13.5l2 2",
  ],
  exam: [
    "M6 3.5h10a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-11a1 1 0 0 1 1-1z",
    "M8 7.5h6M8 10.5h4M8 13.5h5",
    "M17 12.5l-3 3-1.5-1.5",
  ],
  intent: [
    "M10 16a6 6 0 1 0 0-12 6 6 0 0 0 0 12z",
    "M10 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM10 10h.01",
  ],
  multimodal: ["M4.5 15.5h11", "M6 9.5 10 5l4 4.5M10 5v8.5"],
  history: ["M10 4.5v5l3 1.5", "M10 17a7 7 0 1 0 0-14 7 7 0 0 0 0 14z"],
  iterate: [
    "M15.5 7.5A5.5 5.5 0 0 0 6 5l-1.5 1.5M4.5 3.5v3h3",
    "M4.5 12.5A5.5 5.5 0 0 0 14 15l1.5-1.5M15.5 16.5v-3h-3",
  ],
};

const overviewCards = computed(() => [
  {
    label: "本周生成",
    value: stats.value.total,
    detail: history.value[0]
      ? `最近任务：${history.value[0].title}`
      : "还没有生成记录，先开启一次创作吧",
    tone: "blue",
    icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c.5 2.5 2.5 4.5 5 5-2.5.5-4.5 2.5-5 5-.5-2.5-2.5-4.5-5-5 2.5-.5 4.5-2.5 5-5z"/><path d="M18 13c.3 1.2 1.5 2.4 3 2.7-1.5.3-2.7 1.5-3 2.7-.3-1.2-1.5-2.4-3-2.7 1.5-.3 2.7-1.5 3-2.7z"/><path d="M5 16c.2.8 1 1.6 2 1.8-1 .2-1.8 1-2 1.8-.2-.8-1-1.6-2-1.8 1-.2 1.8-1 2-1.8z"/></svg>`,
  },
  {
    label: "已完成",
    value: stats.value.completed,
    detail: "支持继续编辑，PPT/Word/互动课件一键导出",
    tone: "mint",
    icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="9 13 11 15 15 9"/><path d="M8 5.5C6.3 6.7 5 9.2 5 12c0 3.9 3.1 7 7 7s7-3.1 7-7-3.1-7-7-7"/></svg>`,
  },
  {
    label: "待优化",
    value: stats.value.iterating,
    detail: "可在教学档案中查看反馈，一键重新生成",
    tone: "violet",
    icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.2-8.6"/><polyline points="12 7 12 12 15 14"/><path d="M21 3v5h-5"/></svg>`,
  },
  {
    label: "覆盖学科",
    value: new Set(history.value.map((item) => item.subject)).size || 1,
    detail:
      "按学科管理教学档案，" +
      [...new Set(history.value.map((item) => item.subject))]
        .slice(0, 3)
        .join(" · "),
    tone: "amber",
    icon: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="9" y1="7" x2="16" y2="7"/><line x1="9" y1="11" x2="14" y2="11"/><line x1="9" y1="15" x2="12" y2="15"/></svg>`,
  },
]);

// 本周创作趋势 —— 直接从教学档案（history）按自然日聚合，日期取真实的滚动 7 天
const trendItems = computed(() => {
  const records = history.value || [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (6 - i));
    return d;
  });

  const counts = days.map(
    (d) => records.filter((r) => dateKey(r.createdAt) === dateKey(d)).length,
  );

  // 档案为空（首次进入演示环境）时给一条稳定的基线曲线：用「日期」当种子，
  // 同一天刷新看到的是同一条曲线，不会每次跳变（这正是乱数一眼假的原因）。
  const hasData = counts.some((c) => c > 0);
  const values = counts.map((c, i) =>
    hasData ? c : seededInt(`trend:${dateKey(days[i])}`, 2, 8),
  );

  const max = Math.max(...values);
  const min = Math.min(...values);

  return days.map((d, index) => ({
    key: dateKey(d),
    label: weekdays[d.getDay()],
    date: shortDate(d),
    fullDate: `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`,
    value: values[index],
    x: 50 + index * 68,
    y: 175 - ((values[index] - min) / (max - min || 1)) * 110,
  }));
});

// 统计概览数据
const trendStats = computed(() => {
  const values = trendItems.value.map((item) => item.value);
  const total = values.reduce((sum, v) => sum + v, 0);
  const avg = Math.round(total / values.length);
  const maxValue = Math.max(...values);
  const maxIndex = values.indexOf(maxValue);
  const maxDay = trendItems.value[maxIndex]?.label || "-";

  // 覆盖学科取自真实档案；没有档案时退回稳定的演示集合
  const subjects = [
    ...new Set(
      (history.value || []).map((item) => item.subject).filter(Boolean),
    ),
  ].slice(0, 3);

  return {
    total,
    avg,
    maxDay,
    subjects: subjects.length ? subjects : ["物理", "数学", "化学"],
  };
});

const weeklyFlowPath = computed(() =>
  trendItems.value
    .map((item, index) => `${index === 0 ? "M" : "L"} ${item.x} ${item.y}`)
    .join(" "),
);

const weeklyAreaPath = computed(
  () => `${weeklyFlowPath.value} L 480 200 L 36 200 Z`,
);

// 选中的日期详情
const selectedDay = ref(null);

// 获取某天的创作详情：当天有真实档案就直接展示真实条目；否则用「日期」做种子
// 生成稳定的演示条目 —— 同一天多次点开内容一致（乱数会让每次都不一样，很假）。
function getDayDetails(dayData) {
  const seedKey = dayData.key || dayData.label || "day";
  const daySubjects = ["物理", "数学", "化学"];
  const dayTypes = ["课件", "教案", "教学题"];
  const dayTypesEn = ["ppt", "doc", "interactive"];

  const realRecords = (history.value || []).filter(
    (r) => dateKey(r.createdAt) === seedKey,
  );

  const items = realRecords.length
    ? realRecords.map((r, i) => ({
        id: r.id || i,
        title: r.title,
        type: (TYPE_LABELS[r.type] || "内容").replace("生成", ""),
        typeEn: r.type,
        subject: r.subject || "未分类",
        time: generateTime(i, seedKey),
        aiScore: seededInt(`score:${seedKey}:${i}`, 86, 96),
        completeness: seededInt(`complete:${seedKey}:${i}`, 88, 98),
      }))
    : Array.from({ length: dayData.value }, (_, i) => {
        const typeIndex = i % 3;
        const subjectIndex = (i + Math.floor(dayData.value / 2)) % 3;
        return {
          id: i,
          title: generateCoursewareTitle(
            daySubjects[subjectIndex],
            dayTypes[typeIndex],
            i,
          ),
          type: dayTypes[typeIndex],
          typeEn: dayTypesEn[typeIndex],
          subject: daySubjects[subjectIndex],
          time: generateTime(i, seedKey),
          aiScore: seededInt(`score:${seedKey}:${i}`, 86, 96),
          completeness: seededInt(`complete:${seedKey}:${i}`, 88, 98),
        };
      });

  // 计算类型分布（试卷归入「教学题」一族，与前端其它处的归档口径保持一致）
  const countByType = (typeKey) =>
    items.filter(
      (i) =>
        i.typeEn === typeKey ||
        (typeKey === "interactive" && i.typeEn === "exam"),
    ).length;

  const typeDistribution = {
    ppt: countByType("ppt"),
    doc: countByType("doc"),
    interactive: countByType("interactive"),
  };

  // 计算学科分布
  const subjectDistribution = {};
  items.forEach((item) => {
    subjectDistribution[item.subject] =
      (subjectDistribution[item.subject] || 0) + 1;
  });

  return {
    ...dayData,
    efficiency:
      dayData.value >= 6 ? "高效" : dayData.value >= 4 ? "正常" : "轻松",
    efficiencyLevel:
      dayData.value >= 6 ? "high" : dayData.value >= 4 ? "normal" : "low",
    subjects: Object.keys(subjectDistribution),
    subjectDistribution,
    typeDistribution,
    items,
    avgScore: Math.round(
      items.reduce((sum, i) => sum + i.aiScore, 0) / items.length,
    ),
    totalTime: items.length * 15 + seededInt(`spent:${seedKey}`, 0, 30), // 预估总耗时
    peakHour: ["09:00", "14:00", "20:00"][seededInt(`peak:${seedKey}`, 0, 2)],
  };
}

// 生成课件标题
function generateCoursewareTitle(subject, type, index) {
  const titles = {
    物理: {
      课件: ["力学基础概念", "电磁感应现象", "光学实验探究", "热力学定律"],
      教案: ["牛顿定律教学设计", "电路分析教案", "波动光学教案"],
      教学题: ["力学计算题组", "电磁学选择题", "实验探究题"],
    },
    数学: {
      课件: ["函数与图像", "几何证明方法", "数列求和技巧", "概率统计基础"],
      教案: ["二次函数教案", "立体几何教案", "导数应用教案"],
      教学题: ["函数综合题", "几何证明题组", "数列应用题"],
    },
    化学: {
      课件: ["元素周期律", "化学反应速率", "有机化合物", "化学平衡"],
      教案: ["氧化还原教案", "化学键教案", "实验安全教案"],
      教学题: ["化学方程式配平", "计算题精选", "实验分析题"],
    },
  };
  const list = titles[subject][type];
  return (
    list[index % list.length] +
    (index >= list.length ? `(${Math.floor(index / list.length) + 1})` : "")
  );
}

// 生成时间（按天做种子，保证同一天的条目时间稳定不跳）
function generateTime(index, seedKey = "") {
  const hours = [8, 9, 10, 14, 15, 16, 19, 20, 21];
  const hour = hours[index % hours.length];
  const minute = seededInt(`time:${seedKey}:${index}`, 0, 5) * 10;
  return `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
}

// 点击日期显示详情
function showDayDetail(item) {
  // 点击同一天则关闭
  if (selectedDay.value && selectedDay.value.label === item.label) {
    selectedDay.value = null;
    return;
  }
  selectedDay.value = getDayDetails(item);
}

// 关闭详情
function closeDayDetail() {
  selectedDay.value = null;
}

const typeShare = computed(() => {
  const list = [
    { label: "课件生成", value: stats.value.ppt, color: "#4c7dff" },
    { label: "教案生成", value: stats.value.doc, color: "#23c3b2" },
    { label: "教学题生成", value: stats.value.interactive, color: "#8b5cf6" },
  ];
  const total = Math.max(
    list.reduce((sum, item) => sum + item.value, 0),
    1,
  );

  return list.map((item) => ({
    ...item,
    percent: Math.round((item.value / total) * 100),
  }));
});

// 雷达图基础维度配置
const radarBaseDimensions = [
  { name: "课件制作", angle: -90 },
  { name: "教案编写", angle: -30 },
  { name: "课堂练习", angle: 30 },
  { name: "互动设计", angle: 90 },
  { name: "评估测试", angle: 150 },
  { name: "资源整合", angle: 210 },
];

// 雷达图能力数据
const radarMetrics = computed(() => {
  const baseScores = {
    ppt: Math.min(95, 60 + stats.value.ppt * 3),
    doc: Math.min(90, 55 + stats.value.doc * 4),
    interactive: Math.min(85, 50 + stats.value.interactive * 5),
  };

  return [
    {
      name: "课件制作能力",
      score: Math.round(baseScores.ppt),
      color: "#4c7dff",
    },
    {
      name: "教案编写能力",
      score: Math.round(baseScores.doc),
      color: "#23c3b2",
    },
    {
      name: "互动设计能力",
      score: Math.round(baseScores.interactive),
      color: "#8b5cf6",
    },
    {
      name: "评估测试能力",
      score: Math.round(baseScores.interactive * 0.9),
      color: "#f59e0b",
    },
    {
      name: "资源整合能力",
      score: Math.round((baseScores.ppt + baseScores.doc) / 2),
      color: "#ec4899",
    },
    {
      name: "创新应用能力",
      score: Math.round(baseScores.interactive * 1.1),
      color: "#10b981",
    },
  ];
});

// 雷达图轴线坐标
const radarAxes = computed(() => {
  const radius = 80;
  return radarBaseDimensions.map((dim) => ({
    x2: 100 + radius * Math.cos((dim.angle * Math.PI) / 180),
    y2: 100 + radius * Math.sin((dim.angle * Math.PI) / 180),
  }));
});

// 雷达图网格点
const radarGridPoints = (level) => {
  const radius = (level / 100) * 80;
  return radarBaseDimensions
    .map((dim) => {
      const x = 100 + radius * Math.cos((dim.angle * Math.PI) / 180);
      const y = 100 + radius * Math.sin((dim.angle * Math.PI) / 180);
      return `${x},${y}`;
    })
    .join(" ");
};

// 雷达图数据点坐标
const radarDataPointsArray = computed(() => {
  const radius = 80;
  return radarMetrics.value.map((metric, i) => {
    const angle = radarBaseDimensions[i].angle;
    const r = (metric.score / 100) * radius;
    return {
      x: 100 + r * Math.cos((angle * Math.PI) / 180),
      y: 100 + r * Math.sin((angle * Math.PI) / 180),
    };
  });
});

// 雷达图数据点字符串
const radarDataPoints = computed(() => {
  return radarDataPointsArray.value.map((p) => `${p.x},${p.y}`).join(" ");
});

// 为维度添加标签位置
const radarDimensionsWithLabels = computed(() => {
  const labelRadius = 95;
  const baseDims = [
    { name: "课件制作", angle: -90 },
    { name: "教案编写", angle: -30 },
    { name: "课堂练习", angle: 30 },
    { name: "互动设计", angle: 90 },
    { name: "评估测试", angle: 150 },
    { name: "资源整合", angle: 210 },
  ];
  return baseDims.map((dim) => {
    const x = 100 + labelRadius * Math.cos((dim.angle * Math.PI) / 180);
    const y = 100 + labelRadius * Math.sin((dim.angle * Math.PI) / 180);
    return {
      ...dim,
      labelX: `${(x / 200) * 100}%`,
      labelY: `${(y / 200) * 100}%`,
    };
  });
});

const overviewQueue = computed(() =>
  history.value.slice(0, 4).map((item) => ({
    ...item,
    typeLabel: TYPE_LABELS[item.type],
    statusLabel: STATUS_LABELS[item.status],
    timeLabel: formatFeatureTime(item.createdAt),
  })),
);

// 最近生成轨迹 - 教学产出趋势（堆叠柱状图）
// 按自然日分桶统计（原先用 createdAt >= cutoff 是累计值，越靠后越高，不真实），
// 日期取真实的滚动 7 天；档案为空时用日期做种子给稳定基线。
const recentTrajectoryData = computed(() => {
  const weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  const allRecords = history.value || [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (6 - i));
    return d;
  });

  const countOn = (day, typeKey) =>
    allRecords.filter(
      (r) =>
        dateKey(r.createdAt) === dateKey(day) &&
        (r.type === typeKey || (typeKey === "interactive" && r.type === "exam")),
    ).length;

  const hasData = allRecords.some((r) =>
    days.some((d) => dateKey(r.createdAt) === dateKey(d)),
  );

  return days.map((d) => {
    const key = dateKey(d);
    return {
      label: weekdays[d.getDay()],
      date: shortDate(d),
      key,
      ppt: hasData ? countOn(d, "ppt") : seededInt(`traj:ppt:${key}`, 2, 6),
      doc: hasData ? countOn(d, "doc") : seededInt(`traj:doc:${key}`, 1, 5),
      interactive: hasData
        ? countOn(d, "interactive")
        : seededInt(`traj:int:${key}`, 1, 4),
    };
  });
});

// 柱状图布局计算（段间留缝隙 + 四角圆角）
const trajectoryChartLayout = computed(() => {
  const data = recentTrajectoryData.value;
  const barWidth = 44;
  const gap = 20;
  const groupWidth = barWidth + gap;
  const padding = { left: 52, right: 12, top: 30, bottom: 44 };
  const chartWidth = 720;
  const chartHeight = 260;

  const maxVal = Math.max(...data.map((d) => d.ppt + d.doc + d.interactive), 1);
  const barAreaHeight = chartHeight - padding.top - padding.bottom;
  const segGap = 2; // 段间 2px 缝隙

  const bars = data.map((d, i) => {
    const x = padding.left + i * groupWidth;
    const pptH = Math.max((d.ppt / maxVal) * barAreaHeight, 2);
    const docH = Math.max((d.doc / maxVal) * barAreaHeight, 2);
    const interactiveH = Math.max((d.interactive / maxVal) * barAreaHeight, 2);
    const totalH = pptH + docH + interactiveH + segGap * 2;
    const y = padding.top + barAreaHeight - totalH;

    const interactiveY = padding.top + barAreaHeight - interactiveH - segGap;
    const docY = interactiveY - docH - segGap;

    return {
      label: d.label,
      date: d.date,
      x,
      y,
      total: d.ppt + d.doc + d.interactive,
      // 从下到上：课堂练习 → 教案编写 → 课件制作
      segments: [
        {
          type: "interactive",
          label: "课堂练习",
          value: d.interactive,
          height: interactiveH,
          y: interactiveY,
          color: "#8b5cf6",
        },
        {
          type: "doc",
          label: "教案编写",
          value: d.doc,
          height: docH,
          y: docY,
          color: "#23c3b2",
        },
        {
          type: "ppt",
          label: "课件制作",
          value: d.ppt,
          height: pptH,
          y,
          color: "#4c7dff",
        },
      ].filter((s) => s.height > 0),
    };
  });

  return { bars, maxVal, chartWidth, chartHeight };
});

const hoveredTrajectoryBar = ref(-1);

// ==================== ECharts 雷达图 ====================
const radarChartRef = ref(null);
const radarChartInstance = ref(null);

// 生成组合图表配置（柱状图+折线图）
function generateRadarChartOption() {
  const data = recentTrajectoryData.value;
  const dates = data.map((d) => d.label);

  // 计算每日累计使用时间（模拟数据：每个任务约15-30分钟）
  const usageTimeData = data.map((d, i) => {
    const totalTasks = d.ppt + d.doc + d.interactive;
    return Math.round(totalTasks * 18 + 12 + i * 3);
  });

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        crossStyle: { color: "#999" },
      },
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      padding: [12, 16],
      textStyle: { color: "#1e293b" },
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 12px;",
      formatter: function (params) {
        const dayData = data[params[0].dataIndex];
        let html = `<div style="font-weight: 600; margin-bottom: 8px; font-size: 14px;">${dayData.label} ${dayData.date}</div>`;

        params.forEach((param) => {
          if (param.seriesType === "bar") {
            html += `<div style="display: flex; align-items: center; margin: 4px 0;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 2px; margin-right: 8px;"></span>
              <span style="flex: 1;">${param.seriesName}:</span>
              <span style="font-weight: 600;">${param.value} 个</span>
            </div>`;
          } else if (param.seriesType === "line") {
            html += `<div style="display: flex; align-items: center; margin: 4px 0; border-top: 1px solid #e2e8f0; padding-top: 8px; margin-top: 8px;">
              <span style="display: inline-block; width: 10px; height: 10px; background: ${param.color}; border-radius: 50%; margin-right: 8px;"></span>
              <span style="flex: 1;">${param.seriesName}:</span>
              <span style="font-weight: 600;">${param.value} 分钟</span>
            </div>`;
          }
        });

        const total = dayData.ppt + dayData.doc + dayData.interactive;
        html += `<div style="border-top: 1px solid #e2e8f0; margin-top: 8px; padding-top: 8px;">
          <span style="color: #64748b;">任务总计: </span>
          <span style="font-weight: 600; color: #4c7dff;">${total} 项</span>
        </div>`;

        return html;
      },
    },
    legend: {
      data: ["课件制作", "教案编写", "课堂练习", "累计用时"],
      bottom: "2%",
      textStyle: { color: "#64748b", fontSize: 11 },
      itemWidth: 12,
      itemHeight: 12,
      icon: "roundRect",
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "18%",
      top: "15%",
      containLabel: true,
    },
    xAxis: {
      type: "category",
      name: "日期",
      nameLocation: "middle",
      nameGap: 30,
      nameTextStyle: {
        color: "#64748b",
        fontSize: 12,
        fontWeight: 500,
      },
      data: dates,
      axisLine: { lineStyle: { color: "#e2e8f0" } },
      axisTick: { show: false },
      axisLabel: {
        color: "#64748b",
        fontSize: 11,
        interval: 0,
      },
    },
    yAxis: [
      {
        type: "value",
        name: "任务数量 (个)",
        nameLocation: "middle",
        nameGap: 45,
        nameTextStyle: {
          color: "#64748b",
          fontSize: 12,
          fontWeight: 500,
        },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: "#94a3b8",
          fontSize: 10,
          formatter: "{value} 个",
        },
        splitLine: { lineStyle: { color: "#f1f5f9", type: "dashed" } },
      },
      {
        type: "value",
        name: "累计用时 (分钟)",
        nameLocation: "middle",
        nameGap: 50,
        nameTextStyle: {
          color: "#64748b",
          fontSize: 12,
          fontWeight: 500,
        },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: "#94a3b8",
          fontSize: 10,
          formatter: "{value} 分",
        },
        splitLine: { show: false },
      },
    ],
    series: [
      // 课件制作 - 蓝色柱状图（非堆叠，独立显示）
      {
        name: "课件制作",
        type: "bar",
        data: data.map((d) => d.ppt),
        barWidth: "22%",
        barGap: "8%",
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#4c7dff" },
            { offset: 1, color: "#6b9aff" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          formatter: "{c}",
          fontSize: 11,
          fontWeight: 600,
          color: "#4c7dff",
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(43,108,176, 0.5)",
          },
          label: {
            fontSize: 13,
            fontWeight: 700,
          },
        },
        animationDelay: function (idx) {
          return idx * 50;
        },
      },
      // 教案编写 - 青色柱状图（非堆叠，独立显示）
      {
        name: "教案编写",
        type: "bar",
        data: data.map((d) => d.doc),
        barWidth: "22%",
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#23c3b2" },
            { offset: 1, color: "#4dd9c4" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          formatter: "{c}",
          fontSize: 11,
          fontWeight: 600,
          color: "#23c3b2",
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(35, 195, 178, 0.5)",
          },
          label: {
            fontSize: 13,
            fontWeight: 700,
          },
        },
        animationDelay: function (idx) {
          return idx * 50 + 100;
        },
      },
      // 课堂练习 - 紫色柱状图（非堆叠，独立显示）
      {
        name: "课堂练习",
        type: "bar",
        data: data.map((d) => d.interactive),
        barWidth: "22%",
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#8b5cf6" },
            { offset: 1, color: "#a78bfa" },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        label: {
          show: true,
          position: "top",
          formatter: "{c}",
          fontSize: 11,
          fontWeight: 600,
          color: "#8b5cf6",
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: "rgba(139, 92, 246, 0.5)",
          },
          label: {
            fontSize: 13,
            fontWeight: 700,
          },
        },
        animationDelay: function (idx) {
          return idx * 50 + 200;
        },
      },
      // 累计用时 - 橙色折线图
      {
        name: "累计用时",
        type: "line",
        yAxisIndex: 1,
        data: usageTimeData,
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: "#f59e0b",
          shadowColor: "rgba(245, 158, 11, 0.3)",
          shadowBlur: 8,
        },
        itemStyle: {
          color: "#f59e0b",
          borderColor: "#fff",
          borderWidth: 2,
        },
        emphasis: {
          scale: true,
          itemStyle: {
            shadowBlur: 15,
            shadowColor: "rgba(245, 158, 11, 0.5)",
          },
        },
        animationDelay: function (idx) {
          return idx * 50 + 300;
        },
      },
    ],
    // 出场动画配置
    animationEasing: "elasticOut",
    animationDuration: 1500,
  };
}

// 初始化雷达图
function initRadarChart() {
  console.log("初始化雷达图, ref:", radarChartRef.value);
  if (!radarChartRef.value) {
    setTimeout(initRadarChart, 100);
    return;
  }

  try {
    if (radarChartInstance.value) {
      radarChartInstance.value.dispose();
      radarChartInstance.value = null;
    }

    const container = radarChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("雷达图容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      setTimeout(initRadarChart, 200);
      return;
    }

    radarChartInstance.value = echarts.init(container);
    const option = generateRadarChartOption();
    radarChartInstance.value.setOption(option);
    console.log("雷达图初始化成功");
  } catch (error) {
    console.error("雷达图初始化失败:", error);
  }
}

// 更新雷达图
function updateRadarChart() {
  if (radarChartInstance.value) {
    const option = generateRadarChartOption();
    radarChartInstance.value.setOption(option, true);
  }
}

// 监听窗口大小变化
function handleRadarResize() {
  if (radarChartInstance.value) {
    radarChartInstance.value.resize();
  }
}

const pptPreviewStructure = {
  实验探究型: [
    "情境导入",
    "提出问题",
    "实验设计",
    "现象分析",
    "规律归纳",
    "课堂训练",
  ],
  讲授演示型: [
    "目标导入",
    "概念讲解",
    "典型例题",
    "难点辨析",
    "课堂小结",
    "巩固练习",
  ],
  问题驱动型: [
    "核心问题",
    "线索拆解",
    "推导验证",
    "方法提炼",
    "拓展追问",
    "课堂反馈",
  ],
  翻转课堂型: [
    "课前任务",
    "问题聚焦",
    "重点讲评",
    "协作展示",
    "方法沉淀",
    "课后延展",
  ],
};

const docPreviewStructure = {
  标准教案: [
    "教学目标",
    "重点难点",
    "学情分析",
    "教学准备",
    "课堂流程",
    "作业布置",
  ],
  详细教案: [
    "目标分层",
    "环节脚本",
    "师生互动",
    "板书设计",
    "即时评价",
    "课后反思",
  ],
  简版教案: [
    "目标概览",
    "流程总览",
    "重点提示",
    "例题设计",
    "收束总结",
    "课后任务",
  ],
  校本模板: [
    "模板字段匹配",
    "课程目标",
    "教学流程",
    "资源使用",
    "课堂评价",
    "反思记录",
  ],
};

const questionPreviewStructure = {
  随堂检测: {
    基础巩固: ["概念判断", "基础单选", "知识填空", "即时反馈"],
    综合提升: ["情境辨析", "综合分析", "变式训练", "限时检测"],
    拓展挑战: ["高阶推理", "实验探究", "开放论述", "思维拓展"],
  },
  课后练习: {
    基础巩固: ["知识回顾", "单选巩固", "基础填空", "自检清单"],
    综合提升: ["综合应用", "计算推导", "案例分析", "错题整理"],
    拓展挑战: ["拓展阅读", "实践探究", "小论文", "项目任务"],
  },
  单元复习: {
    基础巩固: ["知识梳理", "概念辨析", "基础检测", "出门测"],
    综合提升: ["专题训练", "综合大题", "易错判断", "重点复盘"],
    拓展挑战: ["跨章综合", "创新应用", "高阶挑战", "成果展示"],
  },
  分层作业: {
    基础巩固: ["必做A组", "概念判断", "基础巩固", "自评反馈"],
    综合提升: ["选做B组", "变式训练", "综合应用", "互助互评"],
    拓展挑战: ["挑战C组", "探究实践", "拓展阅读", "反思总结"],
  },
};

const pptRecommendation = computed(() =>
  (
    pptPreviewStructure[pptForm.value.style] ||
    pptPreviewStructure["实验探究型"]
  ).map((title, index) => ({
    index: index + 1,
    title,
    note:
      index === 0
        ? `${pptForm.value.topic || "等待填写课题"} · ${
            pptForm.value.grade || "未选学段"
          } · ${pptForm.value.duration}`
        : "",
  })),
);

const docRecommendation = computed(() =>
  (
    docPreviewStructure[docForm.value.format] || docPreviewStructure["标准教案"]
  ).map((title, index) => ({
    index: index + 1,
    title,
    note:
      index === 0
        ? `明确"${docForm.value.topic || "本课"}"的教学目标与${docForm.value.subject || "学科"}核心素养方向`
        : index === 1
          ? `聚焦${docForm.value.subject || "学科"}关键难点，预设差异化突破策略`
          : index === 2
            ? `参考${docForm.value.style || "常规"}风格，分析学生认知起点与潜在误区`
            : index === 3
              ? `按${docForm.value.format}结构准备教具、多媒体与板书框架`
              : index === 4
                ? `设计导入→探究→收束主线，每环节嵌入互动与即时反馈`
                : `围绕"${docForm.value.topic || "本课"}"布置分层课后任务，巩固核心知识`,
  })),
);

const questionRecommendation = computed(() => {
  const scenarioKey = questionForm.value.scenario || "随堂检测";
  const diffKey = questionForm.value.difficulty || "综合提升";
  const structure = questionPreviewStructure[scenarioKey];
  const entries = structure?.[diffKey] || structure?.["综合提升"] || [];

  return entries.map((title, index) => ({
    index: index + 1,
    title,
    note:
      index === 0
        ? `以"${questionForm.value.topic || "知识点"}"切入，${questionForm.value.stage}水平快速摸底`
        : index === 1
          ? `聚焦${diffKey}目标，设计典型例题与即时变式`
          : index === 2
            ? `结合${scenarioKey}场景，推送${questionForm.value.subject || "学科"}情境应用题`
            : `汇总共${questionForm.value.count}题作答数据，生成随堂诊断与课后建议`,
  }));
});

const examRecommendation = computed(() => {
  const blueprint =
    examPreviewStructure[examForm.value.difficulty] ||
    examPreviewStructure["中等"];
  let total = 0;
  const totalScore = examForm.value.totalScore || 100;
  return blueprint.map((section, index) => {
    const subtotal = section.count * section.score;
    total += subtotal;
    return {
      index: index + 1,
      ...section,
      subtotal,
      caption:
        index === 0
          ? `覆盖${examForm.value.topic || "知识点"}的基础概念，检查${examForm.value.grade}学生掌握程度`
          : index === 1
            ? `从"${section.desc}"切入，衔接选择题的薄弱环节`
            : `设置${section.count}道综合题，考查${examForm.value.difficulty}难度的完整推理能力`,
    };
  });
});

const filteredHistory = computed(() => {
  let result = history.value;

  // 按类型筛选
  const typeFilter = archiveFilters.value.type;
  if (typeFilter && typeFilter !== "all") {
    result = result.filter((item) => item.type === typeFilter);
  }

  // 按学科筛选
  if (archiveFilters.value.subject) {
    result = result.filter(
      (item) => item.subject === archiveFilters.value.subject,
    );
  }

  // 按状态筛选
  if (archiveFilters.value.status) {
    result = result.filter(
      (item) => item.status === archiveFilters.value.status,
    );
  }

  // 按时间范围筛选
  if (archiveFilters.value.timeRange) {
    const now = Date.now();
    const ranges = {
      today: 1,
      week: 7,
      month: 30,
      quarter: 90,
    };
    const days = ranges[archiveFilters.value.timeRange];
    if (days) {
      const cutoff = now - days * 24 * 60 * 60 * 1000;
      result = result.filter((item) => item.createdAt >= cutoff);
    }
  }

  // 按搜索关键词
  const keyword = (archiveFilters.value.searchQuery || historyQuery.value)
    .trim()
    .toLowerCase();
  if (keyword) {
    result = result.filter((item) =>
      [item.title, item.subject, TYPE_LABELS[item.type]]
        .filter(Boolean)
        .some((text) => text.toLowerCase().includes(keyword)),
    );
  }

  // 按排序
  if (archiveSortBy.value === "newest") {
    result = [...result].sort((a, b) => b.createdAt - a.createdAt);
  } else if (archiveSortBy.value === "oldest") {
    result = [...result].sort((a, b) => a.createdAt - b.createdAt);
  } else if (archiveSortBy.value === "title") {
    result = [...result].sort((a, b) => a.title.localeCompare(b.title));
  }

  return result;
});

const pageSize = 8;
const totalHistoryPages = computed(() =>
  Math.max(1, Math.ceil(filteredHistory.value.length / pageSize)),
);
const paginatedHistory = computed(() => {
  const start = (historyPage.value - 1) * pageSize;
  return filteredHistory.value.slice(start, start + pageSize);
});
const archivePageNumbers = computed(() => {
  const total = totalHistoryPages.value;
  const current = historyPage.value;
  if (total <= 5) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [];
  if (current <= 3) {
    for (let i = 1; i <= 4; i++) pages.push(i);
    pages.push(total);
  } else if (current >= total - 2) {
    pages.push(1);
    for (let i = total - 3; i <= total; i++) pages.push(i);
  } else {
    pages.push(1);
    for (let i = current - 1; i <= current + 1; i++) pages.push(i);
    pages.push(total);
  }
  return [...new Set(pages)];
});

// 筛选后的意见反馈列表
const feedbackItems = computed(() => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
  const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

  return history.value
    .filter((item) => item.status === "iterating" || item.status === "draft")
    .filter((item) => {
      if (
        feedbackFilters.value.subject &&
        item.subject !== feedbackFilters.value.subject
      )
        return false;
      if (
        feedbackFilters.value.type &&
        item.type !== feedbackFilters.value.type
      )
        return false;
      if (feedbackFilters.value.timeRange) {
        const itemDate = new Date(item.createdAt);
        switch (feedbackFilters.value.timeRange) {
          case "today":
            if (itemDate < today) return false;
            break;
          case "week":
            if (itemDate < weekAgo) return false;
            break;
          case "month":
            if (itemDate < monthAgo) return false;
            break;
        }
      }
      if (feedbackFilters.value.searchQuery) {
        const query = feedbackFilters.value.searchQuery.toLowerCase();
        const matchTitle = item.title?.toLowerCase().includes(query);
        const matchSubject = item.subject?.toLowerCase().includes(query);
        if (!matchTitle && !matchSubject) return false;
      }
      return true;
    })
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .map((item) => ({
      ...item,
      typeLabel: TYPE_LABELS[item.type],
      statusLabel: STATUS_LABELS[item.status],
      timeLabel: formatFeatureTime(item.createdAt),
      feedback: iterateFeedback.value[item.id] || "",
    }));
});

// 意见反馈统计
const feedbackStats = computed(() => {
  const items = feedbackItems.value;
  return {
    total: items.length,
    byType: {
      ppt: items.filter((i) => i.type === "ppt").length,
      doc: items.filter((i) => i.type === "doc").length,
      interactive: items.filter((i) => i.type === "interactive").length,
    },
  };
});

// 重置筛选
function resetFeedbackFilters() {
  feedbackFilters.value = {
    subject: "",
    type: "",
    timeRange: "",
    searchQuery: "",
  };
}

const intentSupport = [
  "把“教学意图”做成生成流程的前置信息层，而不是单独孤立的工具页。",
  "先明确课堂目标、学生难点和使用场景，再让系统去生成课件、教案和教学题。",
];

const taskMoments = computed(() => [
  {
    label: "进行中任务",
    value: isGenerating.value
      ? "1个"
      : `${Math.max(stats.value.iterating, 1)}个`,
    detail: isGenerating.value
      ? "正在整理内容结构与推荐目录"
      : "待优化内容会在这里形成下一步动作",
  },
  {
    label: "推荐动作",
    value: activePanel.value === "overview" ? "3条" : "2条",
    detail:
      activePanel.value === "overview"
        ? "继续生成课件、整理教案、补充教学题"
        : `当前聚焦：${panelTitles[activePanel]}`,
  },
]);

// 任务状态环形图数据
const taskRingData = computed(() => [
  {
    label: "已完成",
    value: stats.value.completed || 8,
    color: "#23c3b2",
    innerColor: "#d1fae5",
  },
  {
    label: "待优化",
    value: stats.value.iterating || 4,
    color: "#7c5cff",
    innerColor: "#ede9fe",
  },
  {
    label: "草稿中",
    value:
      stats.value.total -
        (stats.value.completed || 8) -
        (stats.value.iterating || 4) || 2,
    color: "#f59e0b",
    innerColor: "#fef3c7",
  },
]);

// 计算环形图 SVG 路径
const ringChartSegments = computed(() => {
  const total =
    taskRingData.value.reduce((s, d) => s + Math.max(d.value, 0), 0) || 1;
  const radius = 58;
  const strokeWidth = 22;
  const center = 70;
  const circumference = 2 * Math.PI * radius;
  let offset = 0.25; // 从顶部开始

  return taskRingData.value.map((item) => {
    const ratio = Math.max(item.value, 0) / total;
    const length = ratio * circumference;
    const start = offset * circumference;
    const segment = {
      dashArray: `${length} ${circumference - length}`,
      dashOffset: -start,
      color: item.color,
      label: item.label,
      value: item.value,
      ratio: Math.round(ratio * 100),
    };
    offset += ratio;
    return segment;
  });
});

let toastTimer = null;
const hoveredRingSegment = ref(-1);

// ==================== ECharts 任务状态饼图 ====================
const taskPieChartRef = ref(null);
const taskPieChartInstance = ref(null);

// 生成任务状态饼图配置
function generateTaskPieChartOption() {
  const data = taskRingData.value.map((item) => ({
    value: item.value,
    name: item.label,
    itemStyle: {
      color: item.color,
    },
  }));

  const total = data.reduce((sum, item) => sum + item.value, 0);

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
      right: "0%",
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
        return `{name|${name}}  {value|${count}}`;
      },
      textStyle: {
        rich: {
          name: {
            fontSize: 13,
            color: "#475569",
            width: 60,
          },
          value: {
            fontSize: 14,
            fontWeight: 600,
            color: "#334155",
          },
        },
      },
    },
    series: [
      {
        name: "任务状态",
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
          show: true,
          position: "center",
          formatter: function () {
            return `{total|${total}}\n{label|全部任务}`;
          },
          rich: {
            total: {
              fontSize: 24,
              fontWeight: 800,
              color: "#334155",
              lineHeight: 32,
            },
            label: {
              fontSize: 11,
              color: "#94a3b8",
              lineHeight: 16,
            },
          },
        },
        emphasis: {
          scale: true,
          scaleSize: 10,
          label: {
            show: true,
            formatter: function (params) {
              return `{name|${params.name}}\n{value|${params.value}}\n{unit|个}`;
            },
            rich: {
              name: {
                fontSize: 12,
                color: "#64748b",
                lineHeight: 18,
              },
              value: {
                fontSize: 22,
                fontWeight: 800,
                color: "#334155",
                lineHeight: 28,
              },
              unit: {
                fontSize: 11,
                color: "#94a3b8",
              },
            },
          },
          itemStyle: {
            shadowBlur: 20,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.2)",
            borderWidth: 3,
          },
        },
        labelLine: {
          show: false,
        },
        data: data,
        // 动画效果
        animationType: "scale",
        animationEasing: "elasticOut",
        animationDelay: function (idx) {
          return Math.random() * 200;
        },
      },
    ],
    animationDuration: 1000,
    animationEasing: "cubicOut",
  };
}

// 初始化任务状态饼图
function initTaskPieChart() {
  console.log("初始化任务状态饼图, ref:", taskPieChartRef.value);
  if (!taskPieChartRef.value) {
    setTimeout(initTaskPieChart, 100);
    return;
  }

  try {
    if (taskPieChartInstance.value) {
      taskPieChartInstance.value.dispose();
      taskPieChartInstance.value = null;
    }

    const container = taskPieChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("任务状态饼图容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      setTimeout(initTaskPieChart, 200);
      return;
    }

    taskPieChartInstance.value = echarts.init(container);
    const option = generateTaskPieChartOption();
    taskPieChartInstance.value.setOption(option);
    console.log("任务状态饼图初始化成功");

    // 监听数据变化更新图表
    watch(
      taskRingData,
      () => {
        updateTaskPieChart();
      },
      { deep: true },
    );
  } catch (error) {
    console.error("任务状态饼图初始化失败:", error);
  }
}

// 更新任务状态饼图
function updateTaskPieChart() {
  if (taskPieChartInstance.value) {
    const option = generateTaskPieChartOption();
    taskPieChartInstance.value.setOption(option, true);
  }
}

// 监听窗口大小变化
function handleTaskPieResize() {
  if (taskPieChartInstance.value) {
    taskPieChartInstance.value.resize();
  }
}

// ==================== ECharts 本周创作趋势折线图 ====================
const trendLineChartRef = ref(null);
const trendLineChartInstance = ref(null);

// 生成本周创作趋势折线图配置
function generateTrendLineChartOption() {
  const data = trendItems.value;
  const dates = data.map((item) => item.label);
  const values = data.map((item) => item.value);
  const maxValue = Math.max(...values, 8);
  const minValue = Math.min(...values);
  const avgValue = Math.round(
    values.reduce((a, b) => a + b, 0) / values.length,
  );
  const maxIndex = values.indexOf(maxValue);

  // 按值分档颜色
  function getNodeColor(val) {
    if (val >= 7) return "#23c3b2";
    if (val >= 5) return "#4c7dff";
    return "#a78bfa";
  }

  return {
    // ===== 颜色主题 =====
    color: ["#4c7dff"],
    // ===== 背景区域标识生产效率区间 =====
    visualMap: {
      show: false,
      pieces: [
        { gte: 7, color: "#23c3b2" },
        { gte: 5, lte: 6, color: "#4c7dff" },
        { lt: 5, color: "#a78bfa" },
      ],
      dimension: 1,
    },
    // ===== 提示框 =====
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderColor: "#e2e8f0",
      borderWidth: 1,
      padding: [14, 18],
      textStyle: { color: "#1e293b", fontSize: 13 },
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-radius: 14px;",
      formatter: function (params) {
        const idx = params[0].dataIndex;
        const item = data[idx];
        const value = params[0].value;
        const efficiency =
          value >= 7 ? "🔥 高效日" : value >= 5 ? "📋 正常" : "☕ 轻松";
        const efficiencyColor = getNodeColor(value);
        const isMax = value === maxValue;
        const isAvgAbove = value >= avgValue;

        let html =
          '<div style="font-weight:700;margin-bottom:8px;font-size:14px;color:#1e293b;">' +
          item.label +
          " " +
          item.date;
        if (isMax)
          html +=
            ' <span style="color: #f59e0b; font-size: 13px;">🏆 本周最高</span>';
        html += "</div>";

        html +=
          '<div style="display: flex; align-items: center; gap: 8px; margin: 8px 0;">';
        html +=
          '<span style="display:inline-block;width:8px;height:8px;background:' +
          efficiencyColor +
          ';border-radius:50%;"></span>';
        html +=
          '<span>创作数量: <strong style="font-size:16px;color:' +
          efficiencyColor +
          ';">' +
          value +
          "</strong> 个</span>";
        html += "</div>";

        html +=
          '<div style="display:flex;gap:12px;font-size:12px;color:#64748b;">';
        html += "<span>日均 " + avgValue + " 个</span>";
        html +=
          "<span>" + (value >= avgValue ? "高于均值" : "低于均值") + "</span>";
        html += "</div>";

        html +=
          '<div style="display:inline-block;margin-top:8px;padding:2px 10px;background:' +
          efficiencyColor +
          "15;border-radius:10px;color:" +
          efficiencyColor +
          ';font-size:11px;font-weight:600;">';
        html += efficiency;
        html += "</div>";

        return html;
      },
    },
    // ===== 网格布局 =====
    grid: {
      left: "5%",
      right: "6%",
      bottom: "12%",
      top: "12%",
      containLabel: true,
    },
    // ===== X轴 =====
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: dates,
      axisLine: {
        lineStyle: { color: "#e8ecf1" },
      },
      axisTick: { show: false },
      axisLabel: {
        color: "#334155",
        fontSize: 13,
        fontWeight: 600,
        margin: 14,
        formatter: function (value, index) {
          return `{day|${value}}\n{date|${data[index].date}}`;
        },
        rich: {
          day: {
            fontSize: 13,
            fontWeight: 700,
            color: "#334155",
            lineHeight: 20,
            padding: [0, 0, 2, 0],
          },
          date: {
            fontSize: 10,
            color: "#94a3b8",
            lineHeight: 14,
          },
        },
      },
    },
    // ===== Y轴 =====
    yAxis: {
      type: "value",
      name: "创作数量（个）",
      nameLocation: "end",
      nameGap: 10,
      nameTextStyle: {
        color: "#94a3b8",
        fontSize: 11,
        fontWeight: 500,
      },
      min: 0,
      max: Math.ceil(maxValue * 1.25),
      interval: 2,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: "#94a3b8",
        fontSize: 12,
        fontWeight: 500,
        formatter: "{value}",
      },
      splitLine: {
        lineStyle: {
          color: "#f1f5f9",
          type: "dashed",
          dashOffset: 5,
        },
      },
    },
    // ===== 数据系列 =====
    series: [
      {
        name: "创作数量",
        type: "line",
        smooth: 0.35,
        symbol: "circle",
        symbolSize: function (val, params) {
          return params.dataIndex === maxIndex ? 14 : 8;
        },
        // === 线条样式 ===
        lineStyle: {
          width: 3.5,
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#667eea" },
            { offset: 0.5, color: "#764ba2" },
            { offset: 1, color: "#23c3b2" },
          ]),
          shadowColor: "rgba(102, 126, 234, 0.35)",
          shadowBlur: 12,
          shadowOffsetY: 4,
        },
        // === 节点样式 ===
        itemStyle: {
          color: function (params) {
            return getNodeColor(params.value);
          },
          borderColor: "#fff",
          borderWidth: 2.5,
          shadowColor: "rgba(102, 126, 234, 0.4)",
          shadowBlur: 10,
        },
        // === 面积填充 ===
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(102, 126, 234, 0.45)" },
            { offset: 0.35, color: "rgba(118, 75, 162, 0.22)" },
            { offset: 0.7, color: "rgba(35, 195, 178, 0.08)" },
            { offset: 1, color: "rgba(35, 195, 178, 0.01)" },
          ]),
        },
        // === 高亮状态 ===
        emphasis: {
          scale: 3,
          focus: "series",
          itemStyle: {
            shadowBlur: 20,
            shadowColor: "rgba(102, 126, 234, 0.6)",
            borderWidth: 3,
          },
        },
        // === 数据标签 ===
        label: {
          show: true,
          position: "top",
          distance: 12,
          color: "#334155",
          fontSize: 12,
          fontWeight: 700,
          formatter: function (params) {
            return params.dataIndex === maxIndex
              ? `{max|${params.value}}\n{tag|最高}`
              : `{normal|${params.value}}`;
          },
          rich: {
            normal: {
              fontSize: 12,
              fontWeight: 600,
              color: "#64748b",
            },
            max: {
              fontSize: 15,
              fontWeight: 800,
              color: "#23c3b2",
              textShadowColor: "rgba(35, 195, 178, 0.3)",
              textShadowBlur: 6,
            },
            tag: {
              fontSize: 10,
              color: "#f59e0b",
              fontWeight: 700,
              backgroundColor: "#fffbeb",
              borderRadius: 4,
              padding: [1, 6],
            },
          },
        },
        // === 平均线标记 ===
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: {
            color: "#f59e0b",
            type: "dashed",
            width: 2,
            opacity: 0.7,
          },
          label: {
            position: "end",
            formatter: `均值 ${avgValue}`,
            fontSize: 12,
            fontWeight: 600,
            color: "#f59e0b",
            backgroundColor: "#fffbeb",
            borderRadius: 8,
            padding: [4, 12],
            borderColor: "#f59e0b30",
            borderWidth: 1,
          },
          data: [{ yAxis: avgValue, name: "日均产出" }],
        },
        data: values,
        // === 动画 ===
        animationDuration: 2000,
        animationEasing: "cubicOut",
        animationDelay: function (idx) {
          return idx * 80;
        },
      },
    ],
  };
}

// 初始化本周创作趋势折线图
function initTrendLineChart() {
  console.log("初始化趋势折线图, ref:", trendLineChartRef.value);
  if (!trendLineChartRef.value) {
    setTimeout(initTrendLineChart, 100);
    return;
  }

  try {
    if (trendLineChartInstance.value) {
      trendLineChartInstance.value.dispose();
      trendLineChartInstance.value = null;
    }

    const container = trendLineChartRef.value;
    const rect = container.getBoundingClientRect();
    console.log("趋势折线图容器尺寸:", rect.width, rect.height);

    if (rect.width === 0 || rect.height === 0) {
      setTimeout(initTrendLineChart, 200);
      return;
    }

    trendLineChartInstance.value = echarts.init(container);
    const option = generateTrendLineChartOption();
    trendLineChartInstance.value.setOption(option);
    console.log("趋势折线图初始化成功");

    // 点击事件 - 支持数据点和X轴标签
    trendLineChartInstance.value.on("click", function (params) {
      let item = null;
      if (params.componentType === "series") {
        // 点击数据点
        item = trendItems.value[params.dataIndex];
      } else if (params.componentType === "xAxis") {
        // 点击X轴日期标签
        item = trendItems.value.find((d) => d.label === params.value);
      }
      if (item) {
        showDayDetail(item);
      }
    });
    // 已选中日期的数据点高亮还原
    trendLineChartInstance.value.getZr().on("click", function (params) {
      if (!params.target) {
        // 点击空白区域关闭详情
        closeDayDetail();
      }
    });
  } catch (error) {
    console.error("趋势折线图初始化失败:", error);
  }
}

// 更新趋势折线图
function updateTrendLineChart() {
  if (trendLineChartInstance.value) {
    const option = generateTrendLineChartOption();
    trendLineChartInstance.value.setOption(option, true);
  }
}

// 监听窗口大小变化
function handleTrendLineResize() {
  if (trendLineChartInstance.value) {
    trendLineChartInstance.value.resize();
  }
}

function refresh() {
  history.value = getHistory();
  stats.value = getStats();
}

function selectPanel(id) {
  activePanel.value = id;
  sidebarOpen.value = false;
}

function showToast(message) {
  toast.value = message;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.value = "";
  }, 2600);
}

// ── 真实 API 课件生成 ─────────────────────────────────
const typeToApiType = {
  ppt: "ppt",
  doc: "doc",
  interactive: "quiz",
};

async function callApiGenerate(apiType, params) {
  const panel = panelByApiType[apiType] || "ppt";
  isGenerating.value = true;
  exporting.value = false;
  currentTaskProgress.value = 0;
  currentTaskStage.value = "启动中…";
  contentReady.value = false;
  generatedFilename.value = "";
  reviseMessages.value[panel] = [];

  try {
    const { taskId } = await submitCoursewareTask({
      type: apiType,
      ...params,
    });
    currentTaskId.value = taskId;

    // 新建流式正文消息，随后续 SSE delta 增量填充
    const streamMsg = startStreamMessage(panel);

    // 订阅 SSE：正文增量 + 进度
    subscribeProgress(taskId, {
      ...subscribeStream(streamMsg),
      onDone: () => {
        isGenerating.value = false;
        streamMsg.streaming = false;
        contentReady.value = true;
        showToast("内容已生成，可在右侧查看并修改");

        // 将新记录写入历史列表（localStorage）
        // API type 映射: quiz → interactive, exam → exam
        const typeMap = { quiz: "interactive", exam: "exam" };
        const historyType = typeMap[apiType] || apiType;
        addRecord({
          taskId,
          type: historyType,
          title: params.topic || "新生成的内容",
          subject: params.subject || "未分类",
          status: "completed",
        });

        history.value = getHistory();
        stats.value = getStats();
      },
    });
  } catch (err) {
    isGenerating.value = false;
    reviseMessages.value[panel] = [
      {
        id: nextReviseId(),
        role: "assistant",
        text: `提交失败：${err.message}`,
      },
    ];
    showToast(`提交失败：${err.message}`);
  }
}

// 课件生成
function handlePptGenerate() {
  if (!pptForm.value.topic.trim()) return showToast("请先填写课题名称");
  const subject = resolveSubjectName(pptForm.value);
  if (!subject) return showToast("请选择学科");
  if (!pptForm.value.grade) return showToast("请选择学段");
  const goals = resolveText(
    pptForm.value.teachingGoals,
    pptForm.value.goalCustom,
  );
  const keys = resolveText(pptForm.value.keyPoints, pptForm.value.keyCustom);
  if (!goals.trim()) return showToast("请选择或填写教学目标");
  if (!keys.trim()) return showToast("请选择或填写重点与难点");

  const student = resolveText(
    pptForm.value.studentProfile,
    pptForm.value.studentProfileCustom,
  );
  const interaction = resolveText(
    pptForm.value.interactionDesign,
    pptForm.value.interactionCustom,
  );
  const scene = resolveText(
    pptForm.value.usageScene,
    pptForm.value.usageSceneCustom,
  );
  const assess = resolveText(
    pptForm.value.assessment,
    pptForm.value.assessmentCustom,
  );

  const outlineParts = [`教学目标：${goals}`, `重点与难点：${keys}`];
  if (student.trim()) outlineParts.push(`学生学情：${student}`);
  if (interaction.trim()) outlineParts.push(`课堂互动设计：${interaction}`);
  if (scene.trim()) outlineParts.push(`使用场景：${scene}`);
  if (assess.trim()) outlineParts.push(`评估侧重：${assess}`);
  const pagesHint = PAGES_SECTION_HINT[pptForm.value.pages] || "";
  if (pagesHint)
    outlineParts.push(`课件篇幅：${pptForm.value.pages}，${pagesHint}`);
  const outlineCustom = pptForm.value.outlineCustom.trim();
  if (outlineCustom) {
    const sections = outlineCustom
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean)
      .map((s) =>
        s.replace(
          /^[（(]?第?[一二三四五六七八九十\d]+[章节部分]?[）)]?[、.\s]*/,
          "",
        ),
      );
    outlineParts.push(
      `请严格按照以下章节结构组织课件内容，每章一节扉页：\n${sections.join("\n")}`,
    );
  }
  callApiGenerate("ppt", {
    subject,
    topic: pptForm.value.topic,
    grade: pptForm.value.grade,
    duration: pptForm.value.duration,
    style: pptForm.value.style || "实验探究型",
    outline: outlineParts.join("；"),
    studentProfile: student,
    interactionDesign: interaction,
    usageScene: scene,
    assessment: assess,
    sparkTemplateId: pptForm.value.sparkTemplateId || "",
    isCardNote: pptForm.value.isCardNote,
    isFigure: pptForm.value.isFigure,
  });
}

// 教案生成
function handleDocGenerate() {
  if (!docForm.value.topic.trim()) return showToast("请先填写课题名称");
  const subject = resolveSubjectName(docForm.value);
  if (!subject) return showToast("请选择学科");
  if (!docForm.value.grade) return showToast("请选择学段");
  const goals = resolveText(
    docForm.value.teachingGoals,
    docForm.value.goalCustom,
  );
  const keys = resolveText(docForm.value.keyPoints, docForm.value.keyCustom);
  if (!goals.trim()) return showToast("请选择或填写教学目标");
  if (!keys.trim()) return showToast("请选择或填写重点与难点");

  const student = resolveText(
    docForm.value.studentProfile,
    docForm.value.studentProfileCustom,
  );
  const focus = resolveText(
    docForm.value.lessonFocus,
    docForm.value.lessonFocusCustom,
  );
  const scene = resolveText(
    docForm.value.usageScene,
    docForm.value.usageSceneCustom,
  );
  const assess = resolveText(
    docForm.value.assessment,
    docForm.value.assessmentCustom,
  );

  const parts = [
    docForm.value.format || "标准教案",
    docForm.value.style || "",
    `教学目标：${goals}`,
    `重点与难点：${keys}`,
  ];
  if (student.trim()) parts.push(`学生学情：${student}`);
  if (focus.trim()) parts.push(`教学环节侧重：${focus}`);
  if (scene.trim()) parts.push(`使用场景：${scene}`);
  if (assess.trim()) parts.push(`评估侧重：${assess}`);

  callApiGenerate("doc", {
    subject,
    topic: docForm.value.topic,
    grade: docForm.value.grade,
    duration: docForm.value.duration,
    requirements: parts.join(" | "),
    studentProfile: student,
    lessonFocus: focus,
    usageScene: scene,
    assessment: assess,
  });
}

// 教学题生成
function handleQuestionGenerate() {
  if (!questionForm.value.topic.trim()) return showToast("请先填写知识点");
  const subject = resolveSubjectName(questionForm.value);
  if (!subject) return showToast("请选择学科");
  const target = resolveText(
    questionForm.value.target,
    questionForm.value.targetCustom,
  );
  const student = resolveText(
    questionForm.value.studentProfile,
    questionForm.value.studentProfileCustom,
  );
  const qtypes = resolveText(
    questionForm.value.questionTypes,
    questionForm.value.questionTypesCustom,
  );
  const assess = resolveText(
    questionForm.value.assessment,
    questionForm.value.assessmentCustom,
  );
  const scenario = resolveText(
    questionForm.value.scenario,
    questionForm.value.scenarioCustom,
  );
  callApiGenerate("quiz", {
    subject,
    topic: questionForm.value.topic,
    grade: questionForm.value.stage || "高中",
    difficulty: questionForm.value.difficulty || "综合提升",
    scenario: scenario || "随堂检测",
    count: questionForm.value.count || 8,
    questionTypes: qtypes,
    target,
    studentProfile: student,
    assessment: assess,
  });
}

function handleExamGenerate() {
  if (!examForm.value.topic.trim())
    return showToast("请先填写知识点或考试范围");
  const subject = resolveSubjectName(examForm.value);
  if (!subject) return showToast("请选择学科");
  const target = resolveText(
    examForm.value.target,
    examForm.value.targetCustom,
  );
  const student = resolveText(
    examForm.value.studentProfile,
    examForm.value.studentProfileCustom,
  );
  const scene = resolveText(
    examForm.value.usageScene,
    examForm.value.usageSceneCustom,
  );
  const assess = resolveText(
    examForm.value.assessment,
    examForm.value.assessmentCustom,
  );
  callApiGenerate("exam", {
    subject,
    topic: examForm.value.topic,
    grade: examForm.value.grade,
    difficulty: examForm.value.difficulty,
    totalScore: examForm.value.totalScore,
    choiceCount: examForm.value.choiceCount,
    fillCount: examForm.value.fillCount,
    essayCount: examForm.value.essayCount,
    generateAB: examForm.value.generateAB,
    usageScene: scene,
    assessment: assess,
    target,
    studentProfile: student,
  });
}

// 课件文件上传处理
const pptFileInput = ref(null);

function triggerPptFileUpload() {
  pptFileInput.value?.click();
}

function handlePptFileChange(event) {
  const file = event.target.files[0];
  if (file) {
    const validTypes = [
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/vnd.ms-powerpoint",
      "application/pdf",
    ];
    if (
      !validTypes.includes(file.type) &&
      !file.name.match(/\.(ppt|pptx|pdf)$/i)
    ) {
      showToast("请上传 PPT 或 PDF 格式的文件");
      return;
    }
    pptForm.value.referenceFile = file;
    showToast(`已上传参考课件：${file.name}`);
  }
}

function handlePptFileDrop(event) {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) {
    const validTypes = [
      "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      "application/vnd.ms-powerpoint",
      "application/pdf",
    ];
    if (
      !validTypes.includes(file.type) &&
      !file.name.match(/\.(ppt|pptx|pdf)$/i)
    ) {
      showToast("请上传 PPT 或 PDF 格式的文件");
      return;
    }
    pptForm.value.referenceFile = file;
    showToast(`已上传参考课件：${file.name}`);
  }
}

function removePptFile() {
  pptForm.value.referenceFile = null;
  if (pptFileInput.value) {
    pptFileInput.value.value = "";
  }
}

// 教案文件上传处理
const docFileInput = ref(null);

function triggerDocFileUpload() {
  docFileInput.value?.click();
}

function handleDocFileChange(event) {
  const file = event.target.files[0];
  if (file) {
    const validTypes = [
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/pdf",
    ];
    if (
      !validTypes.includes(file.type) &&
      !file.name.match(/\.(doc|docx|pdf)$/i)
    ) {
      showToast("请上传 DOC 或 PDF 格式的文件");
      return;
    }
    docForm.value.referenceFile = file;
    showToast(`已上传参考教案：${file.name}`);
  }
}

function handleDocFileDrop(event) {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) {
    const validTypes = [
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "application/pdf",
    ];
    if (
      !validTypes.includes(file.type) &&
      !file.name.match(/\.(doc|docx|pdf)$/i)
    ) {
      showToast("请上传 DOC 或 PDF 格式的文件");
      return;
    }
    docForm.value.referenceFile = file;
    showToast(`已上传参考教案：${file.name}`);
  }
}

function removeDocFile() {
  docForm.value.referenceFile = null;
  if (docFileInput.value) {
    docFileInput.value.value = "";
  }
}

function onFileChange(event) {
  const files = Array.from(event.target.files || []);
  uploadFiles.value = [
    ...uploadFiles.value,
    ...files.map((file) => ({
      name: file.name,
      size: file.size,
      type: file.type,
    })),
  ];
  event.target.value = "";
}

function removeFile(index) {
  uploadFiles.value.splice(index, 1);
}

function handleDelete(id) {
  if (!confirm("确定要删除这条记录吗？删除后无法恢复。")) return;
  deleteRecord(id);
  refresh();
  showToast("记录已删除");
}

// 记录卡片展开/收起
function toggleRecordExpand(id) {
  expandedRecord.value = expandedRecord.value === id ? null : id;
}

// ==================== 教学档案筛选方法（新版）====================
// 计算已选筛选条件数量
const activeArchiveFilterCount = computed(() => {
  return Object.values(archiveFilters.value).filter((v) => v && v !== "")
    .length;
});

// 切换筛选组展开状态
function toggleArchiveFilterGroup(group) {
  const index = activeArchiveFilterGroups.value.indexOf(group);
  if (index > -1) {
    activeArchiveFilterGroups.value.splice(index, 1);
  } else {
    activeArchiveFilterGroups.value.push(group);
  }
}

// 重置所有筛选条件
function resetArchiveFilters() {
  archiveFilters.value = {
    type: "",
    subject: "",
    grade: "",
    status: "",
    timeRange: "",
    format: "",
    difficulty: "",
    searchQuery: "",
  };
  historyQuery.value = "";
  historyPage.value = 1;
}

// 应用保存的筛选方案
function applySavedArchiveFilter(saved) {
  archiveFilters.value = { ...archiveFilters.value, ...saved.filters };
  historyPage.value = 1;
}

// 保存当前筛选方案
function saveCurrentArchiveFilter() {
  const name = `方案 ${savedArchiveFilters.value.length + 1}`;
  savedArchiveFilters.value.push({
    name,
    filters: { ...archiveFilters.value },
  });
  showToast(`已保存筛选方案：${name}`);
}

// 获取记录预览文本
function getRecordPreview(item) {
  const previews = {
    ppt: `本课件围绕"${item.title}"展开，包含教学目标、重难点分析、教学过程设计等内容。适合用于课堂投屏讲授，帮助学生理解核心概念。`,
    doc: `本教案详细规划了"${item.title}"的教学流程，包括导入、新课讲授、练习巩固、小结等环节，可直接用于备课参考。`,
    interactive: `本教学题针对"${item.title}"设计，包含多种题型和难度层次，适合课堂练习或课后作业使用。`,
  };
  return previews[item.type] || "暂无预览内容";
}

// 查看记录详情
function previewRecord(item) {
  previewItem.value = item;
  showPreview.value = true;
}

// 继续编辑记录
function editRecord(item) {
  showToast(`正在加载编辑：${item.title}`);
  // 这里可以跳转到对应生成页面并加载内容
}

// 下载记录 — 真实 API 文件下载
function downloadRecord(item) {
  if (item.taskId) {
    downloadFile(item.taskId, item.filename || item.title);
    showToast(`正在下载：${item.filename || item.title}`);
  } else {
    showToast("该记录暂无可用文件");
  }
}

// 提交反馈
function feedbackRecord(item) {
  activePanel.value = "iterate";
  showToast(`已切换到意见反馈，请为"${item.title}"提交建议`);
}

function submitFeedback(item) {
  const value = iterateFeedback.value[item.id]?.trim();
  if (!value) return showToast("请先填写反馈内容");
  updateRecord(item.id, { status: "iterating" });
  showToast("反馈已提交，系统会据此继续优化");
  iterateFeedback.value = {
    ...iterateFeedback.value,
    [item.id]: "",
  };
  refresh();
}

function appendTag(tag) {
  const prefix = feedbackDesc.value.trim() ? `；${tag}：` : `${tag}：`;
  feedbackDesc.value += prefix;
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

function handleFileChange(e) {
  const file = e.target.files?.[0];
  if (file) {
    if (file.size > 20 * 1024 * 1024) {
      showToast("文件大小不能超过 20MB");
      return;
    }
    feedbackFileName.value = file.name;
  }
}

function removeFeedbackFile() {
  feedbackFileName.value = "";
  if (fileInputRef.value) fileInputRef.value.value = "";
}

function submitNewFeedback() {
  if (!feedbackType.value) return showToast("请选择反馈类型");
  if (!feedbackTitle.value?.trim()) return showToast("请填写反馈标题");
  if (!feedbackDesc.value?.trim()) return showToast("请填写详细描述");
  const contactInfo = feedbackContact.value?.trim()
    ? `（联系方式：${feedbackContact.value}）`
    : "";
  const fileInfo = feedbackFileName.value
    ? `[附件：${feedbackFileName.value}] `
    : "";
  showToast(`感谢您的反馈，已提交成功！${fileInfo}${contactInfo}`);
  feedbackType.value = "";
  feedbackTitle.value = "";
  feedbackDesc.value = "";
  feedbackContact.value = "";
  feedbackFileName.value = "";
  if (fileInputRef.value) fileInputRef.value.value = "";
}

// 添加快速提示到反馈
function addTipToFeedback(itemId, tip) {
  const currentFeedback = iterateFeedback.value[itemId] || "";
  const separator = currentFeedback ? "；" : "";
  iterateFeedback.value = {
    ...iterateFeedback.value,
    [itemId]: currentFeedback + separator + tip + "：",
  };
  showToast(`已添加「${tip}」到反馈内容`);
}

// 查看详情
function viewDetail(item) {
  showToast(`正在打开《${item.title}》详情...`);
}

watch(activePanel, refresh);
watch(historyQuery, () => {
  historyPage.value = 1;
});
watch(totalHistoryPages, (value) => {
  if (historyPage.value > value) historyPage.value = value;
});

// 生命周期钩子
onMounted(() => {
  // 加载讯飞智文模板（仅元数据，不消耗额度）
  fetchSparkTemplates();
  // 处理路由参数：面板
  const queryPanel = route.query.panel;
  if (queryPanel) {
    activePanel.value = queryPanel;
  }
  // 处理 AI 助手「转入生成」跳转参数：type=topic/outline 自动预填
  const queryType = route.query.type;
  const queryTopic = route.query.topic;
  const queryOutline = route.query.outline;
  if (queryType) {
    const panelMap = {
      ppt: "ppt",
      doc: "doc",
      quiz: "interactive",
      exam: "exam",
    };
    if (panelMap[queryType]) {
      activePanel.value = panelMap[queryType];
    }
    if (queryTopic) {
      if (queryType === "ppt") pptForm.value.topic = queryTopic;
      else if (queryType === "doc") docForm.value.topic = queryTopic;
      else if (queryType === "quiz") questionForm.value.topic = queryTopic;
      else if (queryType === "exam") examForm.value.topic = queryTopic;
    }
    if (queryType === "ppt" && queryOutline) {
      pptForm.value.outlineCustom = queryOutline;
    }
  }
  // 延迟初始化确保DOM完全渲染
  setTimeout(() => {
    nextTick(() => {
      initRadarChart();
      initTaskPieChart();
      initTrendLineChart();
    });
  }, 300);
  window.addEventListener("resize", handleRadarResize);
  window.addEventListener("resize", handleTaskPieResize);
  window.addEventListener("resize", handleTrendLineResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleRadarResize);
  window.removeEventListener("resize", handleTaskPieResize);
  window.removeEventListener("resize", handleTrendLineResize);
  if (radarChartInstance.value) {
    radarChartInstance.value.dispose();
    radarChartInstance.value = null;
  }
  if (taskPieChartInstance.value) {
    taskPieChartInstance.value.dispose();
    taskPieChartInstance.value = null;
  }
  if (trendLineChartInstance.value) {
    trendLineChartInstance.value.dispose();
    trendLineChartInstance.value = null;
  }
});
</script>

<template>
  <div class="features-page">
    <div class="features-page__ambient" aria-hidden="true">
      <span class="ambient-orb ambient-orb--one" />
      <span class="ambient-orb ambient-orb--two" />
      <span class="ambient-grid" />
    </div>

    <aside class="sidebar" :class="{ 'sidebar--open': sidebarOpen }">
      <div class="sidebar__head">
        <RouterLink to="/" class="icon-btn" title="返回首页">
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M12 4l-6 6 6 6"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </RouterLink>
        <div class="sidebar__brand">
          <span class="sidebar__brand-name">核心功能</span>
          <span class="sidebar__brand-sub">多模态教学创作工作台</span>
        </div>
      </div>

      <button
        class="overview-btn"
        :class="{ 'overview-btn--active': activePanel === 'overview' }"
        @click="selectPanel('overview')"
      >
        <svg viewBox="0 0 20 20" fill="none">
          <rect
            x="3"
            y="3"
            width="6"
            height="6"
            rx="1.5"
            stroke="currentColor"
            stroke-width="1.3"
          />
          <rect
            x="11"
            y="3"
            width="6"
            height="6"
            rx="1.5"
            stroke="currentColor"
            stroke-width="1.3"
          />
          <rect
            x="3"
            y="11"
            width="6"
            height="6"
            rx="1.5"
            stroke="currentColor"
            stroke-width="1.3"
          />
          <rect
            x="11"
            y="11"
            width="6"
            height="6"
            rx="1.5"
            stroke="currentColor"
            stroke-width="1.3"
          />
        </svg>
        核心功能概览
      </button>

      <nav
        v-for="group in navGroups"
        :key="group.label"
        class="nav-group"
        :class="{ 'nav-group--featured': group.featured }"
      >
        <p class="nav-group__label">{{ group.label }}</p>
        <button
          v-for="item in group.items"
          :key="item.id"
          class="nav-item"
          :class="{ 'nav-item--active': activePanel === item.id }"
          @click="selectPanel(item.id)"
        >
          <span class="nav-item__icon" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="none">
              <path
                v-for="path in featureIcons[item.icon]"
                :key="path"
                :d="path"
                stroke="currentColor"
                stroke-width="1.45"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
          <span class="nav-item__text">
            <strong>{{ item.label }}</strong>
            <small>{{ item.desc }}</small>
          </span>
        </button>
      </nav>

      <div class="sidebar__foot">
        <RouterLink to="/assistant" class="assistant-link">
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M4 6a3 3 0 0 1 3-3h6a3 3 0 0 1 3 3v4a3 3 0 0 1-3 3H9l-3 3v-3H7a3 3 0 0 1-3-3V6z"
              stroke="currentColor"
              stroke-width="1.3"
            />
          </svg>
          前往 AI 助手对话
        </RouterLink>
      </div>
    </aside>

    <div
      v-if="sidebarOpen"
      class="sidebar-overlay"
      @click="sidebarOpen = false"
    />

    <main class="main">
      <header class="main__header">
        <button
          class="icon-btn mobile-only"
          aria-label="打开菜单"
          @click="sidebarOpen = true"
        >
          <svg viewBox="0 0 20 20" fill="none">
            <path
              d="M3 5h14M3 10h14M3 15h14"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
            />
          </svg>
        </button>
        <div>
          <span class="header-chip">{{ panelChips[activePanel] }}</span>
        </div>
      </header>

      <div class="main__body">
        <div v-if="activePanel === 'overview'" class="panel panel--overview">
          <section class="workspace-header">
            <div class="workspace-header__text">
              <h2>创作工作台</h2>
              <p>查看本周任务状态，掌握创作节奏</p>
            </div>
            <div class="workspace-header__meta">
              <span class="meta-item">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <circle cx="12" cy="12" r="10" />
                  <polyline points="12 6 12 12 16 14" />
                </svg>
                更新于 {{ new Date().toLocaleDateString("zh-CN") }}
              </span>
            </div>
          </section>

          <div class="metric-grid">
            <article
              v-for="card in overviewCards"
              :key="card.label"
              class="metric-card"
              :data-tone="card.tone"
            >
              <div class="metric-card__head">
                <span class="metric-card__num" v-html="card.icon"></span>
                <span class="metric-card__label">{{ card.label }}</span>
              </div>
              <strong class="metric-card__value">{{ card.value }}</strong>
              <p class="metric-card__detail">{{ card.detail }}</p>
            </article>
          </div>

          <section class="insight-grid">
            <article class="dashboard-card dashboard-card--chart">
              <div class="section-head">
                <div>
                  <span class="section-tag">生成节奏</span>
                  <h3>本周创作趋势</h3>
                </div>
                <small>近 7 天</small>
              </div>

              <!-- 统计概览 -->
              <div class="trend-stats-bar">
                <div class="trend-stat">
                  <span class="trend-stat__value">{{ trendStats.total }}</span>
                  <span class="trend-stat__label">本周创作</span>
                </div>
                <div class="trend-stat">
                  <span class="trend-stat__value">{{ trendStats.avg }}</span>
                  <span class="trend-stat__label">日均产出</span>
                </div>
                <div class="trend-stat">
                  <span class="trend-stat__value">{{ trendStats.maxDay }}</span>
                  <span class="trend-stat__label">最高产日</span>
                </div>
                <div class="trend-stat trend-stat--subjects">
                  <div class="subject-tags">
                    <span
                      v-for="subj in trendStats.subjects"
                      :key="subj"
                      class="subject-tag"
                      >{{ subj }}</span
                    >
                  </div>
                  <span class="trend-stat__label">涉及学科</span>
                </div>
              </div>

              <!-- ECharts 本周创作趋势折线图 -->
              <div
                ref="trendLineChartRef"
                class="trend-line-chart-container"
              ></div>

              <!-- 日期详情面板 - 丰富内容 -->
              <Transition name="slide-fade">
                <div v-if="selectedDay" class="day-detail-panel">
                  <!-- 头部 -->
                  <div class="day-detail-header">
                    <div class="day-header-left">
                      <div class="day-date-badge">
                        <span class="day-weekday">{{ selectedDay.label }}</span>
                        <span class="day-date">{{ selectedDay.date }}</span>
                      </div>
                      <h4>创作详情</h4>
                    </div>
                    <div class="day-header-right">
                      <span
                        class="day-efficiency"
                        :class="selectedDay.efficiencyLevel"
                      >
                        <svg
                          viewBox="0 0 16 16"
                          fill="none"
                          class="efficiency-icon"
                        >
                          <circle
                            cx="8"
                            cy="8"
                            r="6"
                            stroke="currentColor"
                            stroke-width="2"
                          />
                          <path
                            d="M8 4v4l3 2"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                          />
                        </svg>
                        {{ selectedDay.efficiency }}
                      </span>
                      <button class="btn-close" @click="closeDayDetail">
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
                  </div>

                  <!-- 核心指标卡片 -->
                  <div class="day-metrics-grid">
                    <div class="day-metric-card total">
                      <div class="metric-icon"></div>
                      <div class="metric-info">
                        <span class="metric-value">{{
                          selectedDay.value
                        }}</span>
                        <span class="metric-label">创作总数</span>
                      </div>
                    </div>
                    <div class="day-metric-card score">
                      <div class="metric-icon">
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
                            d="M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z"
                          />
                        </svg>
                      </div>
                      <div class="metric-info">
                        <span class="metric-value">{{
                          selectedDay.avgScore
                        }}</span>
                        <span class="metric-label">平均质量分</span>
                      </div>
                    </div>
                    <div class="day-metric-card time">
                      <div class="metric-icon"></div>
                      <div class="metric-info">
                        <span class="metric-value"
                          >{{ selectedDay.totalTime }}<small>min</small></span
                        >
                        <span class="metric-label">预估耗时</span>
                      </div>
                    </div>
                    <div class="day-metric-card peak">
                      <div class="metric-icon">🔥</div>
                      <div class="metric-info">
                        <span class="metric-value">{{
                          selectedDay.peakHour
                        }}</span>
                        <span class="metric-label">创作高峰</span>
                      </div>
                    </div>
                  </div>

                  <!-- 分布统计 -->
                  <div class="day-distribution">
                    <!-- 类型分布 -->
                    <div class="dist-section">
                      <h5>类型分布</h5>
                      <div class="dist-bars">
                        <div
                          v-if="selectedDay.typeDistribution.ppt > 0"
                          class="dist-bar-item"
                        >
                          <span class="dist-label">课件</span>
                          <div class="dist-bar-bg">
                            <div
                              class="dist-bar-fill ppt"
                              :style="{
                                width:
                                  (selectedDay.typeDistribution.ppt /
                                    selectedDay.value) *
                                    100 +
                                  '%',
                              }"
                            ></div>
                          </div>
                          <span class="dist-count">{{
                            selectedDay.typeDistribution.ppt
                          }}</span>
                        </div>
                        <div
                          v-if="selectedDay.typeDistribution.doc > 0"
                          class="dist-bar-item"
                        >
                          <span class="dist-label">教案</span>
                          <div class="dist-bar-bg">
                            <div
                              class="dist-bar-fill doc"
                              :style="{
                                width:
                                  (selectedDay.typeDistribution.doc /
                                    selectedDay.value) *
                                    100 +
                                  '%',
                              }"
                            ></div>
                          </div>
                          <span class="dist-count">{{
                            selectedDay.typeDistribution.doc
                          }}</span>
                        </div>
                        <div
                          v-if="selectedDay.typeDistribution.interactive > 0"
                          class="dist-bar-item"
                        >
                          <span class="dist-label">教学题</span>
                          <div class="dist-bar-bg">
                            <div
                              class="dist-bar-fill interactive"
                              :style="{
                                width:
                                  (selectedDay.typeDistribution.interactive /
                                    selectedDay.value) *
                                    100 +
                                  '%',
                              }"
                            ></div>
                          </div>
                          <span class="dist-count">{{
                            selectedDay.typeDistribution.interactive
                          }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 学科分布 -->
                    <div class="dist-section subjects">
                      <h5>学科分布</h5>
                      <div class="subject-pills">
                        <div
                          v-for="(
                            count, subject
                          ) in selectedDay.subjectDistribution"
                          :key="subject"
                          class="subject-pill"
                        >
                          <span class="pill-name">{{ subject }}</span>
                          <span class="pill-count">{{ count }}个</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 课件列表 -->
                  <div class="day-items-section">
                    <h5>
                      创作清单 <small>({{ selectedDay.items.length }}项)</small>
                    </h5>
                    <div class="day-items">
                      <div
                        v-for="dItem in selectedDay.items"
                        :key="dItem.id"
                        class="day-item"
                      >
                        <div class="item-left">
                          <span class="day-item__type" :class="dItem.typeEn">{{
                            dItem.type
                          }}</span>
                          <span class="day-item__subject">{{
                            dItem.subject
                          }}</span>
                        </div>
                        <span class="day-item__title">{{ dItem.title }}</span>
                        <div class="item-right">
                          <span
                            class="day-item__score"
                            :class="{ high: dItem.aiScore >= 90 }"
                            >{{ dItem.aiScore }}分</span
                          >
                          <span class="day-item__time">{{ dItem.time }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 底部提示 -->
                  <div class="day-footer-tip">
                    <svg viewBox="0 0 20 20" fill="none" class="tip-icon">
                      <path
                        d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16z"
                        stroke="currentColor"
                        stroke-width="1.5"
                      />
                      <path
                        d="M10 14v-4M10 6h.01"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                      />
                    </svg>
                    <span>点击课件可查看详情或继续编辑</span>
                  </div>
                </div>
              </Transition>
            </article>

            <article class="dashboard-card dashboard-card--radar">
              <div class="section-head">
                <div>
                  <span class="section-tag">能力雷达</span>
                  <h3>教学产出能力分析</h3>
                </div>
              </div>

              <div class="radar-panel">
                <!-- 雷达图 -->
                <div class="radar-chart">
                  <svg viewBox="0 0 200 200" class="radar-svg">
                    <!-- 背景网格 -->
                    <g class="radar-grid">
                      <polygon
                        v-for="level in 4"
                        :key="level"
                        :points="radarGridPoints(level * 25)"
                        fill="none"
                        stroke="rgba(148, 163, 184, 0.15)"
                        stroke-width="1"
                      />
                    </g>
                    <!-- 轴线 -->
                    <g class="radar-axes">
                      <line
                        v-for="(axis, i) in radarAxes"
                        :key="i"
                        x1="100"
                        y1="100"
                        :x2="axis.x2"
                        :y2="axis.y2"
                        stroke="rgba(148, 163, 184, 0.2)"
                        stroke-width="1"
                      />
                    </g>
                    <!-- 数据区域 -->
                    <polygon
                      :points="radarDataPoints"
                      fill="url(#radarGradient)"
                      stroke="#4c7dff"
                      stroke-width="2"
                      class="radar-area"
                    />
                    <!-- 数据点 -->
                    <circle
                      v-for="(point, i) in radarDataPointsArray"
                      :key="i"
                      :cx="point.x"
                      :cy="point.y"
                      r="4"
                      fill="#fff"
                      stroke="#4c7dff"
                      stroke-width="2"
                      class="radar-point"
                    />
                    <!-- 渐变定义 -->
                    <defs>
                      <radialGradient
                        id="radarGradient"
                        cx="50%"
                        cy="50%"
                        r="50%"
                      >
                        <stop
                          offset="0%"
                          stop-color="#4c7dff"
                          stop-opacity="0.25"
                        />
                        <stop
                          offset="100%"
                          stop-color="#4c7dff"
                          stop-opacity="0.05"
                        />
                      </radialGradient>
                    </defs>
                  </svg>
                  <!-- 维度标签 -->
                  <div class="radar-labels">
                    <span
                      v-for="(dim, i) in radarDimensionsWithLabels"
                      :key="i"
                      class="radar-label"
                      :style="{ left: dim.labelX, top: dim.labelY }"
                    >
                      {{ dim.name }}
                    </span>
                  </div>
                </div>

                <!-- 能力指标列表 -->
                <div class="radar-metrics">
                  <div
                    v-for="(metric, i) in radarMetrics"
                    :key="i"
                    class="radar-metric-item"
                  >
                    <div class="metric-header">
                      <span class="metric-name">{{ metric.name }}</span>
                      <span class="metric-score">{{ metric.score }}分</span>
                    </div>
                    <div class="metric-bar">
                      <div
                        class="metric-fill"
                        :style="{
                          width: `${metric.score}%`,
                          background: metric.color,
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section class="dashboard-card dashboard-card--queue">
            <div class="section-head">
              <div>
                <span class="section-tag">最近任务</span>
                <h3>最近生成与优化轨迹</h3>
              </div>
              <button class="btn-secondary" @click="selectPanel('history')">
                查看全部记录
              </button>
            </div>

            <!-- 任务状态饼图 -->
            <div class="task-pie-chart">
              <div ref="taskPieChartRef" class="pie-chart-container"></div>
            </div>

            <!-- ECharts 雷达图 -->
            <div ref="radarChartRef" class="radar-chart-container"></div>
          </section>
        </div>

        <section
          v-else-if="activePanel === 'ppt'"
          class="panel"
          data-panel="ppt"
        >
          <div class="generator-layout">
            <article class="form-card">
              <div class="section-head">
                <div>
                  <span class="section-tag">Prompt Workspace</span>
                  <h2>课件制作</h2>
                </div>
              </div>

              <FormWizard :steps="PPT_STEPS" v-model="currentFormStep">
                <template #base>
                  <div class="form-row">
                    <label>
                      学科
                      <select v-model="pptForm.subject">
                        <option value="" disabled>请选择学科</option>
                        <option v-for="s in commonSubjects" :key="s" :value="s">
                          {{ s }}
                        </option>
                        <option :value="CUSTOM_OPTION">自定义学科…</option>
                      </select>
                      <textarea
                        v-if="pptForm.subject === CUSTOM_OPTION"
                        v-model="pptForm.subjectCustom"
                        rows="1"
                        placeholder="请输入学科名称"
                      ></textarea>
                    </label>

                    <label>
                      学段
                      <select v-model="pptForm.grade">
                        <option value="" disabled>请选择学段</option>
                        <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">
                          {{ g }}
                        </option>
                      </select>
                      <small class="field-hint">决定内容深度与模版匹配</small>
                    </label>
                  </div>

                  <label>
                    课题
                    <input
                      v-model="pptForm.topic"
                      type="text"
                      placeholder="例如：牛顿第二定律"
                    />
                  </label>
                </template>

                <template #content>
                  <div class="form-row">
                    <label>
                      课时长度
                      <select v-model="pptForm.duration">
                        <option
                          v-for="d in DURATION_OPTIONS"
                          :key="d"
                          :value="d"
                        >
                          {{ d }}
                        </option>
                      </select>
                      <small class="field-hint">本节课堂时长</small>
                    </label>
                    <label>
                      课件篇幅
                      <select v-model="pptForm.pages">
                        <option value="精炼">精炼（2-3 章，导入/短课）</option>
                        <option value="标准">标准（3-4 章，常规课）</option>
                        <option value="充实">
                          充实（4 章，公开课/示范课）
                        </option>
                      </select>
                    </label>
                  </div>
                  <small class="field-hint">{{
                    PAGES_SECTION_HINT[pptForm.pages]
                  }}</small>

                  <label>
                    章节大纲（可选）
                    <textarea
                      v-model="pptForm.outlineCustom"
                      rows="3"
                      placeholder="每行一个章节，将严格按此组织课件内容，例如：&#10;认识图形与分类&#10;图形的拼组与变换&#10;生活中的图形应用"
                    ></textarea>
                    <small class="field-hint"
                      >留空则由系统自动设计章节；填写后更贴合模版槽位，建议 2-4
                      个章节</small
                    >
                  </label>

                  <label>
                    讲授风格
                    <select v-model="pptForm.style">
                      <option value="实验探究型">
                        实验探究型（实验/观察 → 归纳结论）
                      </option>
                      <option value="讲授演示型">
                        讲授演示型（讲解为主，配合演示）
                      </option>
                      <option value="问题驱动型">
                        问题驱动型（用问题串层层推进）
                      </option>
                      <option value="翻转课堂型">
                        翻转课堂型（课前自学，课上研讨）
                      </option>
                    </select>
                    <small class="field-hint">决定课件的内容组织主线</small>
                  </label>

                  <label>
                    互动设计
                    <select v-model="pptForm.interactionDesign">
                      <option value="" disabled>请选择互动设计</option>
                      <option
                        v-for="it in pptInteractions"
                        :key="it"
                        :value="it"
                      >
                        {{ it }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="pptForm.interactionDesign === CUSTOM_OPTION"
                      v-model="pptForm.interactionCustom"
                      rows="2"
                      placeholder="请描述课堂互动设计…"
                    ></textarea>
                  </label>
                </template>

                <!-- 教学目标 -->
                <template #goals>
                  <div class="objectives-card">
                    <div class="objectives-card__header">
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
                      教学目标与重难点
                    </div>
                    <div class="objectives-card__body">
                      <label>
                        教学目标
                        <select v-model="pptForm.teachingGoals">
                          <option value="" disabled>请选择教学目标</option>
                          <option v-for="g in pptGoals" :key="g" :value="g">
                            {{ g }}
                          </option>
                          <option :value="CUSTOM_OPTION">自定义目标…</option>
                        </select>
                        <textarea
                          v-if="pptForm.teachingGoals === CUSTOM_OPTION"
                          v-model="pptForm.goalCustom"
                          rows="2"
                          placeholder="请输入本节课的教学目标…"
                        ></textarea>
                      </label>
                      <label>
                        重点与难点
                        <select v-model="pptForm.keyPoints">
                          <option value="" disabled>请选择重点与难点</option>
                          <option v-for="k in pptKeys" :key="k" :value="k">
                            {{ k }}
                          </option>
                          <option :value="CUSTOM_OPTION">自定义重难点…</option>
                        </select>
                        <textarea
                          v-if="pptForm.keyPoints === CUSTOM_OPTION"
                          v-model="pptForm.keyCustom"
                          rows="2"
                          placeholder="请输入重点与难点…"
                        ></textarea>
                      </label>
                      <label>
                        学生学情
                        <select v-model="pptForm.studentProfile">
                          <option value="" disabled>请选择学生学情</option>
                          <option
                            v-for="p in STUDENT_PROFILE_OPTIONS"
                            :key="p"
                            :value="p"
                          >
                            {{ p }}
                          </option>
                          <option :value="CUSTOM_OPTION">自定义…</option>
                        </select>
                        <textarea
                          v-if="pptForm.studentProfile === CUSTOM_OPTION"
                          v-model="pptForm.studentProfileCustom"
                          rows="2"
                          placeholder="请描述本班学生的知识基础与学习特点…"
                        ></textarea>
                      </label>
                    </div>
                  </div>
                </template>

                <template #apply>
                  <label>
                    使用场景
                    <select v-model="pptForm.usageScene">
                      <option value="" disabled>请选择使用场景</option>
                      <option v-for="s in USAGE_SCENE.ppt" :key="s" :value="s">
                        {{ s }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="pptForm.usageScene === CUSTOM_OPTION"
                      v-model="pptForm.usageSceneCustom"
                      rows="2"
                      placeholder="请描述使用场景…"
                    ></textarea>
                  </label>

                  <label>
                    评估标准
                    <select v-model="pptForm.assessment">
                      <option value="" disabled>请选择评估标准</option>
                      <option v-for="a in pptAssessments" :key="a" :value="a">
                        {{ a }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="pptForm.assessment === CUSTOM_OPTION"
                      v-model="pptForm.assessmentCustom"
                      rows="2"
                      placeholder="请描述评估侧重…"
                    ></textarea>
                  </label>

                  <!-- 参考课件上传 -->
                  <label class="form-section-title">📎 参考课件（可选）</label>
                  <div
                    class="file-upload-area"
                    @click="triggerPptFileUpload"
                    @drop="handlePptFileDrop"
                    @dragover.prevent
                  >
                    <input
                      ref="pptFileInput"
                      type="file"
                      accept=".ppt,.pptx,.pdf"
                      style="display: none"
                      @change="handlePptFileChange"
                    />
                    <div
                      v-if="!pptForm.referenceFile"
                      class="upload-placeholder"
                    >
                      <span class="upload-icon"
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
                          <path
                            d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
                          /></svg
                      ></span>
                      <p>点击或拖拽上传参考课件</p>
                      <small>支持 PPT、PPTX、PDF 格式</small>
                    </div>
                    <div v-else class="uploaded-file">
                      <span class="file-icon">📄</span>
                      <span class="file-name">{{
                        pptForm.referenceFile.name
                      }}</span>
                      <button
                        type="button"
                        class="remove-file"
                        @click.stop="removePptFile"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  <div class="chip-row">
                    <button type="button" class="chip-row__chip">
                      情境导入
                    </button>
                    <button type="button" class="chip-row__chip">
                      板书提示
                    </button>
                    <button type="button" class="chip-row__chip">
                      课堂追问
                    </button>
                  </div>
                </template>

                <template #actions>
                  <button
                    v-if="currentFormStep === 3"
                    class="btn-primary"
                    :disabled="isGenerating"
                    @click="handlePptGenerate"
                  >
                    {{ isGenerating ? "正在生成课件…" : "开始生成课件" }}
                  </button>
                </template>
              </FormWizard>
            </article>

            <ContentRevisePanel
              :title="currentReviseTitle"
              :messages="currentReviseMessages"
              :ready="reviseReady"
              :generating="isGenerating"
              :exporting="exporting"
              :progress="currentTaskProgress"
              :stage="currentTaskStage"
              :filename="generatedFilename"
              :placeholder="currentRevisePlaceholder"
              :pipeline="currentPipeline"
              @send="handleReviseSend"
              @export="handleContentExport"
            >
              <template #footer-tools>
                <TemplateMarket
                  :spark-templates="sparkTemplates"
                  :spark-loading="sparkTemplateLoading"
                  :spark-error="sparkTemplateError"
                  :selected-spark-id="pptForm.sparkTemplateId"
                  :card-note="pptForm.isCardNote"
                  :figure="pptForm.isFigure"
                  :resolve-preview="previewUrl"
                  @spark-change="(v) => (pptForm.sparkTemplateId = v)"
                  @refresh-spark="fetchSparkTemplates"
                  @card-note-change="(v) => (pptForm.isCardNote = v)"
                  @figure-change="(v) => (pptForm.isFigure = v)"
                />
              </template>
            </ContentRevisePanel>
          </div>
        </section>

        <section
          v-else-if="activePanel === 'doc'"
          class="panel"
          data-panel="doc"
        >
          <div class="generator-layout">
            <article class="form-card">
              <div class="section-head">
                <div>
                  <span class="section-tag">Prompt Workspace</span>
                  <h2>教案编写</h2>
                  <p class="section-annotation">
                    编写完整教案，支持多种教学风格
                  </p>
                </div>
              </div>

              <FormWizard :steps="DOC_STEPS" v-model="currentFormStep">
                <template #base>
                  <div class="form-row">
                    <label>
                      学科
                      <select v-model="docForm.subject">
                        <option value="" disabled>请选择学科</option>
                        <option v-for="s in commonSubjects" :key="s" :value="s">
                          {{ s }}
                        </option>
                        <option :value="CUSTOM_OPTION">自定义学科…</option>
                      </select>
                      <textarea
                        v-if="docForm.subject === CUSTOM_OPTION"
                        v-model="docForm.subjectCustom"
                        rows="1"
                        placeholder="请输入学科名称"
                      ></textarea>
                    </label>

                    <label>
                      课题
                      <input
                        v-model="docForm.topic"
                        type="text"
                        placeholder="例如：力的分解"
                      />
                    </label>
                  </div>

                  <div class="form-row">
                    <label>
                      学段
                      <select v-model="docForm.grade">
                        <option value="" disabled>请选择学段</option>
                        <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">
                          {{ g }}
                        </option>
                      </select>
                    </label>
                    <label>
                      课时长度
                      <select v-model="docForm.duration">
                        <option
                          v-for="d in DURATION_OPTIONS"
                          :key="d"
                          :value="d"
                        >
                          {{ d }}
                        </option>
                      </select>
                    </label>
                  </div>
                </template>

                <template #goals>
                  <!-- 教学目标 -->
                  <label class="form-section-title"
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
                      <circle cx="12" cy="12" r="10" />
                      <circle cx="12" cy="12" r="6" />
                      <circle cx="12" cy="12" r="2" fill="currentColor" />
                    </svg>
                    教学目标与重难点</label
                  >
                  <label>
                    教学目标
                    <select v-model="docForm.teachingGoals">
                      <option value="" disabled>请选择教学目标</option>
                      <option v-for="g in docGoals" :key="g" :value="g">
                        {{ g }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义目标…</option>
                    </select>
                    <textarea
                      v-if="docForm.teachingGoals === CUSTOM_OPTION"
                      v-model="docForm.goalCustom"
                      rows="2"
                      placeholder="请输入本节课的教学目标…"
                    ></textarea>
                  </label>

                  <label>
                    重点与难点
                    <select v-model="docForm.keyPoints">
                      <option value="" disabled>请选择重点与难点</option>
                      <option v-for="k in docKeys" :key="k" :value="k">
                        {{ k }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义重难点…</option>
                    </select>
                    <textarea
                      v-if="docForm.keyPoints === CUSTOM_OPTION"
                      v-model="docForm.keyCustom"
                      rows="2"
                      placeholder="请输入重点与难点…"
                    ></textarea>
                  </label>
                  <label>
                    学生学情
                    <select v-model="docForm.studentProfile">
                      <option value="" disabled>请选择学生学情</option>
                      <option
                        v-for="p in STUDENT_PROFILE_OPTIONS"
                        :key="p"
                        :value="p"
                      >
                        {{ p }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="docForm.studentProfile === CUSTOM_OPTION"
                      v-model="docForm.studentProfileCustom"
                      rows="2"
                      placeholder="请描述本班学生的知识基础与学习特点…"
                    ></textarea>
                  </label>
                </template>

                <template #process>
                  <label>
                    教案格式
                    <select v-model="docForm.format">
                      <option value="标准教案">
                        标准教案（常规备课，环节完整）
                      </option>
                      <option value="详细教案">
                        详细教案（公开课/评比，含设计意图）
                      </option>
                      <option value="简版教案">
                        简版教案（日常速备，重点突出）
                      </option>
                      <option value="校本模板">
                        校本模板（沿用学校统一格式）
                      </option>
                    </select>
                  </label>
                  <label>
                    讲授风格
                    <select v-model="docForm.style">
                      <option value="实验探究型">
                        实验探究型（实验/观察 → 归纳结论）
                      </option>
                      <option value="讲授演示型">
                        讲授演示型（讲解为主，配合演示）
                      </option>
                      <option value="问题驱动型">
                        问题驱动型（用问题串层层推进）
                      </option>
                      <option value="翻转课堂型">
                        翻转课堂型（课前自学，课上研讨）
                      </option>
                    </select>
                  </label>
                  <label>
                    环节侧重
                    <select v-model="docForm.lessonFocus">
                      <option value="" disabled>请选择环节侧重</option>
                      <option
                        v-for="f in LESSON_FOCUS_OPTIONS"
                        :key="f"
                        :value="f"
                      >
                        {{ f }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="docForm.lessonFocus === CUSTOM_OPTION"
                      v-model="docForm.lessonFocusCustom"
                      rows="2"
                      placeholder="请描述教学环节侧重…"
                    ></textarea>
                  </label>
                </template>

                <template #apply>
                  <label>
                    使用场景
                    <select v-model="docForm.usageScene">
                      <option value="" disabled>请选择使用场景</option>
                      <option v-for="s in USAGE_SCENE.doc" :key="s" :value="s">
                        {{ s }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="docForm.usageScene === CUSTOM_OPTION"
                      v-model="docForm.usageSceneCustom"
                      rows="2"
                      placeholder="请描述使用场景…"
                    ></textarea>
                  </label>
                  <label>
                    评估标准
                    <select v-model="docForm.assessment">
                      <option value="" disabled>请选择评估标准</option>
                      <option v-for="a in docAssessments" :key="a" :value="a">
                        {{ a }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="docForm.assessment === CUSTOM_OPTION"
                      v-model="docForm.assessmentCustom"
                      rows="2"
                      placeholder="请描述评估侧重…"
                    ></textarea>
                  </label>

                  <!-- 参考教案上传 -->
                  <label class="form-section-title">📎 参考教案（可选）</label>
                  <div
                    class="file-upload-area"
                    @click="triggerDocFileUpload"
                    @drop="handleDocFileDrop"
                    @dragover.prevent
                  >
                    <input
                      ref="docFileInput"
                      type="file"
                      accept=".doc,.docx,.pdf"
                      style="display: none"
                      @change="handleDocFileChange"
                    />
                    <div
                      v-if="!docForm.referenceFile"
                      class="upload-placeholder"
                    >
                      <span class="upload-icon"
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
                          <path
                            d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
                          /></svg
                      ></span>
                      <p>点击或拖拽上传参考教案</p>
                      <small>支持 DOC、DOCX、PDF 格式</small>
                    </div>
                    <div v-else class="uploaded-file">
                      <span class="file-icon">📄</span>
                      <span class="file-name">{{
                        docForm.referenceFile.name
                      }}</span>
                      <button
                        type="button"
                        class="remove-file"
                        @click.stop="removeDocFile"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  <div class="chip-row">
                    <button type="button" class="chip-row__chip">
                      学情分析
                    </button>
                    <button type="button" class="chip-row__chip">
                      板书设计
                    </button>
                    <button type="button" class="chip-row__chip">
                      作业布置
                    </button>
                  </div>
                </template>

                <template #actions>
                  <button
                    v-if="currentFormStep === 3"
                    class="btn-primary"
                    :disabled="isGenerating"
                    @click="handleDocGenerate"
                  >
                    {{ isGenerating ? "正在生成教案…" : "开始生成教案" }}
                  </button>
                </template>
              </FormWizard>
            </article>

            <ContentRevisePanel
              :title="currentReviseTitle"
              :messages="currentReviseMessages"
              :ready="reviseReady"
              :generating="isGenerating"
              :exporting="exporting"
              :progress="currentTaskProgress"
              :stage="currentTaskStage"
              :filename="generatedFilename"
              :placeholder="currentRevisePlaceholder"
              :pipeline="currentPipeline"
              @send="handleReviseSend"
              @export="handleContentExport"
            />
          </div>
        </section>

        <section
          v-else-if="activePanel === 'interactive'"
          class="panel"
          data-panel="interactive"
        >
          <div class="generator-layout">
            <article class="form-card">
              <div class="section-head">
                <div>
                  <span class="section-tag">Teaching Question Flow</span>
                  <h2>课堂练习</h2>
                  <p class="section-annotation">
                    选择场景和难度，一键生成教学练习题
                  </p>
                </div>
              </div>

              <FormWizard :steps="QUIZ_STEPS" v-model="currentFormStep">
                <template #base>
                  <div class="form-row">
                    <label>
                      学科
                      <select v-model="questionForm.subject">
                        <option value="" disabled>请选择学科</option>
                        <option v-for="s in commonSubjects" :key="s" :value="s">
                          {{ s }}
                        </option>
                        <option :value="CUSTOM_OPTION">自定义学科…</option>
                      </select>
                      <textarea
                        v-if="questionForm.subject === CUSTOM_OPTION"
                        v-model="questionForm.subjectCustom"
                        rows="1"
                        placeholder="请输入学科名称"
                      ></textarea>
                    </label>
                    <label>
                      知识点
                      <input
                        v-model="questionForm.topic"
                        type="text"
                        placeholder="例如：牛顿第二定律应用"
                      />
                    </label>
                  </div>
                  <label>
                    学段
                    <select v-model="questionForm.stage">
                      <option value="" disabled>请选择学段</option>
                      <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">
                        {{ g }}
                      </option>
                    </select>
                  </label>
                </template>

                <template #goals>
                  <label>
                    考查目标
                    <select v-model="questionForm.target">
                      <option value="" disabled>请选择考查目标</option>
                      <option value="知识记忆">知识记忆</option>
                      <option value="理解应用">理解应用</option>
                      <option value="综合运用">综合运用</option>
                      <option value="迁移创新">迁移创新</option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="questionForm.target === CUSTOM_OPTION"
                      v-model="questionForm.targetCustom"
                      rows="2"
                      placeholder="请描述考查目标…"
                    ></textarea>
                  </label>
                  <label>
                    学生学情
                    <select v-model="questionForm.studentProfile">
                      <option value="" disabled>请选择学生学情</option>
                      <option
                        v-for="p in STUDENT_PROFILE_OPTIONS"
                        :key="p"
                        :value="p"
                      >
                        {{ p }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="questionForm.studentProfile === CUSTOM_OPTION"
                      v-model="questionForm.studentProfileCustom"
                      rows="2"
                      placeholder="请描述本班学生的知识基础与学习特点…"
                    ></textarea>
                  </label>
                </template>

                <template #design>
                  <label>
                    难度风格
                    <select v-model="questionForm.difficulty">
                      <option value="基础巩固">
                        基础巩固（课后即时练，夯实概念）
                      </option>
                      <option value="综合提升">
                        综合提升（章节综合，练方法）
                      </option>
                      <option value="拓展挑战">
                        拓展挑战（思维拓展，冲刺拔高）
                      </option>
                    </select>
                  </label>
                  <label>
                    题量
                    <select v-model.number="questionForm.count">
                      <option :value="5">5 题（快速练习）</option>
                      <option :value="8">8 题（标准练习）</option>
                      <option :value="10">10 题（完整检测）</option>
                      <option :value="15">15 题（充分训练）</option>
                    </select>
                  </label>
                  <label>
                    题型构成
                    <select v-model="questionForm.questionTypes">
                      <option value="" disabled>请选择题型构成</option>
                      <option
                        v-for="q in QUESTION_TYPE_OPTIONS"
                        :key="q"
                        :value="q"
                      >
                        {{ q }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="questionForm.questionTypes === CUSTOM_OPTION"
                      v-model="questionForm.questionTypesCustom"
                      rows="2"
                      placeholder="请描述题型构成…"
                    ></textarea>
                  </label>
                </template>

                <template #apply>
                  <label>
                    使用场景
                    <select v-model="questionForm.scenario">
                      <option value="" disabled>请选择使用场景</option>
                      <option
                        v-for="s in USAGE_SCENE.interactive"
                        :key="s"
                        :value="s"
                      >
                        {{ s }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="questionForm.scenario === CUSTOM_OPTION"
                      v-model="questionForm.scenarioCustom"
                      rows="2"
                      placeholder="请描述使用场景…"
                    ></textarea>
                  </label>
                  <label>
                    评估标准
                    <select v-model="questionForm.assessment">
                      <option value="" disabled>请选择评估标准</option>
                      <option v-for="a in quizAssessments" :key="a" :value="a">
                        {{ a }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="questionForm.assessment === CUSTOM_OPTION"
                      v-model="questionForm.assessmentCustom"
                      rows="2"
                      placeholder="请描述评估侧重…"
                    ></textarea>
                  </label>
                </template>

                <template #actions>
                  <button
                    v-if="currentFormStep === 3"
                    class="btn-primary"
                    :disabled="isGenerating"
                    @click="handleQuestionGenerate"
                  >
                    {{ isGenerating ? "正在生成题组…" : "一键生成" }}
                  </button>
                </template>
              </FormWizard>
            </article>

            <ContentRevisePanel
              :title="currentReviseTitle"
              :messages="currentReviseMessages"
              :ready="reviseReady"
              :generating="isGenerating"
              :exporting="exporting"
              :progress="currentTaskProgress"
              :stage="currentTaskStage"
              :filename="generatedFilename"
              :placeholder="currentRevisePlaceholder"
              :pipeline="currentPipeline"
              @send="handleReviseSend"
              @export="handleContentExport"
            />
          </div>
        </section>

        <!-- 试卷生成面板 -->
        <section
          v-else-if="activePanel === 'exam'"
          class="panel"
          data-panel="exam"
        >
          <div class="generator-layout">
            <article class="form-card">
              <div class="section-head">
                <div>
                  <span class="section-tag">Paper Generator</span>
                  <h2>试卷生成</h2>
                  <p class="section-annotation">
                    选择题 + 填空题 + 解答题混合组卷，支持 A/B 卷与答题卡导出
                  </p>
                </div>
              </div>

              <FormWizard :steps="EXAM_STEPS" v-model="currentFormStep">
                <template #base>
                  <div class="form-row">
                    <label>
                      学科
                      <select v-model="examForm.subject">
                        <option value="" disabled>请选择学科</option>
                        <option v-for="s in commonSubjects" :key="s" :value="s">
                          {{ s }}
                        </option>
                        <option :value="CUSTOM_OPTION">自定义学科…</option>
                      </select>
                      <textarea
                        v-if="examForm.subject === CUSTOM_OPTION"
                        v-model="examForm.subjectCustom"
                        rows="1"
                        placeholder="请输入学科名称"
                      ></textarea>
                    </label>
                    <label>
                      知识点 / 考试范围
                      <input
                        v-model="examForm.topic"
                        type="text"
                        placeholder="例如：牛顿运动定律综合"
                      />
                    </label>
                  </div>
                  <label>
                    学段
                    <select v-model="examForm.grade">
                      <option value="" disabled>请选择学段</option>
                      <option v-for="g in GRADE_OPTIONS" :key="g" :value="g">
                        {{ g }}
                      </option>
                    </select>
                  </label>
                </template>

                <template #goals>
                  <label>
                    考查目标
                    <select v-model="examForm.target">
                      <option value="" disabled>请选择考查目标</option>
                      <option value="知识记忆">知识记忆</option>
                      <option value="理解应用">理解应用</option>
                      <option value="综合运用">综合运用</option>
                      <option value="迁移创新">迁移创新</option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="examForm.target === CUSTOM_OPTION"
                      v-model="examForm.targetCustom"
                      rows="2"
                      placeholder="请描述考查目标…"
                    ></textarea>
                  </label>
                  <label>
                    学生学情
                    <select v-model="examForm.studentProfile">
                      <option value="" disabled>请选择学生学情</option>
                      <option
                        v-for="p in STUDENT_PROFILE_OPTIONS"
                        :key="p"
                        :value="p"
                      >
                        {{ p }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="examForm.studentProfile === CUSTOM_OPTION"
                      v-model="examForm.studentProfileCustom"
                      rows="2"
                      placeholder="请描述本班学生的知识基础与学习特点…"
                    ></textarea>
                  </label>
                </template>

                <template #paper>
                  <div class="form-row">
                    <label>
                      难度
                      <select v-model="examForm.difficulty">
                        <option value="基础">基础（面向全体，过关为主）</option>
                        <option value="中等">
                          中等（贴近月考，区分度适中）
                        </option>
                        <option value="提高">提高（选拔拔高，区分度大）</option>
                      </select>
                    </label>
                    <label>
                      总分
                      <input
                        v-model.number="examForm.totalScore"
                        type="number"
                        min="50"
                        max="150"
                      />
                    </label>
                  </div>

                  <label
                    class="checkbox-label"
                    style="
                      display: flex;
                      align-items: center;
                      gap: 8px;
                      margin-top: 8px;
                    "
                  >
                    <input v-model="examForm.generateAB" type="checkbox" />
                    <span style="font-weight: 500; color: #475569"
                      >生成 A/B 卷（防作弊）</span
                    >
                  </label>

                  <div
                    style="
                      margin-top: 8px;
                      padding: 12px 14px;
                      background: #f8fafc;
                      border-radius: 8px;
                      border: 1px solid rgba(0, 0, 0, 0.04);
                    "
                  >
                    <p
                      style="
                        margin: 0 0 8px 0;
                        font-size: 0.78rem;
                        font-weight: 600;
                        color: #475569;
                      "
                    >
                      题量分配
                    </p>
                    <div
                      style="
                        display: grid;
                        grid-template-columns: 1fr 1fr 1fr;
                        gap: 10px;
                      "
                    >
                      <label style="font-size: 0.8rem; color: #6b7280">
                        选择题
                        <input
                          v-model.number="examForm.choiceCount"
                          type="number"
                          min="4"
                          max="20"
                          style="
                            display: block;
                            width: 100%;
                            margin-top: 4px;
                            padding: 6px 8px;
                            border: 1px solid rgba(0, 0, 0, 0.08);
                            border-radius: 6px;
                            font-size: 0.85rem;
                          "
                        />
                      </label>
                      <label style="font-size: 0.8rem; color: #6b7280">
                        填空题
                        <input
                          v-model.number="examForm.fillCount"
                          type="number"
                          min="2"
                          max="12"
                          style="
                            display: block;
                            width: 100%;
                            margin-top: 4px;
                            padding: 6px 8px;
                            border: 1px solid rgba(0, 0, 0, 0.08);
                            border-radius: 6px;
                            font-size: 0.85rem;
                          "
                        />
                      </label>
                      <label style="font-size: 0.8rem; color: #6b7280">
                        解答题
                        <input
                          v-model.number="examForm.essayCount"
                          type="number"
                          min="1"
                          max="8"
                          style="
                            display: block;
                            width: 100%;
                            margin-top: 4px;
                            padding: 6px 8px;
                            border: 1px solid rgba(0, 0, 0, 0.08);
                            border-radius: 6px;
                            font-size: 0.85rem;
                          "
                        />
                      </label>
                    </div>
                  </div>
                </template>

                <template #apply>
                  <label>
                    使用场景
                    <select v-model="examForm.usageScene">
                      <option value="" disabled>请选择使用场景</option>
                      <option v-for="s in USAGE_SCENE.exam" :key="s" :value="s">
                        {{ s }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="examForm.usageScene === CUSTOM_OPTION"
                      v-model="examForm.usageSceneCustom"
                      rows="2"
                      placeholder="请描述使用场景…"
                    ></textarea>
                  </label>
                  <label>
                    评估标准
                    <select v-model="examForm.assessment">
                      <option value="" disabled>请选择评估标准</option>
                      <option v-for="a in examAssessments" :key="a" :value="a">
                        {{ a }}
                      </option>
                      <option :value="CUSTOM_OPTION">自定义…</option>
                    </select>
                    <textarea
                      v-if="examForm.assessment === CUSTOM_OPTION"
                      v-model="examForm.assessmentCustom"
                      rows="2"
                      placeholder="请描述评估侧重…"
                    ></textarea>
                  </label>
                </template>

                <template #actions>
                  <button
                    v-if="currentFormStep === 3"
                    class="btn-primary"
                    :disabled="isGenerating"
                    @click="handleExamGenerate"
                  >
                    {{ isGenerating ? "正在生成试卷…" : "开始生成试卷" }}
                  </button>
                </template>
              </FormWizard>
            </article>

            <ContentRevisePanel
              :title="currentReviseTitle"
              :messages="currentReviseMessages"
              :ready="reviseReady"
              :generating="isGenerating"
              :exporting="exporting"
              :progress="currentTaskProgress"
              :stage="currentTaskStage"
              :filename="generatedFilename"
              :placeholder="currentRevisePlaceholder"
              :pipeline="currentPipeline"
              @send="handleReviseSend"
              @export="handleContentExport"
            />
          </div>
        </section>

        <section v-else-if="activePanel === 'visualize'" class="panel">
          <div class="insight-grid insight-grid--simple">
            <article class="viz-card viz-card--flow">
              <div class="section-head">
                <div>
                  <span class="section-tag">工作流</span>
                  <h2>生成路径</h2>
                </div>
              </div>

              <svg
                viewBox="0 0 420 170"
                class="mini-flow"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient id="flowStroke" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stop-color="#4c7dff" />
                    <stop offset="100%" stop-color="#7c5cff" />
                  </linearGradient>
                </defs>
                <path
                  d="M20 110 C100 110 110 40 180 40 S300 130 390 68"
                  fill="none"
                  stroke="url(#flowStroke)"
                  stroke-width="6"
                  stroke-linecap="round"
                />
                <circle cx="20" cy="110" r="8" fill="#4c7dff" />
                <circle cx="180" cy="40" r="8" fill="#23c3b2" />
                <circle cx="390" cy="68" r="8" fill="#8b5cf6" />
              </svg>
              <p class="viz-note">
                把“教学意图 → 生成内容 →
                反馈优化”做成更容易理解的工作流，而不是传统统计图堆砌。
              </p>
            </article>

            <article class="viz-card">
              <div class="section-head">
                <div>
                  <span class="section-tag">推荐动作</span>
                  <h2>下一步建议</h2>
                </div>
              </div>

              <div class="support-list">
                <article class="support-item">
                  <span>01</span>
                  <p>
                    优先补齐“教学题生成”的课堂检测模板，让课件、教案和题组三者形成闭环。
                  </p>
                </article>
                <article class="support-item">
                  <span>02</span>
                  <p>把高频学科沉淀成可复用模板，减少重复填写成本。</p>
                </article>
                <article class="support-item">
                  <span>03</span>
                  <p>
                    将有反馈的记录优先推进到下一轮优化，提高演示时的完成度。
                  </p>
                </article>
              </div>
            </article>
          </div>
        </section>

        <section
          v-else-if="activePanel === 'history'"
          class="panel"
          data-panel="history"
        >
          <!-- 教学档案标题 -->
          <div class="archive-section-header">
            <h2>
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                style="vertical-align: -3px; margin-right: 6px"
              >
                <path
                  d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
                />
              </svg>
              教学档案
            </h2>
            <p>筛选和浏览您的教学创作记录</p>
          </div>

          <!-- 多维筛选栏 -->
          <div class="archive-filter-bar">
            <div class="archive-filter-row">
              <!-- 课件类型 -->
              <div class="archive-filter-group">
                <label class="archive-filter-label">课件类型</label>
                <select
                  v-model="archiveFilters.type"
                  class="archive-filter-select"
                >
                  <option value="">全部类型</option>
                  <option
                    v-for="opt in contentTypeOptions.filter((o) => o.value)"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <!-- 学科 -->
              <div class="archive-filter-group">
                <label class="archive-filter-label">学科</label>
                <select
                  v-model="archiveFilters.subject"
                  class="archive-filter-select"
                >
                  <option value="">全部学科</option>
                  <option
                    v-for="sub in availableSubjects"
                    :key="sub"
                    :value="sub"
                  >
                    {{ sub }}
                  </option>
                </select>
              </div>

              <!-- 状态 -->
              <div class="archive-filter-group">
                <label class="archive-filter-label">状态</label>
                <select
                  v-model="archiveFilters.status"
                  class="archive-filter-select"
                >
                  <option value="">全部状态</option>
                  <option value="completed">已完成</option>
                  <option value="draft">待完善</option>
                  <option value="iterating">优化中</option>
                </select>
              </div>

              <!-- 创建时间 -->
              <div class="archive-filter-group">
                <label class="archive-filter-label">创建时间</label>
                <select
                  v-model="archiveFilters.timeRange"
                  class="archive-filter-select"
                >
                  <option value="">全部时间</option>
                  <option
                    v-for="tr in timeRangeOptions.filter((o) => o.value)"
                    :key="tr.value"
                    :value="tr.value"
                  >
                    {{ tr.label }}
                  </option>
                </select>
              </div>

              <!-- 排序 -->
              <div class="archive-filter-group">
                <label class="archive-filter-label">排序</label>
                <select v-model="archiveSortBy" class="archive-filter-select">
                  <option value="newest">最新优先</option>
                  <option value="oldest">最早优先</option>
                  <option value="title">按名称</option>
                </select>
              </div>
            </div>

            <!-- 搜索 + 操作行 -->
            <div class="archive-filter-actions">
              <div class="archive-search-wrapper">
                <span class="archive-search-icon"
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
                <input
                  v-model="archiveFilters.searchQuery"
                  type="text"
                  placeholder="搜索课件名称或学科..."
                  class="archive-search-input"
                />
              </div>
              <button
                class="archive-btn archive-btn--reset"
                :disabled="
                  activeArchiveFilterCount === 0 && !archiveFilters.searchQuery
                "
                @click="resetArchiveFilters()"
              >
                重置
              </button>
            </div>
          </div>

          <!-- 统计信息 -->
          <div class="archive-table-info">
            共 <strong>{{ filteredHistory.length }}</strong> 条记录
            <template v-if="archiveFilters.searchQuery"
              >，搜索 "<em>{{ archiveFilters.searchQuery }}</em
              >"</template
            >
          </div>

          <!-- 数据表格 -->
          <div class="archive-table-wrapper">
            <table class="archive-table">
              <thead>
                <tr>
                  <th class="col-num">#</th>
                  <th class="col-name">名称</th>
                  <th class="col-subject">学科</th>
                  <th class="col-type">类型</th>
                  <th class="col-status">状态</th>
                  <th class="col-time">创建时间</th>
                  <th class="col-actions">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, index) in paginatedHistory"
                  :key="item.id"
                  class="archive-row"
                >
                  <td class="col-num">
                    {{ (historyPage - 1) * pageSize + index + 1 }}
                  </td>
                  <td class="col-name">
                    <div class="archive-name-cell">
                      <span
                        class="archive-type-icon"
                        :class="item.type"
                        v-html="getTypeIcon(item.type)"
                      ></span>
                      <span class="archive-name-text">{{ item.title }}</span>
                    </div>
                  </td>
                  <td class="col-subject">
                    <span class="archive-subject-tag">{{ item.subject }}</span>
                  </td>
                  <td class="col-type">
                    <span class="archive-type-label">{{
                      TYPE_LABELS[item.type]
                    }}</span>
                  </td>
                  <td class="col-status">
                    <span
                      class="archive-status-badge"
                      :data-status="item.status"
                    >
                      <span class="archive-status-dot"></span>
                      {{ STATUS_LABELS[item.status] }}
                    </span>
                  </td>
                  <td class="col-time">
                    {{ formatFeatureTime(item.createdAt) }}
                  </td>
                  <td class="col-actions">
                    <div class="archive-actions">
                      <button
                        class="archive-action-btn"
                        title="查看详情"
                        @click="previewRecord(item)"
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <path
                            d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
                          />
                          <circle cx="12" cy="12" r="3" />
                        </svg>
                      </button>
                      <button
                        v-if="item.taskId && item.status === 'completed'"
                        class="archive-action-btn archive-action-btn--download"
                        title="下载课件"
                        @click="downloadRecord(item)"
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                      </button>
                      <button
                        class="archive-action-btn"
                        title="继续编辑"
                        @click="editRecord(item)"
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <path
                            d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                          />
                          <path
                            d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                          />
                        </svg>
                      </button>
                      <button
                        class="archive-action-btn archive-action-btn--delete"
                        title="删除"
                        @click="handleDelete(item.id)"
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                        >
                          <polyline points="3 6 5 6 21 6" />
                          <path
                            d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                          />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!paginatedHistory.length">
                  <td colspan="7">
                    <div class="archive-empty">
                      <svg
                        width="36"
                        height="36"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="1.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path
                          d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"
                        />
                        <polyline points="13 2 13 9 20 9" />
                      </svg>
                      <p>暂无生成记录<br />快去开始创作吧</p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 分页 -->
          <div class="archive-pagination">
            <span class="archive-page-info"
              >第 {{ historyPage }} / {{ totalHistoryPages }} 页，共
              {{ filteredHistory.length }} 条</span
            >
            <div class="archive-page-btns">
              <button
                class="archive-page-btn"
                :disabled="historyPage <= 1"
                @click="historyPage -= 1"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="15 18 9 12 15 6" />
                </svg>
                上一页
              </button>
              <button
                v-for="p in archivePageNumbers"
                :key="p"
                class="archive-page-btn"
                :class="{ active: p === historyPage }"
                @click="historyPage = p"
              >
                {{ p }}
              </button>
              <button
                class="archive-page-btn"
                :disabled="historyPage >= totalHistoryPages"
                @click="historyPage += 1"
              >
                下一页
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="activePanel === 'iterate'" class="panel">
          <!-- 页面标题 -->
          <div class="reflect-page-title">
            <h3 class="reflect-title">
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path
                  d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"
                />
              </svg>
              教学反思
            </h3>
            <p class="reflect-desc">记录教学心得，持续优化内容质量</p>
          </div>

          <div class="reflect-divider"></div>

          <!-- 左右分栏：左 3/5 表单 | 右 2/5 历史记录 -->
          <div class="reflect-layout">
            <!-- ===== 左侧：提交新反馈表单 ===== -->
            <div class="reflect-form-card">
              <div class="reflect-form-card__header">
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
                  <path d="M12 5v14" />
                  <path d="M5 12h14" />
                </svg>
                提交新反馈
              </div>

              <div class="reflect-form-body">
                <div class="reflect-field">
                  <label class="reflect-field__label"
                    >反馈类型
                    <span class="reflect-field__required">*</span></label
                  >
                  <select v-model="feedbackType" class="reflect-select">
                    <option value="" disabled>请选择反馈类型</option>
                    <option value="courseware">课件优化</option>
                    <option value="lesson-plan">教案改进</option>
                    <option value="activity">教学活动设计</option>
                    <option value="ai-quality">AI 生成质量</option>
                    <option value="platform">平台功能建议</option>
                    <option value="other">其他</option>
                  </select>
                </div>

                <div class="reflect-field">
                  <label class="reflect-field__label"
                    >反馈标题
                    <span class="reflect-field__required">*</span></label
                  >
                  <input
                    v-model="feedbackTitle"
                    type="text"
                    class="reflect-input"
                    placeholder="例如：关于《二次函数》课件的修改建议"
                  />
                </div>

                <div class="reflect-field">
                  <label class="reflect-field__label"
                    >详细描述
                    <span class="reflect-field__required">*</span></label
                  >
                  <textarea
                    v-model="feedbackDesc"
                    class="reflect-textarea"
                    rows="4"
                    placeholder="请详细描述您的修改建议或遇到的问题..."
                  />
                </div>

                <div class="reflect-field">
                  <label class="reflect-field__label">附件上传</label>
                  <div class="reflect-upload">
                    <button
                      class="reflect-upload__btn"
                      @click="triggerFileInput"
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
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                      选择文件
                    </button>
                    <span class="reflect-upload__hint"
                      >支持 .docx、.pptx、.pdf、.png、.jpg ≤20MB</span
                    >
                    <input
                      ref="fileInputRef"
                      type="file"
                      class="reflect-upload__input"
                      @change="handleFileChange"
                      accept=".docx,.pptx,.pdf,.png,.jpg,.jpeg"
                    />
                    <div v-if="feedbackFileName" class="reflect-upload__file">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path
                          d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"
                        />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                      </svg>
                      {{ feedbackFileName }}
                      <button
                        class="reflect-upload__remove"
                        @click="removeFeedbackFile"
                      >
                        &times;
                      </button>
                    </div>
                  </div>
                </div>

                <div class="reflect-field">
                  <label class="reflect-field__label">联系方式</label>
                  <input
                    v-model="feedbackContact"
                    type="text"
                    class="reflect-input"
                    placeholder="邮箱或手机号（选填）"
                  />
                </div>
              </div>

              <div class="reflect-tips">
                <span class="reflect-tips__label">快捷填入</span>
                <div class="reflect-tips__tags">
                  <button class="tip-tag" @click="appendTag('结构调整')">
                    结构调整
                  </button>
                  <button class="tip-tag" @click="appendTag('讲授风格')">
                    讲授风格
                  </button>
                  <button class="tip-tag" @click="appendTag('题目难度')">
                    题目难度
                  </button>
                  <button class="tip-tag" @click="appendTag('课堂互动')">
                    课堂互动
                  </button>
                  <button class="tip-tag" @click="appendTag('内容深度')">
                    内容深度
                  </button>
                  <button class="tip-tag" @click="appendTag('视觉设计')">
                    视觉设计
                  </button>
                </div>
              </div>

              <div class="reflect-form-card__actions">
                <button class="btn-primary" @click="submitNewFeedback">
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
                    <path d="M22 2L11 13" />
                    <path d="M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                  提交反馈
                </button>
              </div>
            </div>

            <!-- ===== 右侧：历史反馈记录 ===== -->
            <div class="reflect-history-card">
              <div class="reflect-history-card__head">
                <span class="reflect-history-card__title">
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
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  历史反馈记录
                </span>
                <span class="reflect-history-card__badge">{{
                  feedbackItems.length
                }}</span>
              </div>

              <div class="reflect-history-list">
                <div
                  v-for="item in feedbackItems.slice(0, 4)"
                  :key="item.id"
                  class="reflect-history-item"
                >
                  <div class="reflect-history-item__head">
                    <div class="reflect-history-item__tags">
                      <span class="rh-type" :class="item.type">{{
                        item.typeLabel
                      }}</span>
                      <span class="rh-subject">{{ item.subject }}</span>
                    </div>
                    <span class="rh-status" :data-status="item.status">{{
                      item.statusLabel
                    }}</span>
                  </div>
                  <div class="reflect-history-item__title">
                    {{ item.title }}
                  </div>
                  <div class="reflect-history-item__preview">
                    {{ item.contentPreview || item.feedback || "暂无反馈内容" }}
                  </div>
                  <div class="reflect-history-item__time">
                    <svg
                      width="12"
                      height="12"
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
                    {{ item.timeLabel }}
                  </div>
                </div>

                <div v-if="!feedbackItems.length" class="reflect-history-empty">
                  <svg
                    width="40"
                    height="40"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  <p>暂无反馈记录<br />提交反馈后将在此展示</p>
                </div>
              </div>

              <div class="reflect-history-card__foot">
                <button class="view-all-btn" @click="resetFeedbackFilters">
                  查看全部记录
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>

    <!-- 预览弹窗 -->
    <Transition name="modal">
      <div
        v-if="showPreview && previewItem"
        class="preview-overlay"
        @click.self="showPreview = false"
      >
        <div class="preview-dialog">
          <div class="preview-dialog__header">
            <div
              class="preview-dialog__icon"
              v-html="getTypeIcon(previewItem.type)"
            ></div>
            <div>
              <h3>{{ previewItem.title }}</h3>
              <span class="preview-dialog__meta"
                >{{ TYPE_LABELS[previewItem.type] }} ·
                {{ previewItem.subject }}</span
              >
            </div>
            <button class="preview-dialog__close" @click="showPreview = false">
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
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div class="preview-dialog__body">
            <div class="preview-dialog__status">
              <span
                class="archive-status-badge"
                :data-status="previewItem.status"
              >
                <span class="archive-status-dot"></span>
                {{ STATUS_LABELS[previewItem.status] }}
              </span>
              <span class="preview-dialog__time">{{
                formatFeatureTime(previewItem.createdAt)
              }}</span>
            </div>
            <p class="preview-dialog__desc">
              {{ getRecordPreview(previewItem) }}
            </p>
          </div>
          <div class="preview-dialog__footer">
            <button
              class="preview-btn preview-btn--secondary"
              @click="showPreview = false"
            >
              关闭
            </button>
            <button
              v-if="previewItem.taskId && previewItem.status === 'completed'"
              class="preview-btn preview-btn--primary"
              @click="
                downloadRecord(previewItem);
                showPreview = false;
              "
            >
              下载课件
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </Transition>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  background: #f7f5f2;
}

.features-page {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  --font-display: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-body: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --ink: #1a1a1a;
  --ink-soft: #4a4a4a;
  --ink-muted: #6b7280;
  --accent: #2b6cb0;
  --accent-deep: #1e4f82;
  --accent-mint: #23c3b2;
  --accent-violet: #8b5cf6;
  --accent-ppt: #2563eb;
  --accent-doc: #059669;
  --accent-interactive: #7c3aed;
  --accent-exam: #dc2626;
  --accent-classroom: #d97706;
  --accent-feedback: #dc2626;
  --accent-history: #0891b2;
  --accent-iterate: #9333ea;
  --border: rgba(0, 0, 0, 0.06);
  --border-strong: rgba(0, 0, 0, 0.1);
  --panel: #ffffff;
  --panel-strong: #ffffff;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.03);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.06), 0 4px 8px rgba(0, 0, 0, 0.03);
  --ease-out: cubic-bezier(0.2, 0.7, 0.2, 1);
  position: relative;
  min-height: 100vh;
  display: flex;
  color: var(--ink);
  font-family: var(--font-body);
  background: #f7f5f2;
}

.features-page__ambient {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.ambient-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(10px);
  opacity: 0.65;
}

.ambient-orb--one {
  width: 320px;
  height: 320px;
  top: -80px;
  right: 12%;
  background: radial-gradient(
    circle,
    rgba(43, 108, 176, 0.28),
    rgba(43, 108, 176, 0)
  );
}

.ambient-orb--two {
  width: 280px;
  height: 280px;
  bottom: 10%;
  left: -60px;
  background: radial-gradient(
    circle,
    rgba(35, 195, 178, 0.16),
    rgba(35, 195, 178, 0)
  );
}

.ambient-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(43, 108, 176, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(43, 108, 176, 0.04) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 84%);
}

.sidebar {
  position: sticky;
  top: 0;
  width: 292px;
  height: 100vh;
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: #ffffff;
  border-right: 1px solid var(--border);
  box-shadow:
    1px 0 0 rgba(0, 0, 0, 0.03),
    2px 0 8px rgba(0, 0, 0, 0.02);
  z-index: 2;
}

.sidebar__head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: #fafafa;
  color: var(--ink);
  text-decoration: none;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.icon-btn:hover {
  background: #f1f1f2;
}

.icon-btn svg {
  width: 18px;
  height: 18px;
}

.sidebar__brand {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.sidebar__brand-name {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 0.98rem;
  letter-spacing: -0.02em;
}

.sidebar__brand-sub {
  font-size: 0.75rem;
  color: var(--ink-muted);
}

.overview-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #fafafa;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.overview-btn:hover,
.overview-btn--active {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(43, 108, 176, 0.04);
  box-shadow: none;
}

.overview-btn svg {
  width: 18px;
  height: 18px;
}

.nav-group {
  margin-bottom: 10px;
}

.nav-group__label {
  margin: 0 0 8px;
  padding: 0 10px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ink-muted);
  opacity: 0.7;
}

.nav-group--featured .nav-group__label {
  opacity: 1;
  color: var(--accent);
  font-size: 0.78rem;
}

.nav-group--featured {
  margin-bottom: 18px;
}

.nav-group--featured .nav-item {
  margin-bottom: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  margin-bottom: 6px;
  padding: 12px 12px 12px 14px;
  border: 0;
  border-radius: 0 10px 10px 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
  border-left: 2px solid transparent;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.nav-item:hover {
  background: #f1f1f2;
  border-left-color: #e2e8f0;
  transform: translateX(2px);
}

.nav-item--active {
  background: #f2f4f7;
  border-left-color: var(--accent);
}

.nav-item__icon {
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: transparent;
  color: var(--ink-muted);
  border: 0;
  flex-shrink: 0;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.nav-item:hover .nav-item__icon {
  background: #ebedf0;
}

.nav-item--active .nav-item__icon {
  background: transparent;
  color: var(--accent);
  border: 0;
}

.nav-item__icon svg {
  width: 18px;
  height: 18px;
}

.nav-item__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.nav-item__text strong {
  font-size: 0.86rem;
  font-weight: 800;
  color: var(--ink);
}

.nav-item__text small {
  font-size: 0.72rem;
  color: var(--ink-muted);
  line-height: 1.5;
}

.sidebar__foot {
  margin-top: auto;
  padding-top: 18px;
}

.assistant-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(43, 108, 176, 0.06);
  color: var(--accent);
  text-decoration: none;
  font-size: 0.84rem;
  font-weight: 600;
  transition: background 0.2s ease;
}

.assistant-link:hover {
  background: rgba(43, 108, 176, 0.1);
}

.assistant-link svg {
  width: 16px;
  height: 16px;
}

.main {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 0;
  padding: 24px;
}

.main__header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 8px;
}

.header-chip {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 10px;
  background: #f1f1f2;
  color: var(--ink-muted);
  font-size: 0.72rem;
  font-weight: 600;
}

.main__header h1 {
  margin: 10px 0 0;
  font-family: var(--font-display);
  font-size: 1.84rem;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.main__subtitle {
  margin: 8px 0 0;
  max-width: 760px;
  color: var(--ink-muted);
  font-size: 0.92rem;
  line-height: 1.75;
}

.mobile-only {
  display: none;
}

.main__body {
  min-height: calc(100vh - 120px);
  padding: 28px;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: var(--shadow);
  overflow-y: auto;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
  margin-top: 12px;
  animation: panelFadeIn 0.35s var(--ease-out);
}

@keyframes panelFadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-head h2,
.section-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.16rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

/* ── 各面板标题 - 统一纯色 ── */
.panel[data-panel="ppt"] .section-head h2,
.panel[data-panel="doc"] .section-head h2,
.panel[data-panel="interactive"] .section-head h2,
.panel[data-panel="exam"] .section-head h2,
.panel[data-panel="history"] .archive-section-header h2,
.panel[data-panel="feedback"] .placeholder-panel h2 {
  background: none;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: var(--ink);
  background-clip: unset;
  color: var(--ink);
}

/* ── 各面板模块色彩个性 ── */
.panel[data-panel="ppt"] .section-tag {
  background: rgba(37, 99, 235, 0.1);
  color: var(--accent-ppt);
}
.panel[data-panel="doc"] .section-tag {
  background: rgba(5, 150, 105, 0.1);
  color: var(--accent-doc);
}
.panel[data-panel="interactive"] .section-tag {
  background: rgba(124, 58, 237, 0.1);
  color: var(--accent-interactive);
}
.panel[data-panel="exam"] .section-tag {
  background: rgba(220, 38, 38, 0.08);
  color: var(--accent-exam);
}

.panel[data-panel="ppt"] .ai-badge--active {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.2);
  color: var(--accent-ppt);
}
.panel[data-panel="doc"] .ai-badge--active {
  background: rgba(5, 150, 105, 0.08);
  border-color: rgba(5, 150, 105, 0.2);
  color: var(--accent-doc);
}
.panel[data-panel="interactive"] .ai-badge--active {
  background: rgba(124, 58, 237, 0.08);
  border-color: rgba(124, 58, 237, 0.2);
  color: var(--accent-interactive);
}
.panel[data-panel="exam"] .ai-badge--active {
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.2);
  color: var(--accent-exam);
}

.section-head small {
  color: var(--ink-muted);
  font-size: 0.76rem;
}

.section-annotation {
  margin: 4px 0 16px;
  font-size: 0.82rem;
  color: var(--ink-muted);
  line-height: 1.4;
}

.section-tag,
.preview-card__eyebrow {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 10px;
  background: #f1f1f2;
  color: var(--ink-muted);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

/* ===== 创作工作台头部 ===== */
.workspace-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 28px 32px 24px;
  margin-bottom: 8px;
}

.workspace-header__text h2 {
  font-family: var(--font-display);
  font-size: 1.55rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: var(--ink);
  margin-bottom: 4px;
}

.workspace-header__text p {
  font-size: 0.88rem;
  color: var(--ink-muted);
  margin: 0;
}

.workspace-header__meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  color: #94a3b8;
}

.meta-item svg {
  opacity: 0.5;
}

.lead-desc {
  margin: 0 0 24px;
  max-width: 34rem;
  color: #64748b;
  line-height: 1.7;
  font-size: 0.92rem;
}

/* ECharts 饼图容器 */
.task-pie-chart {
  padding: 20px 0 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 8px;
}

.pie-chart-container {
  width: 100%;
  height: 200px;
  min-height: 200px;
}

/* 环形图容器 - 保留旧样式兼容 */
.task-ring-chart {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 20px 0 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 8px;
}

.ring-chart-wrapper {
  flex-shrink: 0;
  width: 140px;
  height: 140px;
  animation: ringEnter 0.7s ease-out;
}

@keyframes ringEnter {
  from {
    opacity: 0;
    transform: scale(0.85) rotate(-15deg);
  }
  to {
    opacity: 1;
    transform: scale(1) rotate(0);
  }
}

.ring-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.08));
}

.ring-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.ring-legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition:
    background 0.25s ease,
    border-color 0.25s ease;
  border: 1px solid transparent;
}

.ring-legend-item:hover,
.ring-legend-item.active {
  background: rgba(43, 108, 176, 0.06);
  border-color: rgba(43, 108, 176, 0.15);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(43, 108, 176, 0.2);
}

.legend-label {
  font-size: 0.82rem;
  color: #64748b;
  flex: 1;
}

.ring-legend-item.active .legend-label {
  color: #334155;
}

.legend-value {
  font-size: 0.88rem;
  font-weight: 700;
  color: #334155;
  min-width: 24px;
  text-align: right;
}

/* ===== 指标卡片网格 ===== */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  padding: 0 32px 28px;
}

.metric-card {
  padding: 24px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: var(--shadow);
  transition:
    transform 0.25s var(--ease-out),
    box-shadow 0.25s ease,
    border-color 0.25s ease;
  cursor: default;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}

.metric-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.metric-card__num {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  color: #fff;
}

.metric-card[data-tone="blue"] .metric-card__num {
  background: var(--accent);
}
.metric-card[data-tone="mint"] .metric-card__num {
  background: #10b981;
}
.metric-card[data-tone="violet"] .metric-card__num {
  background: #7c3aed;
}
.metric-card[data-tone="amber"] .metric-card__num {
  background: #f59e0b;
}

.metric-card__label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--ink-muted);
}

.metric-card__value {
  display: block;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--ink);
  margin-bottom: 8px;
  line-height: 1;
}

.metric-card__detail {
  margin: 0;
  font-size: 0.8rem;
  color: #9a9a9a;
  line-height: 1.55;
}

.insight-grid {
  display: grid;
  grid-template-columns: 1.22fr 0.78fr;
  gap: 18px;
}

.insight-grid--simple {
  grid-template-columns: 1fr 1fr;
}

/* =========================================================
   教学反思 - 新排版
   ========================================================= */
.reflect-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 0;
}
.reflect-header__left {
  flex-shrink: 0;
}
.reflect-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}
.reflect-title svg {
  color: #4c7dff;
}
.reflect-desc {
  margin: 0;
  font-size: 0.85rem;
  color: #94a3b8;
}
.reflect-header__right {
  flex: 1;
  max-width: 460px;
  min-width: 0;
}

/* --- 最近反馈卡片块 --- */
.recent-feedback-card {
  background: rgba(248, 251, 255, 0.7);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 16px 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}
.recent-feedback-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.recent-feedback-card__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}
.recent-feedback-card__title svg {
  color: #4c7dff;
}
.recent-feedback-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(43, 108, 176, 0.1);
  color: #4c7dff;
  font-size: 0.72rem;
  font-weight: 700;
}
.recent-feedback-card__foot {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(128, 151, 185, 0.08);
  display: flex;
  justify-content: flex-end;
}

.recent-feedback-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 0;
}
.recent-feedback-empty {
  padding: 10px 8px;
  text-align: center;
  font-size: 0.82rem;
  color: #94a3b8;
}
.recent-feedback-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.82rem;
  border: 1px solid rgba(128, 151, 185, 0.1);
  transition: background 0.2s;
}
.recent-feedback-item:hover {
  background: #f1f4f9;
}
.recent-feedback__type {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 999px;
  flex-shrink: 0;
}
.recent-feedback__type.ppt {
  background: rgba(43, 108, 176, 0.1);
  color: #4c7dff;
}
.recent-feedback__type.doc {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
.recent-feedback__type.interactive {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}
.recent-feedback__title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #475569;
  font-weight: 500;
}
.recent-feedback__status {
  font-size: 0.7rem;
  padding: 1px 7px;
  border-radius: 999px;
  flex-shrink: 0;
  font-weight: 500;
}
.recent-feedback__status[data-status="pending"] {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}
.recent-feedback__status[data-status="iterating"] {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}
.recent-feedback__status[data-status="done"] {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}
.view-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.8rem;
  color: #4c7dff;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  font-weight: 500;
  margin-left: auto;
}
.view-all-btn:hover {
  color: #3156d3;
}
.view-all-btn svg {
  transition: transform 0.2s;
}
.view-all-btn:hover svg {
  transform: translateX(2px);
}

/* --- 左右分栏布局 --- */
.reflect-layout {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 24px;
  align-items: start;
}

@media (max-width: 900px) {
  .reflect-layout {
    grid-template-columns: 1fr;
  }
}

.reflect-divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    rgba(128, 151, 185, 0.2),
    rgba(128, 151, 185, 0.05)
  );
  margin: 20px 0 24px;
}

/* --- 表单卡片 --- */
.reflect-form-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 22px 24px 20px;
  box-shadow: var(--shadow);
}
.reflect-form-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(128, 151, 185, 0.1);
}
.reflect-form-card__header svg {
  color: var(--accent-iterate);
}

.reflect-form-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reflect-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.reflect-field__label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}
.reflect-field__required {
  color: #ef4444;
}

.reflect-select,
.reflect-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.88rem;
  color: #1e293b;
  background: white;
  font-family: inherit;
  transition:
    border-color 0.25s,
    box-shadow 0.25s;
  box-sizing: border-box;
}
.reflect-select:focus-visible,
.reflect-input:focus-visible {
  outline: none;
  border-color: var(--accent-iterate);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.08);
}
.reflect-select::placeholder,
.reflect-input::placeholder {
  color: #94a3b8;
}

.reflect-textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.88rem;
  color: #1e293b;
  background: white;
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
  line-height: 1.6;
  transition:
    border-color 0.25s,
    box-shadow 0.25s;
  box-sizing: border-box;
}
.reflect-textarea:focus-visible {
  outline: none;
  border-color: var(--accent-iterate);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.08);
}
.reflect-textarea::placeholder {
  color: #94a3b8;
}

/* 附件上传 */
.reflect-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reflect-upload__btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1px dashed rgba(147, 51, 234, 0.3);
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--accent-iterate);
  background: rgba(147, 51, 234, 0.04);
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s,
    border-color 0.2s,
    box-shadow 0.2s,
    transform 0.2s;
  width: fit-content;
}
.reflect-upload__btn:hover {
  background: rgba(147, 51, 234, 0.08);
  border-color: var(--accent-iterate);
}
.reflect-upload__hint {
  font-size: 0.75rem;
  color: #94a3b8;
}
.reflect-upload__input {
  display: none;
}
.reflect-upload__file {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(43, 108, 176, 0.06);
  border-radius: 8px;
  font-size: 0.82rem;
  color: #334155;
  width: fit-content;
}
.reflect-upload__file svg {
  color: #4c7dff;
  flex-shrink: 0;
}
.reflect-upload__remove {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0 2px;
}
.reflect-upload__remove:hover {
  color: #ef4444;
}

/* 快捷填入标签 */
.reflect-tips {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid rgba(128, 151, 185, 0.08);
}
.reflect-tips__label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  flex-shrink: 0;
  padding-top: 4px;
}
.reflect-tips__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.reflect-tips__tags .tip-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--accent-iterate);
  background: rgba(147, 51, 234, 0.07);
  border: 1px solid rgba(147, 51, 234, 0.12);
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s,
    border-color 0.2s,
    box-shadow 0.2s,
    transform 0.2s;
  font-family: inherit;
  line-height: inherit;
}
.reflect-tips__tags .tip-tag:hover {
  background: rgba(147, 51, 234, 0.14);
  border-color: rgba(147, 51, 234, 0.25);
}

/* 提交按钮 */
.reflect-form-card__actions {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
.reflect-form-card__actions .btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 32px;
  border-radius: 14px;
  font-size: 0.9rem;
  font-weight: 600;
}

/* --- 历史反馈记录卡片 --- */
.reflect-history-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px;
  max-height: 580px;
  overflow-y: auto;
  box-shadow: var(--shadow);
}
.reflect-history-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(128, 151, 185, 0.12);
}
.reflect-history-card__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
}
.reflect-history-card__title svg {
  color: var(--accent-iterate);
}
.reflect-history-card__badge {
  background: rgba(147, 51, 234, 0.1);
  color: var(--accent-iterate);
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
}
.reflect-history-card__foot {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(128, 151, 185, 0.12);
  text-align: center;
}

.reflect-history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.reflect-history-item {
  padding: 12px;
  border-radius: 10px;
  background: white;
  border: 1px solid var(--border);
  transition:
    box-shadow 0.2s,
    border-color 0.2s;
}
.reflect-history-item:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}
.reflect-history-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.reflect-history-item__tags {
  display: flex;
  align-items: center;
  gap: 6px;
}
.rh-type {
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 999px;
  font-weight: 500;
  background: rgba(147, 51, 234, 0.08);
  color: var(--accent-iterate);
}
.rh-subject {
  font-size: 0.7rem;
  color: #738197;
}
.rh-status {
  font-size: 0.68rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 500;
}
.rh-status[data-status="pending"] {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}
.rh-status[data-status="iterating"] {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}
.rh-status[data-status="resolved"] {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.reflect-history-item__title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.reflect-history-item__preview {
  font-size: 0.72rem;
  color: #738197;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 6px;
}
.reflect-history-item__time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.68rem;
  color: #94a3b8;
}
.reflect-history-item__time svg {
  color: #94a3b8;
}
.reflect-history-empty {
  text-align: center;
  padding: 30px 0;
  color: #94a3b8;
  font-size: 0.8rem;
}
.reflect-history-empty svg {
  color: #cbd5e1;
  margin-bottom: 8px;
}

.dashboard-card,
.form-card,
.preview-card,
.support-card,
.viz-card,
.feedback-card,
.summary-pill {
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fff;
  box-shadow: var(--shadow);
  transition:
    box-shadow 0.25s ease,
    transform 0.2s var(--ease-out);
}

.dashboard-card,
.form-card,
.support-card,
.viz-card,
.feedback-card {
  padding: 22px;
}

.dashboard-card--chart {
  background: #fff;
}

.dashboard-card--donut {
  background: #fff;
}

/* 柱状图卡片 */
.dashboard-card--queue {
  background: #fff;
}

/* 类型图例 */
.chart-type-legend {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ct-legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  color: var(--ink-muted);
  font-weight: 500;
}

.ct-legend-item i {
  display: block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

/* ========== ECharts 组合图表（柱状图+折线图） ========== */
.radar-chart-container {
  width: 100%;
  height: 320px;
  min-height: 320px;
  animation: chartFadeIn 0.8s ease-out;
}

/* 图表容器出场动画 */
@keyframes chartFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 任务状态饼图容器动画 */
.pie-chart-container {
  width: 100%;
  height: 200px;
  min-height: 200px;
  animation: chartFadeIn 0.8s ease-out 0.2s both;
}

/* 趋势折线图容器动画 */
.trend-line-chart-container {
  width: 100%;
  height: 320px;
  min-height: 320px;
  margin: 12px 0 8px;
  animation: chartFadeIn 0.8s ease-out 0.4s both;
}

/* ========== 现代风格柱状图 ========== */
.modern-chart {
  position: relative;
  padding: 8px 4px 4px;
}

/* 图例 */
.modern-legend {
  display: flex;
  justify-content: center;
  gap: 28px;
  margin-bottom: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.35);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 图表绘制区域 */
.chart-area {
  position: relative;
  background: #f8fafc;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.4);
  padding: 8px 4px 4px;
}

/* 柱状图容器 */
.chart-bars-container {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 200px;
  padding: 0 12px 28px;
  position: relative;
}

/* 单个柱子包装 */
.modern-bar-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 48px;
  animation: barGrowIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}

@keyframes barGrowIn {
  from {
    opacity: 0;
    transform: scaleY(0);
  }
  to {
    opacity: 1;
    transform: scaleY(1);
  }
}

/* 数值标签（柱顶） */
.bar-value-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 6px;
  opacity: 0;
  transform: translateY(4px);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.bar-value-label.show {
  opacity: 1;
  transform: translateY(0);
}

/* 堆叠柱 */
.modern-bar-stack {
  width: 32px;
  height: 160px;
  display: flex;
  flex-direction: column-reverse;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.25s ease;
}

.modern-bar-wrapper:hover .modern-bar-stack,
.modern-bar-wrapper.active .modern-bar-stack {
  box-shadow: 0 4px 16px rgba(43, 108, 176, 0.15);
}

.modern-bar-segment {
  width: 100%;
  transition: opacity 0.2s ease;
  min-height: 4px;
}

/* 日期标签 */
.bar-day-label {
  position: absolute;
  bottom: -24px;
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
  white-space: nowrap;
}

.modern-bar-wrapper.active .bar-day-label {
  color: #4c7dff;
  font-weight: 600;
}

/* Y轴刻度线 */
.y-axis-lines {
  position: absolute;
  left: 0;
  right: 0;
  top: 16px;
  bottom: 32px;
  pointer-events: none;
  z-index: 0;
}

.y-line {
  position: absolute;
  left: 8px;
  right: 8px;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(226, 232, 240, 0.6) 10%,
    rgba(226, 232, 240, 0.6) 90%,
    transparent
  );
}

.y-line:nth-child(1) {
  top: 0;
}
.y-line:nth-child(2) {
  top: 25%;
}
.y-line:nth-child(3) {
  top: 50%;
}
.y-line:nth-child(4) {
  top: 75%;
}

.y-label {
  position: absolute;
  left: -4px;
  top: -8px;
  font-size: 0.65rem;
  color: #cbd5e1;
  font-weight: 500;
}

/* 悬停提示卡片 */
.modern-tooltip {
  position: absolute;
  bottom: calc(100% + 12px);
  left: 50%;
  transform: translateX(-50%);
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  min-width: 130px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(226, 232, 240, 0.8);
  z-index: 10;
}

.modern-tooltip::after {
  content: "";
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-top: 6px solid #fff;
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f1f5f9;
}

.tooltip-day {
  font-size: 0.8rem;
  font-weight: 600;
  color: #1e293b;
}

.tooltip-total {
  font-size: 0.7rem;
  color: #64748b;
  background: #f8fafc;
  padding: 2px 8px;
  border-radius: 10px;
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
}

.row-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.row-label {
  color: #64748b;
  flex: 1;
}

.row-value {
  font-weight: 600;
  color: #334155;
}

/* 提示框过渡动画 */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-8px);
}

.line-chart-card {
  margin-top: 8px;
  position: relative;
}

.line-chart {
  width: 100%;
  height: 190px;
  display: block;
}

/* 旧版SVG折线图样式保留兼容 */
.line-chart__grid {
  stroke: rgba(114, 135, 168, 0.12);
  stroke-width: 1;
}

.y-axis-label {
  font-size: 0.72rem;
  fill: var(--ink-muted);
  font-weight: 500;
}

/* 数据点交互 */
.data-point {
  cursor: pointer;
}

.data-point .point-hit-area {
  cursor: pointer;
  pointer-events: all;
}

.data-point .point-circle {
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
}

.data-point:hover .point-circle {
  r: 8;
  fill: #3156d3;
}

.point-tooltip {
  opacity: 0;
  transition: opacity 0.2s ease;
  pointer-events: none;
}

.data-point:hover .point-tooltip {
  opacity: 1;
}

.line-chart__labels {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10px;
  margin-top: 8px;
}

.line-chart__label {
  text-align: center;
  cursor: pointer;
  padding: 6px 4px;
  border-radius: 10px;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.line-chart__label:hover {
  background: rgba(43, 108, 176, 0.08);
}

.line-chart__label strong {
  display: block;
  font-size: 0.84rem;
  color: var(--accent-deep);
}

.line-chart__label span {
  font-size: 0.72rem;
  color: var(--ink-muted);
}

/* 统计概览 */
.trend-stats-bar {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  margin: 14px 0 0;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #eef2f6;
}

.trend-stat__value {
  display: block;
  font-size: 1.3rem;
  font-weight: 800;
  color: #3b5998;
  line-height: 1.2;
}

.trend-stat__label {
  display: block;
  font-size: 0.7rem;
  color: #7c8db5;
  margin-top: 2px;
}

.trend-stat--subjects {
  flex: 1.5;
}

.subject-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  margin-bottom: 2px;
}

.subject-tag {
  padding: 2px 7px;
  background: rgba(43, 108, 176, 0.08);
  border-radius: 10px;
  font-size: 0.68rem;
  color: #4c7dff;
  font-weight: 500;
}

.trend-stat {
  flex: 1;
  text-align: center;
}

/* 日期详情面板 */
.day-detail-panel {
  margin-top: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 20px;
  border: 1px solid #eef2f6;
  box-shadow: 0 8px 32px rgba(43, 108, 176, 0.12);
}

/* 头部 */
.day-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(43, 108, 176, 0.08);
}

.day-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.day-date-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: var(--accent);
  border-radius: 10px;
  color: #fff;
}

.day-weekday {
  font-size: 0.7rem;
  font-weight: 600;
  opacity: 0.9;
}

.day-date {
  font-size: 1.1rem;
  font-weight: 800;
}

.day-header-left h4 {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}

.day-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.day-efficiency {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}

.day-efficiency.high {
  background: rgba(35, 195, 178, 0.12);
  color: #23c3b2;
}

.day-efficiency.normal {
  background: rgba(43, 108, 176, 0.12);
  color: #4c7dff;
}

.day-efficiency.low {
  background: rgba(139, 92, 246, 0.12);
  color: #8b5cf6;
}

.efficiency-icon {
  width: 16px;
  height: 16px;
}

.btn-close {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  background: rgba(113, 129, 151, 0.1);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.btn-close:hover {
  background: rgba(113, 129, 151, 0.2);
  transform: rotate(90deg);
}

.btn-close svg {
  width: 18px;
  height: 18px;
  color: var(--ink-muted);
}

/* 核心指标卡片 */
.day-metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.day-metric-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 14px;
  border: 1px solid #eef2f6;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.day-metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(43, 108, 176, 0.1);
}

.metric-icon {
  font-size: 1.6rem;
}

.metric-info {
  display: flex;
  flex-direction: column;
}

.metric-value {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--ink);
  line-height: 1;
}

.metric-value small {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--ink-muted);
  margin-left: 2px;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--ink-muted);
  margin-top: 4px;
}

/* 分布统计 */
.day-distribution {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
  margin-bottom: 20px;
}

.dist-section {
  padding: 16px;
  background: #f8fafc;
  border-radius: 14px;
}

.dist-section h5 {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 12px;
}

.dist-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dist-bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dist-label {
  width: 48px;
  font-size: 0.78rem;
  color: var(--ink-soft);
  font-weight: 600;
}

.dist-bar-bg {
  flex: 1;
  height: 8px;
  background: rgba(43, 108, 176, 0.08);
  border-radius: 4px;
  overflow: hidden;
}

.dist-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.dist-bar-fill.ppt {
  background: var(--accent);
}
.dist-bar-fill.doc {
  background: #10b981;
}
.dist-bar-fill.interactive {
  background: #7c3aed;
}

.dist-count {
  width: 24px;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--ink);
  text-align: right;
}

/* 学科分布 */
.subject-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.subject-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 20px;
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.pill-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--accent-deep);
}

.pill-count {
  font-size: 0.72rem;
  font-weight: 700;
  color: #fff;
  background: var(--accent-deep);
  padding: 2px 8px;
  border-radius: 10px;
}

/* 占位面板样式 */
.placeholder-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 48px;
  text-align: center;
  background: #fafafa;
  border-radius: 10px;
  border: 1px solid var(--border);
}

.placeholder-icon {
  font-size: 4rem;
  margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.placeholder-panel h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 12px;
}

.placeholder-panel > p {
  font-size: 1rem;
  color: #64748b;
  margin-bottom: 24px;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 32px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 480px;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: white;
  border-radius: 12px;
  font-size: 0.9rem;
  color: #334155;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.feature-list li:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.placeholder-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  background: #fafafa;
  border-radius: 10px;
  border: 1px solid var(--border);
  font-size: 0.875rem;
  color: var(--ink-soft);
  max-width: 480px;
}

.placeholder-tip span {
  font-size: 1.2rem;
}

/* 课件列表 */
.day-items-section {
  margin-bottom: 16px;
}

.day-items-section h5 {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 12px;
}

.day-items-section h5 small {
  font-size: 0.75rem;
  color: var(--ink-muted);
  font-weight: 500;
  margin-left: 6px;
}

.day-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.day-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  border: 1px solid rgba(43, 108, 176, 0.06);
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.day-item:hover {
  background: rgba(248, 251, 255, 1);
  border-color: rgba(43, 108, 176, 0.12);
  transform: translateX(4px);
}

.item-left {
  display: flex;
  gap: 8px;
}

.day-item__type {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 700;
}

.day-item__type.ppt {
  background: rgba(43, 108, 176, 0.12);
  color: #4c7dff;
}
.day-item__type.doc {
  background: rgba(35, 195, 178, 0.12);
  color: #23c3b2;
}
.day-item__type.interactive {
  background: rgba(139, 92, 246, 0.12);
  color: #8b5cf6;
}

.day-item__subject {
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.08);
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent-deep);
}

.day-item__title {
  flex: 1;
  font-size: 0.88rem;
  color: var(--ink);
  font-weight: 500;
}

.item-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.day-item__score {
  padding: 4px 10px;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 700;
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.day-item__score.high {
  background: rgba(35, 195, 178, 0.12);
  color: #23c3b2;
}

.day-item__time {
  font-size: 0.75rem;
  color: var(--ink-muted);
  font-family: monospace;
}

/* 底部提示 */
.day-footer-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(43, 108, 176, 0.04);
  border-radius: 12px;
  color: var(--ink-muted);
  font-size: 0.8rem;
}

.tip-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ========== 雷达图样式 ========== */
.dashboard-card--radar {
  background: #fff;
}

.radar-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 12px;
}

.radar-chart {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto;
}

.radar-svg {
  width: 100%;
  height: 100%;
  overflow: visible;
}

.radar-area {
  animation: radarPulse 2s ease-in-out infinite;
}

@keyframes radarPulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.radar-point {
  animation: radarPointPop 0.5s ease-out both;
}

.radar-point:nth-child(1) {
  animation-delay: 0.1s;
}
.radar-point:nth-child(2) {
  animation-delay: 0.2s;
}
.radar-point:nth-child(3) {
  animation-delay: 0.3s;
}
.radar-point:nth-child(4) {
  animation-delay: 0.4s;
}
.radar-point:nth-child(5) {
  animation-delay: 0.5s;
}
.radar-point:nth-child(6) {
  animation-delay: 0.6s;
}

@keyframes radarPointPop {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.radar-labels {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.radar-label {
  position: absolute;
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 500;
  transform: translate(-50%, -50%);
  white-space: nowrap;
}

.radar-metrics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.radar-metric-item {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.6);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.metric-name {
  font-size: 0.8rem;
  color: #475569;
  font-weight: 500;
}

.metric-score {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
}

.metric-bar {
  height: 5px;
  background: rgba(226, 232, 240, 0.6);
  border-radius: 3px;
  overflow: hidden;
}

.metric-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s ease;
}

/* 旧版环形图样式保留 */
.donut-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 12px;
}

.donut-chart {
  position: relative;
  width: 180px;
  height: 180px;
  margin: 0 auto;
}

.donut-chart svg {
  width: 100%;
  height: 100%;
}

.donut-chart__track {
  fill: none;
  stroke: rgba(43, 108, 176, 0.08);
  stroke-width: 18;
}

.donut-chart__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.donut-chart__center strong {
  font-size: 1.7rem;
  font-weight: 800;
}

.donut-chart__center span {
  font-size: 0.78rem;
  color: var(--ink-muted);
}

.donut-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.donut-legend__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
}

.donut-legend__item i {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
}

.donut-legend__item strong,
.queue-item__info strong,
.record-card__info strong,
.feedback-card h3,
.recommendation-item strong {
  display: block;
  font-size: 0.94rem;
  font-weight: 800;
}

.donut-legend__item span,
.queue-item__info span,
.record-card__info span,
.recommendation-item p,
.feedback-card__meta,
.viz-note,
.support-item p,
.upload-zone__drop p,
.preview-highlight p {
  font-size: 0.82rem;
  color: var(--ink-soft);
  line-height: 1.65;
}

.queue-list,
.record-list,
.feedback-list,
.support-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(43, 108, 176, 0.08);
}

.queue-item__icon {
  width: 46px;
  height: 46px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(43, 108, 176, 0.08);
  flex-shrink: 0;
}

.queue-item__icon :deep(svg) {
  width: 22px;
  height: 22px;
  color: var(--accent);
}

.queue-item__info {
  flex: 1;
  min-width: 0;
}

/* 新版记录卡片 */
.record-card {
  border-radius: 12px;
  background: #fff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  overflow: hidden;
  transition:
    background 0.25s var(--ease-out),
    color 0.25s var(--ease-out),
    border-color 0.25s var(--ease-out),
    box-shadow 0.25s var(--ease-out),
    transform 0.25s var(--ease-out);
  cursor: pointer;
}

.record-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-strong);
}

.record-card.expanded {
  box-shadow: var(--shadow-lg);
  border-color: var(--border-strong);
}

.record-card__header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
}

.record-card__icon {
  width: 52px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  flex-shrink: 0;
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
  position: relative;
  overflow: hidden;
}

/* 图标SVG样式 */
.record-card__icon :deep(svg) {
  width: 26px;
  height: 26px;
}

/* PPT课件 - 蓝色主题 */
.record-card__icon.ppt {
  background: var(--accent);
  box-shadow: none;
}

.record-card__icon.ppt :deep(svg) {
  color: white;
}

/* 教案 - 青色主题 */
.record-card__icon.doc {
  background: #10b981;
  box-shadow: none;
}

.record-card__icon.doc :deep(svg) {
  color: white;
}

/* 互动 - 紫色主题 */
.record-card__icon.interactive {
  background: #7c3aed;
  box-shadow: none;
}

.record-card__icon.interactive :deep(svg) {
  color: white;
}

/* 进度条相关样式 */
.record-card:hover .record-card__icon {
  transform: scale(1.05);
}

.record-card:hover .record-card__icon.ppt {
  box-shadow: 0 2px 8px rgba(43, 108, 176, 0.2);
}

.record-card:hover .record-card__icon.doc {
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.2);
}

.record-card:hover .record-card__icon.interactive {
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.2);
}

.record-card__info {
  flex: 1;
  min-width: 0;
}

.record-card__info strong {
  display: block;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 0.74rem;
  font-weight: 600;
}

.meta-item.subject {
  background: rgba(99, 102, 241, 0.1);
  color: #1e4f82;
}

.meta-item.type {
  background: rgba(43, 108, 176, 0.1);
  color: #4c7dff;
}

.meta-item.time {
  background: rgba(148, 163, 184, 0.1);
  color: #64748b;
}

.record-card__actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-expand {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(43, 108, 176, 0.08);
  border: none;
  color: var(--accent-deep);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.btn-expand:hover {
  background: rgba(43, 108, 176, 0.15);
}

.expand-icon {
  width: 18px;
  height: 18px;
  transition: transform 0.3s ease;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

/* 展开详情区域 */
.record-card__details {
  padding: 0 18px 18px;
  border-top: 1px solid rgba(43, 108, 176, 0.06);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.record-preview {
  padding: 16px 0;
}

.record-preview h5 {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--ink-muted);
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.preview-content {
  padding: 14px 16px;
  background: rgba(248, 251, 255, 0.8);
  border-radius: 12px;
  border: 1px solid rgba(43, 108, 176, 0.08);
}

.preview-content p {
  margin: 0;
  font-size: 0.86rem;
  color: var(--ink-soft);
  line-height: 1.7;
}

/* 快捷操作按钮 */
.record-quick-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding-bottom: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(43, 108, 176, 0.12);
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.action-btn:hover {
  background: rgba(43, 108, 176, 0.08);
  border-color: rgba(43, 108, 176, 0.2);
  transform: translateY(-1px);
}

.action-btn.primary {
  background: var(--accent);
  color: white;
  border-color: transparent;
}

.action-btn.primary:hover {
  background: var(--accent-deep);
}

.action-btn.feedback {
  background: rgba(124, 58, 237, 0.08);
  border-color: rgba(124, 58, 237, 0.2);
  color: #7c3aed;
}

.action-btn.feedback:hover {
  background: rgba(124, 58, 237, 0.15);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

/* 底部操作栏 */
.record-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid rgba(43, 108, 176, 0.06);
}

.record-id {
  font-size: 0.72rem;
  color: var(--ink-muted);
  font-family: monospace;
}

.btn-delete-text {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: none;
  color: #ef4444;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.btn-delete-text:hover {
  background: rgba(239, 68, 68, 0.15);
}

.btn-delete-text svg {
  width: 14px;
  height: 14px;
}

/* 空状态 */
.record-empty {
  text-align: center;
  padding: 60px 20px;
}

.empty-illustration {
  width: 100px;
  height: 100px;
  margin: 0 auto 24px;
}

.empty-illustration svg {
  width: 100%;
  height: 100%;
}

.record-empty h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 8px;
}

.record-empty p {
  font-size: 0.88rem;
  color: var(--ink-soft);
  margin: 0 0 20px;
}

.record-empty .btn-primary {
  padding: 12px 28px;
  border-radius: 10px;
  background: var(--accent);
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.record-empty .btn-primary:hover {
  background: var(--accent-deep);
  transform: translateY(-2px);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-style: normal;
  font-weight: 800;
  white-space: nowrap;
}

.status-badge[data-status="completed"] {
  color: #0f8d73;
  background: rgba(35, 195, 178, 0.12);
}

.status-badge[data-status="draft"] {
  color: #6b46c1;
  background: rgba(139, 92, 246, 0.12);
}

.status-badge[data-status="iterating"] {
  color: var(--accent-deep);
  background: rgba(43, 108, 176, 0.12);
}

/* ── 生成进度条 ────────────────────────────── */
.progress-bar-wrap {
  margin-bottom: 24px;
  padding: 20px 24px;
  background: #fafafa;
  border: 1px solid var(--border);
  border-radius: 10px;
}
.progress-bar__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.progress-bar__stage {
  font-size: 0.9rem;
  font-weight: 600;
  color: #1e40af;
}
.progress-bar__pct {
  font-size: 0.85rem;
  font-weight: 700;
  color: #3b82f6;
}
.progress-bar__track {
  width: 100%;
  height: 8px;
  background: #f1f1f2;
  border-radius: 10px;
  overflow: hidden;
}
.progress-bar__fill {
  height: 100%;
  background: var(--accent);
  border-radius: 10px;
  transition: width 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.progress-bar__done {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #166534;
}
.progress-bar__done a {
  color: #2563eb;
  text-decoration: underline;
  cursor: pointer;
  font-weight: 600;
}

.generator-layout {
  display: grid;
  grid-template-columns: 0.94fr 1.06fr;
  gap: 28px;
}

.form-card__desc {
  margin: 10px 0 22px;
  color: var(--ink-soft);
  font-size: 0.88rem;
  line-height: 1.72;
}

/* 配置分组卡片 */
.form-card__group {
  margin-top: 14px;
  margin-bottom: 8px;
  padding: 0;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  background: #faf9f7;
  overflow: hidden;
}
.form-card__group-label {
  display: block;
  padding: 8px 14px;
  margin: 0;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9a9a9a;
  background: rgba(0, 0, 0, 0.02);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.form-card__group-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  min-height: 42px;
}
.form-card__group-row + .form-card__group-row {
  border-top: 1px solid rgba(0, 0, 0, 0.04);
}
.form-card__group-key {
  font-size: 0.82rem;
  font-weight: 500;
  color: #6b7280;
  white-space: nowrap;
  margin-right: 12px;
}
.form-card__select-wrap {
  position: relative;
  min-width: 0;
  flex: 0 1 220px;
  display: flex;
  align-items: center;
}
.form-card__select-wrap select {
  width: 100%;
  padding: 7px 30px 7px 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: #ffffff;
  font-size: 0.85rem;
  color: #1e293b;
  font-weight: 500;
  outline: none;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  transition:
    border-color 0.18s,
    box-shadow 0.18s;
}
.form-card__select-wrap select:hover {
  border-color: rgba(0, 0, 0, 0.15);
}
.form-card__select-wrap select:focus-visible {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(43, 108, 176, 0.08);
}
.form-card__select-chevron {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: #9ca3af;
}
.form-card__select-chevron path {
  stroke: #9ca3af;
}

.form-card label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
  color: #6b7280;
  font-size: 0.82rem;
  font-weight: 600;
}

.form-card input,
.form-card select,
.history-toolbar input,
.feedback-card textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #ffffff;
  font-size: 0.92rem;
  color: var(--ink);
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.form-card input::placeholder,
.history-toolbar input::placeholder,
.feedback-card textarea::placeholder {
  color: #9a9a9a;
}

.form-card input:focus-visible,
.form-card select:focus-visible,
.history-toolbar input:focus-visible,
.feedback-card textarea:focus-visible {
  border-color: var(--accent);
  box-shadow:
    0 0 0 4px rgba(43, 108, 176, 0.08),
    0 1px 2px rgba(0, 0, 0, 0.02);
}

/* 双栏表单行 */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-row label {
  margin-bottom: 0;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 4px 0 18px;
}

/* objectives-card 卡片 */
.objectives-card {
  margin: 12px 0 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #fafafa;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}

.objectives-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ink);
  background: #fff;
  border-bottom: 1px solid var(--border);
}

.objectives-card__header svg {
  color: var(--accent);
}

.objectives-card__body {
  padding: 14px 16px 4px;
}

.objectives-card__body label {
  margin-bottom: 12px;
}

.objectives-card__body label:last-child {
  margin-bottom: 8px;
}

/* 表单分节标题 */
.form-section-title {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ink);
  margin: 20px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* 文件上传区域 */
.file-upload-area {
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
  background: #fafafa;
  margin-bottom: 16px;
}

.file-upload-area:hover {
  border-color: var(--accent);
  background: #f5f6f8;
  box-shadow: 0 0 0 4px rgba(43, 108, 176, 0.04);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 2rem;
}

.upload-placeholder p {
  font-size: 0.9rem;
  color: #334155;
  margin: 0;
}

.upload-placeholder small {
  font-size: 0.75rem;
  color: #94a3b8;
}

.uploaded-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.file-icon {
  font-size: 1.5rem;
}

.file-name {
  flex: 1;
  font-size: 0.9rem;
  color: #334155;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border: none;
  border-radius: 50%;
  color: #64748b;
  font-size: 0.75rem;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.remove-file:hover {
  background: #e2e8f0;
  color: #334155;
}

/* textarea 样式 */
.form-card textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  font-size: 0.9rem;
  resize: vertical;
  min-height: 60px;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.form-card textarea:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(43, 108, 176, 0.08);
}

.chip-row__chip {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: #f1f1f2;
  color: var(--ink-soft);
  font-size: 0.76rem;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.chip-row__chip:hover {
  background: #e8eaed;
  border-color: var(--border-strong);
  color: var(--ink);
}
.chip-row__chip--active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.chip-row__chip--active:hover {
  opacity: 0.9;
}

.btn-primary,
.btn-secondary,
.record-card__delete,
.pager button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  cursor: pointer;
  transition:
    transform 0.2s var(--ease-out),
    box-shadow 0.2s,
    background 0.2s;
}

.btn-primary {
  padding: 13px 22px;
  border-radius: 10px;
  background: var(--accent);
  color: #fff;
  font-size: 0.92rem;
  font-weight: 700;
  border: none;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(43, 108, 176, 0.15);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  background: var(--accent-deep);
  box-shadow: 0 4px 10px rgba(43, 108, 176, 0.2);
}

.record-card__delete:hover {
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 16px;
  border-radius: 10px;
  background: var(--panel);
  border: 1px solid var(--border);
  color: var(--ink-soft);
  font-size: 0.82rem;
  font-weight: 600;
}

.preview-card {
  overflow: hidden;
  background: #ffffff;
}

.preview-card__chrome {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  background: #f8f8f6;
  color: var(--ink-muted);
  font-size: 0.74rem;
}

.preview-card__chrome span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d0d0d0;
}

.preview-card__chrome span:nth-child(1) {
  background: #d0d0d0;
}

.preview-card__chrome span:nth-child(2) {
  background: #d0d0d0;
}

.preview-card__chrome span:nth-child(3) {
  background: #d0d0d0;
}

.preview-card__chrome em {
  margin-left: auto;
  font-style: normal;
}

.preview-card__body {
  padding: 22px;
}

.preview-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.preview-card__head h3 {
  margin: 10px 0 6px;
  font-size: 1.26rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.preview-card__head p {
  margin: 0;
  color: var(--ink-muted);
  font-size: 0.84rem;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 10px;
  background: #f1f1f2;
  color: var(--ink-muted);
  font-size: 0.72rem;
  font-weight: 600;
  white-space: nowrap;
  align-self: flex-end;
  margin-top: 12px;
  border: 1px solid transparent;
}

.ai-badge i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.ai-badge--active i {
  background: #10b981;
  animation: pulse 1.4s infinite;
}

.preview-highlight,
.feedback-card__tips,
.support-item {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.84);
}

.preview-highlight {
  margin-bottom: 14px;
  padding: 16px;
  border: 1px solid rgba(43, 108, 176, 0.08);
}

.preview-highlight strong,
.feedback-card__tips span {
  display: inline-flex;
  margin-bottom: 6px;
  color: var(--accent-deep);
  font-size: 0.78rem;
  font-weight: 800;
}

.recommendation-list {
  position: relative;
  display: flex;
  flex-direction: column;
  padding-left: 22px;
}

/* 竖向连接线 */
.recommendation-list::before {
  content: "";
  position: absolute;
  left: 15px;
  top: 8px;
  bottom: 8px;
  width: 1.5px;
  background: #e2e8f0;
  border-radius: 2px;
}

.recommendation-item {
  position: relative;
  display: flex;
  gap: 14px;
  padding: 12px 14px;
  margin-left: 0;
  border-radius: 8px;
  background: transparent;
  transition:
    transform 0.2s ease,
    background 0.2s ease;
}

/* 时间轴圆点 */
.recommendation-item span,
.support-item span {
  position: relative;
  z-index: 1;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #ffffff;
  color: var(--ink-muted);
  border: 1.5px solid #e2e8f0;
  font-size: 0.78rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-left: -38px;
  transition:
    border-color 0.2s,
    background 0.2s,
    color 0.2s;
}

.recommendation-item:hover,
.recommendation-item--active {
  transform: translateY(-2px);
  background: #f8fafc;
}

.recommendation-item:hover span,
.recommendation-item--active span {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}

.support-card {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.support-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  transition: background 0.2s ease;
}
.support-item:hover {
  background: #f8fafc;
}

.upload-zone__drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 20px;
  border: 1.5px dashed rgba(43, 108, 176, 0.24);
  border-radius: 20px;
  background: rgba(43, 108, 176, 0.04);
  cursor: pointer;
  text-align: center;
}

.upload-zone__drop strong {
  font-size: 0.92rem;
}

.upload-zone__icon {
  width: 52px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: rgba(43, 108, 176, 0.08);
  color: var(--accent-deep);
  font-size: 1.6rem;
  font-weight: 300;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  font-size: 0.85rem;
}

.file-item button {
  border: 0;
  background: none;
  color: var(--ink-muted);
  cursor: pointer;
}

.viz-card--flow {
  background:
    radial-gradient(
      circle at top right,
      rgba(43, 108, 176, 0.08),
      transparent 28%
    ),
    #fff;
}

.mini-flow {
  width: 100%;
  height: 164px;
  display: block;
  margin-top: 16px;
}

/* ==================== 教学档案面板标题 ==================== */
.archive-section-header {
  margin-bottom: 20px;
}

.archive-section-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.archive-section-header p {
  font-size: 0.85rem;
  color: #94a3b8;
  margin: 0;
}

/* ==================== 教学档案多维筛选栏 ==================== */
.archive-filter-bar {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  border: 1px solid var(--border);
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.archive-filter-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.archive-filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 140px;
  flex: 1;
}

.archive-filter-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--ink-muted);
  letter-spacing: 0.3px;
}

.archive-filter-select {
  padding: 9px 14px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.84rem;
  color: #1e293b;
  background: white;
  outline: none;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.archive-filter-select:focus-visible {
  border-color: var(--accent-history);
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.08);
}

.archive-filter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

.archive-search-wrapper {
  flex: 1;
  position: relative;
}

.archive-search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.9rem;
  pointer-events: none;
}

.archive-search-input {
  width: 100%;
  padding: 10px 14px 10px 36px;
  border: 1.5px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #1e293b;
  background: white;
  outline: none;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.archive-search-input::placeholder {
  color: #9ca3af;
}

.archive-search-input:focus-visible {
  border-color: var(--accent-history);
  box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.08);
}

.archive-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 0.84rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
  white-space: nowrap;
}

.archive-btn--reset {
  background: #f1f5f9;
  color: #64748b;
}

.archive-btn--reset:hover:not(:disabled) {
  background: #e2e8f0;
  color: #475569;
}

.archive-btn--reset:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .archive-filter-row {
    flex-direction: column;
  }

  .archive-filter-group {
    min-width: 100%;
  }

  .archive-filter-bar {
    padding: 16px;
  }
}

/* ==================== 教学档案表格 ==================== */
.archive-table-info {
  font-size: 0.82rem;
  color: #64748b;
  margin-bottom: 12px;
  padding: 0 4px;
}
.archive-table-info strong {
  color: #1e293b;
  font-weight: 700;
}
.archive-table-info em {
  font-style: normal;
  color: #4c7dff;
  font-weight: 600;
}

.archive-table-wrapper {
  overflow-x: auto;
  border-radius: 14px;
  border: 1px solid #eef2f6;
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
  margin-bottom: 16px;
}

.archive-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.archive-table thead {
  background: #f8fafc;
  border-bottom: 2px solid #eef2f6;
}

.archive-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 0.78rem;
  color: #64748b;
  letter-spacing: 0.3px;
  white-space: nowrap;
  user-select: none;
}

.archive-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  vertical-align: middle;
}

.archive-table tbody tr {
  transition: background 0.15s ease;
}
.archive-table tbody tr:hover {
  background: #f8fafc;
}
.archive-table tbody tr:last-child td {
  border-bottom: none;
}

.archive-table .col-num {
  width: 48px;
  text-align: center;
  color: #94a3b8;
  font-size: 0.8rem;
}
.archive-table .col-name {
  min-width: 200px;
}
.archive-table .col-subject {
  width: 130px;
}
.archive-table .col-type {
  width: 100px;
}
.archive-table .col-status {
  width: 90px;
}
.archive-table .col-time {
  width: 100px;
  color: #94a3b8;
  font-size: 0.8rem;
}
.archive-table .col-actions {
  width: 120px;
  text-align: center;
}

.archive-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.archive-type-icon {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  flex-shrink: 0;
}
.archive-type-icon.ppt {
  color: #4c7dff;
  background: rgba(43, 108, 176, 0.1);
}
.archive-type-icon.doc {
  color: #23c3b2;
  background: rgba(35, 195, 178, 0.1);
}
.archive-type-icon.interactive {
  color: #8b5cf6;
  background: rgba(139, 92, 246, 0.1);
}
.archive-type-icon :deep(svg) {
  width: 18px;
  height: 18px;
}

.archive-name-text {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.85rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.archive-subject-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.76rem;
  font-weight: 500;
  background: rgba(43, 108, 176, 0.06);
  color: #4c7dff;
}

.archive-type-label {
  font-size: 0.78rem;
  color: #64748b;
}

/* 状态标签 - 参照参考图蓝/绿/橙配色 */
.archive-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 12px 3px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.archive-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.archive-status-badge[data-status="completed"] {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}
.archive-status-badge[data-status="completed"] .archive-status-dot {
  background: #22c55e;
}
.archive-status-badge[data-status="draft"] {
  background: rgba(245, 158, 11, 0.1);
  color: #d97706;
}
.archive-status-badge[data-status="draft"] .archive-status-dot {
  background: #f59e0b;
}
.archive-status-badge[data-status="iterating"] {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}
.archive-status-badge[data-status="iterating"] .archive-status-dot {
  background: #3b82f6;
}
.archive-status-badge[data-status="failed"] {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}
.archive-status-badge[data-status="failed"] .archive-status-dot {
  background: #ef4444;
}

/* 操作按钮 */
.archive-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}
.archive-action-btn {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}
.archive-action-btn:hover {
  background: rgba(43, 108, 176, 0.08);
  color: #4c7dff;
}
.archive-action-btn--delete:hover {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

/* 空状态 */
.archive-empty {
  text-align: center;
  padding: 40px 0;
  color: #94a3b8;
}
.archive-empty svg {
  color: #cbd5e1;
  margin-bottom: 10px;
}
.archive-empty p {
  font-size: 0.85rem;
  line-height: 1.6;
}

/* 分页 */
.archive-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.archive-page-info {
  font-size: 0.8rem;
  color: #94a3b8;
}
.archive-page-btns {
  display: flex;
  align-items: center;
  gap: 4px;
}
.archive-page-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 7px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  font-size: 0.8rem;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease;
  min-width: 34px;
  justify-content: center;
}
.archive-page-btn:hover:not(:disabled) {
  border-color: #4c7dff;
  color: #4c7dff;
  background: rgba(43, 108, 176, 0.04);
}
.archive-page-btn.active {
  border-color: #4c7dff;
  background: #4c7dff;
  color: white;
}
.archive-page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 900px) {
  .archive-table .col-time,
  .archive-table .col-subject {
    display: none;
  }
  .archive-table .col-type {
    width: auto;
  }
  .archive-pagination {
    flex-direction: column;
    align-items: flex-start;
  }
}

.feedback-card__head,
.feedback-card__actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.feedback-card__meta {
  margin-top: 8px;
}

.feedback-card__tips {
  margin: 18px 0 14px;
  padding: 14px 16px;
  border: 1px solid rgba(43, 108, 176, 0.08);
}

.feedback-card textarea {
  min-height: 112px;
  resize: vertical;
}

.feedback-card__actions {
  justify-content: flex-end;
  margin-top: 14px;
}

.empty-state {
  padding: 56px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  text-align: center;
  color: var(--ink-muted);
}

/* 意见反馈筛选器 */
.feedback-filter-bar {
  margin-bottom: 20px;
  padding: 20px;
  background: #fafafa;
  border-radius: 10px;
  border: 1px solid var(--border);
}
.feedback-filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.feedback-filter-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0;
}
.feedback-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.stat-badge {
  padding: 6px 12px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--accent-deep);
}
.stat-badge.type-ppt {
  background: rgba(43, 108, 176, 0.12);
  color: #4c7dff;
}
.stat-badge.type-doc {
  background: rgba(35, 195, 178, 0.12);
  color: #23c3b2;
}
.stat-badge.type-interactive {
  background: rgba(139, 92, 246, 0.12);
  color: #8b5cf6;
}
.feedback-filters {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filter-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ink-muted);
}
.filter-input,
.filter-select {
  padding: 10px 14px;
  border: 1px solid rgba(43, 108, 176, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.88rem;
  color: var(--ink);
  min-width: 140px;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.filter-input:focus-visible,
.filter-select:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(43, 108, 176, 0.1);
}
.filter-input.search-input {
  min-width: 200px;
}
.btn-reset {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid rgba(43, 108, 176, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.btn-reset:hover {
  background: rgba(43, 108, 176, 0.08);
  border-color: var(--accent);
  color: var(--accent-deep);
}
.reset-icon {
  width: 16px;
  height: 16px;
}

/* 反馈卡片优化 */
.feedback-card__info {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
}
.feedback-card__type-icon {
  width: 50px;
  height: 50px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  flex-shrink: 0;
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
}

.feedback-card__type-icon :deep(svg) {
  width: 24px;
  height: 24px;
}

.feedback-card__type-icon.ppt {
  background: linear-gradient(135deg, #4c7dff 0%, #1e4f82 100%);
  box-shadow: 0 4px 12px rgba(43, 108, 176, 0.3);
}

.feedback-card__type-icon.ppt :deep(svg) {
  color: white;
}

.feedback-card__type-icon.doc {
  background: linear-gradient(135deg, #23c3b2 0%, #14b8a6 100%);
  box-shadow: 0 4px 12px rgba(35, 195, 178, 0.3);
}

.feedback-card__type-icon.doc :deep(svg) {
  color: white;
}

.feedback-card__type-icon.interactive {
  background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.feedback-card__type-icon.interactive :deep(svg) {
  color: white;
}

.feedback-card:hover .feedback-card__type-icon {
  transform: scale(1.08);
}
.feedback-card__title-group {
  flex: 1;
  min-width: 0;
}
.feedback-card__title-group h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.feedback-card__meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 0;
}
.meta-tag {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 600;
}
.meta-tag.subject-tag {
  background: rgba(99, 102, 241, 0.1);
  color: var(--accent-deep);
}
.meta-tag.type-tag {
  background: rgba(43, 108, 176, 0.1);
  color: #4c7dff;
}
.meta-tag.time-tag {
  background: rgba(113, 129, 151, 0.1);
  color: var(--ink-muted);
}

/* 预览区 */
.feedback-card__preview {
  margin: 14px 0;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 14px;
  border: 1px solid rgba(43, 108, 176, 0.06);
}
.preview-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.preview-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--ink-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.preview-content {
  font-size: 0.85rem;
  color: var(--ink-soft);
  line-height: 1.6;
  margin: 0;
}

/* 提示标签 */
.tips-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.tips-icon {
  width: 18px;
  height: 18px;
  color: var(--accent);
}
.tips-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.tip-tag {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(43, 108, 176, 0.15);
  border-radius: 20px;
  font-size: 0.8rem;
  color: var(--ink-soft);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.tip-tag:hover {
  background: rgba(43, 108, 176, 0.1);
  border-color: var(--accent);
  color: var(--accent-deep);
  transform: translateY(-1px);
}

/* 输入框 */
.feedback-textarea {
  min-height: 120px;
  padding: 14px 16px;
  border: 1px solid rgba(43, 108, 176, 0.15);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.95);
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--ink);
  resize: vertical;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.feedback-textarea:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(43, 108, 176, 0.08);
}

/* 按钮 */
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: 1px solid rgba(43, 108, 176, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--ink-soft);
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.btn-secondary:hover {
  background: rgba(43, 108, 176, 0.08);
  border-color: var(--accent);
  color: var(--accent-deep);
}
.btn-icon {
  width: 16px;
  height: 16px;
}

/* 空状态 */
.feedback-empty {
  padding: 60px 40px;
}
.empty-illustration {
  width: 100px;
  height: 100px;
  margin: 0 auto 20px;
}
.empty-illustration svg {
  width: 100%;
  height: 100%;
}
.feedback-empty h4 {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--ink);
  margin: 0 0 8px;
}
.feedback-empty p {
  font-size: 0.88rem;
  color: var(--ink-muted);
  margin: 0 0 20px;
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 28px;
  transform: translateX(-50%);
  z-index: 200;
  padding: 12px 22px;
  border-radius: 999px;
  background: #16233c;
  color: #fff;
  font-size: 0.86rem;
  font-weight: 700;
  box-shadow: 0 16px 32px rgba(22, 35, 60, 0.24);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.28s,
    transform 0.28s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(12px);
}

.sidebar-overlay {
  display: none;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(43, 108, 176, 0.35);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(43, 108, 176, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(43, 108, 176, 0);
  }
}

@media (max-width: 1200px) {
  .workspace-header,
  .insight-grid,
  .generator-layout,
  .insight-grid--simple {
    grid-template-columns: 1fr;
  }

  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.3s var(--ease-out);
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 1;
    background: rgba(15, 23, 42, 0.28);
  }

  .main {
    padding: 12px;
  }

  .main__body {
    min-height: auto;
    padding: 18px 16px;
    border-radius: 22px;
  }

  .mobile-only {
    display: inline-flex;
  }

  .metric-grid,
  .line-chart__labels {
    grid-template-columns: 1fr;
  }

  .history-toolbar,
  .feedback-card__head,
  .feedback-card__actions,
  .preview-card__head {
    flex-direction: column;
    align-items: stretch;
  }

  .history-toolbar input {
    max-width: none;
  }

  .record-card,
  .queue-item {
    flex-wrap: wrap;
  }

  .task-ring-chart {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .ring-chart-wrapper {
    width: 110px;
    height: 110px;
  }

  .chart-type-legend {
    gap: 8px;
  }

  .ct-legend-item {
    font-size: 0.72rem;
    gap: 4px;
  }
}
/* ==================== 课堂互动样式 ==================== */
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
  transition:
    background 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    border-color 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1),
    transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
}

.activity-tab:hover {
  background: rgba(255, 255, 255, 0.92);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(217, 119, 6, 0.1);
}

.activity-tab--active {
  background: rgba(255, 255, 255, 0.95);
  border-color: var(--accent-classroom);
  box-shadow: 0 4px 16px rgba(217, 119, 6, 0.15);
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
  background: linear-gradient(90deg, var(--accent-classroom), #f59e0b);
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
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
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
  color: var(--accent-classroom);
  background: rgba(217, 119, 6, 0.1);
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
  transition:
    background 0.25s ease,
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    transform 0.25s ease;
  cursor: pointer;
}
.qa-option:hover:not(.qa-option--correct):not(.qa-option--wrong) {
  border-color: var(--accent-classroom);
  background: rgba(217, 119, 6, 0.04);
}
.qa-option--selected {
  border-color: var(--accent-classroom);
  background: rgba(217, 119, 6, 0.08);
}
.qa-option--correct {
  border-color: #059669;
  background: rgba(5, 150, 105, 0.08);
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
  transition:
    background 0.25s ease,
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    transform 0.25s ease;
}
.qa-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.qa-action-btn--primary {
  background: linear-gradient(135deg, var(--accent-classroom), #f59e0b);
  color: #fff;
  box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25);
}
.qa-action-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(217, 119, 6, 0.35);
}
.qa-action-btn--secondary {
  background: #fff;
  color: #475569;
  border: 1px solid var(--border);
}
.qa-action-btn--secondary:hover:not(:disabled) {
  background: #f8fafc;
  border-color: var(--border-strong);
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
  transition:
    background 0.25s ease,
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    transform 0.25s ease;
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
  transition:
    background 0.25s ease,
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    transform 0.25s ease;
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
  transition:
    background 0.25s ease,
    color 0.25s ease,
    border-color 0.25s ease,
    box-shadow 0.25s ease,
    transform 0.25s ease;
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
  font-size: 3.5rem;
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
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
  display: flex;
  justify-content: center;
  width: fit-content;
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
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.roster-item:hover {
  border-color: #667eea;
}
.roster-item__avatar {
  font-size: 1.1rem;
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
  font-size: 1rem;
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
  transition:
    background 0.3s ease,
    color 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    transform 0.3s ease;
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
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
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

/* ═══════════════ 预览弹窗 ═══════════ */
.preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(4px);
}
.preview-dialog {
  width: min(520px, 90vw);
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}
.preview-dialog__header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f1f5f9;
}
.preview-dialog__icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: #f1f5f9;
  color: var(--accent-deep);
  flex-shrink: 0;
}
.preview-dialog__icon svg {
  width: 22px;
  height: 22px;
}
.preview-dialog__header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
}
.preview-dialog__meta {
  font-size: 0.78rem;
  color: #94a3b8;
}
.preview-dialog__close {
  margin-left: auto;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.15s;
}
.preview-dialog__close:hover {
  background: #f1f5f9;
  color: #1e293b;
}
.preview-dialog__body {
  padding: 20px 24px;
}
.preview-dialog__status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.preview-dialog__time {
  font-size: 0.78rem;
  color: #94a3b8;
}
.preview-dialog__desc {
  margin: 0;
  font-size: 0.88rem;
  line-height: 1.7;
  color: #475569;
}
.preview-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 24px 20px;
}
.preview-btn {
  padding: 8px 20px;
  border-radius: 10px;
  font-size: 0.85rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s,
    box-shadow 0.15s;
}
.preview-btn--secondary {
  background: #f1f5f9;
  color: #475569;
}
.preview-btn--secondary:hover {
  background: #e2e8f0;
}
.preview-btn--primary {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #fff;
}
.preview-btn--primary:hover {
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
  transform: translateY(-1px);
}

/* 弹窗过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active .preview-dialog,
.modal-leave-active .preview-dialog {
  transition: transform 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from .preview-dialog {
  transform: scale(0.92) translateY(12px);
}
.modal-leave-to .preview-dialog {
  transform: scale(0.95);
}
/* ── prefers-reduced-motion ── */
@media (prefers-reduced-motion: reduce) {
  .panel {
    animation: none;
  }
  .metric-card,
  .record-card,
  .day-metric-card,
  .viz-card,
  .stack-card,
  .feature-list li,
  .data-point .point-circle,
  .bar-value-label {
    transition: none !important;
    animation: none !important;
  }
  .tooltip-fade-enter-active,
  .tooltip-fade-leave-active,
  .slide-fade-enter-active,
  .slide-fade-leave-active {
    transition: opacity 0.15s ease !important;
  }
  [class*="ring"] {
    animation: none !important;
  }
  [class*="radar"] {
    animation: none !important;
  }
  [class*="pulse"] {
    animation: none !important;
  }
  [class*="spin"] {
    animation: none !important;
  }
  [class*="float"] {
    animation: none !important;
  }
}

/* 表单字段辅助说明 */
.field-hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.7rem;
  color: #94a3b8;
  line-height: 1.4;
}
</style>
