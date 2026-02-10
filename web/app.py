"""
Flask web application for natural language portfolio queries.
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from config import DB_CONFIG

# Import web modules (use relative imports when running as module)
try:
    from web.nl_to_sql import NLToSQLConverter
    from web.sql_validator import SQLValidator
    from web.code_generator import CodeGenerator
except ImportError:
    # Fallback for direct execution
    from nl_to_sql import NLToSQLConverter
    from sql_validator import SQLValidator
    from code_generator import CodeGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize components (with error handling)
try:
    db_manager = DatabaseManager(DB_CONFIG)
    logger.info("Database manager initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database manager: {e}")
    db_manager = None

try:
    nl_converter = NLToSQLConverter()
    logger.info("NL to SQL converter initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize NL converter: {e}")
    nl_converter = None

try:
    sql_validator = SQLValidator()
    code_generator = CodeGenerator()
    logger.info("Validators initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize validators: {e}")
    sql_validator = None
    code_generator = None


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors and return JSON."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error', 'details': str(error)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors and return JSON."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions and return JSON."""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify server and components are working."""
    status = {
        'server': 'running',
        'database': 'unknown',
        'nl_converter': 'unknown',
        'sql_validator': 'unknown',
        'code_generator': 'unknown'
    }
    
    # Check database
    if db_manager:
        try:
            # Simple query to test connection
            db_manager.execute_query("SELECT 1", None, fetch=True)
            status['database'] = 'connected'
        except Exception as e:
            status['database'] = f'error: {str(e)}'
    else:
        status['database'] = 'not_initialized'
    
    # Check other components
    status['nl_converter'] = 'initialized' if nl_converter else 'not_initialized'
    status['sql_validator'] = 'initialized' if sql_validator else 'not_initialized'
    status['code_generator'] = 'initialized' if code_generator else 'not_initialized'
    
    all_ok = all(v in ['running', 'connected', 'initialized'] for v in status.values())
    
    return jsonify(status), 200 if all_ok else 503


@app.route('/api/query', methods=['POST'])
def query():
    """
    Execute a natural language query.

    Request body:
        {
            "query": "natural language query",
            "generate_code": false  // optional, if true, generate Python code
        }
    """
    try:
        # Check if components are initialized
        if not db_manager:
            return jsonify({'error': 'Database manager not initialized. Check database connection.'}), 500
        if not nl_converter:
            return jsonify({'error': 'NL converter not initialized.'}), 500
        if not sql_validator:
            return jsonify({'error': 'SQL validator not initialized.'}), 500
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400

        natural_query = data['query']
        generate_code = data.get('generate_code', False)

        logger.info(f"Processing query: {natural_query}")

        # Convert natural language to SQL
        conversion_result = nl_converter.convert_to_sql(natural_query)

        if conversion_result.get('error'):
            return jsonify({
                'error': conversion_result['error'],
                'sql': None,
                'data': None
            }), 400

        sql = conversion_result['sql']
        params = conversion_result.get('params', [])

        # Validate SQL
        is_valid, error_msg = sql_validator.validate(sql)
        if not is_valid:
            return jsonify({
                'error': f'Invalid SQL query: {error_msg}',
                'sql': sql,
                'data': None
            }), 400

        # Sanitize SQL
        sql = sql_validator.sanitize(sql)

        # Execute query
        try:
            # Note: params are already replaced in SQL by _replace_placeholders,
            # so we pass None for query_params
            results = db_manager.execute_query(sql, None, fetch=True)

            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(results)

            # Convert Decimal and other non-JSON types to JSON-serializable types
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        # Try to convert to numeric (handles Decimal)
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        # If conversion fails, try to convert Decimal objects manually
                        try:
                            from decimal import Decimal
                            df[col] = df[col].apply(lambda x: float(x) if isinstance(x, Decimal) else x)
                        except:
                            pass

            # Convert to JSON-serializable format using pandas to_json which handles types better
            import json
            json_str = df.to_json(orient='records', date_format='iso')
            data = json.loads(json_str)

            response = {
                'sql': sql,
                'params': params,
                'data': data,
                'row_count': len(data),
                'columns': list(df.columns) if not df.empty else [],
                'explanation': conversion_result.get('explanation', '')
            }

            # Generate code if requested
            if generate_code:
                method_name = natural_query.lower().replace(' ', '_').replace('?', '')
                method_code = code_generator.generate_method(
                    method_name,
                    natural_query,
                    sql,
                    return_type="pd.DataFrame" if len(data) > 1 else "Dict"
                )
                response['generated_code'] = method_code

            return jsonify(response)

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return jsonify({
                'error': f'Database error: {str(e)}',
                'sql': sql,
                'data': None
            }), 500

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_code', methods=['POST'])
def generate_code():
    """
    Generate Python code for a query and optionally add it to portfolio_analyzer.py.

    Request body:
        {
            "method_name": "get_custom_analysis",
            "description": "Description of what this does",
            "sql": "SELECT ...",
            "add_to_file": false  // optional, if true, add to portfolio_analyzer.py
        }
    """
    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({'error': 'Missing SQL parameter'}), 400

        method_name = data.get('method_name', 'get_custom_analysis')
        description = data.get('description', 'Custom analysis method')
        sql = data['sql']
        add_to_file = data.get('add_to_file', False)

        # Validate SQL
        is_valid, error_msg = sql_validator.validate(sql)
        if not is_valid:
            return jsonify({
                'error': f'Invalid SQL query: {error_msg}'
            }), 400

        # Generate code
        return_type = data.get('return_type', 'pd.DataFrame')
        method_code = code_generator.generate_method(
            method_name,
            description,
            sql,
            return_type
        )

        response = {
            'method_code': method_code,
            'method_name': method_name
        }

        # Add to file if requested
        if add_to_file:
            success = code_generator.add_method_to_analyzer(method_code)
            response['added_to_file'] = success
            if not success:
                response['error'] = 'Failed to add method to file'

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/schema', methods=['GET'])
def get_schema():
    """Get database schema information."""
    try:
        # Get table names
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """
        tables = db_manager.execute_query(tables_query, None, fetch=True)

        schema_info = []
        for table in tables:
            table_name = table['table_name']
            # Get columns
            columns_query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            columns = db_manager.execute_query(columns_query, None, fetch=True)
            schema_info.append({
                'table': table_name,
                'columns': [dict(col) for col in columns]
            })

        return jsonify({'schema': schema_info})

    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example queries."""
    examples = [
        {
            'query': 'Show me my current portfolio allocation by asset category',
            'description': 'Get allocation breakdown by asset type'
        },
        {
            'query': 'What are my top 10 holdings by value?',
            'description': 'List top holdings'
        },
        {
            'query': 'Show me portfolio value over the last 6 months',
            'description': 'Time series analysis'
        },
        {
            'query': 'What is my total portfolio value?',
            'description': 'Simple aggregation'
        },
        {
            'query': 'Show me holdings for Scotiabank accounts',
            'description': 'Filter by institution'
        },
        {
            'query': 'What is my allocation by institution?',
            'description': 'Group by institution'
        }
    ]
    return jsonify({'examples': examples})


# ==================== Multi-Agent API Endpoints ====================

@app.route('/api/v2/comprehensive-review', methods=['POST'])
def comprehensive_review():
    """
    Get comprehensive financial review from all agents.

    Request body:
        {
            "user_context": {
                "tax_rate": float,        // 0.0 - 1.0
                "province": string,       // e.g., "ON", "BC", "AB"
                "age": int,              // optional
                "risk_profile": string,  // "conservative", "moderate", "aggressive"
                "tax_bracket": string    // "low", "mid", "high"
            }
        }
    """
    try:
        from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

        data = request.get_json()
        user_context = data.get('user_context', {})

        # Validate required fields
        if 'tax_rate' not in user_context:
            user_context['tax_rate'] = 0.30  # Default
        if 'province' not in user_context:
            user_context['province'] = 'ON'  # Default

        logger.info(f"Processing comprehensive review with context: {user_context}")

        # Execute comprehensive review
        flow = FinancialAdvisoryFlow()
        results = flow.get_comprehensive_review(user_context)

        return jsonify(results)

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error in comprehensive review: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/agent-query', methods=['POST'])
def agent_query():
    """
    Process a natural language query through the multi-agent system.

    Request body:
        {
            "query": string,
            "user_context": {
                "tax_rate": float,
                "province": string,
                "age": int,
                "risk_profile": string
            },
            "workflow_type": "sequential"|"parallel"  // optional, default: sequential
        }
    """
    try:
        from multi_agent.flows.financial_advisory_flow import FinancialAdvisoryFlow

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400

        query = data['query']
        user_context = data.get('user_context', {})
        workflow_type = data.get('workflow_type', 'sequential')

        logger.info(f"Processing agent query: {query}")

        # Execute query through flow
        flow = FinancialAdvisoryFlow()
        results = flow.process_query(query, user_context, workflow_type)

        return jsonify(results)

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error processing agent query: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/portfolio-data', methods=['GET'])
def get_portfolio_data():
    """
    Get structured portfolio data from Portfolio Data Agent.

    Query parameters:
        institution: string (optional)
        account_number: string (optional)
        action: "get_all"|"get_summary"|"get_holdings"|"get_allocation" (default: get_all)
    """
    try:
        from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent

        # Get query parameters
        institution = request.args.get('institution')
        account_number = request.args.get('account_number')
        action = request.args.get('action', 'get_all')

        # Build request
        agent_request = {
            'action': action,
            'filters': {}
        }

        if institution:
            agent_request['filters']['institution'] = institution
        if account_number:
            agent_request['filters']['account_number'] = account_number

        logger.info(f"Fetching portfolio data: {agent_request}")

        # Get data from agent
        portfolio_agent = PortfolioDataAgent()
        portfolio_data = portfolio_agent.process_request(agent_request)

        # Convert to dict for JSON serialization
        return jsonify(portfolio_data.dict())

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error fetching portfolio data: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/tax-analysis', methods=['POST'])
def tax_analysis():
    """
    Get tax optimization analysis from Tax Advisor Agent.

    Request body:
        {
            "user_context": {
                "tax_rate": float,
                "province": string,
                "age": int
            }
        }
    """
    try:
        from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent
        from multi_agent.agents.tax_advisor_agent import TaxAdvisorAgent

        data = request.get_json()
        user_context = data.get('user_context', {})

        logger.info(f"Processing tax analysis with context: {user_context}")

        # Get portfolio data first
        portfolio_agent = PortfolioDataAgent()
        portfolio_data = portfolio_agent.process_request({'action': 'get_all', 'filters': {}})

        # Run tax analysis
        tax_agent = TaxAdvisorAgent()
        tax_result = tax_agent.analyze_portfolio(portfolio_data.holdings, user_context)

        return jsonify(tax_result.dict())

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error in tax analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/estate-analysis', methods=['POST'])
def estate_analysis():
    """
    Get estate planning analysis from Estate Planner Agent.

    Request body:
        {
            "user_context": {
                "province": string,
                "age": int,
                "marital_status": string,
                "dependents": int
            }
        }
    """
    try:
        from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent
        from multi_agent.agents.estate_planner_agent import EstatePlannerAgent

        data = request.get_json()
        user_context = data.get('user_context', {})

        logger.info(f"Processing estate analysis with context: {user_context}")

        # Get portfolio data first
        portfolio_agent = PortfolioDataAgent()
        portfolio_data = portfolio_agent.process_request({'action': 'get_all', 'filters': {}})

        # Run estate analysis
        estate_agent = EstatePlannerAgent()
        estate_result = estate_agent.analyze_estate(
            portfolio_data.portfolio_summary,
            portfolio_data.holdings,
            user_context
        )

        return jsonify(estate_result.dict())

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error in estate analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v2/investment-analysis', methods=['POST'])
def investment_analysis():
    """
    Get investment analysis from Investment Analyst Agent.

    Request body:
        {
            "user_context": {
                "risk_profile": string,  // "conservative", "moderate", "aggressive"
                "investment_goals": []
            }
        }
    """
    try:
        from multi_agent.agents.portfolio_data_agent import PortfolioDataAgent
        from multi_agent.agents.investment_analyst_agent import InvestmentAnalystAgent

        data = request.get_json()
        user_context = data.get('user_context', {})

        logger.info(f"Processing investment analysis with context: {user_context}")

        # Get portfolio data first
        portfolio_agent = PortfolioDataAgent()
        portfolio_data = portfolio_agent.process_request({'action': 'get_all', 'filters': {}})

        # Run investment analysis
        investment_agent = InvestmentAnalystAgent()
        investment_result = investment_agent.analyze_investments(
            portfolio_data.holdings,
            portfolio_data.portfolio_summary,
            user_context
        )

        return jsonify(investment_result.dict())

    except ImportError as e:
        logger.error(f"Multi-agent system not available: {e}")
        return jsonify({
            'error': 'Multi-agent system not available. Please ensure multi_agent package is installed.',
            'details': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Error in investment analysis: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==================== Observability API (Multi-Agent Monitor) ====================

def _get_observability():
    """Lazy import of observability collector."""
    try:
        from multi_agent.observability.collector import get_observer
        return get_observer()
    except ImportError:
        return None


@app.route('/monitor')
def monitor_page():
    """Render the multi-agent observability monitor page."""
    return render_template('monitor.html')


@app.route('/api/observability/sessions', methods=['GET'])
def observability_list_sessions():
    """List recent observability sessions."""
    observer = _get_observability()
    if observer is None:
        return jsonify({'error': 'Observability not available', 'sessions': []}), 503
    limit = request.args.get('limit', 50, type=int)
    sessions = observer.list_sessions(limit=min(limit, 100))
    return jsonify({'sessions': sessions})


@app.route('/api/observability/sessions/<session_id>', methods=['GET'])
def observability_get_session(session_id):
    """Get a single observability session with all spans."""
    observer = _get_observability()
    if observer is None:
        return jsonify({'error': 'Observability not available'}), 503
    session = observer.get_session(session_id)
    if session is None:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

