# LLM Integration Setup Guide

The multi-agent system now supports LLM-enhanced analysis using Anthropic Claude or DeepSeek APIs.

## Features

- **Automatic LLM Detection**: System automatically detects available API keys
- **Enhanced Analysis**: Agents use LLM to provide deeper insights and recommendations
- **Fallback Support**: Works without LLM (uses rule-based analysis)
- **Dual Provider Support**: Supports both Anthropic and DeepSeek

## Setup

### Option 1: DeepSeek (Recommended - Cost-Effective)

1. Get your API key from [DeepSeek](https://platform.deepseek.com/)

2. Set environment variable:
   ```bash
   export DEEPSEEK_API_KEY="your-deepseek-api-key"
   ```

3. Install dependencies (if not already installed):
   ```bash
   pip install openai  # DeepSeek uses OpenAI-compatible API
   ```

### Option 2: Anthropic Claude

1. Get your API key from [Anthropic](https://console.anthropic.com/)

2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-anthropic-api-key"
   ```

3. Install dependencies (already in requirements.txt):
   ```bash
   pip install anthropic langchain-anthropic
   ```

## Priority Order

The system checks for API keys in this order:
1. **DeepSeek** (if `DEEPSEEK_API_KEY` is set)
2. **Anthropic** (if `ANTHROPIC_API_KEY` is set and DeepSeek is not)

## Usage

### Basic Usage

Simply set the environment variable and run:

```bash
export DEEPSEEK_API_KEY="your-key"
python -m multi_agent.main
```

The system will automatically:
- Detect the API key
- Use LLM to enhance analysis
- Add `llm_insights` to agent outputs

### Programmatic Usage

```python
from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

# LLM will be automatically detected from environment
flow = FinancialAdvisoryFlow()
results = flow.get_comprehensive_review({
    "tax_rate": 0.30,
    "province": "ON"
})

# Check if LLM was used
if results.get('tax_analysis', {}).get('llm_insights'):
    print("LLM-enhanced analysis available!")
    insights = results['tax_analysis']['llm_insights']
    print(f"Provider: {insights['llm_provider']}")
    print(f"Explanation: {insights['explanation']}")
    print(f"Recommendations: {insights['recommendations']}")
```

### Custom Model Selection

You can specify a model when creating agents:

```python
from multi_agent.agents.tax_advisor_agent import TaxAdvisorAgent

agent = TaxAdvisorAgent(model="deepseek-chat")  # or "claude-3-opus-20240229"
```

## Output Structure

When LLM is available, agent outputs include an `llm_insights` field:

```python
{
    "tax_optimization_report": {...},
    "recommendations": [...],
    "llm_insights": {
        "explanation": "Natural language explanation of the analysis...",
        "recommendations": [
            {
                "priority": "High",
                "action": "Specific action to take",
                "rationale": "Why this recommendation",
                "impact": "Expected impact"
            }
        ],
        "llm_provider": "DeepSeek"  # or "Anthropic"
    }
}
```

## What LLM Enhances

### Tax Advisor Agent
- Provides natural language explanations of tax strategies
- Generates additional recommendations based on portfolio context
- Explains complex tax concepts in simple terms

### Estate Planner Agent
- Explains estate planning strategies
- Provides context-aware product recommendations
- Clarifies probate and beneficiary considerations

### Investment Analyst Agent
- Explains portfolio health scores
- Provides market context and trends
- Generates actionable investment recommendations

## Troubleshooting

### LLM Not Being Used

1. **Check API Key**:
   ```bash
   echo $DEEPSEEK_API_KEY  # or $ANTHROPIC_API_KEY
   ```

2. **Check Logs**: Look for messages like:
   ```
   Tax Advisor Agent: LLM available (DeepSeek)
   Tax Advisor Agent: Enhancing analysis with LLM
   ```

3. **Verify Installation**:
   ```bash
   pip list | grep -E "(openai|anthropic)"
   ```

### API Errors

- **Rate Limits**: Both providers have rate limits. The system will log errors but continue with rule-based analysis.
- **Invalid Key**: Check that your API key is correct and has proper permissions.
- **Network Issues**: Ensure you have internet connectivity.

### Cost Considerations

- **DeepSeek**: Very cost-effective, good for high-volume usage
- **Anthropic**: Higher cost but excellent quality, best for critical analysis

## Disabling LLM

To disable LLM and use only rule-based analysis:

```bash
unset DEEPSEEK_API_KEY
unset ANTHROPIC_API_KEY
python -m multi_agent.main
```

The system will work perfectly fine without LLM - it just won't have the enhanced insights.

## Best Practices

1. **Start with DeepSeek**: It's cost-effective and works well for most use cases
2. **Use Anthropic for Critical Analysis**: When you need the highest quality insights
3. **Monitor API Usage**: Both providers have usage dashboards
4. **Cache Results**: Consider caching LLM responses for repeated queries
5. **Error Handling**: The system gracefully falls back to rule-based analysis if LLM fails

## Example Output

With LLM enabled, you'll see additional insights:

```
Tax Analysis:
  Unrealized Gains: $50,000.00
  Unrealized Losses: $10,000.00
  Estimated Tax Liability: $7,500.00
  Potential Tax Savings: $1,500.00

  LLM Insights (DeepSeek):
    Based on your portfolio analysis, you have significant unrealized 
    capital gains that could result in substantial tax liability. 
    Consider tax-loss harvesting strategies...
```

Without LLM, you'll see:
```
Note: Using rule-based analysis (set DEEPSEEK_API_KEY or ANTHROPIC_API_KEY for LLM enhancement)
```

