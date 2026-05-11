"""
Risk Scoring Framework

Calculates compliance risk scores using Likelihood × Severity methodology.
Determines actions based on risk level (block, reduce, pass).
"""

from typing import List, Optional

from AIM.src.aim.subagents.schemas.compliance import (
    RiskLevel,
    ComplianceAction,
    PatternMatch,
    FDAEnforcementRecord,
)


class RiskScorer:
    """Risk scoring for compliance checks

    Methodology:
    - Likelihood (1-5): Probability of regulatory action
    - Severity (1-5): Impact of consequences
    - Risk Score = Likelihood × Severity (1-25)

    Risk Levels:
    - CRITICAL (20-25): Block keyword immediately
    - HIGH (15-19): Reduce priority by 50%
    - MEDIUM (8-14): Pass with documentation
    - LOW (1-7): Pass with documentation

    Likelihood Factors:
    - Pattern severity (1-5)
    - FDA enforcement history (0-2 bonus)
    - Pattern count (0-1 bonus)

    Severity Factors:
    - Disease seriousness (1-5)
    - Claim type (1-5)
    - Regulatory history (0-2 bonus)
    """

    # Disease severity mapping
    DISEASE_SEVERITY = {
        "cancer": 5,
        "covid": 5,
        "coronavirus": 5,
        "hiv": 5,
        "aids": 5,
        "alzheimer": 5,
        "heart disease": 5,
        "stroke": 5,
        "diabetes": 4,
        "arthritis": 3,
        "obesity": 3,
        "acne": 2,
        "wrinkles": 1,
    }

    def calculate_likelihood(
        self,
        pattern_matches: List[PatternMatch],
        fda_enforcement_count: int,
    ) -> int:
        """Calculate likelihood score (1-5)

        Args:
            pattern_matches: List of matched patterns
            fda_enforcement_count: Number of FDA enforcement actions

        Returns:
            Likelihood score (1-5)
        """
        if not pattern_matches:
            return 1  # Minimum likelihood

        # Base likelihood from max pattern severity
        max_severity = max(match.severity for match in pattern_matches)
        likelihood = max_severity

        # Bonus for FDA enforcement history
        if fda_enforcement_count > 0:
            likelihood = min(5, likelihood + 1)  # +1 for any FDA history
        if fda_enforcement_count >= 3:
            likelihood = min(5, likelihood + 1)  # +1 for multiple actions

        # Bonus for multiple pattern matches
        if len(pattern_matches) >= 3:
            likelihood = min(5, likelihood + 1)  # +1 for multiple violations

        return min(5, likelihood)  # Cap at 5

    def calculate_severity(
        self,
        keyword: str,
        pattern_matches: List[PatternMatch],
        fda_enforcement_records: List[FDAEnforcementRecord],
    ) -> int:
        """Calculate severity score (1-5)

        Args:
            keyword: Keyword being checked
            pattern_matches: List of matched patterns
            fda_enforcement_records: FDA enforcement records

        Returns:
            Severity score (1-5)
        """
        # Base severity from disease mentions
        base_severity = 1
        keyword_lower = keyword.lower()

        for disease, severity in self.DISEASE_SEVERITY.items():
            if disease in keyword_lower:
                base_severity = max(base_severity, severity)

        # Increase severity for certain claim types
        if pattern_matches:
            for match in pattern_matches:
                # Cure claims are always severe
                if match.category in ["cure_claims", "treatment_claims", "diagnostic_claims"]:
                    base_severity = max(base_severity, 5)
                # FDA misrepresentation is severe
                elif match.category == "fda_misrepresentation":
                    base_severity = max(base_severity, 5)
                # Supplement drug claims are severe
                elif match.category == "supplement_drug_claims":
                    base_severity = max(base_severity, 4)

        # Bonus for FDA enforcement with serious classifications
        if fda_enforcement_records:
            for record in fda_enforcement_records:
                if record.classification == "Class I":  # Most serious
                    base_severity = min(5, base_severity + 2)
                elif record.classification == "Class II":
                    base_severity = min(5, base_severity + 1)

        return min(5, base_severity)  # Cap at 5

    def calculate_risk_score(
        self,
        likelihood: int,
        severity: int,
    ) -> int:
        """Calculate total risk score

        Args:
            likelihood: Likelihood score (1-5)
            severity: Severity score (1-5)

        Returns:
            Risk score (1-25)
        """
        return likelihood * severity

    def determine_risk_level(self, risk_score: int) -> RiskLevel:
        """Determine risk level from score

        Args:
            risk_score: Risk score (1-25)

        Returns:
            Risk level enum
        """
        if risk_score >= 20:
            return RiskLevel.CRITICAL
        elif risk_score >= 15:
            return RiskLevel.HIGH
        elif risk_score >= 8:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def determine_action(self, risk_level: RiskLevel) -> ComplianceAction:
        """Determine action from risk level

        Args:
            risk_level: Risk level

        Returns:
            Compliance action
        """
        if risk_level == RiskLevel.CRITICAL:
            return ComplianceAction.BLOCKED
        elif risk_level == RiskLevel.HIGH:
            return ComplianceAction.REDUCED
        else:
            return ComplianceAction.PASSED

    def generate_rationale(
        self,
        keyword: str,
        risk_level: RiskLevel,
        risk_score: int,
        likelihood: int,
        severity: int,
        pattern_matches: List[PatternMatch],
        fda_enforcement_count: int,
    ) -> str:
        """Generate human-readable rationale

        Args:
            keyword: Keyword being checked
            risk_level: Risk level
            risk_score: Risk score
            likelihood: Likelihood score
            severity: Severity score
            pattern_matches: Pattern matches
            fda_enforcement_count: FDA enforcement count

        Returns:
            Rationale string
        """
        action = self.determine_action(risk_level)

        # Build rationale parts
        parts = []

        # Risk level and action
        parts.append(f"{risk_level.value} risk: ")

        # Pattern matches
        if pattern_matches:
            categories = set(match.category for match in pattern_matches)
            category_names = ", ".join(categories)
            parts.append(f"{category_names}")

        # FDA enforcement
        if fda_enforcement_count > 0:
            parts.append(f" + FDA enforcement history ({fda_enforcement_count} actions)")

        # Scoring
        parts.append(f". Likelihood={likelihood} (pattern severity + FDA history), ")
        parts.append(f"Severity={severity} (disease seriousness + claim type). ")
        parts.append(f"Risk={risk_score}. ")

        # Action
        if action == ComplianceAction.BLOCKED:
            parts.append("Action: BLOCK keyword.")
        elif action == ComplianceAction.REDUCED:
            parts.append("Action: REDUCE priority by 50%.")
        else:
            parts.append("Action: PASS with documentation.")

        return "".join(parts)

    def score_keyword(
        self,
        keyword: str,
        pattern_matches: List[PatternMatch],
        fda_enforcement_count: int,
        fda_enforcement_records: List[FDAEnforcementRecord],
    ) -> dict:
        """Complete risk scoring for a keyword

        Args:
            keyword: Keyword to score
            pattern_matches: Pattern matches
            fda_enforcement_count: FDA enforcement count
            fda_enforcement_records: FDA enforcement records

        Returns:
            Dictionary with scoring results
        """
        # Calculate scores
        likelihood = self.calculate_likelihood(pattern_matches, fda_enforcement_count)
        severity = self.calculate_severity(keyword, pattern_matches, fda_enforcement_records)
        risk_score = self.calculate_risk_score(likelihood, severity)
        risk_level = self.determine_risk_level(risk_score)
        action = self.determine_action(risk_level)
        rationale = self.generate_rationale(
            keyword,
            risk_level,
            risk_score,
            likelihood,
            severity,
            pattern_matches,
            fda_enforcement_count,
        )

        return {
            "likelihood_score": likelihood,
            "severity_score": severity,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "action": action,
            "rationale": rationale,
        }
