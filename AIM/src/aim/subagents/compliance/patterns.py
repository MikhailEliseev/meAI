"""
Prohibited Language Pattern Library

Fast pattern matching for FDA prohibited language in medical marketing.
Target: <10ms per keyword check.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from AIM.src.aim.subagents.schemas.compliance import PatternMatch


class ProhibitedPatternLibrary:
    """Library of FDA prohibited language patterns

    Loads patterns from YAML and provides fast regex matching.
    Optimized for <10ms per keyword check.

    Pattern categories:
    - cure_claims: Cure/eliminate/eradicate claims (severity 5)
    - treatment_claims: Treatment/therapy claims (severity 4-5)
    - diagnostic_claims: Diagnosis/detection claims (severity 5)
    - prevention_claims: Prevention/protection claims (severity 4-5)
    - guarantees: Guaranteed results claims (severity 4)
    - fda_misrepresentation: False FDA approval claims (severity 5)
    - supplement_drug_claims: Supplements making drug claims (severity 5)
    - miracle_claims: Miracle/breakthrough claims (severity 4)
    - comparison_claims: Superiority over drugs (severity 3-4)
    - high_risk_diseases: COVID/cancer/HIV claims (severity 5)
    - weight_loss_claims: Specific weight loss promises (severity 3-4)
    - prescription_drug_names: Using Rx drug names (severity 5)
    - medical_terminology_misuse: Clinical/medical terms (severity 3-4)
    - anti_aging_claims: Anti-aging exaggerations (severity 3)
    """

    def __init__(self, patterns_file: Optional[str] = None):
        """Initialize pattern library

        Args:
            patterns_file: Path to YAML patterns file (default: config/compliance_patterns.yaml)
        """
        if patterns_file is None:
            # Default to config/compliance_patterns.yaml relative to AIM root
            # Path: AIM/src/aim/subagents/compliance/patterns.py -> AIM/config/
            aim_root = Path(__file__).parent.parent.parent.parent.parent
            patterns_file = str(aim_root / "config" / "compliance_patterns.yaml")

        self.patterns_file = patterns_file
        self.patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.compiled_patterns: Dict[str, List[Dict[str, Any]]] = {}

        self._load_patterns()
        self._compile_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from YAML file"""
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            self.patterns = yaml.safe_load(f)

    def _compile_patterns(self) -> None:
        """Compile regex patterns for fast matching

        Pre-compiles all patterns with IGNORECASE flag for performance.
        """
        for category, pattern_list in self.patterns.items():
            if not isinstance(pattern_list, list):
                continue

            compiled_list = []
            for pattern_dict in pattern_list:
                compiled_dict = pattern_dict.copy()
                # Compile regex with IGNORECASE for case-insensitive matching
                compiled_dict['compiled'] = re.compile(
                    pattern_dict['pattern'],
                    re.IGNORECASE
                )
                compiled_list.append(compiled_dict)

            self.compiled_patterns[category] = compiled_list

    def check_keyword(self, keyword: str) -> List[PatternMatch]:
        """Check keyword against all prohibited patterns

        Fast pattern matching optimized for <10ms per keyword.

        Args:
            keyword: Keyword to check

        Returns:
            List of pattern matches (empty if no matches)
        """
        matches: List[PatternMatch] = []

        for category, pattern_list in self.compiled_patterns.items():
            for pattern_dict in pattern_list:
                compiled_regex = pattern_dict['compiled']

                # Fast regex search
                if compiled_regex.search(keyword):
                    match = PatternMatch(
                        pattern=pattern_dict['pattern'],
                        category=category,
                        severity=pattern_dict['severity'],
                        rationale=pattern_dict['rationale']
                    )
                    matches.append(match)

        return matches

    def get_max_severity(self, matches: List[PatternMatch]) -> Optional[int]:
        """Get maximum severity from pattern matches

        Args:
            matches: List of pattern matches

        Returns:
            Maximum severity (1-5) or None if no matches
        """
        if not matches:
            return None

        return max(match.severity for match in matches)

    def get_categories(self) -> List[str]:
        """Get list of all pattern categories

        Returns:
            List of category names
        """
        return list(self.patterns.keys())

    def get_pattern_count(self) -> int:
        """Get total number of patterns

        Returns:
            Total pattern count
        """
        count = 0
        for pattern_list in self.patterns.values():
            if isinstance(pattern_list, list):
                count += len(pattern_list)
        return count

    def get_patterns_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all patterns in a category

        Args:
            category: Category name

        Returns:
            List of pattern dictionaries
        """
        return self.patterns.get(category, [])

    def get_high_severity_patterns(self, min_severity: int = 4) -> List[Dict[str, Any]]:
        """Get all patterns with severity >= threshold

        Args:
            min_severity: Minimum severity (default: 4)

        Returns:
            List of high-severity pattern dictionaries
        """
        high_severity = []

        for category, pattern_list in self.patterns.items():
            if not isinstance(pattern_list, list):
                continue

            for pattern_dict in pattern_list:
                if pattern_dict['severity'] >= min_severity:
                    pattern_with_category = pattern_dict.copy()
                    pattern_with_category['category'] = category
                    high_severity.append(pattern_with_category)

        return high_severity

    def reload_patterns(self) -> None:
        """Reload patterns from file

        Useful for hot-reloading pattern updates without restart.
        """
        self._load_patterns()
        self._compile_patterns()

    def __repr__(self) -> str:
        """String representation"""
        return f"<ProhibitedPatternLibrary(patterns={self.get_pattern_count()}, categories={len(self.get_categories())})>"
