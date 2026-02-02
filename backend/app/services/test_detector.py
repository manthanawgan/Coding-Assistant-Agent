from typing import Optional, Dict, Any, List
from pathlib import Path

from app.config.settings import settings
from app.config.logging import logger


class TestDetector:
    def __init__(self):
        self.frameworks = {
            "pytest": {
                "files": ["pytest.ini", "pyproject.toml", "setup.cfg", "conftest.py"],
                "pattern": "test_*.py",
                "run_cmd": "python -m pytest",
                "coverage_cmd": "python -m pytest --cov"
            },
            "jest": {
                "files": ["package.json", "jest.config.js", "jest.config.ts"],
                "pattern": "*.test.js",
                "run_cmd": "npm test",
                "coverage_cmd": "npm test -- --coverage"
            },
            "mocha": {
                "files": ["package.json"],
                "pattern": "*.test.js",
                "run_cmd": "npx mocha",
                "coverage_cmd": "npx nyc mocha"
            },
            "unittest": {
                "files": [],
                "pattern": "test_*.py",
                "run_cmd": "python -m unittest discover",
                "coverage_cmd": "python -m coverage run -m unittest discover"
            },
            "go_test": {
                "files": ["go.mod"],
                "pattern": "*_test.go",
                "run_cmd": "go test -v",
                "coverage_cmd": "go test -v -coverprofile=coverage.out"
            },
            "maven": {
                "files": ["pom.xml"],
                "pattern": "src/test/java/**/*.java",
                "run_cmd": "mvn test",
                "coverage_cmd": "mvn test jacoco:report"
            },
            "gradle": {
                "files": ["build.gradle", "build.gradle.kts"],
                "pattern": "src/test/java/**/*.java",
                "run_cmd": "./gradlew test",
                "coverage_cmd": "./gradlew test jacocoTestReport"
            },
            "rust": {
                "files": ["Cargo.toml"],
                "pattern": "tests/**/*.rs",
                "run_cmd": "cargo test",
                "coverage_cmd": "cargo tarpaulin"
            },
            "phpunit": {
                "files": ["phpunit.xml", "composer.json"],
                "pattern": "tests/**/*.php",
                "run_cmd": "./vendor/bin/phpunit",
                "coverage_cmd": "./vendor/bin/phpunit --coverage-html coverage"
            }
        }

    async def detect(self, repo_path: Path) -> Dict[str, Any]:
        detected = {
            "framework": None,
            "test_files": [],
            "run_command": None,
            "coverage_command": None
        }

        for name, config in self.frameworks.items():
            found = False
            for file in config["files"]:
                if (repo_path / file).exists():
                    found = True
                    break

            if found or config["files"]:
                for pattern in ["test_*.py", "*.test.js", "*_test.go", "tests/**/*.rs"]:
                    detected["test_files"].extend(repo_path.glob(pattern) if "*" in pattern else [])

                if detected["test_files"] or found:
                    detected["framework"] = name
                    detected["run_command"] = config["run_cmd"]
                    detected["coverage_command"] = config["coverage_cmd"]
                    break

        if not detected["framework"]:
            all_tests = list(repo_path.glob("test_*.*")) + list(repo_path.glob("*_test.*"))
            if all_tests:
                detected["framework"] = "generic"
                detected["test_files"] = all_tests
                detected["run_command"] = "echo 'No test command detected'"

        detected["test_count"] = len(detected["test_files"])
        return detected
