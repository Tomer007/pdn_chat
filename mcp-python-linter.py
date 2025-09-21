#!/usr/bin/env python3
"""
Custom MCP Python Linter Server
Provides Python code quality analysis and linting through MCP protocol
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List

class PythonLinterMCP:
    def __init__(self):
        self.pylint_path = "/Users/tomer.gur/Library/Python/3.9/bin/pylint"
        
    def lint_file(self, file_path: str) -> Dict[str, Any]:
        """Lint a Python file and return results"""
        try:
            # Run pylint on the file
            result = subprocess.run(
                [self.pylint_path, "--output-format=json", file_path],
                capture_output=True,
                text=True,
                cwd="/Users/tomer.gur/dev-tools/pdn_chat"
            )
            
            # Parse JSON output
            if result.stdout:
                issues = json.loads(result.stdout)
            else:
                issues = []
                
            return {
                "file": file_path,
                "issues": issues,
                "exit_code": result.returncode,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "file": file_path,
                "error": str(e),
                "issues": [],
                "exit_code": -1
            }
    
    def lint_directory(self, directory: str) -> Dict[str, Any]:
        """Lint all Python files in a directory"""
        python_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        results = []
        for file_path in python_files:
            results.append(self.lint_file(file_path))
            
        return {
            "directory": directory,
            "files_checked": len(python_files),
            "results": results
        }
    
    def get_code_metrics(self, file_path: str) -> Dict[str, Any]:
        """Get code quality metrics for a file"""
        try:
            # Run pylint with specific metrics
            result = subprocess.run(
                [self.pylint_path, "--reports=y", "--output-format=json", file_path],
                capture_output=True,
                text=True,
                cwd="/Users/tomer.gur/dev-tools/pdn_chat"
            )
            
            metrics = {
                "file": file_path,
                "raw_output": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
            
            return metrics
        except Exception as e:
            return {
                "file": file_path,
                "error": str(e),
                "exit_code": -1
            }

def main():
    linter = PythonLinterMCP()
    
    # Simple command line interface
    if len(sys.argv) < 2:
        print("Usage: python mcp-python-linter.py <command> [args]")
        print("Commands:")
        print("  lint <file_path> - Lint a specific Python file")
        print("  lint-dir <directory> - Lint all Python files in directory")
        print("  metrics <file_path> - Get code metrics for a file")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "lint" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        result = linter.lint_file(file_path)
        print(json.dumps(result, indent=2))
    
    elif command == "lint-dir" and len(sys.argv) > 2:
        directory = sys.argv[2]
        result = linter.lint_directory(directory)
        print(json.dumps(result, indent=2))
    
    elif command == "metrics" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        result = linter.get_code_metrics(file_path)
        print(json.dumps(result, indent=2))
    
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)

if __name__ == "__main__":
    main()

