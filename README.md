# GraphRAG 电商智能问答系统

基于 Neo4j 图数据库和 LLM (通义千问) 构建的电商领域智能问答系统。支持 Text-to-Cypher 自动查询生成、向量实体对齐和实时执行流程监控。

## ✨ 核心功能

- **智能问答 (GraphRAG)**: 将自然语言问题转换为 Cypher 查询语句，直接从知识图谱中检索答案。
- **实体对齐 (Entity Alignment)**: 结合向量检索 (Vector Search) 和关键词匹配，自动纠正用户输入中的模糊实体名称（如 "华威" -> "华为"）。
- **实时监控 (Live Monitor)**: 提供可视化的 Web 监控面板，实时展示 LLM 思考过程、Cypher 生成、参数构建和查询执行的完整流程。
- **混合检索**: 结合全文索引和向量索引，提高检索准确率。

## 🛠 技术栈

- **后端**: Python, FastAPI, LangChain
- **数据库**: Neo4j (图存储 + 向量索引)
- **大模型**: 阿里云通义千问 (qwen-turbo)
- **前端**: Vanilla JS + Mermaid.js (监控面板)

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+ 和 Neo4j 数据库。

```bash
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

在 `src/conf` 目录下配置你的环境变量（如 API Key 和数据库连接信息）。

### 3. 启动服务

```bash
# 启动 FastAPI 服务 (默认端口 8086)
python3 -m src.web.controller
```

## 🖥 使用说明

### 1. 智能问答

服务启动后，访问聊天页面：
👉 [http://localhost:8086/static/index.html](http://localhost:8086/static/index.html)

### 2. 实时监控面板

在另一个标签页打开监控面板，观察系统运行流程：
👉 [http://localhost:8086/static/monitor.html](http://localhost:8086/static/monitor.html)

**监控指标包括：**
- **Generate Cypher**: LLM 生成的原始查询语句
- **Entity Align**: 实体对齐过程和结果
- **Build Params**: 最终构建的查询参数
- **Execute Cypher**: 数据库执行结果
- **Generate Answer**: 最终生成的自然语言回答

## 📂 项目结构

```
.
├── src
│   ├── conf        # 配置文件
│   ├── datasync    # 数据同步脚本
│   ├── ner         # 实体识别模型训练
│   └── web         # Web 服务核心代码
│       ├── controller.py  # FastAPI 控制器
│       ├── service.py     # 核心业务逻辑 (GraphRAG)
│       ├── monitor.py     # WebSocket 监控服务
│       └── static         # 前端静态资源
├── main.py         # 入口文件
└── requirements.txt
```

## 📝 开发日志

- **Text-to-Cypher**: 优化了 Prompt 模板，增加了 Schema 注入，解决了参数化查询缺少 `$` 符号的问题。
- **模型升级**: 切换至 `qwen-turbo` 模型，平衡了响应速度和指令遵循能力。
- **可视化监控**: 引入 WebSocket 和 Mermaid.js，实现了全链路的可视化追踪。
