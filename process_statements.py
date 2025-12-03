#!/usr/bin/env python3
"""
Main script to process financial statements and load data into database.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from database import DatabaseManager
from analysis import PortfolioAnalyzer
from visualization import PortfolioVisualizer
from parser_loader import ParserLoader
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_parser_for_file(file_path: str, parser_loader: ParserLoader):
    """
    Determine which parser to use based on file path using dynamic loader.

    Args:
        file_path: Path to the PDF file
        parser_loader: ParserLoader instance

    Returns:
        Appropriate parser class
    """
    return parser_loader.get_parser_for_file(file_path)


def process_pdf_file(file_path: str, db_manager: DatabaseManager,
                     parser_loader: ParserLoader) -> bool:
    """
    Process a single PDF file.

    Args:
        file_path: Path to the PDF file
        db_manager: DatabaseManager instance
        parser_loader: ParserLoader instance

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing file: {file_path}")

        # Get appropriate parser
        parser_class = get_parser_for_file(file_path, parser_loader)

        if not parser_class:
            logger.warning(f"Could not determine parser for file: {file_path}")
            logger.warning(f"  Make sure the institution has a parser configured in institutions.yaml")
            return False

        # Parse the PDF
        parser = parser_class(file_path)
        statement_data = parser.parse()

        # Add file path to statement data
        statement_data['file_path'] = file_path

        # Validate required fields
        if not statement_data.get('account_number'):
            logger.warning(f"No account number found in {file_path}")
            return False

        if not statement_data.get('statement_date'):
            logger.warning(f"No statement date found in {file_path}")
            return False

        # Save to database
        db_manager.save_statement_data(statement_data)

        logger.info(f"Successfully processed {file_path}")
        logger.info(f"  Institution: {statement_data.get('institution')}")
        logger.info(f"  Account: {statement_data.get('account_number')}")
        logger.info(f"  Date: {statement_data.get('statement_date')}")
        logger.info(f"  Holdings: {len(statement_data.get('holdings', []))}")

        return True

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def find_pdf_files(directory: str) -> List[str]:
    """
    Find all PDF files in directory and subdirectories.

    Args:
        directory: Root directory to search

    Returns:
        List of PDF file paths
    """
    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))

    return sorted(pdf_files)


def process_all_statements(statements_dir: str, db_config: dict):
    """
    Process all PDF statements in the directory.

    Args:
        statements_dir: Directory containing statements
        db_config: Database configuration dictionary
    """
    logger.info(f"Starting to process statements from {statements_dir}")

    # Initialize database manager and parser loader
    db_manager = DatabaseManager(db_config)
    parser_loader = ParserLoader()

    # Find all PDF files
    pdf_files = find_pdf_files(statements_dir)
    logger.info(f"Found {len(pdf_files)} PDF files")

    if not pdf_files:
        logger.warning("No PDF files found!")
        return

    # Process each file
    successful = 0
    failed = 0

    for pdf_file in pdf_files:
        if process_pdf_file(pdf_file, db_manager, parser_loader):
            successful += 1
        else:
            failed += 1

    # Summary
    logger.info("=" * 80)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total files: {len(pdf_files)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 80)

    # Close database connections
    db_manager.close_all_connections()


def generate_reports(db_config: dict, output_dir: str = 'reports'):
    """
    Generate analysis reports and charts.

    Args:
        db_config: Database configuration dictionary
        output_dir: Directory to save reports
    """
    logger.info("Generating portfolio reports...")

    # Initialize components
    db_manager = DatabaseManager(db_config)
    analyzer = PortfolioAnalyzer(db_manager)
    visualizer = PortfolioVisualizer(analyzer)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate dashboard
    visualizer.create_dashboard(output_dir)

    logger.info(f"Reports generated in {output_dir}")

    # Close database connections
    db_manager.close_all_connections()


def reset_database(db_config: dict, reset_type: str = 'data'):
    """
    Reset database tables.

    Args:
        db_config: Database configuration dictionary
        reset_type: 'data' to reset only data tables, 'all' to reset everything
    """
    db_manager = DatabaseManager(db_config)

    if reset_type == 'all':
        logger.warning("=" * 80)
        logger.warning("WARNING: This will delete ALL data including reference tables!")
        logger.warning("=" * 80)
        response = input("Are you sure you want to reset ALL tables? Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            db_manager.reset_all_tables(confirm=True)
            logger.info("All tables have been reset")
        else:
            logger.info("Reset cancelled")
    else:
        logger.warning("=" * 80)
        logger.warning("This will delete statements, holdings, and cash balances")
        logger.warning("Reference data (institutions, accounts, securities, asset_types) will be preserved")
        logger.warning("=" * 80)
        response = input("Are you sure you want to reset data tables? Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            db_manager.reset_data_tables(confirm=True)
            logger.info("Data tables have been reset")
        else:
            logger.info("Reset cancelled")

    db_manager.close_all_connections()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process financial statements and generate portfolio reports'
    )
    parser.add_argument(
        'command',
        choices=['process', 'report', 'all', 'reset'],
        help='Command to execute: process statements, generate reports, both, or reset database'
    )
    parser.add_argument(
        '--statements-dir',
        default='statements',
        help='Directory containing PDF statements (default: statements)'
    )
    parser.add_argument(
        '--output-dir',
        default='reports',
        help='Directory for output reports (default: reports)'
    )
    parser.add_argument(
        '--db-config',
        help='Path to database configuration file (default: use config.py)'
    )
    parser.add_argument(
        '--reset-type',
        choices=['data', 'all'],
        default='data',
        help='Type of reset: data (statements/holdings only) or all (everything) (default: data)'
    )

    args = parser.parse_args()

    # Get database configuration
    if args.db_config:
        import json
        with open(args.db_config, 'r') as f:
            db_config = json.load(f)
    else:
        db_config = config.DB_CONFIG

    # Execute command
    try:
        if args.command == 'reset':
            reset_database(db_config, args.reset_type)

        elif args.command == 'process':
            process_all_statements(args.statements_dir, db_config)

        elif args.command == 'report':
            generate_reports(db_config, args.output_dir)

        elif args.command == 'all':
            process_all_statements(args.statements_dir, db_config)
            generate_reports(db_config, args.output_dir)

        logger.info("Done!")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()
