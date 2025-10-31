# Self-Review: Kasparro Agentic FB Analyst

## Overview
This document describes the design choices, tradeoffs, and architecture decisions made in building the Kasparro Agentic Facebook Performance Analyst system.

## Architecture Design

### Agent-Based Architecture
**Decision**: Separated functionality into distinct agents (Planner, Data Agent, Insight Agent, Evaluator, Creative Generator)

**Rationale**:
- Clear separation of concerns enables independent development and testing
- Each agent has a single responsibility (SRP)
- Easy to extend with new agents without modifying existing ones
- Supports parallel execution where possible

**Tradeoffs**:
- More files/modules to maintain
- Requires careful I/O schema design (currently using Dict[str, Any], could be improved with strict Pydantic validation)

### Hybrid Planner (LLM + Rule-Based)
**Decision**: Implemented a hybrid planner that tries LLM first, falls back to rule-based

**Rationale**:
- LLM provides flexibility for novel queries but can fail (API issues, rate limits)
- Rule-based ensures system always works even without API key
- Best of both worlds: intelligent when possible, reliable always

**Tradeoffs**:
- More complex implementation
- Two code paths to maintain
- Rule-based may not handle edge cases as well as LLM

### I/O Schemas (Pydantic)
**Decision**: Defined Pydantic schemas in `io_schemas.py` but agents use `Dict[str, Any]` at runtime

**Rationale**:
- Schemas serve as documentation of data contracts
- Flexible dict-based I/O allows incremental adoption
- Easier to iterate during development

**Tradeoffs**:
- No runtime validation (could catch errors earlier)
- Less type safety
- **Future improvement**: Add schema validation at agent boundaries

### Prompt Externalization
**Decision**: All prompts stored in `prompts/*.md` files, not inline

**Rationale**:
- Easy to edit prompts without touching code
- Version control tracks prompt changes
- Supports A/B testing of prompts
- Non-technical users can modify prompts

**Tradeoffs**:
- Slightly more file I/O
- Need to handle missing prompt files gracefully

### JSONL Logging
**Decision**: Log all agent interactions to JSONL files in `logs/`

**Rationale**:
- Structured logs enable debugging and analysis
- JSONL is easy to parse and query
- Supports observability without external dependencies
- Can be easily ingested by log analysis tools

**Tradeoffs**:
- File-based logging (no centralized log aggregation)
- Could add Langfuse/Weights & Biases integration later

### Evaluator Feedback Loop
**Decision**: Evaluator validates insights and flags low-confidence ones for retry

**Rationale**:
- Ensures quality of generated insights
- Quantitative validation catches math errors
- Reflection loop improves system over time

**Tradeoffs**:
- Adds complexity to workflow
- May slow down generation (but improves quality)

## Data Handling

### CSV as Primary Input
**Decision**: Use CSV files for ad performance data

**Rationale**:
- Universal format, easy to export from Facebook Ads Manager
- No API complexity
- Works offline

**Tradeoffs**:
- Manual export required (could add API integration)
- Static snapshots (not real-time)

### Sample Data Included
**Decision**: Include synthetic sample data for testing

**Rationale**:
- Allows testing without real data
- Protects user privacy
- Demonstrates expected format

## Configuration

### YAML Configuration
**Decision**: Use YAML for configuration (`config/config.yaml`)

**Rationale**:
- Human-readable
- Supports nested structures
- Standard format

**Tradeoffs**:
- Less programmatic than Python config
- Requires YAML parser dependency

### Confidence Thresholds
**Decision**: Configurable `confidence_min` threshold (default 0.6)

**Rationale**:
- Allows tuning quality vs quantity tradeoff
- Different use cases may need different thresholds

## Testing Strategy

### Unit Tests for Evaluator
**Decision**: Focused test coverage on evaluator (critical path)

**Rationale**:
- Evaluator is core quality control mechanism
- Test quantitative validation logic
- High ROI for testing effort

**Tradeoffs**:
- Other agents have less test coverage
- Could add integration tests

## CLI Design

### Typer-Based CLI
**Decision**: Use Typer for CLI interface

**Rationale**:
- Type hints provide automatic help generation
- Clean API
- Rich terminal output

**Tradeoffs**:
- Typer dependency
- Could use argparse (stdlib) for zero dependencies

## Output Formats

### Multiple Output Formats
**Decision**: Generate both human-readable (`report.md`) and machine-readable JSON files

**Rationale**:
- Markdown for humans to read
- JSON for programmatic consumption
- Best of both worlds

**Tradeoffs**:
- More files to generate and maintain
- Risk of inconsistency between formats

### Reports Directory Structure
**Decision**: Separate files for plan, insights, creatives, segments, etc.

**Rationale**:
- Modular output
- Easy to consume individual pieces
- Clear organization

**Tradeoffs**:
- More file management
- Could be single JSON with nested structure

## Future Improvements

1. **Strict Schema Validation**: Enforce Pydantic schemas at agent boundaries
2. **API Integration**: Add Facebook Ads API integration for real-time data
3. **More Test Coverage**: Add integration tests for full workflow
4. **Langfuse Integration**: Add Langfuse for LLM observability
5. **Caching**: Cache LLM responses for cost savings
6. **Parallel Agent Execution**: Run independent agents in parallel
7. **Streaming Output**: Support streaming insights as they're generated

## Known Limitations

1. **No Real-Time Data**: Requires CSV export (not live API)
2. **Schema Validation**: I/O schemas defined but not enforced
3. **Limited Error Recovery**: Basic retry logic, could be more sophisticated
4. **No Authentication**: Assumes local/trusted environment
5. **Single CSV**: Processes one CSV at a time

## Performance Considerations

- CSV loading: Pandas handles large files efficiently
- LLM calls: Timeout and retry logic prevents hanging
- Logging: JSONL format is efficient for appending
- No caching: Could add Redis/file cache for repeated queries

## Security Considerations

- API keys in environment variables (not hardcoded)
- No data sent to external services except OpenAI (optional)
- Local file processing
- No user authentication (assumes trusted environment)

