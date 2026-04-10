# AI 学术论文助手 📚

一个允许用户输入搜索查询，搜索与查询相关的*真实、可追溯*的学术论文，使用LLM整理和总结发现，并提供**零幻觉**的连贯答案的Web应用程序。

## 🎯 目标

构建一个Web应用程序，该程序：
1. 接受用户搜索查询
2. 使用Semantic Scholar API搜索真实的学术论文
3. 使用LLM**严格**基于检索到的论文生成答案
4. 为每个主张提供引用
5. 在干净、用户友好的界面中呈现结果

## 🚀 核心约束（关键）

**零幻觉** - AI的最终答案必须*严格*基于检索到的论文数据。每个主张必须引用真实的论文。LLM不允许编造论文标题、作者或内容。

## ✨ 主要特性

- **简洁的Web界面**：基于Streamlit的GUI，具有直观的搜索和结果展示
- **真实论文搜索**：与Semantic Scholar API集成，获取真实的学术论文
- **AI驱动的总结**：集成LLM（OpenAI/Anthropic）以生成连贯的答案
- **引用追踪**：答案中的每个主张都链接到具体的论文
- **论文详情**：查看摘要、作者、引用次数以及原始论文链接
- **可配置设置**：调整搜索限制、LLM模型和温度
- **双配置持久化**：支持`.env`文件和`config.json`两种配置方式
- **中英文国际化**：完整的中英文界面切换，支持双语用户
- **智能联网搜索**：自动重试、连接状态检查、优化的错误处理
- **模拟数据模式**：测试模式下可使用模拟数据，无需API密钥

## 🏗️ 架构

```mermaid
用户查询 → Streamlit UI → AcademicPaperOrchestrator → Semantic Scholar API → LLM Processor → 结果展示
```

### 组件：
1. **前端**：Streamlit 应用程序 (`app.py`)
2. **协调器**：协调搜索和处理 (`src/core/orchestrator.py`)
3. **论文搜索**：Semantic Scholar API 客户端 (`src/api/semantic_scholar.py`)
4. **LLM 集成**：带有抗幻觉提示的 OpenAI/Anthropic 处理器 (`src/llm/processor.py`)
5. **数据模型**：论文和作者数据结构 (`src/models/paper.py`)
6. **配置**：基于环境的设置 (`src/utils/config.py`)

## 🛠️ 安装

### 先决条件
- Python 3.8+
- pip 包管理器

### 步骤1：克隆和设置
```bash
# 克隆仓库
git clone <repository-url>
cd ai_academic_paper_assistant

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤2：配置环境
```bash
# 复制示例环境文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
# 你需要至少一个 LLM API 密钥以获得完整功能
nano .env  # 或使用你喜欢的编辑器
```

### 依赖说明
项目依赖已简化，仅包含核心必要包：
- **Streamlit**：Web 界面框架
- **OpenAI / Anthropic**：LLM API 客户端
- **Requests**：HTTP 请求库
- **Python-dotenv**：环境变量管理

其他依赖（如 Pandas、NumPy）由 Streamlit 自动引入。开发工具（Pytest、Black、Flake8）已包含。

### 步骤3：环境变量
配置你的 `.env` 文件：
```env
# OpenAI API 密钥（可选但推荐）
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API 密钥（可选替代）
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Semantic Scholar API（基础使用无需密钥）
SEMANTIC_SCHOLAR_API_KEY=optional_semantic_scholar_api_key

# 应用程序设置
MAX_PAPERS_TO_RETRIEVE=10
LLM_MODEL=gpt-4o  # 或 claude-3-5-sonnet, gpt-3.5-turbo 等
MAX_TOKENS=2000
TEMPERATURE=0.1  # 低温度以获得更多事实性响应
RATE_LIMIT_DELAY=0.1
USE_MOCK_DATA=false  # 设置为true使用模拟数据（用于测试）
STREAMLIT_PORT=8501
STREAMLIT_HOST=0.0.0.0
```

### 双配置持久化选项

项目支持两种配置持久化方式，可在侧边栏中切换：

#### 选项A：环境变量文件（.env） - 默认
- 使用 `.env` 文件存储配置
- 符合十二要素应用原则
- 易于与现有CI/CD工具集成
- 文件示例：`.env.example`

#### 选项B：JSON配置文件（config.json）
- 使用 `config/config.json` 文件存储配置
- 结构化格式，易于阅读和编辑
- 支持注释和复杂配置结构
- 文件示例：`config/config.example.json`

**创建JSON配置文件：**
```bash
# 从模板创建配置文件
cp config/config.example.json config/config.json

# 编辑配置文件
nano config/config.json
```

**配置优先级：** 应用程序自动检测可用的配置文件，优先级为：
1. `.env` 文件（如果存在）
2. `config/config.json` 文件（如果存在）
3. 默认配置值

### 🌐 国际化支持

应用程序提供完整的中英文双语支持：

#### 语言切换
- **侧边栏切换**：在应用侧边栏的语言选择器中切换中英文界面
- **自动检测**：默认根据系统语言设置，支持手动覆盖
- **完整翻译**：所有用户界面文本、错误消息、帮助文档均已翻译

#### 翻译范围
- 用户界面（标题、按钮、表单标签）
- 错误消息和警告提示
- 帮助文本和操作说明
- 配置界面和状态显示

#### 技术实现
- 模块化翻译系统，易于扩展更多语言
- 实时切换，无需刷新页面
- 翻译键值对系统，支持动态内容

### 🔗 联网搜索优化

应用程序优化了联网搜索体验，确保稳定可靠的论文检索：

#### 智能重试机制
- **指数退避重试**：网络错误时自动重试，避免单点故障
- **错误分类处理**：区分网络错误、API限制和服务器错误
- **最多3次重试**：在失败前尝试多次连接

#### 连接状态监控
- **实时连接检查**：侧边栏提供"检查连接"按钮
- **状态可视化**：清晰显示API连接状态和响应时间
- **错误诊断**：提供详细的错误信息和解决建议

#### 模拟数据回退
- **优雅降级**：当API不可用时自动切换到模拟数据模式
- **无缝体验**：用户界面保持一致，无需手动切换
- **测试友好**：设置`USE_MOCK_DATA=true`可强制使用模拟数据

#### 默认设置优化
- **真实API优先**：默认启用真实API搜索（`USE_MOCK_DATA=false`）
- **安全速率限制**：默认0.1秒延迟，避免触发API限制
- **连接超时**：10秒连接超时，避免长时间等待

## 🚀 使用

### 运行应用程序
```bash
# 启动 Streamlit 应用程序
streamlit run app.py

# 或使用自定义主机/端口
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 访问应用程序
运行后，打开浏览器并导航至：
- **本地**：`http://localhost:8501`
- **远程**：`http://<your-server-ip>:8501`

### 使用应用程序
1. **在搜索框中输入你的研究问题**
2. **调整设置**（可选）：更改要检索的论文数量
3. **点击"搜索与分析"**：系统将：
   - 在 Semantic Scholar 中搜索相关论文
   - 处理摘要和元数据
   - 严格基于论文生成 AI 驱动的答案
   - 显示带有引用的答案
4. **查看结果**：
   - 带有高亮引用的 AI 生成答案
   - 包含详细信息的引用论文列表
   - 搜索到的所有论文

## 📊 示例查询

尝试以下示例查询以开始：
- "What are the latest advancements in quantum computing?"
- "How does deep learning improve natural language processing?"
- "What are the environmental impacts of cryptocurrency mining?"
- "Recent developments in CRISPR gene editing technology"

## 🔧 配置选项

### LLM 模型
应用程序支持多个 LLM 提供商：
- **OpenAI**: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet`, `claude-3-opus`, `claude-3-haiku`

### 搜索参数
- `MAX_PAPERS_TO_RETRIEVE`: 要获取的论文数量 (1-50)
- `TEMPERATURE`: LLM 创造力与事实性之间的权衡 (0.0-1.0)
- `MAX_TOKENS`: 最大响应长度 (100-4000)

### 速率限制
- `RATE_LIMIT_DELAY`: API调用之间的延迟，以遵守速率限制

## 🧪 测试

运行集成测试以验证功能：
```bash
python test_integration.py
```

## 🏗️ 项目结构

```plaintext
ai_academic_paper_assistant/
├── app.py                    # 主 Streamlit 应用程序
├── requirements.txt          # Python 依赖
├── README.md                # 本文档
├── .env.example             # 示例环境配置
├── .gitignore              # Git 忽略规则
├── test_integration.py     # 集成测试
│
├── src/                    # 源代码
│   ├── __init__.py
│   │
│   ├── core/              # 核心协调逻辑
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   │
│   ├── api/               # API 客户端
│   │   ├── __init__.py
│   │   └── semantic_scholar.py
│   │
│   ├── llm/               # LLM 集成
│   │   ├── __init__.py
│   │   └── processor.py
│   │
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   └── paper.py
│   │
│   └── utils/             # 工具类
│       ├── __init__.py
│       ├── config.py
│       └── config_manager.py  # 配置管理器（支持双配置持久化）
│
├── i18n/               # 国际化支持
│   ├── __init__.py
│   └── translations.py # 中英文翻译文件
│
├── config/                # 配置文件
│   └── config.example.json # JSON配置文件示例
├── data/                  # 数据存储（如果需要）
└── tests/                 # 测试文件
```

## 🔒 安全与隐私

- **API 密钥**：存储在 `.env` 文件中（从不提交到版本控制）
- **数据处理**：论文通过安全的 API 调用处理
- **无数据存储**：用户查询和结果不会持久存储
- **速率限制**：内置延迟以遵守 API 速率限制

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 开启一个 Pull Request

## 📝 许可证

本项目基于 MIT 许可证 - 详情请见 LICENSE 文件。

## 🙏 致谢

- **Semantic Scholar**：提供学术论文搜索 API
- **OpenAI & Anthropic**：提供 LLM API
- **Streamlit**：提供优秀的 Web 应用程序框架

## 🆘 支持

如有问题、疑问或功能请求：
1. 查看 [Issues](https://github.com/yourusername/ai-academic-paper-assistant/issues) 页面
2. 创建包含详细描述的新 issue

## 📈 未来增强

计划功能：
- [ ] **扩展学术数据库**：支持额外的学术数据库（arXiv、PubMed等），扩大论文搜索范围
- [ ] **高级筛选选项**：添加年份范围、引用次数、作者等高级筛选功能
- [ ] **论文聚类和趋势分析**：自动对搜索结果进行聚类，分析研究趋势和热点
- [ ] **多格式导出**：支持导出结果为PDF、CSV、BibTeX等格式
- [ ] **用户账户系统**：添加用户账户和搜索历史功能，方便用户管理和回顾历史查询
- [ ] **多语言支持**：扩展支持更多语言，包括日文、德文、法文等
- [ ] **批量查询处理**：支持同时处理多个查询，提高研究效率

---

**使用 Streamlit、Semantic Scholar 和 LLMs 构建，用心打造 ❤️**
