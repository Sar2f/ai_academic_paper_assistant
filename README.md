# AI 学术论文助手

一个功能强大的 Web 应用程序，支持多 API 学术论文搜索、智能查询翻译、零幻觉 AI 分析和跨论文综合研究。

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [配置指南](#配置指南)
- [使用说明](#使用说明)
- [API 支持](#api-支持)
- [项目结构](#项目结构)
- [开发与测试](#开发与测试)
- [未来计划](#未来计划)

---

## 项目简介

AI 学术论文助手是一个研究工具，旨在帮助研究人员、学生和专业人士：

1. **搜索真实学术论文** - 通过多个学术 API 检索高质量论文
2. **获取智能分析** - 使用 LLM 基于真实论文生成零幻觉答案
3. **获得引用支持** - 每个主张都链接到具体的论文
4. **进行跨论文研究** - 自动分析研究趋势、方法论对比和研究空白

**零幻觉承诺** - AI 的答案严格基于检索到的真实论文数据，绝不编造内容。

---

## 核心特性

### 多 API 论文搜索

- **4 个学术数据库集成**：Semantic Scholar、arXiv、PubMed、OpenAlex
- **智能合并与去重**：自动合并多个 API 的搜索结果，去除重复论文
- **灵活的速率限制**：为每个 API 配置独立的请求延迟

### AI 智能分析

- **查询翻译**：自动将中文查询翻译为英文，优化搜索效果
- **摘要生成**：基于多篇论文生成连贯的研究总结
- **跨论文分析**：
  - 研究趋势分析
  - 方法论对比
  - 研究空白识别
  - 未来方向建议
- **单篇论文深度分析**：关键词提取、研究方法、主要贡献、局限性

### 国际化体验

- **中英文双语界面**：完整的界面翻译，实时切换
- **语言适配**：自动检测系统语言，支持手动覆盖
- **多语言查询**：支持中英文输入，自动翻译优化搜索

### 配置管理

- **双配置持久化**：支持 `.env` 文件和 `config/config.json` 两种方式
- **动态配置加载**：运行时重新加载配置，无需重启
- **API 状态监控**：实时检查所有 API 的连接状态

### 可靠性保障

- **优雅降级**：主 API 失败时自动切换到备用 API
- **智能重试**：网络错误时指数退避重试
- **无密钥模式**：无 API 密钥时仍可进行论文搜索
- **连接检查**：一键检查所有 API 的连接状态

---

## 技术架构

```mermaid
flowchart TD
    A[用户查询] --> B[查询处理]
    B --> C[验证与翻译]
    C --> D[API 管理]
    D --> E[Semantic Scholar]
    D --> F[arXiv]
    D --> G[PubMed]
    D --> H[OpenAlex]
    E --> I[结果合并与去重]
    F --> I
    G --> I
    H --> I
    I --> J[LLM 处理]
    J --> K[答案生成]
    J --> L[跨论文分析]
    J --> M[引用追踪]
    K --> N[Streamlit 界面展示]
    L --> N
    M --> N
```

### 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| **协调器** | [`src/core/orchestrator.py`](src/core/orchestrator.py) | 端到端流程编排 |
| **API 管理器** | [`src/core/api_manager.py`](src/core/api_manager.py) | 统一管理 4 个学术 API |
| **查询处理器** | [`src/core/query_processor.py`](src/core/query_processor.py) | 查询验证与翻译 |
| **回退处理器** | [`src/core/fallback_handler.py`](src/core/fallback_handler.py) | API 失败时的降级策略 |
| **LLM 处理器** | [`src/llm/processor.py`](src/llm/processor.py) | AI 分析与答案生成 |
| **配置管理** | [`src/utils/config_manager.py`](src/utils/config_manager.py) | 配置文件管理 |
| **UI 组件** | [`src/interface/streamlit_components.py`](src/interface/streamlit_components.py) | Streamlit 界面 |

---

## 快速开始

### 前置要求

- Python 3.8+
- pip 包管理器
- 至少一个 LLM API 密钥（OpenAI 或 OpenAI 兼容 API，可选但推荐）

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd ai_academic_paper_assistant

# 2. 创建虚拟环境
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建环境配置文件
cp .env.example .env  # 或手动创建 .env 文件
```

然后编辑 `.env` 文件，填入你的 API 密钥。可参考下面的[配置指南](#配置指南)了解各项配置的含义。

### 运行应用

```bash
# 启动应用
streamlit run app.py

# 或使用自定义端口
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

访问 `http://localhost:8501` 即可使用。

---

## 配置指南

### 环境变量 (.env)

```env
# LLM API 配置（至少配置一个）
OPENAI_API_KEY=your_openai_api_key_here

# OpenAI 兼容接口地址（留空使用官方 api.openai.com）
API_BASE_URL=

# 学术 API 配置（均为可选，免费额度通常够用）
SEMANTIC_SCHOLAR_API_KEY=optional_semantic_scholar_key
PUBMED_API_KEY=optional_pubmed_key
OPENALEX_API_KEY=optional_openalex_key

# 应用设置
LLM_MODEL=gpt-4o-mini
MAX_PAPERS_TO_RETRIEVE=10
MAX_TOKENS=2000
TEMPERATURE=0.1
RATE_LIMIT_DELAY=0.1
```

### JSON 配置 (config/config.json)

```json
{
    "openai_api_key": "",
    "llm_model": "gpt-4o-mini",
    "max_papers_to_retrieve": 10,
    "temperature": 0.1,
    "api_base_url": ""
}
```

### 配置优先级

1. `.env` 文件（最高优先级）
2. `config/config.json` 文件
3. 默认配置值

---

## 使用说明

### 基本搜索流程

1. **输入研究问题** - 在搜索框中输入你的问题（支持中英文）
2. **调整参数** - 可选：修改要检索的论文数量
3. **点击搜索** - 系统会：
   - 验证和翻译查询
   - 在 4 个学术 API 中搜索
   - 合并和去重结果
   - 生成 AI 分析
4. **查看结果** - 浏览答案、引用和跨论文分析

### 示例查询

| 研究主题 | 查询示例 |
|----------|----------|
| 量子计算 | "量子计算的最新进展有哪些？" |
| 深度学习 | "深度学习如何改进自然语言处理？" |
| 环境科学 | "加密货币挖矿对环境有什么影响？" |
| 基因编辑 | "CRISPR基因编辑技术的最新发展" |
| AI 研究 | "大语言模型的对齐问题研究" |

### 高级功能

- **切换语言** - 在侧边栏选择中英文界面
- **检查连接** - 点击"检查连接"按钮验证 API 状态
- **管理配置** - 在侧边栏创建、保存和重新加载配置
- **查看分析** - 展开跨论文分析部分获取深度见解

---

## API 支持

### 学术数据库

| API | 特点 | 速率限制 |
|-----|------|----------|
| **Semantic Scholar** | 覆盖广泛，引用数据丰富 | 免费版：100 请求/5 分钟 |
| **arXiv** | 预印本，物理/计算机科学为主 | 较严格，需要更长延迟 |
| **PubMed** | 生物医学文献 | 需要 API 密钥，严格限制 |
| **OpenAlex** | 开放获取，多学科覆盖 | 免费友好 |

---

## 项目结构

```text
ai_academic_paper_assistant/
├── app.py                          # 主应用入口
├── requirements.txt                # Python 依赖
├── README.md                       # 本文档
├── .gitignore                      # Git 忽略规则
│
├── src/                            # 源代码目录
│   ├── api/                        # API 客户端
│   │   ├── base_api.py             # 基础 API 类
│   │   ├── semantic_scholar.py     # Semantic Scholar API
│   │   ├── arxiv_api.py            # arXiv API
│   │   ├── pubmed_api.py           # PubMed API
│   │   └── openalex_api.py         # OpenAlex API
│   │
│   ├── core/                       # 核心业务逻辑
│   │   ├── orchestrator.py         # 主协调器
│   │   ├── api_manager.py          # API 管理器
│   │   ├── query_processor.py      # 查询处理器
│   │   └── fallback_handler.py     # 回退处理器
│   │
│   ├── llm/                        # LLM 集成
│   │   └── processor.py            # LLM 处理器
│   │
│   ├── models/                     # 数据模型
│   │   └── paper.py                # 论文数据结构
│   │
│   ├── utils/                      # 工具类
│   │   ├── config.py               # 配置类
│   │   ├── config_manager.py       # 配置管理器
│   │   └── validation.py           # 验证工具
│   │
│   ├── interface/                  # UI 组件
│   │   └── streamlit_components.py # Streamlit 组件
│   │
│   └── i18n/                       # 国际化
│       └── translations.py         # 翻译文件
│
└── tests/                          # 测试目录
    ├── api/                        # API 测试
    ├── core/                       # 核心逻辑测试
    ├── llm/                        # LLM 测试
    └── integration/                # 集成测试
```

---

## 开发与测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/core/test_orchestrator.py

# 运行带覆盖率的测试（需要安装 pytest-cov）
pytest --cov=src
```

### 代码质量

项目遵循标准 Python 实践，使用：
- 类型注解 (Type Hints)
- 模块化架构
- 结构化日志记录

---

## 安全与隐私

- **API 密钥保护** - 密钥存储在 `.env` 文件，已加入 `.gitignore`
- **无数据持久化** - 用户查询和结果不存储在服务器
- **安全 API 调用** - 使用 HTTPS 进行所有 API 通信
- **速率限制** - 内置延迟确保遵守 API 使用条款

---

## 未来计划

- [ ] **高级筛选** - 按年份、引用次数、作者等筛选论文
- [ ] **结果导出** - 支持导出为 PDF、CSV、BibTeX 格式
- [ ] **搜索历史** - 用户账户和历史查询管理
- [ ] **更多语言** - 扩展支持日语、德语、法语等
- [ ] **批量查询** - 同时处理多个研究问题
- [ ] **论文聚类** - 自动对搜索结果进行主题聚类
- [ ] **趋势可视化** - 研究趋势的图表展示

---

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 开启 Pull Request

---

## 许可证

本项目采用 MIT 许可证。

---

## 致谢

- **Semantic Scholar** - 学术论文搜索 API
- **arXiv** - 预印本平台
- **PubMed** - 生物医学文献数据库
- **OpenAlex** - 开放学术数据库
- **OpenAI** - LLM API 提供商
- **Streamlit** - 优秀的 Web 应用框架

---

*使用 Streamlit、多学术 API 和 LLM 构建，用心打造*
