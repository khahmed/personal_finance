# Automatic Parser Generator

This system allows you to automatically generate parsers for new financial institutions using AI. Instead of manually writing parser code, you can have an AI agent analyze PDF statements and generate production-ready parser code.

## Overview

The parser generator uses **CrewAI** with specialized agents to:
1. Analyze PDF statement structures and formats
2. Generate Python parser code that follows your existing patterns
3. Integrate seamlessly with your codebase

## Architecture

### Components

1. **parser_generator/agent.py** - CrewAI-based agent system
   - `ParserGeneratorAgent` - Main agent class
   - `Financial Statement Analyzer` - Analyzes PDF structures
   - `Parser Code Generator` - Generates Python code

2. **institutions.yaml** - Configuration file
   - Maps institution directories to parser classes
   - Supports multiple parsers per institution
   - Pattern-based matching (e.g., "pps" → CIBCPPSParser)

3. **parser_loader.py** - Dynamic parser loading system
   - Loads parsers based on configuration
   - Eliminates hard-coded parser imports
   - CLI for testing and management

4. **process_statements.py** - Updated to use dynamic loading
   - No more manual parser imports
   - Automatically finds correct parser via configuration

## Installation

1. Install required dependencies:
```bash
venv/bin/pip install crewai crewai-tools anthropic pyyaml
```

2. Set up your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
# Or add to .env file
echo "ANTHROPIC_API_KEY=your-api-key-here" >> .env
```

## Usage

### Generating a Parser for a New Institution

1. **Organize your statements:**
   ```bash
   mkdir statements/TD
   cp /path/to/td-statements/*.pdf statements/TD/
   ```

2. **Run the parser generator:**
   ```bash
   venv/bin/python parser_generator/agent.py TD
   ```

   This will:
   - Analyze all PDFs in statements/TD/
   - Generate a parser class (TDParser)
   - Save it to parsers/td_parser.py
   - Save analysis report to parsers/td_analysis.md

3. **Review the generated code:**
   ```bash
   cat parsers/td_parser.py
   ```

4. **Test the parser:**
   ```bash
   venv/bin/python -c "
   from parsers.td_parser import TDParser
   parser = TDParser('statements/TD/sample.pdf')
   data = parser.parse()
   print(f'Account: {data[\"account_number\"]}')
   print(f'Holdings: {len(data[\"holdings\"])}')
   "
   ```

5. **Register the parser in configuration:**
   ```bash
   venv/bin/python parser_loader.py add TD TDParser parsers.td_parser "TD Bank investment accounts"
   ```

6. **Process statements:**
   ```bash
   venv/bin/python process_statements.py process --statements-dir statements
   ```

### Managing Parsers

**List all configured parsers:**
```bash
venv/bin/python parser_loader.py list
```

**Test parser detection for a file:**
```bash
venv/bin/python parser_loader.py test "statements/TD/statement.pdf"
```

**Add a parser manually:**
```bash
venv/bin/python parser_loader.py add TD TDParser parsers.td_parser "TD Bank accounts"
```

## Configuration Format

`institutions.yaml` structure:
```yaml
institutions:
  TD:
    name: "TD Bank"
    parsers:
      - pattern: "direct"  # Matches files containing "direct"
        class: "TDDirectParser"
        module: "parsers.td_direct_parser"
        description: "TD Direct Investing accounts"
      - pattern: "*"  # Default fallback
        class: "TDParser"
        module: "parsers.td_parser"
        description: "Standard TD investment accounts"
```

### Pattern Matching Rules

- Patterns are matched against the lowercase filename
- `"*"` matches anything (use as default/fallback)
- Use keywords like "pps", "tfsa", "rrsp", "direct" to match specific account types
- First matching pattern wins
- If no directory match, falls back to filename matching

### Example Patterns

```yaml
CIBC:
  name: "CIBC"
  parsers:
    - pattern: "pps"
      class: "CIBCPPSParser"
      # Matches: CIBC-RRSP-PPS-2025.pdf
    - pattern: "*"
      class: "CIBCInvestorsEdgeParser"
      # Matches: all other CIBC files
```

## How It Works

### Step 1: PDF Analysis

The `Financial Statement Analyzer` agent:
- Reads all PDFs in the institution directory
- Identifies structural patterns:
  - Account number formats
  - Date formats
  - Holdings table structures
  - Category headers
  - Currency indicators
- Documents special cases and edge cases
- Produces a detailed specification

### Step 2: Code Generation

The `Parser Code Generator` agent:
- Reads the specification from Step 1
- Studies existing parser implementations as templates
- Generates code that:
  - Inherits from `BaseStatementParser`
  - Implements required methods
  - Uses regex for extraction
  - Handles edge cases
  - Follows PEP 8 style
- Includes comprehensive docstrings and comments

### Step 3: Integration

The generated parser:
- Is saved to `parsers/<institution>_parser.py`
- Can be tested immediately
- Needs to be registered in `institutions.yaml`
- Works with existing database and analysis code

## Prompt Engineering

The agent uses carefully crafted prompts based on your experience building parsers for CIBC, ScotiaBank, SunLife, and Olympia Trust. The prompts instruct the agent to:

1. **Analyze like a human expert:**
   - Look for common patterns (account numbers, dates, totals)
   - Identify section headers and table structures
   - Note special characters and formatting quirks
   - Handle multiple currencies

2. **Generate production-ready code:**
   - Follow existing code patterns exactly
   - Use utility methods from BaseStatementParser
   - Handle missing/optional fields gracefully
   - Include error handling

3. **Document thoroughly:**
   - Explain complex regex patterns
   - Show examples in comments
   - Include edge case handling

## Key Prompts Used

### Analysis Prompt (Simplified)
```
Analyze PDF statements and extract:
1. Document Structure (headers, sections)
2. Account Information (number format, type, dates)
3. Holdings Information (table format, columns, categories)
4. Financial Data (totals, cash balances)
5. Special Cases (multi-line entries, special characters, currencies)

Provide regex patterns and examples for each.
```

### Code Generation Prompt (Simplified)
```
Generate a Python parser class that:
1. Inherits from BaseStatementParser
2. Implements parse(), extract_account_info(), extract_holdings()
3. Uses pdfplumber for PDF extraction
4. Follows patterns from existing parsers
5. Handles all cases from the analysis

Reference existing parsers and match their structure exactly.
```

## Examples

### Example 1: TD Direct Investing

```bash
# Place PDFs in directory
mkdir statements/TD
cp ~/Downloads/TD-*.pdf statements/TD/

# Generate parser
venv/bin/python parser_generator/agent.py TD

# Review generated code
cat parsers/td_parser.py

# Test it
venv/bin/python -c "
from parsers.td_parser import TDParser
parser = TDParser('statements/TD/TD-RRSP-Oct-2025.pdf')
print(parser.parse())
"

# Register it
venv/bin/python parser_loader.py add TD TDParser parsers.td_parser "TD investment accounts"

# Process all statements
venv/bin/python process_statements.py all
```

### Example 2: RBC Investing

```bash
mkdir statements/RBC
cp ~/statements/*.pdf statements/RBC/

venv/bin/python parser_generator/agent.py RBC

# Edit generated code if needed
vim parsers/rbc_parser.py

venv/bin/python parser_loader.py add RBC RBCParser parsers.rbc_parser "RBC investment accounts"

venv/bin/python process_statements.py process
```

## Advanced Features

### Multiple Parsers per Institution

Some institutions have different statement formats for different account types:

```yaml
CIBC:
  parsers:
    - pattern: "pps"           # Bank-managed accounts
      class: "CIBCPPSParser"
    - pattern: "investorsedge" # Self-directed accounts
      class: "CIBCInvestorsEdgeParser"
    - pattern: "*"             # Fallback
      class: "CIBCParser"
```

### Extending the Generator

To customize the agent behavior, edit `parser_generator/agent.py`:

```python
def _create_analysis_agent(self) -> Agent:
    return Agent(
        role="Financial Statement Analyzer",
        goal="Your custom goal here",
        backstory="Your custom backstory",
        # Add custom tools
        tools=[self.file_read_tool, YourCustomTool()],
        llm=llm
    )
```

### Using Different AI Models

Change the model in `parser_generator/agent.py`:

```python
# Use Claude Opus for better quality
llm = ChatAnthropic(
    model="claude-opus-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Or use a different provider
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4")
```

## Troubleshooting

### Issue: Parser not found for institution

```bash
# Check configuration
venv/bin/python parser_loader.py list

# Test file detection
venv/bin/python parser_loader.py test "path/to/file.pdf"

# Add missing institution
venv/bin/python parser_loader.py add InstitutionName ParserClass parsers.module
```

### Issue: Generated parser has errors

1. Review the analysis report: `parsers/<institution>_analysis.md`
2. Check if PDFs have consistent format
3. Edit the generated parser manually
4. Run parser generator again with more/different sample PDFs

### Issue: Parser extracts wrong data

1. Check regex patterns in generated code
2. Print intermediate values for debugging
3. Update the parser class manually
4. Test with multiple statement PDFs

## Best Practices

1. **Use 3-5 sample PDFs** - Include statements from different months/types
2. **Review generated code** - Always check before production use
3. **Test thoroughly** - Test with all statement variations
4. **Version control** - Commit generated parsers to git
5. **Document changes** - If you edit generated code, document why

## Integration with Existing System

The parser generator integrates seamlessly:

1. **BaseStatementParser** - All generated parsers inherit from this
2. **Database** - Uses existing `save_statement_data()` workflow
3. **Classification** - Uses existing `classify_security()` method
4. **Utilities** - Uses `clean_currency_value()`, `parse_date()`, etc.

No changes needed to:
- Database schema
- Analysis code
- Visualization code
- Report generation

## Cost Considerations

Each parser generation uses Claude API:
- Analysis phase: ~10-20K tokens
- Code generation: ~30-50K tokens
- Total cost: ~$0.50-$2.00 per parser (Claude Sonnet)

Consider:
- Using Claude Sonnet for cost efficiency
- Generating parsers in batches
- Caching successful generations

## Future Enhancements

Potential improvements:
1. **Automatic testing** - Generate unit tests for parsers
2. **Validation** - Verify extracted data against known values
3. **Iteration** - Auto-fix common errors and regenerate
4. **Web UI** - Upload PDFs and get parser in browser
5. **Template library** - Learn from successful parsers

## Comparison: Manual vs. Automatic

### Manual Parser Creation (Old Way)
- Time: 2-4 hours per institution
- Requires: PDF analysis, regex expertise, Python knowledge
- Error-prone: Easy to miss edge cases
- Maintenance: Updates require code changes

### Automatic Parser Generation (New Way)
- Time: 5-10 minutes per institution
- Requires: Sample PDFs, API key
- AI-assisted: Analyzes patterns comprehensively
- Maintenance: Regenerate when format changes

## Support

For issues or questions:
1. Check this README
2. Review existing parsers in `parsers/` directory
3. Check CrewAI documentation: https://docs.crewai.com
4. Review agent prompts in `parser_generator/agent.py`

## License

Same as the main application.
