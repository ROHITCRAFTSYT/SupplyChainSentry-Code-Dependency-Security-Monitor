import json
import requests
import docker
import yara
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupplyChainSentry:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.baselines: Dict[str, Dict] = {}
        self.docker_client = docker.from_env()
        self.yara_rules = self.load_yara_rules()
        self.risk_threshold = self.config.get("risk_threshold", 0.7)

    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            return {
                "packages": [],
                "yara_rules_path": "rules.yara",
                "risk_threshold": 0.7,
                "registry_url": "https://pypi.org/pypi"
            }

    def load_yara_rules(self) -> Optional[yara.Rules]:
        """Load YARA rules for static analysis."""
        try:
            return yara.compile(self.config.get("yara_rules_path", "rules.yara"))
        except Exception as e:
            logger.error(f"Failed to load YARA rules: {e}")
            return None

    def create_behavioral_baseline(self, package: str, version: str) -> Dict:
        """Create a baseline for package behavior."""
        baseline = {
            "package": package,
            "version": version,
            "network_calls": [],
            "file_access": [],
            "hash": self.get_package_hash(package, version),
            "created_at": datetime.now().isoformat()
        }
        self.baselines[f"{package}:{version}"] = baseline
        logger.info(f"Baseline created for {package}:{version}")
        return baseline

    def get_package_hash(self, package: str, version: str) -> str:
        """Calculate hash of package content."""
        try:
            url = f"{self.config['registry_url']}/{package}/{version}/json"
            response = requests.get(url)
            if response.status_code == 200:
                content = response.content
                return hashlib.sha256(content).hexdigest()
            return ""
        except Exception as e:
            logger.error(f"Error fetching package {package}:{version}: {e}")
            return ""

    def analyze_package(self, package: str, version: str) -> Dict:
        """Analyze package for potential risks."""
        risk_score = 0.0
        findings = []

        # Static analysis with YARA
        static_results = self.static_analysis(package, version)
        if static_results.get("matches"):
            risk_score += 0.4
            findings.append("Potential backdoors detected in static analysis")

        # Dynamic analysis in container
        dynamic_results = self.dynamic_analysis(package, version)
        if dynamic_results.get("anomalies"):
            risk_score += 0.3
            findings.append("Anomalous behavior detected in dynamic analysis")

        # Maintainer and contribution analysis
        maintainer_score = self.analyze_maintainer(package)
        risk_score += maintainer_score
        if maintainer_score > 0.2:
            findings.append("Suspicious maintainer activity")

        return {
            "package": package,
            "version": version,
            "risk_score": min(risk_score, 1.0),
            "is_safe": risk_score < self.risk_threshold,
            "findings": findings
        }

    def static_analysis(self, package: str, version: str) -> Dict:
        """Perform static analysis using YARA rules."""
        if not self.yara_rules:
            return {"matches": [], "error": "No YARA rules loaded"}

        try:
            # Download package source (simplified for example)
            package_path = self.download_package(package, version)
            matches = self.yara_rules.match(package_path)
            return {"matches": [m.rule for m in matches], "error": None}
        except Exception as e:
            logger.error(f"Static analysis failed for {package}:{version}: {e}")
            return {"matches": [], "error": str(e)}

    def dynamic_analysis(self, package: str, version: str) -> Dict:
        """Run package in a containerized environment and monitor behavior."""
        try:
            container = self.docker_client.containers.run(
                "python:3.9-slim",
                f"pip install {package}=={version} && python -c 'import {package}'",
                detach=True,
                remove=True
            )
            logs = container.logs().decode('utf-8')
            anomalies = self.detect_anomalies(logs, package, version)
            return {"anomalies": anomalies, "logs": logs}
        except Exception as e:
            logger.error(f"Dynamic analysis failed for {package}:{version}: {e}")
            return {"anomalies": [], "error": str(e)}

    def detect_anomalies(self, logs: str, package: str, version: str) -> List[str]:
        """Detect anomalous behavior compared to baseline."""
        baseline = self.baselines.get(f"{package}:{version}")
        if not baseline:
            return ["No baseline available"]

        anomalies = []
        # Simplified anomaly detection (expand with real patterns)
        if "network error" in logs.lower() and not baseline["network_calls"]:
            anomalies.append("Unexpected network activity")
        if "permission denied" in logs.lower() and not baseline["file_access"]:
            anomalies.append("Unexpected file access")
        return anomalies

    def analyze_maintainer(self, package: str) -> float:
        """Analyze package maintainer activity (simplified)."""
        try:
            url = f"{self.config['registry_url']}/{package}/json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                maintainers = data.get("info", {}).get("maintainers", [])
                # Simplified scoring: penalize new or few maintainers
                return 0.1 if len(maintainers) < 2 else 0.05
            return 0.2  # Default risk if no data
        except Exception as e:
            logger.error(f"Maintainer analysis failed for {package}: {e}")
            return 0.2

    def download_package(self, package: str, version: str) -> str:
        """Download package source (placeholder)."""
        # In a real implementation, download and extract package
        return f"/tmp/{package}-{version}.tar.gz"

    def monitor_project(self, requirements_file: str) -> List[Dict]:
        """Monitor all dependencies in a requirements.txt file."""
        results = []
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        package, version = self.parse_requirement(line)
                        if package:
                            result = self.analyze_package(package, version)
                            results.append(result)
        except Exception as e:
            logger.error(f"Error monitoring project: {e}")
        return results

    def parse_requirement(self, line: str) -> tuple:
        """Parse a single requirement line."""
        try:
            parts = line.strip().split('==')
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
            return None, None
        except:
            return None, None

def main():
    sentry = SupplyChainSentry()
    # Example: Monitor a requirements.txt file
    results = sentry.monitor_project("requirements.txt")
    for result in results:
        status = "SAFE" if result["is_safe"] else "UNSAFE"
        logger.info(
            f"Package: {result['package']}:{result['version']}, "
            f"Risk Score: {result['risk_score']:.2f}, "
            f"Status: {status}, Findings: {result['findings']}"
        )

if __name__ == "__main__":
    main()
