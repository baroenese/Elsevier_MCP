# Elsevier MCP Server

An MCP (Model Context Protocol) server for Elsevier's Scopus APIs, enabling direct academic paper search, analysis, and researcher information retrieval through Cursor IDE's AI Composer.

🌐 **Repository**: https://github.com/yasufumi-nakata/Elsevier_MCP
📖 **日本語版README**: [README_ja.md](README_ja.md)

## 📚 Overview

This project provides access to Elsevier's academic database services via MCP (Model Context Protocol). MCP is a standardized protocol for connecting AI applications with external data sources, often referred to as "USB-C for AI."

### 🔗 Available Elsevier API Services

- **Scopus API**: World's largest citation and abstract database (78 million records, 16 million author profiles)
- **Abstract Retrieval API**: Detailed paper abstracts and metadata retrieval
- **SciVal API**: Research performance analysis and author metrics

### ⚠️ Important API & AI Usage Terms

**Critical**: Please read Elsevier's policies carefully before use:

- **📋 API Terms**: All usage must comply with [Elsevier API Service Agreement](https://dev.elsevier.com/api_service_agreement.html)
- **🤖 AI Usage Policy**: Data obtained via this tool should follow [Elsevier's AI Guidelines](https://www.elsevier.com/about/policies/ai-policy)
- **📊 Text & Data Mining**: Academic text mining must comply with [TDM Policy](https://www.elsevier.com/about/open-science/research-data/text-and-data-mining)
- **🚫 Prohibited Uses**:
  - Training AI models without explicit permission
  - Large-scale data scraping beyond research purposes
  - Commercial redistribution of obtained data
- **🔒 Data Retention**: Retrieved data should not be stored permanently without proper licensing

For detailed terms, visit the [Elsevier Developer Portal](https://dev.elsevier.com/).

## ✨ Key Features

### 🔍 Paper Search
- Search papers by keywords, author names, and fields
- Year-specific search capabilities
- Retrieve up to 25 search results

### 👨‍🔬 Researcher Analysis
- Detailed author profile information
- ORCID ID-based researcher search
- Citation counts, H-Index, and research activity metrics

### 📊 Research Trend Analysis
- Field-specific year-over-year analysis
- Institution-based paper statistics
- Open access paper search

### 📄 Detailed Paper Information
- Abstract and metadata retrieval
- DOI and EID-based detailed search

## 🚀 Quick Start

### Step 1: Verify Required Environment

You need the following environment:
- 🐍 **Python 3.10 or higher** (Python 3.10+ recommended)
- 💻 **Cursor IDE** (Please use the latest version)
- 🔑 **Elsevier API Key** (Available from Elsevier Developer Portal)

### Step 2: Download Project

```bash
# Clone project from GitHub
git clone https://github.com/yasufumi-nakata/Elsevier_MCP.git
cd Elsevier_MCP

# Install required Python libraries
pip install -e .
```

### Step 3: Obtain Elsevier API Key

#### 3-1. Create Account on Elsevier Developer Portal

1. Visit [Elsevier Developer Portal](https://dev.elsevier.com/)
2. Click "I want an API Key"
3. Fill in account information and create account

#### 3-2. Generate API Key

1. After login, select "My API Key"
2. Create a new API key
3. **Follow Elsevier's current terms and policies**

#### 3-3. Set Environment Variable

**Windows (Command Prompt):**
```cmd
set ELSEVIER_API_KEY=your_api_key_here
```

**Windows (PowerShell):**
```powershell
$env:ELSEVIER_API_KEY="your_api_key_here"
```

**macOS/Linux:**
```bash
export ELSEVIER_API_KEY="your_api_key_here"
```

### Step 4: Configure MCP in Cursor IDE

#### 4-1. Open Cursor Settings

1. Launch **Cursor IDE**
2. Open settings with `⌘ + ,` (Mac) or `Ctrl + ,` (Windows/Linux)
3. Select "**MCP**" from the left menu

#### 4-2. Add MCP Server

1. Click "**Add new global MCP server**" button
2. Add the following JSON configuration:

```json
{
  "mcpServers": {
    "elsevier-research": {
      "comment": "🔬 Elsevier Academic Paper Search MCP",
      "command": "elsevier-mcp-server",
      "args": [],
      "env": {
        "ELSEVIER_API_KEY": "insert_your_api_key_here"
      }
    }
  }
}
```

**Important**:
- Install the package in the same Python environment that Cursor can access
- Replace `insert_your_api_key_here` with your obtained API key

#### 4-3. Save and Verify Settings

1. Save the configuration file (`⌘ + S` or `Ctrl + S`)
2. Green indicator in MCP server list indicates success
3. If errors appear, double-check the package installation and API key

## 📖 Usage Guide

### Step 1: Open Cursor AI Composer

1. Start a new chat in **Cursor IDE**
2. Click the **"Composer" icon** in the upper right, or press `⌘ + I` (Mac) / `Ctrl + I` (Windows)
3. Make sure **"Agent" mode** is selected (required to use MCP tools)

### Step 2: Try Paper Search

Input questions like the following:

#### 🔍 Basic Paper Search
```
"Search for 5 papers on machine learning"
```

#### 📊 Research Trend Analysis
```
"Analyze research trends in AI and machine learning fields for 2023"
```

#### 👨‍🔬 Researcher Information Retrieval
```
"Tell me about the researcher with ORCID: 0000-0003-1419-2405"
```

#### 🏛️ Institution-based Research Status
```
"Research the number of papers and major research fields at MIT (Massachusetts Institute of Technology) in 2023"
```

#### 🔓 Open Access Paper Search
```
"Search for 3 open access papers on quantum computing"
```

### Step 3: Tool Approval and Execution

1. When AI displays **"Tool Approval Required"**, click "**Use Tool**"
2. Wait a few seconds for results to display
3. **For more detailed information**, you can continue asking additional questions

### 💡 Usage Tips

- **Use specific keywords** for more accurate results
- **Specify years** to understand latest research trends
- **Specify number of papers** to adjust the amount of information needed

## 🛠️ Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `search_papers` | Paper search (supports keywords and `AUTH`, `TITLE`, `AFFIL`, `DOI` field codes) | `query`, `count`, `year` |
| `get_paper_abstract` | Paper abstract retrieval | `eid` or `doi` |
| `get_author_info` | Author information | `author_id` |
| `analyze_research_trends` | Research trend analysis | `field`, `years` |
| `get_institution_papers` | Institution paper statistics | `institution`, `year` |
| `search_open_access_papers` | Open access paper search | `field`, `count` |

## 📝 Available MCP Prompts

| Prompt Name | Description | Arguments |
|-------------|-------------|-----------|
| `systematic_literature_review` | Synthesizes state-of-the-art literature with methodology comparison tables and research gap discovery | `topic` (required), `year_range`, `focus` |
| `paper_deep_dive` | Critical appraisal covering research questions, methodology, proof vs claims, and threats to validity | `paper_title_or_eid` (required), `analysis_depth` |
| `research_trend_analysis` | Evaluates multi-year publication velocity, contributing institutions, and emerging sub-disciplines | `field` (required), `timeframe` |

## 📦 Available MCP Resources

| URI / Template | Type | Description |
|----------------|------|-------------|
| `elsevier://docs/scopus-search-syntax` | Static | Complete Scopus search syntax, field code cheatsheet, and Boolean logic guide |
| `elsevier://paper/{eid}` | Dynamic | Fetches paper abstract and bibliographic metadata rendered in clean Markdown |
| `elsevier://trends/{field}` | Dynamic | Fetches multi-year publication trends and growth statistics rendered in Markdown |

## 🧪 Testing

```bash
# Package and metadata checks
python -m compileall -q elsevier_mcp_complete.py examples test.py
python -m build
python -m twine check dist/*

# Live API tests (requires ELSEVIER_API_KEY)
python test.py

# Direct handler examples
python examples/basic_usage.py
```

## 🔧 Troubleshooting

### 🚨 Common Issues and Solutions

#### Issue 1: "MCP Server Won't Start"

**Symptoms**: Red indicator appears for MCP server in Cursor settings

**Solutions**:
1. **Check the console command is installed**:
   ```bash
   elsevier-mcp-server --version
   ```
2. **Reinstall required libraries**:
   ```bash
   pip install -e .
   ```

#### Issue 2: "API Key Error Occurs"

**Symptoms**: `401 Unauthorized` error, "Invalid API Key", or "ELSEVIER_API_KEY environment variable is not set"

**Solutions**:
1. **If a tool returns "environment variable is not set"**: The MCP server can start without an API key, but API-backed tools need it
   - Set your API key: `export ELSEVIER_API_KEY="your_api_key_here"`
   - Restart the MCP server in Cursor
2. **Check API key format**: Confirm it's 32 alphanumeric characters
3. **Reset environment variable**:
   ```bash
   # Check current setting
   echo $ELSEVIER_API_KEY

   # Reset
   export ELSEVIER_API_KEY="your_actual_api_key"
   ```
4. **Reload Cursor settings**: Save settings and restart Cursor

#### Issue 3: "No Search Results Displayed"

**Symptoms**: "No papers found" message appears

**Solutions**:
1. **Change keywords**: Try more general terms (e.g., "AI" → "artificial intelligence")
2. **Remove year restrictions**: Delete specific year specifications
3. **Try open access search**: Search only freely accessible papers

#### Issue 4: "Tools Not Used in Cursor Agent Mode"

**Symptoms**: Only regular responses returned, MCP tools not used

**Solutions**:
1. **Check Agent mode**: Confirm chat setting is "Agent"
2. **Explicitly request tool use**:
   ```
   "Use the search_papers tool to search for machine learning papers"
   ```
3. **Enable Auto-run**: Enable automatic tool execution in Cursor settings

#### Issue 5: "Usage Limit Reached"

**Symptoms**: `Rate limit exceeded` error

**Solutions**:
- **Usage limits**: Check current API limits in your Elsevier Developer Portal
- **Limit reset**: Limits reset every Monday
- **Higher limits**: Contact Elsevier for expanded access if needed

### 📞 When You Need Support

1. **GitHub Issues**: [Report Issues](https://github.com/yasufumi-nakata/Elsevier_MCP/issues)
2. **Elsevier API Support**: apisupport@elsevier.com
3. **Cursor Support**: [Cursor Help Center](https://docs.cursor.com/)

### ✅ Operation Verification Checklist

To confirm settings are working correctly:

- [ ] Python 3.10+ is installed
- [ ] Required libraries are installed
- [ ] Elsevier API key is valid
- [ ] Server shows green in Cursor MCP settings
- [ ] Agent mode is selected
- [ ] File path is correctly set

## 📦 Dependencies

- `requests`: HTTP API client
- `python-dotenv`: Environment variable management

See `requirements.txt` for complete details.

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Pull requests and issue reports are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🔗 Related Links

### 📚 Official Documentation
- [Elsevier Developer Portal](https://dev.elsevier.com/) - API key acquisition and specifications
- [Scopus API Documentation](https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl) - Detailed Scopus API specifications
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Official MCP protocol site
- [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol) - MCP setup guide for Cursor

### 🛠️ Development Tools
- [Cursor IDE](https://cursor.sh/) - AI-integrated development environment
- [MCP Directory](https://cursor.directory/mcp) - Directory of 1800+ MCP servers
- [GitHub - MCP Servers](https://github.com/modelcontextprotocol/servers) - Official MCP server collection

### 🎓 Learning Resources
- [MCP Tutorial Series](https://medium.com/search?q=model+context+protocol) - MCP learning articles
- [Elsevier API Examples](https://dev.elsevier.com/start_coding.html) - API usage examples

## 📞 Support & Contact

### 🐛 Issue Reporting
- **GitHub Issues**: [Report Issues](https://github.com/yasufumi-nakata/Elsevier_MCP/issues)
- **Feature Request**: [Request New Features](https://github.com/yasufumi-nakata/Elsevier_MCP/issues/new)

### 💬 Questions & Discussions
- **GitHub Discussions**: [Join Discussions](https://github.com/yasufumi-nakata/Elsevier_MCP/discussions)
- **Elsevier API Support**: apisupport@elsevier.com

### 📝 Feedback
Help us improve the project:
- Usage experience reports
- Feature suggestions
- Documentation improvements

---

## ⚖️ Terms & Disclaimer

### 📋 Usage Terms
- This project is developed for **educational and research purposes**
- Users must comply with **all Elsevier API terms and AI usage policies**
- **Your responsibility**: Ensure your use complies with institutional and legal requirements
- **Data handling**: You are responsible for appropriate data management and retention policies

### 🛡️ Important Disclaimers
- **API Compliance**: Users must independently verify compliance with Elsevier's current terms
- **AI & Ethics**: Use of retrieved data for AI training requires explicit permission from Elsevier
- **Legal Responsibility**: The author assumes no liability for policy violations or misuse
- **Data Accuracy**: Information accuracy is subject to Elsevier's data quality and policies
- **Commercial Use**: Any commercial application requires separate licensing from Elsevier

### 🚨 User Responsibilities
- **Read Terms**: Always review current Elsevier policies before use
- **Respect Limits**: Adhere to API rate limits and usage restrictions
- **Proper Attribution**: Cite sources appropriately when using retrieved data
- **Institutional Compliance**: Ensure compliance with your institution's data policies

### 📜 License
This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.

### 🤝 Contributions Welcome
Pull requests and issues are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---
**🔬 Elsevier MCP Server** - Academic Research Made Easier with AI
**📝 Last Updated**: May 21, 2026
**🌟 GitHub**: https://github.com/yasufumi-nakata/Elsevier_MCP
