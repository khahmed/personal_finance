"""
Dynamic Parser Loader
Loads parsers dynamically based on configuration file.
"""

import yaml
import importlib
from pathlib import Path
from typing import Optional, Type
from parsers.base_parser import BaseStatementParser


class ParserLoader:
    """Dynamically loads parser classes based on configuration."""

    def __init__(self, config_path: str = "institutions.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self._parser_cache = {}

    def _load_config(self) -> dict:
        """Load the institutions configuration file."""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Run the parser generator to create parsers for your institutions."
            )

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern."""
        filename_lower = filename.lower()

        if pattern == "*":
            return True

        # Simple keyword matching
        return pattern.lower() in filename_lower

    def _load_parser_class(self, module_path: str, class_name: str) -> Type[BaseStatementParser]:
        """Dynamically import and return parser class."""
        cache_key = f"{module_path}.{class_name}"

        if cache_key in self._parser_cache:
            return self._parser_cache[cache_key]

        try:
            module = importlib.import_module(module_path)
            parser_class = getattr(module, class_name)

            # Verify it's a valid parser
            if not issubclass(parser_class, BaseStatementParser):
                raise TypeError(
                    f"{class_name} is not a subclass of BaseStatementParser"
                )

            self._parser_cache[cache_key] = parser_class
            return parser_class

        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to import {class_name} from {module_path}: {e}\n"
                f"Make sure the parser module exists and is properly installed."
            )

    def get_parser_for_file(self, file_path: str) -> Optional[Type[BaseStatementParser]]:
        """
        Determine which parser to use based on file path.

        Args:
            file_path: Path to the PDF file

        Returns:
            Parser class or None if no matching parser found
        """
        path = Path(file_path)
        filename = path.name
        parent_dir = path.parent.name

        # Try to match by parent directory first
        if parent_dir in self.config.get('institutions', {}):
            institution_config = self.config['institutions'][parent_dir]

            # Try each parser pattern
            for parser_config in institution_config.get('parsers', []):
                pattern = parser_config.get('pattern', '*')

                if self._match_pattern(filename, pattern):
                    return self._load_parser_class(
                        parser_config['module'],
                        parser_config['class']
                    )

        # Fallback: try matching filename against all institutions
        for inst_name, inst_config in self.config.get('institutions', {}).items():
            if inst_name.lower() in filename.lower():
                # Use the default parser (pattern "*")
                for parser_config in inst_config.get('parsers', []):
                    if parser_config.get('pattern') == '*':
                        return self._load_parser_class(
                            parser_config['module'],
                            parser_config['class']
                        )

        return None

    def list_institutions(self) -> dict:
        """List all configured institutions and their parsers."""
        result = {}
        for inst_name, inst_config in self.config.get('institutions', {}).items():
            parsers = []
            for parser_config in inst_config.get('parsers', []):
                parsers.append({
                    'pattern': parser_config.get('pattern', '*'),
                    'class': parser_config['class'],
                    'description': parser_config.get('description', 'No description')
                })
            result[inst_name] = {
                'name': inst_config.get('name', inst_name),
                'parsers': parsers
            }
        return result

    def add_institution(self, institution_name: str, parser_class: str,
                       parser_module: str, description: str = "") -> None:
        """
        Add a new institution to the configuration.

        Args:
            institution_name: Name of the institution (directory name)
            parser_class: Parser class name
            parser_module: Module path (e.g., 'parsers.td_parser')
            description: Description of the parser
        """
        if 'institutions' not in self.config:
            self.config['institutions'] = {}

        self.config['institutions'][institution_name] = {
            'name': institution_name,
            'parsers': [
                {
                    'pattern': '*',
                    'class': parser_class,
                    'module': parser_module,
                    'description': description
                }
            ]
        }

        # Save updated config
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        # Clear cache
        self._parser_cache.clear()


def main():
    """CLI for managing parser configuration."""
    import sys

    if len(sys.argv) < 2:
        print("Parser Loader CLI")
        print("\nUsage:")
        print("  python parser_loader.py list")
        print("  python parser_loader.py test <file_path>")
        print("  python parser_loader.py add <inst_name> <class> <module> [description]")
        sys.exit(1)

    command = sys.argv[1]
    loader = ParserLoader()

    if command == "list":
        print("\nConfigured Institutions:")
        print("=" * 80)
        institutions = loader.list_institutions()
        for inst_name, inst_data in institutions.items():
            print(f"\n{inst_name} ({inst_data['name']})")
            for parser in inst_data['parsers']:
                print(f"  Pattern: {parser['pattern']}")
                print(f"  Class: {parser['class']}")
                print(f"  Description: {parser['description']}")

    elif command == "test":
        if len(sys.argv) < 3:
            print("Usage: python parser_loader.py test <file_path>")
            sys.exit(1)

        file_path = sys.argv[2]
        print(f"\nTesting parser detection for: {file_path}")
        print("=" * 80)

        parser_class = loader.get_parser_for_file(file_path)
        if parser_class:
            print(f"✓ Found parser: {parser_class.__name__}")
            print(f"  Module: {parser_class.__module__}")
        else:
            print("✗ No parser found for this file")

    elif command == "add":
        if len(sys.argv) < 5:
            print("Usage: python parser_loader.py add <inst_name> <class> <module> [description]")
            sys.exit(1)

        inst_name = sys.argv[2]
        parser_class = sys.argv[3]
        parser_module = sys.argv[4]
        description = sys.argv[5] if len(sys.argv) > 5 else ""

        loader.add_institution(inst_name, parser_class, parser_module, description)
        print(f"✓ Added {inst_name} to configuration")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
