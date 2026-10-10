import { reactive } from 'vue'
import { storageKey } from '../config/storage.js'

const STORAGE_KEY = storageKey('community-data')

const VISUAL_PRESETS = {
  教学讨论: {
    badge: '教研现场',
    kicker: '课堂问题正在被拆解',
    subtitle: '把真实课堂场景、难点与限制条件说清楚，更容易收到可执行建议。',
    palette: ['#ecf5ff', '#d4e7ff', '#8eb8f4'],
    scene: 'discussion',
    chips: ['真实问题', '同行速答'],
    shots: [
      { label: '场景', value: '课堂导入', tone: 'blue' },
      { label: '目标', value: '问题拆解', tone: 'cyan' },
      { label: '产出', value: '方案共创', tone: 'slate' },
    ],
  },
  课件结构: {
    badge: '真实案例',
    kicker: '课件骨架先搭起来',
    subtitle: '从导入、讲授、练习到板书，把课堂节奏和知识梯度一并排清楚。',
    palette: ['#f3f7fd', '#dfeafb', '#aec6e6'],
    scene: 'spotlight',
    chips: ['PPT 结构', '节奏设计'],
    shots: [
      { label: '导入', value: '冲突感', tone: 'blue' },
      { label: '讲授', value: '问题链', tone: 'cyan' },
      { label: '作业', value: '迁移练', tone: 'slate' },
    ],
  },
  互动设计: {
    badge: '课堂互动',
    kicker: '把环节做得可参与',
    subtitle: '适合投票、演示动画、小组协作与追问链设计的互动型内容结构。',
    palette: ['#f5f8ff', '#dfe9fb', '#97d5f2'],
    scene: 'interface',
    chips: ['互动脚本', '演示动画'],
    shots: [
      { label: '提问', value: '先猜想', tone: 'blue' },
      { label: '演示', value: '可交互', tone: 'cyan' },
      { label: '反馈', value: '即点评', tone: 'green' },
    ],
  },
  多模态参考: {
    badge: '资料融合',
    kicker: '图片和文档一起用',
    subtitle: '适合 PDF、图片、表格和校本模板混合输入后的统一编排与风格对齐。',
    palette: ['#f7f9fd', '#e3ebf8', '#b7cbea'],
    scene: 'document',
    chips: ['PDF', '图片', '模板'],
    shots: [
      { label: '输入', value: 'PDF / 图片', tone: 'blue' },
      { label: '抽取', value: '知识点', tone: 'cyan' },
      { label: '输出', value: '统一风格', tone: 'slate' },
    ],
  },
  'AI 提示词': {
    badge: '提示词库',
    kicker: '把 AI 调教得更懂课堂',
    subtitle: '适合沉淀追问模板、角色设定、输出格式约束和评价标准。',
    palette: ['#f5f8ff', '#e7edff', '#b9c7ff'],
    scene: 'prompt',
    chips: ['Prompt', '输出约束'],
    shots: [
      { label: '角色', value: '教研员', tone: 'blue' },
      { label: '格式', value: '表格化', tone: 'cyan' },
      { label: '标准', value: '可复制', tone: 'slate' },
    ],
  },
}

function createVisual(tag, title, content = '') {
  const preset = VISUAL_PRESETS[tag] || VISUAL_PRESETS.教学讨论
  return {
    badge: preset.badge,
    kicker: preset.kicker,
    headline: title,
    subtitle: preset.subtitle || content.slice(0, 36),
    palette: preset.palette,
    scene: preset.scene,
    chips: preset.chips,
    shots: preset.shots,
  }
}

function normalizePost(post) {
  return {
    ...post,
    comments: Array.isArray(post.comments) ? post.comments : [],
    media: post.media || createVisual(post.tag, post.title, post.content),
  }
}

const SEED_POSTS = [
  {
    id: 'p1',
    tag: '课件结构',
    title: '如何设计「先破后立」的历史课导入？',
    content:
      '我在讲《鸦片战争》时想让学生先有认知冲突，再引入新课。大家有没有比较好的导入案例或 AI 提示词模板？',
    author: '王老师',
    createdAt: Date.now() - 86400000 * 2,
    likes: 42,
    media: createVisual(
      '课件结构',
      '历史导入案例拆解',
      '把“认知冲突”转成课堂导入画面与问题链。'
    ),
    comments: [
      {
        id: 'c1',
        author: '李老师',
        content: '可以试试用「假如你是当时的一名商人」角色扮演开场，学生参与度会高很多。',
        createdAt: Date.now() - 86400000,
        likes: 8,
      },
      {
        id: 'c2',
        author: '陈老师',
        content: '我用 AI 生成了一个对比表格，展示战前中英贸易数据，效果还不错。',
        createdAt: Date.now() - 43200000,
        likes: 5,
      },
    ],
  },
  {
    id: 'p2',
    tag: '互动设计',
    title: '物理实验课怎样用 AI 生成可交互演示动画？',
    content:
      '牛顿第二定律实验，想加入可拖拽的交互组件。知启灵枢 能直接生成吗？还是需要额外工具配合？',
    author: '李老师',
    createdAt: Date.now() - 86400000 * 4,
    likes: 36,
    media: createVisual(
      '互动设计',
      '物理实验互动看板',
      '把拖拽、演示和追问链拆成一张可执行的互动脚本。'
    ),
    comments: [
      {
        id: 'c3',
        author: '张老师',
        content: '建议先在对话里把实验步骤和交互逻辑描述清楚，再让智能体生成动画创意脚本。',
        createdAt: Date.now() - 86400000 * 3,
        likes: 12,
      },
    ],
  },
  {
    id: 'p3',
    tag: '多模态参考',
    title: '上传 PDF 教案后，怎样让排版风格保持一致？',
    content:
      '上传了学校统一模板的 PDF 教案，但生成的 PPT 字体和配色总是不一致，有什么好的参考描述方式？',
    author: '张老师',
    createdAt: Date.now() - 86400000 * 6,
    likes: 58,
    media: createVisual(
      '多模态参考',
      '统一排版风格预览',
      '同一份教案素材在 PPT 与 Word 中保持一致的版式语言。'
    ),
    comments: [],
  },
  {
    id: 'p4',
    tag: '教学讨论',
    title: '六年级分数应用题，怎么帮学生建立单位「1」的直观感受？',
    content:
      '每次讲到分数乘除法应用题，学生一看到单位「1」就懵。有没有什么生活化情景或教具能帮他们把抽象概念落地？',
    author: '赵老师',
    createdAt: Date.now() - 86400000 * 3,
    likes: 35,
    media: createVisual('教学讨论', '分数单位「1」课堂导入', '用分披萨、分蛋糕的场景帮学生建立单位"1"的直观感受。'),
    comments: [
      {
        id: 'c4',
        author: '刘老师',
        content: '我用「分披萨」的动画开场，把整个披萨看作单位"1"，切几块就是几分之几，学生一下子就懂了。',
        createdAt: Date.now() - 86400000 * 2,
        likes: 14,
      },
      {
        id: 'c5',
        author: '周老师',
        content: '推荐用数轴+线段图双线并进，左边画实物右边画线段，慢慢过渡到纯线段。',
        createdAt: Date.now() - 86400000,
        likes: 9,
      },
    ],
  },
  {
    id: 'p5',
    tag: 'AI 提示词',
    title: '想让 AI 帮忙批改作文，怎么写提示词才能保留学生的个性表达？',
    content:
      '试了几个通用提示词，批改结果太模板化了，把学生最有灵气的句子改得千篇一律。求有经验的老师分享提示词思路。',
    author: '刘老师',
    createdAt: Date.now() - 86400000 * 5,
    likes: 67,
    media: createVisual(
      'AI 提示词',
      '作文批改提示词调优',
      '用角色设定+评价维度约束，让 AI 既给结构性反馈又不抹杀童真。'
    ),
    comments: [
      {
        id: 'c6',
        author: '吴老师',
        content: '我用的提示词开场是「你是一位温和的语文特级教师，点评时先说3个亮点再说2个建议」，效果很好。',
        createdAt: Date.now() - 86400000 * 3,
        likes: 22,
      },
      {
        id: 'c7',
        author: '郑老师',
        content: '建议分两轮：第一轮只找亮点不做修改，第二轮才提结构建议，避免 AI 一次性改太多。',
        createdAt: Date.now() - 86400000 * 2,
        likes: 17,
      },
      {
        id: 'c8',
        author: '孙老师',
        content: '在提示词里加一句「保留学生原句中的语气和修辞，仅修正语病」可以大幅减少模板化问题。',
        createdAt: Date.now() - 86400000,
        likes: 25,
      },
    ],
  },
  {
    id: 'p6',
    tag: '互动设计',
    title: '英语课堂小组活动总是冷场，有什么互动设计能让全员开口？',
    content:
      '我带初一，小组讨论经常变成几个好学生包场，后排学生全程沉默。想设计一种必须全员参与的互动机制。',
    author: '周老师',
    createdAt: Date.now() - 86400000 * 7,
    likes: 23,
    media: createVisual(
      '互动设计',
      '英语全员开口互动方案',
      '用角色轮换+限定表达框架确保每个学生都有话可说。'
    ),
    comments: [
      {
        id: 'c9',
        author: '孙老师',
        content: '试试「发言卡」机制，每人每节课必须用完3张发言卡，用完才能获得小组积分。',
        createdAt: Date.now() - 86400000 * 5,
        likes: 11,
      },
      {
        id: 'c10',
        author: '黄老师',
        content: '我把对话模板拆成A/B角色卡，学生必须两两配对完成信息差任务，不开口就填不了表。',
        createdAt: Date.now() - 86400000 * 3,
        likes: 8,
      },
    ],
  },
  {
    id: 'p7',
    tag: '课件结构',
    title: '《细胞分裂》一节课内容太多，课件结构怎么安排才不赶进度？',
    content:
      '有丝分裂和减数分裂放在一起讲，学生容易混淆。课件里想加动画又怕时间不够，求合理的结构建议。',
    author: '吴老师',
    createdAt: Date.now() - 86400000 * 9,
    likes: 52,
    media: createVisual(
      '课件结构',
      '细胞分裂课件节奏规划',
      '把有丝分裂与减数分裂拆成两课时，中间穿插对比活动巩固。'
    ),
    comments: [
      {
        id: 'c11',
        author: '赵老师',
        content: '强烈建议分两课时，第一课时只讲有丝分裂，用动画演示染色体行为，第二课时再用对比表引入减数分裂。',
        createdAt: Date.now() - 86400000 * 7,
        likes: 20,
      },
      {
        id: 'c12',
        author: '郑老师',
        content: '我做了个「分裂阶段排序卡」的小组活动，每组一套卡片，边排边讲，比纯课件效果好很多。',
        createdAt: Date.now() - 86400000 * 5,
        likes: 15,
      },
    ],
  },
  {
    id: 'p8',
    tag: '教学讨论',
    title: '初二学生理解浮力很吃力，有没有好的生活化类比教学案例？',
    content:
      '阿基米德原理讲了三遍，做题还是乱套公式。想找个生活中随手可做的类比实验，让学生真正「看到」浮力。',
    author: '郑老师',
    createdAt: Date.now() - 86400000 * 11,
    likes: 18,
    media: createVisual(
      '教学讨论',
      '浮力生活化实验案例',
      '用矿泉水瓶+乒乓球的浮沉实验，把抽象原理变成看得见的体验。'
    ),
    comments: [
      {
        id: 'c13',
        author: '孙老师',
        content: '用一个矿泉水瓶装水、一个乒乓球，演示「按压-上浮」的过程，学生立马明白浮力和排开水体积的关系。',
        createdAt: Date.now() - 86400000 * 9,
        likes: 13,
      },
    ],
  },
  {
    id: 'p9',
    tag: '多模态参考',
    title: '手头有一批老照片和文献 PDF，怎样融合进《抗日战争》课件？',
    content:
      '档案馆扫描了一批抗战老照片和原始报纸PDF，想做到课件里当素材，但图片清晰度不一，排版也很难统一。',
    author: '孙老师',
    createdAt: Date.now() - 86400000 * 13,
    likes: 73,
    media: createVisual(
      '多模态参考',
      '抗战历史素材融合排版',
      '把不同分辨率的旧照片和文献 PDF 统一风格后融入课件时间轴。'
    ),
    comments: [
      {
        id: 'c14',
        author: '周老师',
        content: '可以先把图片统一调成黑白或复古色调，加上统一的边框和标注格式，视觉上就协调了。',
        createdAt: Date.now() - 86400000 * 11,
        likes: 18,
      },
      {
        id: 'c15',
        author: '吴老师',
        content: '推荐用时间轴结构来组织，每张照片配上简短的历史背景说明，PDF节选做成可点击展开的注释。',
        createdAt: Date.now() - 86400000 * 8,
        likes: 24,
      },
      {
        id: 'c16',
        author: '黄老师',
        content: '我一般把PDF关键段落截图后加半透明底色作为背景，上面叠加文字，既有文献感又不杂乱。',
        createdAt: Date.now() - 86400000 * 5,
        likes: 16,
      },
    ],
  },
  {
    id: 'p10',
    tag: 'AI 提示词',
    title: '化学方程式配平学生总出错，能用 AI 设计分层练习吗？',
    content:
      '从简单配平到氧化还原，学生水平参差不齐。想用 AI 生成差异化练习题，每人一套不重复。有没有提示词参考？',
    author: '黄老师',
    createdAt: Date.now() - 86400000 * 15,
    likes: 44,
    media: createVisual(
      'AI 提示词',
      '化学配平分层次练习',
      '用提示词约束难度梯度与题型变量，为每位学生生成个性化配平练习。'
    ),
    comments: [
      {
        id: 'c17',
        author: '赵老师',
        content: '我用这个提示词框架：难度分三级、每级5题、附带步骤提示。生成后手动调一两道偏题就行。',
        createdAt: Date.now() - 86400000 * 12,
        likes: 19,
      },
      {
        id: 'c18',
        author: '郑老师',
        content: '建议在提示词里指定「用最小公倍数法配平的题」和「用氧化数法配平的题」分开出，方便分类讲解。',
        createdAt: Date.now() - 86400000 * 9,
        likes: 11,
      },
    ],
  },
]

function loadData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        posts: (parsed.posts || []).map(normalizePost),
        likedIds: parsed.likedIds || [],
        favoriteIds: parsed.favoriteIds || [],
        likedCommentIds: parsed.likedCommentIds || [],
      }
    }
  } catch {
    /* ignore */
  }
  return {
    posts: structuredClone(SEED_POSTS).map(normalizePost),
    likedIds: [],
    favoriteIds: [],
    likedCommentIds: [],
  }
}

const state = reactive(loadData())

function persist() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      posts: state.posts,
      likedIds: state.likedIds,
      favoriteIds: state.favoriteIds,
      likedCommentIds: state.likedCommentIds,
    })
  )
}

function uid(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
}

export function useCommunity() {
  function isLiked(postId) {
    return state.likedIds.includes(postId)
  }

  function isFavorite(postId) {
    return state.favoriteIds.includes(postId)
  }

  function isCommentLiked(commentId) {
    return state.likedCommentIds.includes(commentId)
  }

  function toggleLike(postId) {
    const post = state.posts.find((p) => p.id === postId)
    if (!post) return false

    const idx = state.likedIds.indexOf(postId)
    if (idx >= 0) {
      state.likedIds.splice(idx, 1)
      post.likes = Math.max(0, post.likes - 1)
      persist()
      return false
    }

    state.likedIds.push(postId)
    post.likes += 1
    persist()
    return true
  }

  function toggleFavorite(postId) {
    const idx = state.favoriteIds.indexOf(postId)
    if (idx >= 0) {
      state.favoriteIds.splice(idx, 1)
      persist()
      return false
    }
    state.favoriteIds.push(postId)
    persist()
    return true
  }

  function toggleCommentLike(commentId) {
    let comment = null
    for (const post of state.posts) {
      comment = post.comments?.find((c) => c.id === commentId)
      if (comment) break
    }
    if (!comment) return false

    const idx = state.likedCommentIds.indexOf(commentId)
    if (idx >= 0) {
      state.likedCommentIds.splice(idx, 1)
      comment.likes = Math.max(0, comment.likes - 1)
      persist()
      return false
    }

    state.likedCommentIds.push(commentId)
    comment.likes += 1
    persist()
    return true
  }

  function addComment(postId, content, author = '匿名老师') {
    const post = state.posts.find((p) => p.id === postId)
    if (!post || !content.trim()) return null

    const comment = {
      id: uid('c'),
      author,
      content: content.trim(),
      createdAt: Date.now(),
      likes: 0,
    }
    post.comments.push(comment)
    persist()
    return comment
  }

  function addPost({ tag, title, content, author = '匿名老师' }) {
    if (!title.trim() || !content.trim()) return null

    const post = {
      id: uid('p'),
      tag: tag || '教学讨论',
      title: title.trim(),
      content: content.trim(),
      author,
      createdAt: Date.now(),
      likes: 0,
      comments: [],
      media: createVisual(tag || '教学讨论', title.trim(), content.trim()),
    }
    state.posts.unshift(post)
    persist()
    return post
  }

  function getPosts(filter = 'all') {
    if (filter === 'favorite') {
      return [...state.posts]
        .filter((p) => state.favoriteIds.includes(p.id))
        .sort((a, b) => b.createdAt - a.createdAt)
    }
    if (filter === 'hot') {
      return [...state.posts].sort((a, b) => b.likes - a.likes || b.createdAt - a.createdAt)
    }
    return [...state.posts].sort((a, b) => b.createdAt - a.createdAt)
  }

  return {
    state,
    isLiked,
    isFavorite,
    isCommentLiked,
    toggleLike,
    toggleFavorite,
    toggleCommentLike,
    addComment,
    addPost,
    getPosts,
  }
}

export function formatTime(ts) {
  const diff = Date.now() - ts
  const min = 60000
  const hour = 3600000
  const day = 86400000

  if (diff < min) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / min)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < day * 30) return `${Math.floor(diff / day)} 天前`
  return new Date(ts).toLocaleDateString('zh-CN')
}
