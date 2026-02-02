import subprocess
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.config.settings import settings
from app.config.logging import logger


class SecretScanner:
    def __init__(self):
        self.gitleaks_path = "/usr/local/bin/gitleaks"

    async def scan_directory(self, directory: Path) -> Dict[str, Any]:
        result = {
            "secrets_found": [],
            "severity": "none",
            "scan_successful": False
        }

        try:
            proc = await asyncio.create_subprocess_exec(
                self.gitleaks_path, "detect",
                "--source", str(directory),
                "--verbose",
                "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                output = stdout.decode()
                if output.strip():
                    try:
                        import json
                        findings = json.loads(output)
                        for finding in findings:
                            result["secrets_found"].append({
                                "file": finding.get("file", "unknown"),
                                "line": finding.get("lineNumber", 0),
                                "secret": finding.get("secret", "REDACTED"),
                                "description": finding.get("description", "")
                            })
                    except:
                        pass

                result["scan_successful"] = True
                result["severity"] = "high" if result["secrets_found"] else "none"

        except FileNotFoundError:
            logger.warning("Gitleaks not found, using basic pattern matching")
            result = await self.basic_scan(directory)

        return result

    async def basic_scan(self, directory: Path) -> Dict[str, Any]:
        result = {
            "secrets_found": [],
            "severity": "none",
            "scan_successful": True,
            "note": "Basic pattern matching only"
        }

        patterns = [
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
            (r'github_pat_[a-zA-Z0-9_]{22,}', "GitHub App Token"),
            (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API Key"),
            (r'sk-ant-api03-[a-zA-Z0-9_-]{50,}', "Anthropic API Key"),
            (r'aws_access_key_id', "AWS Access Key"),
            (r'-----BEGIN RSA PRIVATE KEY-----', "RSA Private Key"),
        ]

        import re
        for py_file in directory.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern, description in patterns:
                    if re.search(pattern, content):
                        result["secrets_found"].append({
                            "file": str(py_file.relative_to(directory)),
                            "secret": description,
                            "description": "Pattern matched"
                        })
            except:
                pass

        result["severity"] = "high" if result["secrets_found"] else "none"
        return result


class SecurityScanner:
    def __init__(self):
        self.secret_scanner = SecretScanner()

    async def scan_code(self, directory: Path) -> Dict[str, Any]:
        secret_results = await self.secret_scanner.scan_directory(directory)

        findings = []
        for secret in secret_results.get("secrets_found", []):
            findings.append({
                "type": "secret_detected",
                "file": secret.get("file"),
                "line": secret.get("line"),
                "message": f"Potential secret detected: {secret.get('description')}",
                "severity": "critical"
            })

        return {
            "scan_type": "comprehensive",
            "findings": findings,
            "critical_count": len(findings),
            "secret_scan": secret_results,
            "passed": len(findings) == 0,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
