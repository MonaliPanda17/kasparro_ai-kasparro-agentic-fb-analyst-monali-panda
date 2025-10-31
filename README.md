# Kasparro — Agentic Facebook Performance Analyst

An intelligent agentic system that analyzes Facebook ad performance, diagnoses issues, and generates actionable insights with creative recommendations.

## Quick Start

### Prerequisites
- Python 3.10 or higher
- Virtual environment (recommended)

### Installation

```bash
# Check Python version
python -V  # should be >= 3.10

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the project root (optional but recommended):

```bash
# For OpenAI LLM features (optional)
OPENAI_API_KEY=your_api_key_here

# For custom data path (optional)
DATA_CSV=/path/to/your/fb_ads_data.csv

```

### Run Analysis

```bash
# Using Typer CLI
python src/run.py "Analyze ROAS drop in last 7 days"

# Or as Python module
python -m src.run "Analyze ROAS drop in last 7 days"

# Or directly as script
python src/run.py analyze "Analyze ROAS drop in last 7 days"
```

## Data Setup

### Option 1: Use Sample Data (Default)
The system uses `data/synthetic_fb_ads_undergarments.csv` by default (if `use_sample_data: true` in config).

### Option 2: Use Custom Data
1. Place your CSV file anywhere on your system
2. Set environment variable:
   ```bash
   export DATA_CSV=/path/to/your/fb_ads_data.csv  # Linux/Mac
   set DATA_CSV=C:\path\to\your\synthetic_fb_ads_undergarments.csv.csv    # Windows
   ```
3. Set `use_sample_data: false` in `config/config.yaml`

### Expected CSV Format
Your CSV should include these columns:
- `date` (YYYY-MM-DD format)
- `campaign_name`
- `adset_name`
- `spend`, `impressions`, `clicks`, `purchases`, `revenue`
- `creative_type`, `creative_message`
- `audience_type`
- `platform`
- `country`

See `data/README.md` for more details.

## Configuration

Edit `config/config.yaml` to customize behavior:

```yaml
# Basic settings
python: "3.10"
random_seed: 42
confidence_min: 0.6          # Minimum confidence threshold for insights
use_sample_data: true        # Use sample data vs environment variable

# Analysis windows
time_windows: [7, 14, 28]   # Days for period comparison

# Segments to analyze
segment_dims:
  - campaign_name
  - adset_name
  - country
  - platform
  - creative_type
  - audience_type

# LLM settings (optional)
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.2
  use_llm_planner: true      # Enable LLM-based planning
  max_retries: 2
  timeout_seconds: 10

# Planner configuration
planner:
  problem_types:             # Extensible list
    - roas_drop
    - revenue_decline
    - cpa_spike
    - ctr_decline
    - performance_issue
    - budget_allocation
    - creative_performance
    - audience_quality
    - seasonal_analysis
  allow_custom_problem_types: true
```

## Project Structure

```
kasparro_ai/
├── src/
│   ├── agents/
│   │   ├── planner.py           # Decomposes queries into subtasks
│   │   ├── data_agent.py        # Loads and summarizes dataset
│   │   ├── insight_agent.py     # Generates hypotheses with reasoning
│   │   ├── evaluator.py         # Validates insights quantitatively
│   │   ├── creative_generator.py # Generates creative recommendations
│   │   └── llm.py               # LLM integration
│   ├── utils.py                 # Data loading utilities
│   ├── io_schemas.py            # Pydantic models for I/O
│   └── run.py                   # Main CLI entry point
├── prompts/                     # Structured prompt templates
│   ├── planner.md
│   ├── insight.md
│   ├── evaluator.md
│   └── creative.md
├── config/
│   └── config.yaml              # Configuration file
├── data/                        # Data files
│   ├── README.md
│   ├── sample_fb_ads.csv
│   └── synthetic_fb_ads_undergarments.csv
├── reports/                     # Generated outputs
│   ├── report.md                # Human-readable report
│   ├── plan.json                # Analysis plan
│   ├── insights.json            # All insights with evaluation
│   ├── creatives.json           # Creative recommendations
│   ├── overview.json            # Period comparison
│   ├── segments.json            # Segment analysis
│   └── data_summary.json        # Data summary for planner
├── logs/                        # JSONL traces
├── tests/                       # Unit tests
│   ├── test_evaluator.py
│   └── test_utils.py
└── requirements.txt
```

## Example Queries

```bash
# Analyze ROAS drop
python src/run.py "Analyze ROAS drop in last 7 days"

# Investigate revenue decline
python src/run.py "Why did revenue decline?"

# Check CTR issues
python src/run.py "What's causing low CTR?"

# Budget optimization
python src/run.py "How should I reallocate budget?"

# Creative performance
python src/run.py "Which creatives are underperforming?"
```

## Outputs

### Reports Directory
After running analysis, check `reports/` directory:

- **`report.md`** - Main human-readable report with:
  - Executive summary (LLM narrative)
  - Analysis plan with subtask decomposition
  - Overview metrics (current vs baseline)
  - Top insights with reasoning (Think→Analyze→Conclude)
  - Problem drivers (underperforming segments)
  - Creative recommendations for low-CTR campaigns

- **`plan.json`** - Structured analysis plan with:
  - Problem classification
  - Hypotheses to test
  - Subtask decomposition
  - Reasoning structure

- **`insights.json`** - Full insights data with:
  - All insights (validated and flagged)
  - Evaluation scores
  - Confidence metrics
  - Validation feedback

- **`creatives.json`** - Creative recommendations:
  - Target campaigns/adsets
  - New creative messages (hook, body, CTA)
  - Expected CTR improvement
  - Rationale

- **`overview.json`** - Period comparison metrics
- **`segments.json`** - Segment-level analysis
- **`data_summary.json`** - Data summary for planner

### Logs Directory
JSONL traces are saved to `logs/trace_YYYYMMDD_HHMMSS.jsonl`:
- Agent call traces
- LLM interactions (requests/responses)
- Evaluation scores
- Validation notes

## How It Works

### Agent Workflow

1. **Planner Agent**: 
   - Decomposes user query into subtasks
   - Classifies problem type
   - Generates testable hypotheses
   - Uses LLM (if enabled) or rule-based planning

2. **Data Agent**:
   - Loads CSV and generates data summary
   - Compares current vs baseline periods
   - Performs segment-level analysis

3. **Insight Agent**:
   - Transforms data evidence into insights
   - Adds reasoning structure (Think→Analyze→Conclude)
   - Prioritizes by impact (high/medium/low)

4. **Evaluator Agent**:
   - Quantitatively validates insights
   - Cross-checks numbers against evidence
   - Provides feedback (strengths, improvements)
   - Flags low-confidence insights for retry

5. **Creative Generator**:
   - Identifies low-CTR campaigns
   - Adapts winning creative patterns
   - Generates new creative messages with rationale

### Planner-Evaluator Loop

The system implements a feedback loop:
- Evaluator validates insights
- Low-confidence insights are flagged
- Planner receives feedback to improve future hypotheses
- Warnings displayed if >50% insights need retry

## Testing

Run unit tests:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_evaluator.py
pytest tests/test_utils.py

# With verbose output
pytest tests/ -v
```

## Troubleshooting

### Common Issues

1. **"Missing config/config.yaml"**
   - Ensure you're running from project root directory

2. **"OPENAI_API_KEY not set"**
   - This is optional - system falls back to rule-based planning
   - To use LLM features, set environment variable or add to `.env`

3. **"No data found"**
   - Check `DATA_CSV` environment variable if using custom data
   - Or ensure `use_sample_data: true` in config for sample data

4. **Import errors**
   - Activate virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
   - Install dependencies: `pip install -r requirements.txt`

5. **Low confidence insights**
   - System flags insights with confidence < threshold
   - Check `confidence_min` in config.yaml
   - Review `reports/insights.json` for detailed feedback

## Features

**Agentic Reasoning Architecture**
- Planner decomposes queries into subtasks
- Clear Planner-Evaluator feedback loop

**Structured Prompts**
- Layered prompts with JSON schema
- Think → Analyze → Conclude reasoning structure

**Quantitative Validation**
- Cross-validates numbers against evidence
- Mathematical consistency checks
- Reflection/retry logic

**Low-CTR Focus**
- Identifies underperforming campaigns
- Data-driven creative recommendations
- Expected improvement metrics

**Observability**
- JSONL traces in `logs/` directory for all agent interactions
- Detailed evaluation feedback and confidence scoring

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `pydantic` - Data validation
- `pyyaml` - Config parsing
- `typer` - CLI interface
- `rich` - Terminal output formatting
- `openai` - LLM integration (optional)
- `pytest` - Testing

## Release

- Tag: [`v1.0`](https://github.com/MonaliPanda17/kasparro_ai-kasparro-agentic-fb-analyst-monali-panda/releases/tag/v1.0)


## Self-Review

See [SELF_REVIEW.md](SELF_REVIEW.md) for detailed design choices, tradeoffs, and architecture decisions.

**Highlights**:
- Agent-based architecture with clear separation of concerns
- Hybrid LLM + rule-based planner for reliability
- Externalized prompts for easy iteration
- Quantitative validation with evaluator feedback loop
- Multiple output formats (Markdown + JSON)

## License

See assignment documentation for license terms.

