import ast
from typing import Dict, List, Optional

class CodeParser: #using AST for parsing code adn extrcting metadata
    @staticmethod
    def parse_code(code: str) -> Dict:
        try:
            tree = ast.parse(code)
            
            analysis = {
                "valid": True,
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": [],
                "errors": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "line": node.lineno
                    })
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "line": node.lineno
                    })
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append(alias.name)
                    else:
                        analysis["imports"].append(node.module)
            
            return analysis
            
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [{
                    "type": "SyntaxError",
                    "message": str(e),
                    "line": e.lineno
                }]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [{
                    "type": "ParseError",
                    "message": str(e)
                }]
            }
    
    @staticmethod
    def get_code_complexity(code: str) -> Dict:
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            return {
                "lines_of_code": len([l for l in lines if l.strip()]),
                "num_functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "num_classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "max_nesting": CodeParser._max_nesting_depth(tree)
            }
        except:
            return {}
    
    @staticmethod
    def _max_nesting_depth(node, depth=0):
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = CodeParser._max_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth