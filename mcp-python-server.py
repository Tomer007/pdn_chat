#!/usr/bin/env python3
"""
MCP Python Linter Server
A proper MCP server for Python code analysis and linting
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List

class MCPPythonServer:
    def __init__(self):
        self.pylint_path = "/Users/tomer.gur/Library/Python/3.9/bin/pylint"
        self.project_root = "/Users/tomer.gur/dev-tools/pdn_chat"
        
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "lint_python_file",
                            "description": "Lint a Python file for code quality issues",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Path to the Python file to lint"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        },
                        {
                            "name": "lint_python_directory",
                            "description": "Lint all Python files in a directory",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "directory": {
                                        "type": "string",
                                        "description": "Path to the directory to lint"
                                    }
                                },
                                "required": ["directory"]
                            }
                        },
                        {
                            "name": "get_python_metrics",
                            "description": "Get code quality metrics for a Python file",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {
                                        "type": "string",
                                        "description": "Path to the Python file to analyze"
                                    }
                                },
                                "required": ["file_path"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            if tool_name == "lint_python_file":
                file_path = arguments.get("file_path", "")
                result = self.lint_file(file_path)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "lint_python_directory":
                directory = arguments.get("directory", "")
                result = self.lint_directory(directory)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_python_metrics":
                file_path = arguments.get("file_path", "")
                result = self.get_code_metrics(file_path)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32601,
                "message": "Method not found"
            }
        }
    
    def lint_file(self, file_path: str) -> Dict[str, Any]:
        """Lint a Python file and return results"""
        try:
            # Make path relative to project root
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)
            
            # Run pylint on the file
            result = subprocess.run(
                [self.pylint_path, "--output-format=json", file_path],
                capture_output=True,
                text=True,
                cwd=self.project_root
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
                "stderr": result.stderr,
                "summary": {
                    "total_issues": len(issues),
                    "by_type": self._categorize_issues(issues)
                }
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
        if not os.path.isabs(directory):
            directory = os.path.join(self.project_root, directory)
            
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
            "results": results,
            "summary": self._summarize_results(results)
        }
    
    def get_code_metrics(self, file_path: str) -> Dict[str, Any]:
        """Get code quality metrics for a file"""
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.join(self.project_root, file_path)
                
            # Run pylint with specific metrics
            result = subprocess.run(
                [self.pylint_path, "--reports=y", "--output-format=json", file_path],
                capture_output=True,
                text=True,
                cwd=self.project_root
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
    
    def _categorize_issues(self, issues: List[Dict]) -> Dict[str, int]:
        """Categorize issues by type"""
        categories = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            categories[issue_type] = categories.get(issue_type, 0) + 1
        return categories
    
    def _summarize_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Summarize linting results"""
        total_issues = 0
        total_files = len(results)
        files_with_issues = 0
        
        for result in results:
            if "issues" in result:
                issue_count = len(result["issues"])
                total_issues += issue_count
                if issue_count > 0:
                    files_with_issues += 1
        
        return {
            "total_files": total_files,
            "files_with_issues": files_with_issues,
            "total_issues": total_issues,
            "average_issues_per_file": total_issues / total_files if total_files > 0 else 0
        }

def main():
    server = MCPPythonServer()
    
    # Read MCP requests from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    main()

