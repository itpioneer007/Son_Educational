# 知启灵枢

面向中小学教师的 AI 备课与课件制作平台。教师用自然语言描述教学目标与知识点，
系统调用大模型生成 **课件 PPT、教案 Word、课堂练习、试卷** 四类可直接使用的教学材料，
并支持像对话一样提出修改意见、反复迭代后再导出。

> 参赛项目：中国大学生服务外包创新创业大赛 · 教育信息化创新赛道

## 功能一览

| 模块 | 说明 |
|---|---|
| AI 教师助手 | 与「知启灵枢」教学助手多轮对话，聊课标、教材、课堂与学生（通义千问） |
| 教学创作台 | 课件 / 教案 / 练习题 / 试卷 四类内容的生成与迭代（DeepSeek） |
| 课件模版 | 本地模版库 + 讯飞智文创意模版，按学科自动匹配 |
| 课程教程 | 六大学科教学视频与封面，支持在线播放与进度拖动 |
| 教学档案 | 生成历史、按学科/类型/时间筛选，一键重新生成 |
| 教学社区 | 教研话题发布、回复、点赞收藏 |

## 技术栈

- 前端：Vue 3 + Vite + Vue Router + Tailwind CSS + ECharts
- 后端：Python FastAPI（uvicorn，默认 `:8000`）
- 模型：内容生成走 DeepSeek；教师问答走阿里云百炼 DashScope 的 Qwen

## 本地开发

```sh
# 前端（默认 http://127.0.0.1:5173）
npm install
npm run dev

# 后端（默认 http://127.0.0.1:8000）
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

### 凭据配置

仓库内**不保存任何明文 Key**。读取优先级：环境变量 > `server/config.local.py` > 空值。
需要配置的项见 `server/config.py`（`DEEPSEEK_API_KEY`、`QWEN_API_KEY` 等），
讯飞智文另见 `server/spark_ppt/config/spark_config.py`。

### 构建

```sh
npm run build
```

## 说明

- `public/video/` 体积较大，按 `.gitignore` 规则不入库，需另行拷贝。
- 社区、数据分析等模块在比赛演示环境下使用本地种子数据 + 本地存储，无需后端即可展示。
