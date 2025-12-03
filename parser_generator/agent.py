"""
Parser Generator Agent using CrewAI.
Automatically generates parser code for new financial institutions.
"""

import os
from pathlib import Path
from typing import Dict, List
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, DirectoryReadTool
from langchain_anthropic import ChatAnthropic

# Initialize Claude model for CrewAI
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


class ParserGeneratorAgent:
    """Agent that analyzes PDFs and generates parser code."""

    def __init__(self, statements_dir: str = "statements"):
        self.statements_dir = statements_dir
        self.file_read_tool = FileReadTool()
        self.dir_read_tool = DirectoryReadTool()

    def _create_analysis_agent(self) -> Agent:
        """Create an agent to analyze PDF statements."""
        return Agent(
            role="Financial Statement Analyzer",
            goal="Analyze PDF financial statements to understand their structure, "
                 "format, and data fields for parser generation",
            backstory="""You are an expert in analyzing financial documents from
            various institutions. You have deep knowledge of different statement formats,
            including RRSP, TFSA, and non-registered investment accounts. You can identify
            account numbers, dates, holdings, cash balances, and asset classifications.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[self.file_read_tool, self.dir_read_tool]
        )

    def _create_code_generation_agent(self) -> Agent:
        """Create an agent to generate parser code."""
        return Agent(
            role="Parser Code Generator",
            goal="Generate Python parser code that follows existing patterns and "
                 "integrates seamlessly with the existing codebase",
            backstory="""You are an expert Python developer specializing in PDF parsing
            and data extraction. You understand the pdfplumber library, regex patterns,
            and object-oriented design. You follow coding best practices and can generate
            clean, well-documented code that matches the existing codebase style.""",
            verbose=True,
            allow_delegation=False,
            llm=llm,
            tools=[self.file_read_tool]
        )

    def _create_analysis_task(self, agent: Agent, institution_name: str,
                             pdf_files: List[str]) -> Task:
        """Create a task to analyze PDF statements."""
        pdf_list = "\n".join([f"  - {pdf}" for pdf in pdf_files])

        return Task(
            description=f"""Analyze the PDF statements for {institution_name} and extract:

1. **Document Structure**:
   - How is the institution name displayed?
   - Where is the account number located and what format does it use?
   - How are dates formatted (statement date, period start, period end)?
   - What are the section headers (e.g., "Portfolio Assets", "Holdings", "Account Summary")?

2. **Account Information**:
   - Account number format and location
   - Account type identification (RRSP, TFSA, Non-Registered, etc.)
   - Statement date and period extraction patterns

3. **Holdings Information**:
   - How are holdings listed? (table format, line-by-line, multi-line entries)
   - What columns are present? (security name, quantity, price, book value, market value)
   - Are there category headers? (Equities, Fixed Income, Cash, etc.)
   - Are there special characters or formatting quirks? (e.g., 'ƒ' for transferred securities)
   - How to distinguish between different currencies (CAD vs USD)?

4. **Financial Data**:
   - Total portfolio value location and format
   - Cash balance location and format
   - Currency indicators

5. **Special Cases**:
   - Multi-line entries
   - Special characters
   - Multiple account types in different formats
   - Currency sections

PDF files to analyze:
{pdf_list}

Based on the analysis, provide a detailed specification document that will be used
to generate the parser code.""",
            expected_output="""A detailed specification document containing:
- Institution name pattern
- Account number regex patterns with examples
- Account type detection logic
- Date extraction patterns
- Holdings parsing strategy (regex patterns, line-by-line logic)
- Category detection patterns
- Currency handling approach
- Special cases and edge cases to handle
- Example text snippets from the PDFs showing each pattern""",
            agent=agent
        )

    def _create_code_generation_task(self, agent: Agent, institution_name: str,
                                    analysis_output: str) -> Task:
        """Create a task to generate parser code."""

        # Read example parsers to use as templates
        example_parser_path = Path("parsers/cibc_investorsedge_parser.py")
        base_parser_path = Path("parsers/base_parser.py")

        return Task(
            description=f"""Generate a complete Python parser class for {institution_name}
based on the analysis provided. Follow these requirements:

1. **Code Structure**:
   - Inherit from BaseStatementParser
   - Implement required abstract methods: parse(), extract_account_info(), extract_holdings()
   - Use pdfplumber for PDF extraction
   - Follow the exact same structure as existing parsers

2. **Patterns to Follow**:
   - Study these example files:
     * parsers/base_parser.py - base class with utility methods
     * parsers/cibc_investorsedge_parser.py - reference implementation
     * parsers/scotiabank_parser.py - another reference

3. **Key Implementation Details**:
   - Use regex patterns to extract account number, dates, and values
   - Handle currency detection (CAD vs USD)
   - Use classify_security() from base class for asset classification
   - Handle multi-line entries if needed
   - Clean currency values using clean_currency_value()
   - Parse dates using parse_date()

4. **Code Quality**:
   - Include docstrings for class and all methods
   - Add inline comments explaining complex regex patterns
   - Handle edge cases identified in the analysis
   - Use descriptive variable names
   - Follow PEP 8 style guidelines

5. **Testing Considerations**:
   - Include examples in comments showing what regex patterns match
   - Handle missing or optional fields gracefully

Analysis provided:
{analysis_output}

Reference the existing parser files in the parsers/ directory and follow their
exact structure and patterns. The generated code should be production-ready.""",
            expected_output=f"""Complete Python parser code for {institution_name}Parser class
that can be directly saved to parsers/{institution_name.lower()}_parser.py file.
The code should:
- Be properly formatted with correct indentation
- Include all necessary imports
- Have complete docstrings
- Handle all cases identified in the analysis
- Follow the exact same patterns as existing parsers""",
            agent=agent
        )

    def generate_parser(self, institution_name: str) -> Dict[str, str]:
        """
        Generate parser code for a new institution.

        Args:
            institution_name: Name of the institution (should match directory name)

        Returns:
            Dictionary with 'analysis' and 'code' keys containing the results
        """
        # Find PDF files for this institution
        institution_dir = Path(self.statements_dir) / institution_name
        if not institution_dir.exists():
            raise ValueError(f"Institution directory not found: {institution_dir}")

        pdf_files = list(institution_dir.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {institution_dir}")

        print(f"\nFound {len(pdf_files)} PDF files for {institution_name}")
        print(f"Files: {[pdf.name for pdf in pdf_files]}")

        # Create agents
        analysis_agent = self._create_analysis_agent()
        code_agent = self._create_code_generation_agent()

        # Create tasks
        analysis_task = self._create_analysis_task(
            analysis_agent,
            institution_name,
            [str(pdf) for pdf in pdf_files]
        )

        # First crew: Analyze PDFs
        print(f"\n{'='*80}")
        print(f"STEP 1: Analyzing {institution_name} PDF statements...")
        print(f"{'='*80}\n")

        analysis_crew = Crew(
            agents=[analysis_agent],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )

        analysis_result = analysis_crew.kickoff()
        analysis_output = str(analysis_result)

        # Create code generation task with analysis results
        code_task = self._create_code_generation_task(
            code_agent,
            institution_name,
            analysis_output
        )

        # Second crew: Generate code
        print(f"\n{'='*80}")
        print(f"STEP 2: Generating parser code for {institution_name}...")
        print(f"{'='*80}\n")

        code_crew = Crew(
            agents=[code_agent],
            tasks=[code_task],
            process=Process.sequential,
            verbose=True
        )

        code_result = code_crew.kickoff()
        code_output = str(code_result)

        return {
            'analysis': analysis_output,
            'code': code_output,
            'institution': institution_name
        }

    def save_parser(self, result: Dict[str, str], output_dir: str = "parsers") -> str:
        """
        Save the generated parser code to a file.

        Args:
            result: Dictionary from generate_parser()
            output_dir: Directory to save the parser file

        Returns:
            Path to the saved file
        """
        institution = result['institution']
        code = result['code']

        # Extract just the Python code from the output (remove any markdown formatting)
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        # Save the parser file
        output_path = Path(output_dir) / f"{institution.lower()}_parser.py"
        with open(output_path, 'w') as f:
            f.write(code)

        print(f"\n{'='*80}")
        print(f"Parser code saved to: {output_path}")
        print(f"{'='*80}\n")

        # Save the analysis for reference
        analysis_path = Path(output_dir) / f"{institution.lower()}_analysis.md"
        with open(analysis_path, 'w') as f:
            f.write(f"# Analysis for {institution}\n\n")
            f.write(result['analysis'])

        print(f"Analysis saved to: {analysis_path}\n")

        return str(output_path)


def main():
    """Main entry point for parser generation."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser_generator/agent.py <institution_name>")
        print("\nExample: python parser_generator/agent.py TD")
        print("\nThe institution name should match a subdirectory in the statements/ folder.")
        sys.exit(1)

    institution_name = sys.argv[1]

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        sys.exit(1)

    try:
        generator = ParserGeneratorAgent()
        result = generator.generate_parser(institution_name)
        parser_path = generator.save_parser(result)

        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print(f"\nGenerated parser: {parser_path}")
        print(f"\nNext steps:")
        print(f"1. Review the generated parser code in {parser_path}")
        print(f"2. Test the parser: python -c \"from parsers.{institution_name.lower()}_parser import *; parser = {institution_name}Parser('statements/{institution_name}/sample.pdf'); print(parser.parse())\"")
        print(f"3. If it works, add it to parsers/__init__.py")
        print(f"4. Update institutions.yaml configuration")
        print(f"5. Run: python process_statements.py process")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
