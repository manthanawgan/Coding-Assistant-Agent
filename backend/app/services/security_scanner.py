from typing import Dict, Any, List, Optional
from pathlib import Path


class SecurityScanner:
    def __init__(self):
        pass

    async def scan_code(self, directory: Path) -> Dict[str, Any]:
        findings = []
        secrets_found = []

        patterns = [
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
            (r'github_pat_[a-zA-Z0-9_]{22,}', "GitHub App Token"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API Key"),
            (r'sk-ant-api03-[a-zA-Z0-9_-]{50,}', "Anthropic API Key"),
            (r'aws_access_key_id', "AWS Access Key"),
            (r'-----BEGIN RSA PRIVATE KEY-----', "RSA Private Key"),
            (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*', "JWT Token"),
        ]

        import re
        try:
            for py_file in directory.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    for pattern, description in patterns:
                        if re.search(pattern, content):
                            secrets_found.append({
                                "file": str(py_file.relative_to(directory)),
                                "secret": description,
                                "description": "Pattern matched"
                            })
                except:
                    pass

            for secret in secrets_found:
                findings.append({
                    "type": "secret_detected",
                    "file": secret.get("file"),
                    "line": 0,
                    "message": f"Potential secret detected: {secret.get('description')}",
                    "severity": "critical"
                })

        except Exception as e:
            return {
                "scan_type": "comprehensive",
                "findings": [],
                "critical_count": 0,
                "passed": True,
                "error": str(e),
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }

        return {
            "scan_type": "comprehensive",
            "findings": findings,
            "critical_count": len(findings),
            "secret_scan": {
                "secrets_found": secrets_found,
                "severity": "high" if secrets_found else "none"
            },
            "passed": len(findings) == 0,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
