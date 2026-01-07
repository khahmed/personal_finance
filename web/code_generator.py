"""
Code generator for creating/updating analysis methods in portfolio_analyzer.py.
"""

import os
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Generates Python analysis code from natural language descriptions."""

    def __init__(self, analyzer_path: str = None):
        """
        Initialize code generator.

        Args:
            analyzer_path: Path to portfolio_analyzer.py file
        """
        self.analyzer_path = analyzer_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'analysis',
            'portfolio_analyzer.py'
        )

    def generate_method(self, method_name: str, description: str, sql_query: str,
                       return_type: str = "pd.DataFrame") -> str:
        """
        Generate a Python method for portfolio analysis.

        Args:
            method_name: Name of the method (e.g., 'get_my_custom_analysis')
            description: Description of what the method does
            sql_query: SQL query to execute
            return_type: Return type (pd.DataFrame or Dict)

        Returns:
            Generated method code as string
        """
        # Convert method name to valid Python identifier
        method_name = re.sub(r'[^a-zA-Z0-9_]', '_', method_name)
        if not method_name.startswith('get_'):
            method_name = f'get_{method_name}'

        # Generate docstring
        docstring = f'        """\n        {description}\n\n        Returns:\n            {return_type} with analysis results\n        """'

        # Generate method code
        if return_type == "pd.DataFrame":
            code = f"""    def {method_name}(self) -> {return_type}:
        {docstring}
        query = \"\"\"{sql_query}\"\"\"
        data = self.db.execute_query(query, None, fetch=True)
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Convert Decimal to float for numeric columns
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass
        
        return df"""
        else:  # Dict
            code = f"""    def {method_name}(self) -> {return_type}:
        {docstring}
        query = \"\"\"{sql_query}\"\"\"
        data = self.db.execute_query(query, None, fetch=True)
        df = pd.DataFrame(data)
        
        if df.empty:
            return {{}}
        
        # Convert to dictionary format
        result = df.to_dict('records')
        return result[0] if len(result) == 1 else result"""

        return code

    def add_method_to_analyzer(self, method_code: str) -> bool:
        """
        Add a new method to portfolio_analyzer.py.

        Args:
            method_code: Complete method code to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing file
            with open(self.analyzer_path, 'r') as f:
                lines = f.readlines()

            # Find the end of the PortfolioAnalyzer class
            # Look for the last method (indented with 4 spaces) and insert after it
            insert_index = len(lines)
            
            # Find the last method definition in the class
            for i in range(len(lines) - 1, -1, -1):
                line = lines[i]
                # Check if this is a method definition (starts with 4 spaces and 'def ')
                if line.startswith('    def ') and not line.startswith('        def '):
                    # Found a method, now find where it ends
                    # Look for the next line that's not indented more than the method
                    method_indent = 4  # Methods are indented 4 spaces
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        if next_line.strip():  # Non-empty line
                            # Check if it's still part of the method (more indented) or a new method/class end
                            if next_line.startswith(' ' * (method_indent + 1)) or next_line.startswith(' ' * method_indent):
                                # Still in the method
                                j += 1
                                continue
                            else:
                                # End of method found
                                break
                        j += 1
                    insert_index = j
                    break

            # Insert the new method with proper spacing
            if insert_index < len(lines) and lines[insert_index - 1].strip():
                # Add blank line before if previous line is not blank
                lines.insert(insert_index, '\n')
                insert_index += 1
            
            # Split method_code into lines and insert
            method_lines = method_code.split('\n')
            for line in method_lines:
                lines.insert(insert_index, line + '\n')
                insert_index += 1

            # Write back
            with open(self.analyzer_path, 'w') as f:
                f.writelines(lines)

            logger.info(f"Successfully added method to {self.analyzer_path}")
            return True

        except Exception as e:
            logger.error(f"Error adding method to analyzer: {e}")
            return False

    def update_method_in_analyzer(self, method_name: str, new_code: str) -> bool:
        """
        Update an existing method in portfolio_analyzer.py.

        Args:
            method_name: Name of the method to update
            new_code: New method code

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.analyzer_path, 'r') as f:
                content = f.read()

            # Find the method
            pattern = rf'(    def {re.escape(method_name)}\(.*?\):.*?)(?=\n    def |\n\nclass |\Z)'
            match = re.search(pattern, content, re.DOTALL)

            if not match:
                logger.warning(f"Method {method_name} not found, adding as new method")
                return self.add_method_to_analyzer(new_code)

            # Replace the method
            new_content = content[:match.start()] + new_code + content[match.end():]

            with open(self.analyzer_path, 'w') as f:
                f.write(new_content)

            logger.info(f"Successfully updated method {method_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating method: {e}")
            return False

