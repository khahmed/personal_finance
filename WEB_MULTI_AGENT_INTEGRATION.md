# Web UI Multi-Agent Integration

## Overview

This document describes the integration of the multi-agent system into the web UI. The web interface now provides two modes:

1. **SQL Queries Mode** - Original functionality for natural language to SQL conversion
2. **Multi-Agent Analysis Mode** - New functionality for comprehensive financial analysis using specialized AI agents

## Architecture

### API Endpoints

The following API endpoints have been added to `web/app.py`:

#### 1. `/api/v2/comprehensive-review` (POST)
Get comprehensive financial analysis from all agents (Tax, Estate, Investment).

**Request:**
```json
{
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55,
    "risk_profile": "moderate"
  }
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "portfolio_data": { ... },
  "tax_analysis": { ... },
  "estate_analysis": { ... },
  "investment_analysis": { ... },
  "workflow_state": { ... }
}
```

#### 2. `/api/v2/agent-query` (POST)
Process natural language queries through the multi-agent system.

**Request:**
```json
{
  "query": "What's the most tax-efficient way to withdraw $50,000?",
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON"
  },
  "workflow_type": "sequential"
}
```

#### 3. `/api/v2/portfolio-data` (GET)
Get structured portfolio data from the Portfolio Data Agent.

**Query Parameters:**
- `institution` (optional)
- `account_number` (optional)
- `action`: "get_all", "get_summary", "get_holdings", "get_allocation"

#### 4. `/api/v2/tax-analysis` (POST)
Get tax optimization analysis.

**Request:**
```json
{
  "user_context": {
    "tax_rate": 0.30,
    "province": "ON",
    "age": 55
  }
}
```

#### 5. `/api/v2/estate-analysis` (POST)
Get estate planning analysis.

**Request:**
```json
{
  "user_context": {
    "province": "ON",
    "age": 55,
    "marital_status": "married",
    "dependents": 2
  }
}
```

#### 6. `/api/v2/investment-analysis` (POST)
Get investment analysis and rebalancing recommendations.

**Request:**
```json
{
  "user_context": {
    "risk_profile": "moderate",
    "investment_goals": ["retirement", "growth"]
  }
}
```

## User Interface

### Mode Selector

The UI features a toggle between two modes:
- **SQL Queries** - Original functionality
- **Multi-Agent Analysis** - New multi-agent functionality

### Multi-Agent Mode Components

#### 1. User Context Form
Collects user-specific information:
- **Tax Rate (%)** - User's marginal tax rate (0-100)
- **Province** - Canadian province for provincial tax calculations
- **Age** - Optional, for age-specific planning
- **Risk Profile** - Conservative, Moderate, or Aggressive

#### 2. Analysis Type Buttons
Five analysis types available:
- **Comprehensive Review** - All agents (Tax + Estate + Investment)
- **Tax Analysis** - Tax optimization and loss harvesting
- **Estate Planning** - Product recommendations and structure
- **Investment Analysis** - Securities analysis and rebalancing
- **Portfolio Data** - Structured data access

#### 3. Natural Language Query
Text area for complex questions that agents will analyze using the user context.

#### 4. Results Display
Results are displayed in cards with:
- Portfolio summary metrics
- Agent-specific analysis
- Recommendations with priority levels
- LLM insights (if LLM is configured)

## Integration with Existing Functionality

The multi-agent system **preserves** all existing SQL query functionality. Users can switch between modes seamlessly.

### Portfolio Data Agent as SQL Enhancement

The Portfolio Data Agent provides an alternative to direct SQL queries:

| Feature | SQL Mode | Portfolio Data Agent |
|---------|----------|---------------------|
| **Query Type** | Natural language → SQL | Pre-built methods |
| **Data Access** | Direct SELECT queries | Agent abstraction |
| **Calculations** | Basic aggregations | Full analytics |
| **Context** | Query results only | Data + business logic |
| **Safety** | SQL validator | Parameterized + validated |

## Configuration

### Environment Variables

To enable LLM-enhanced analysis, set one of:
```bash
export DEEPSEEK_API_KEY="your-key"      # Recommended (cost-effective)
export OPENAI_API_KEY="your-key"        # Alternative
export ANTHROPIC_API_KEY="your-key"     # Alternative
```

### Dependencies

The multi-agent system requires:
```
crewai>=0.28.8
langchain
pydantic
anthropic  # or openai
```

## Usage Examples

### Example 1: Comprehensive Review

1. Navigate to the web UI at `http://localhost:5000`
2. Click "Multi-Agent Analysis" mode
3. Set user context (tax rate, province, age, risk profile)
4. Click "Comprehensive Review"
5. View results for all three analyses

### Example 2: Tax-Specific Query

1. Switch to "Multi-Agent Analysis" mode
2. Set user context
3. Enter query: "What's the most tax-efficient way to withdraw $50,000?"
4. Click "Process with Agents"
5. View tax optimization recommendations

### Example 3: Portfolio Data Access

1. Switch to "Multi-Agent Analysis" mode
2. Click "Portfolio Data"
3. View structured portfolio summary

## Error Handling

The system gracefully handles errors:

- **503 Service Unavailable** - Multi-agent system not installed
- **500 Internal Error** - Agent processing error
- **400 Bad Request** - Missing required parameters

Error messages display in a red alert box with details.

## File Structure

```
web/
├── app.py                      # Flask app with multi-agent endpoints
├── templates/
│   └── index.html             # Updated with multi-agent UI
├── static/
│   ├── css/
│   │   └── style.css          # Updated with multi-agent styles
│   └── js/
│       └── app.js             # Updated with multi-agent JavaScript
├── nl_to_sql.py               # Existing SQL converter (preserved)
├── sql_validator.py           # Existing validator (preserved)
└── code_generator.py          # Existing generator (preserved)
```

## Key Design Decisions

### 1. Dual-Mode Interface
Chose to preserve SQL mode rather than replace it, allowing users to:
- Use simple SQL queries for basic data retrieval
- Use multi-agent system for complex financial analysis

### 2. User Context Form
User context is collected once and reused for all agent calls in a session, improving UX.

### 3. Individual vs. Comprehensive
Users can request:
- Individual agent analysis (faster, focused)
- Comprehensive review (slower, complete picture)

### 4. Progressive Enhancement
If multi-agent system is not installed, SQL mode continues to work. This allows for gradual deployment.

## Performance Considerations

- **Comprehensive Review**: ~5-10 seconds (sequential execution of 4 agents)
- **Individual Analysis**: ~2-3 seconds (single agent)
- **Portfolio Data**: <1 second (direct database access)

## Security

- All endpoints validate user input
- SQL injection prevented by Portfolio Data Agent's parameterized queries
- Read-only database access for agents
- API keys stored in environment variables (not in code)

## Future Enhancements

Potential improvements:
1. **Caching** - Cache portfolio data to reduce database queries
2. **Streaming** - Stream agent results as they complete
3. **Session Management** - Persist user context across sessions
4. **Export** - Export analysis results to PDF
5. **Comparison** - Compare multiple scenarios side-by-side
6. **Scheduling** - Schedule periodic comprehensive reviews

## Troubleshooting

### Multi-agent system not available
**Error:** "Multi-agent system not available. Please ensure multi_agent package is installed."

**Solution:**
```bash
cd /home/khalid/personal_finance
pip install crewai langchain pydantic
```

### LLM insights not showing
**Issue:** Results don't include LLM insights section

**Solution:** Set an LLM API key:
```bash
export DEEPSEEK_API_KEY="your-key"
```

### Agents taking too long
**Issue:** Comprehensive review takes >30 seconds

**Solution:**
- Use individual analyses instead
- Check database performance
- Verify network connectivity to LLM provider

## Testing

To test the integration:

```bash
# Start the web server
./run_web_app.sh
# OR
python -m web.app

# Access the UI
open http://localhost:5000

# Test SQL mode (original functionality)
1. Enter query: "Show me my top 10 holdings"
2. Click "Execute Query"
3. Verify results display

# Test multi-agent mode
1. Click "Multi-Agent Analysis"
2. Set tax rate: 30%
3. Select province: Ontario
4. Click "Comprehensive Review"
5. Verify all four cards display results
```

## API Testing with curl

```bash
# Test comprehensive review
curl -X POST http://localhost:5000/api/v2/comprehensive-review \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "tax_rate": 0.30,
      "province": "ON",
      "age": 55,
      "risk_profile": "moderate"
    }
  }'

# Test portfolio data
curl http://localhost:5000/api/v2/portfolio-data?action=get_summary

# Test tax analysis
curl -X POST http://localhost:5000/api/v2/tax-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "user_context": {
      "tax_rate": 0.30,
      "province": "ON"
    }
  }'
```

## Maintenance

### Updating Agent Behavior

To modify agent behavior, edit files in:
```
multi_agent/agents/
├── tax_advisor_agent.py
├── estate_planner_agent.py
└── investment_analyst_agent.py
```

Changes to agents will be reflected immediately (no web UI changes needed).

### Adding New Endpoints

To add new agent functionality:

1. Add endpoint to `web/app.py`
2. Update `web/static/js/app.js` with new handler
3. Update `web/templates/index.html` with new UI element
4. Update this documentation

## Support

For issues or questions:
- Check `/home/khalid/personal_finance/multi_agent/TROUBLESHOOTING.md`
- Check `/home/khalid/personal_finance/web/TROUBLESHOOTING.md`
- Review agent logs in console output
- Inspect browser console for JavaScript errors

## License

This integration follows the same license as the main project.
