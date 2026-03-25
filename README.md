# AI Academic Paper Assistant 📚

A web application that allows users to input a search query, searches for *real, traceable* academic papers related to the query, curates and summarizes the findings using an LLM, and provides a coherent answer with **zero hallucination**.

## 🎯 Objective

Build a web application that:
1. Accepts user search queries
2. Searches for real academic papers using Semantic Scholar API
3. Uses LLMs to generate answers based **strictly** on retrieved papers
4. Provides citations for every claim
5. Presents results in a clean, user-friendly interface

## 🚀 Core Constraint (CRITICAL)

**ZERO HALLUCINATION** - The AI's final answer must be based *strictly* on the retrieved paper data. Every claim must have a citation to a real paper. The LLM is not allowed to invent paper titles, authors, or content.

## ✨ Key Features

- **Clean Web Interface**: Streamlit-based GUI with intuitive search and results display
- **Real Paper Search**: Integration with Semantic Scholar API for authentic academic papers
- **AI-Powered Summarization**: LLM integration (OpenAI/Anthropic) for generating coherent answers
- **Citation Tracking**: Every claim in the answer is linked to specific papers
- **Paper Details**: View abstracts, authors, citations, and links to original papers
- **Configurable Settings**: Adjust search limits, LLM models, and temperature

## 🏗️ Architecture

```
User Query → Streamlit UI → AcademicPaperOrchestrator → Semantic Scholar API → LLM Processor → Results Display
```

### Components:
1. **Frontend**: Streamlit application (`app.py`)
2. **Orchestrator**: Coordinates search and processing (`src/core/orchestrator.py`)
3. **Paper Search**: Semantic Scholar API client (`src/api/semantic_scholar.py`)
4. **LLM Integration**: OpenAI/Anthropic processor with anti-hallucination prompts (`src/llm/processor.py`)
5. **Data Models**: Paper and author data structures (`src/models/paper.py`)
6. **Configuration**: Environment-based settings (`src/utils/config.py`)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd ai_academic_paper_assistant

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file with your API keys
# You need at least one LLM API key for full functionality
nano .env  # or use your favorite editor
```

### Step 3: Environment Variables
Configure your `.env` file:
```env
# OpenAI API Key (optional but recommended)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API Key (optional alternative)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Semantic Scholar API (no key needed for basic usage)
SEMANTIC_SCHOLAR_API_KEY=optional_semantic_scholar_api_key

# Application Settings
MAX_PAPERS_TO_RETRIEVE=10
LLM_MODEL=gpt-4o  # or claude-3-5-sonnet, gpt-3.5-turbo, etc.
MAX_TOKENS=2000
TEMPERATURE=0.1  # Low temperature for more factual responses
```

## 🚀 Usage

### Running the Application
```bash
# Start the Streamlit application
streamlit run app.py

# Or with custom host/port
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Access the Application
Once running, open your browser and navigate to:
- **Local**: `http://localhost:8501`
- **Remote**: `http://<your-server-ip>:8501`

### Using the Application
1. **Enter your research question** in the search box
2. **Adjust settings** (optional): Change the number of papers to retrieve
3. **Click "Search & Analyze"**: The system will:
   - Search Semantic Scholar for relevant papers
   - Process abstracts and metadata
   - Generate an AI-powered answer based strictly on the papers
   - Display the answer with citations
4. **Review results**:
   - AI-generated answer with highlighted citations
   - List of referenced papers with details
   - All papers found in the search

## 📊 Example Queries

Try these example queries to get started:
- "What are the latest advancements in quantum computing?"
- "How does deep learning improve natural language processing?"
- "What are the environmental impacts of cryptocurrency mining?"
- "Recent developments in CRISPR gene editing technology"

## 🔧 Configuration Options

### LLM Models
The application supports multiple LLM providers:
- **OpenAI**: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet`, `claude-3-opus`, `claude-3-haiku`

### Search Parameters
- `MAX_PAPERS_TO_RETRIEVE`: Number of papers to fetch (1-50)
- `TEMPERATURE`: LLM creativity vs. factuality (0.0-1.0)
- `MAX_TOKENS`: Maximum response length (100-4000)

### Rate Limiting
- `RATE_LIMIT_DELAY`: Delay between API calls to respect rate limits

## 🧪 Testing

Run the integration tests to verify functionality:
```bash
python test_integration.py
```

## 🏗️ Project Structure

```
ai_academic_paper_assistant/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── .env.example             # Example environment configuration
├── .gitignore              # Git ignore rules
├── test_integration.py     # Integration tests
│
├── src/                    # Source code
│   ├── __init__.py
│   │
│   ├── core/              # Core orchestration logic
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   │
│   ├── api/               # API clients
│   │   ├── __init__.py
│   │   └── semantic_scholar.py
│   │
│   ├── llm/               # LLM integration
│   │   ├── __init__.py
│   │   └── processor.py
│   │
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   └── paper.py
│   │
│   └── utils/             # Utilities
│       ├── __init__.py
│       └── config.py
│
├── config/                # Configuration files
├── data/                  # Data storage (if needed)
└── tests/                 # Test files
```

## 🔒 Security & Privacy

- **API Keys**: Stored in `.env` file (never committed to version control)
- **Data Processing**: Papers are processed through secure API calls
- **No Data Storage**: User queries and results are not persistently stored
- **Rate Limiting**: Built-in delays to respect API rate limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Semantic Scholar**: For providing the academic paper search API
- **OpenAI & Anthropic**: For LLM APIs
- **Streamlit**: For the excellent web application framework

## 🆘 Support

For issues, questions, or feature requests:
1. Check the [Issues](https://github.com/yourusername/ai-academic-paper-assistant/issues) page
2. Create a new issue with detailed description

## 📈 Future Enhancements

Planned features:
- [ ] Support for additional academic databases (arXiv, PubMed)
- [ ] Advanced filtering options (year range, citation count)
- [ ] Paper clustering and trend analysis
- [ ] Export results (PDF, CSV, BibTeX)
- [ ] User accounts and search history
- [ ] Multi-language support
- [ ] Batch processing of queries

---

**Built with ❤️ using Streamlit, Semantic Scholar, and LLMs**