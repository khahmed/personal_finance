# Portfolio Query Web Interface

A natural language query interface for your portfolio database. Ask questions in plain English and get SQL queries generated automatically, with the ability to create reusable analysis methods.

## Features

- **Natural Language Queries**: Ask questions about your portfolio in plain English
- **Automatic SQL Generation**: Uses LLM (DeepSeek, OpenAI GPT, or Anthropic Claude) to convert natural language to SQL
- **Safe Query Execution**: SQL validator ensures only SELECT queries are executed
- **Code Generation**: Automatically generate Python methods for portfolio_analyzer.py
- **Modern UI**: Clean, responsive web interface with example queries

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional but Recommended)

For best results, configure an LLM API key (priority order: DeepSeek > OpenAI > Anthropic):

**DeepSeek (Recommended - Cost-effective):**
```bash
export DEEPSEEK_API_KEY="your-api-key-here"
```

**OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Anthropic:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

If no API key is provided, the system will use a fallback rule-based SQL generator (less accurate but functional).

### 3. Configure Database

Ensure your database configuration in `config.py` is correct, or set environment variables:

```bash
export DB_HOST=localhost
export DB_NAME=portfolio_db
export DB_USER=bankapp
export DB_PASSWORD=your-password
export DB_PORT=5432
```

### 4. Run the Application

```bash
cd web
python app.py
```

Or from the project root:

```bash
python -m web.app
```

The application will be available at `http://localhost:5000`

## Usage

### Basic Query

1. Enter a natural language query in the text area
2. Click "Execute Query" or press Ctrl+Enter
3. View the generated SQL and results

### Example Queries

- "Show me my current portfolio allocation by asset category"
- "What are my top 10 holdings by value?"
- "Show me portfolio value over the last 6 months"
- "What is my total portfolio value?"
- "Show me holdings for Scotiabank accounts"
- "What is my allocation by institution?"

### Generating Code

1. Execute a query
2. Check "Generate Python code for this query" or click "Generate Code"
3. Review the generated Python method
4. Click "Add to portfolio_analyzer.py" to save it

The generated code will be added to `analysis/portfolio_analyzer.py` as a new method that can be reused.

## API Endpoints

### POST `/api/query`
Execute a natural language query.

**Request:**
```json
{
  "query": "Show me my top holdings",
  "generate_code": false
}
```

**Response:**
```json
{
  "sql": "SELECT ...",
  "params": [],
  "data": [...],
  "row_count": 10,
  "columns": ["security_name", "market_value", ...],
  "explanation": "...",
  "generated_code": "..." // if generate_code=true
}
```

### POST `/api/generate_code`
Generate Python code for a SQL query.

**Request:**
```json
{
  "method_name": "get_custom_analysis",
  "description": "Custom analysis",
  "sql": "SELECT ...",
  "add_to_file": false,
  "return_type": "pd.DataFrame"
}
```

### GET `/api/schema`
Get database schema information.

### GET `/api/examples`
Get example queries.

## Architecture

- **`app.py`**: Flask application with API endpoints
- **`nl_to_sql.py`**: Natural language to SQL converter using LLM
- **`sql_validator.py`**: SQL safety validator
- **`code_generator.py`**: Python code generator for analysis methods
- **`templates/index.html`**: Frontend HTML
- **`static/css/style.css`**: Styling
- **`static/js/app.js`**: Frontend JavaScript

## Security

- Only SELECT queries are allowed
- SQL injection protection through validation
- Parameterized queries for user inputs
- No DROP, DELETE, INSERT, UPDATE, or other dangerous operations

## Troubleshooting

### "No module named 'flask'"
Install dependencies: `pip install -r requirements.txt`

### "Database connection error"
Check your database configuration in `config.py` or environment variables.

### "API key not found"
The system will use rule-based conversion if no API key is provided. For better results, configure an OpenAI or Anthropic API key.

### Generated SQL is incorrect
- Try rephrasing your query
- Be more specific about what you want
- Check the example queries for patterns
- Consider using an LLM API key for better results

