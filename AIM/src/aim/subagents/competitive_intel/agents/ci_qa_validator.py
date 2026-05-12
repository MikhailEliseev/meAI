"""
CI QA Validator - Quality Assurance Agent

Валидирует качество анализа CI Deep Analyzer перед отправкой результатов.

Проверяет:
1. Полноту метрик (все ли 19 метрик собраны)
2. Достоверность данных (нет ли аномалий)
3. Consistency (нет ли противоречий)
4. Quality Score корректность

Lesson learned: Always validate analysis quality before reporting.
"""

from datetime import datetime
from typing import Any, Dict, List

from meai.agents.base_agent import Agent, Task, TaskResult
from AIM.src.aim.core.agent_learning import AgentLearning


class CIQAValidator(Agent):
    """QA Validator Agent

    Валидирует результаты CI Deep Analyzer:
    1. Проверяет полноту метрик (completeness)
    2. Проверяет достоверность данных (validity)
    3. Проверяет consistency (нет противоречий)
    4. Генерирует отчёт о качестве
    """

    # Expected metrics counts
    EXPECTED_METRICS = {
        "seo": 4,           # title, description, h1, schema
        "cwv": 5,           # LCP, INP, CLS, TTFB, FCP
        "mobile": 5,        # viewport, responsive, tap_targets, font_size, content_width
        "accessibility": 6, # color_contrast, aria, alt_text, form_labels, keyboard_nav, screen_reader
        "security": 6       # https, hsts, csp, x_frame_options, x_content_type, mixed_content
    }

    TOTAL_EXPECTED_METRICS = sum(EXPECTED_METRICS.values())  # 26 metrics

    def __init__(self, agent_id: str, database_url: str, vault_path: str):
        super().__init__(agent_id, database_url, vault_path)

        # Initialize learning system
        self.learning = AgentLearning(agent_id=agent_id)

    def get_capabilities(self) -> list[str]:
        return [
            "completeness_check",
            "validity_check",
            "consistency_check",
            "quality_report"
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute QA validation

        Task payload:
        {
            "analysis_result": {
                "name": "...",
                "url": "...",
                "deep_analysis": {...},
                "issues": {...}
            }
        }

        Returns:
        {
            "validation_status": "passed" | "failed" | "warning",
            "completeness": {...},
            "validity": {...},
            "consistency": {...},
            "quality_score": float,
            "issues": [...]
        }
        """
        try:
            start_time = datetime.now()
            analysis_result = task.payload.get("analysis_result", {})

            if not analysis_result:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No analysis result provided"},
                    error="No analysis result provided",
                    duration_seconds=0.0,
                    completed_at=datetime.now()
                )

            competitor_name = analysis_result.get("name", "Unknown")
            print(f"\n[QA Validator] 🔍 Валидирую анализ: {competitor_name}")

            # 1. Completeness check
            print(f"[QA Validator]   1️⃣  Проверка полноты метрик...")
            completeness = self._check_completeness(analysis_result)
            print(f"[QA Validator]   ✓ Полнота: {completeness['coverage_percent']:.1f}%")

            # 2. Validity check
            print(f"[QA Validator]   2️⃣  Проверка достоверности данных...")
            validity = self._check_validity(analysis_result)
            print(f"[QA Validator]   ✓ Достоверность: {validity['valid_metrics']}/{validity['total_metrics']}")

            # 3. Consistency check
            print(f"[QA Validator]   3️⃣  Проверка consistency...")
            consistency = self._check_consistency(analysis_result)
            print(f"[QA Validator]   ✓ Consistency: {len(consistency['issues'])} проблем")

            # 4. Generate quality report
            print(f"[QA Validator]   4️⃣  Генерация отчёта о качестве...")
            quality_report = self._generate_quality_report(
                completeness, validity, consistency
            )
            print(f"[QA Validator]   ✓ Quality Score: {quality_report['quality_score']:.1f}/100")

            # Determine validation status
            validation_status = self._determine_status(quality_report)

            duration = (datetime.now() - start_time).total_seconds()

            print(f"\n[QA Validator] ✅ Валидация завершена: {validation_status.upper()}")
            print(f"[QA Validator]   • Quality Score: {quality_report['quality_score']:.1f}/100")
            print(f"[QA Validator]   • Время: {duration:.1f}s")

            # 🎓 LEARNING: Record success
            await self.learning.record_success(
                task=task,
                result={
                    "validation_status": validation_status,
                    "quality_score": quality_report['quality_score']
                },
                metrics={
                    "quality_score": quality_report['quality_score'],
                    "completeness": completeness['coverage_percent'],
                    "validity_rate": validity['valid_metrics'] / validity['total_metrics'] if validity['total_metrics'] > 0 else 0,
                    "consistency_issues": len(consistency['issues'])
                }
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="completed",
                result={
                    "validation_status": validation_status,
                    "completeness": completeness,
                    "validity": validity,
                    "consistency": consistency,
                    "quality_report": quality_report,
                    "competitor_name": competitor_name
                },
                error=None,
                duration_seconds=duration,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[QA Validator] ❌ Ошибка: {str(e)}")

            # 🎓 LEARNING: Record failure
            await self.learning.record_failure(
                task=task,
                error=e,
                context={
                    "has_analysis_result": bool(analysis_result) if 'analysis_result' in locals() else False
                }
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now()
            )

    def _check_completeness(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if all expected metrics are present

        Returns:
        {
            "coverage_percent": float,
            "missing_metrics": [...],
            "collected_metrics": [...],
            "by_category": {...}
        }
        """
        deep_analysis = analysis_result.get("deep_analysis", {})

        collected = []
        missing = []

        # Check SEO metrics
        seo_coverage = deep_analysis.get("seo_coverage", {})
        if seo_coverage.get("title"):
            collected.append("seo.title")
        else:
            missing.append("seo.title")

        if seo_coverage.get("description"):
            collected.append("seo.description")
        else:
            missing.append("seo.description")

        if seo_coverage.get("h1"):
            collected.append("seo.h1")
        else:
            missing.append("seo.h1")

        if deep_analysis.get("schema_coverage"):
            collected.append("seo.schema")
        else:
            missing.append("seo.schema")

        # Check CWV metrics
        cwv = deep_analysis.get("cwv", {})
        if cwv:
            cwv_metrics = ["lcp", "inp", "cls", "ttfb", "fcp"]
            for metric in cwv_metrics:
                if metric in str(cwv):
                    collected.append(f"cwv.{metric}")
                else:
                    missing.append(f"cwv.{metric}")
        else:
            missing.extend([f"cwv.{m}" for m in ["lcp", "inp", "cls", "ttfb", "fcp"]])

        # Check Mobile metrics
        mobile = deep_analysis.get("mobile", {})
        if mobile:
            mobile_metrics = ["viewport_ok", "responsive", "tap_targets_ok", "font_size_ok", "content_width_ok"]
            for metric in mobile_metrics:
                if metric in str(mobile):
                    collected.append(f"mobile.{metric}")
                else:
                    missing.append(f"mobile.{metric}")
        else:
            missing.extend([f"mobile.{m}" for m in ["viewport", "responsive", "tap_targets", "font_size", "content_width"]])

        # Check Accessibility metrics
        accessibility = deep_analysis.get("accessibility", {})
        if accessibility:
            a11y_metrics = ["color_contrast", "aria_valid", "alt_text", "form_labels", "keyboard_nav", "screen_reader"]
            for metric in a11y_metrics:
                if metric in str(accessibility):
                    collected.append(f"accessibility.{metric}")
                else:
                    missing.append(f"accessibility.{metric}")
        else:
            missing.extend([f"accessibility.{m}" for m in ["color_contrast", "aria", "alt_text", "form_labels", "keyboard_nav", "screen_reader"]])

        # Check Security metrics
        security = deep_analysis.get("security", {})
        if security:
            security_metrics = ["https", "hsts", "csp", "x_frame_options", "x_content_type", "mixed_content"]
            for metric in security_metrics:
                if metric in str(security):
                    collected.append(f"security.{metric}")
                else:
                    missing.append(f"security.{metric}")
        else:
            missing.extend([f"security.{m}" for m in ["https", "hsts", "csp", "x_frame_options", "x_content_type", "mixed_content"]])

        coverage_percent = (len(collected) / self.TOTAL_EXPECTED_METRICS) * 100

        return {
            "coverage_percent": coverage_percent,
            "collected_metrics": collected,
            "missing_metrics": missing,
            "total_expected": self.TOTAL_EXPECTED_METRICS,
            "total_collected": len(collected)
        }

    def _check_validity(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if data values are valid (no anomalies)

        Returns:
        {
            "valid_metrics": int,
            "invalid_metrics": int,
            "total_metrics": int,
            "anomalies": [...]
        }
        """
        deep_analysis = analysis_result.get("deep_analysis", {})
        anomalies = []
        valid_count = 0
        total_count = 0

        # Check Quality Score range
        quality_score = deep_analysis.get("quality_score", 0)
        total_count += 1
        if 0 <= quality_score <= 100:
            valid_count += 1
        else:
            anomalies.append({
                "metric": "quality_score",
                "value": quality_score,
                "issue": "Quality score out of range [0, 100]"
            })

        # Check CWV values
        cwv = deep_analysis.get("cwv", {})
        if cwv:
            # LCP should be > 0 and < 20 seconds (reasonable range)
            if "avg_lcp" in cwv:
                total_count += 1
                lcp = cwv["avg_lcp"]
                if 0 < lcp < 20:
                    valid_count += 1
                else:
                    anomalies.append({
                        "metric": "cwv.lcp",
                        "value": lcp,
                        "issue": "LCP out of reasonable range (0, 20s)"
                    })

            # CLS should be >= 0 and < 1 (reasonable range)
            if "avg_cls" in cwv:
                total_count += 1
                cls = cwv["avg_cls"]
                if 0 <= cls < 1:
                    valid_count += 1
                else:
                    anomalies.append({
                        "metric": "cwv.cls",
                        "value": cls,
                        "issue": "CLS out of reasonable range [0, 1)"
                    })

            # CWV score should be 0-100
            if "score" in cwv:
                total_count += 1
                score = cwv["score"]
                if 0 <= score <= 100:
                    valid_count += 1
                else:
                    anomalies.append({
                        "metric": "cwv.score",
                        "value": score,
                        "issue": "CWV score out of range [0, 100]"
                    })

        # Check Mobile score
        mobile = deep_analysis.get("mobile", {})
        if mobile and "score" in mobile:
            total_count += 1
            score = mobile["score"]
            if 0 <= score <= 100:
                valid_count += 1
            else:
                anomalies.append({
                    "metric": "mobile.score",
                    "value": score,
                    "issue": "Mobile score out of range [0, 100]"
                })

        # Check Accessibility score
        accessibility = deep_analysis.get("accessibility", {})
        if accessibility and "score" in accessibility:
            total_count += 1
            score = accessibility["score"]
            if 0 <= score <= 100:
                valid_count += 1
            else:
                anomalies.append({
                    "metric": "accessibility.score",
                    "value": score,
                    "issue": "Accessibility score out of range [0, 100]"
                })

        # Check Security score
        security = deep_analysis.get("security", {})
        if security and "score" in security:
            total_count += 1
            score = security["score"]
            if 0 <= score <= 100:
                valid_count += 1
            else:
                anomalies.append({
                    "metric": "security.score",
                    "value": score,
                    "issue": "Security score out of range [0, 100]"
                })

        return {
            "valid_metrics": valid_count,
            "invalid_metrics": len(anomalies),
            "total_metrics": total_count,
            "anomalies": anomalies
        }

    def _check_consistency(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check for contradictions in data

        Returns:
        {
            "consistent": bool,
            "issues": [...]
        }
        """
        deep_analysis = analysis_result.get("deep_analysis", {})
        issues = []

        # Check: If CWV score is high, quality_score should also be reasonable
        quality_score = deep_analysis.get("quality_score", 0)
        cwv = deep_analysis.get("cwv", {})

        if cwv and "score" in cwv:
            cwv_score = cwv["score"]

            # If CWV is very low but quality_score is high, that's suspicious
            if cwv_score < 30 and quality_score > 70:
                issues.append({
                    "type": "score_mismatch",
                    "issue": f"CWV score very low ({cwv_score:.1f}) but quality_score high ({quality_score:.1f})",
                    "severity": "warning"
                })

        # Check: If pages_analyzed is 0, there should be no metrics
        pages_analyzed = analysis_result.get("pages_analyzed", 0)
        if pages_analyzed == 0:
            if deep_analysis.get("cwv") or deep_analysis.get("mobile") or deep_analysis.get("accessibility"):
                issues.append({
                    "type": "data_without_pages",
                    "issue": "Metrics present but pages_analyzed is 0",
                    "severity": "critical"
                })

        # Check: If security.https_rate is 0%, quality_score should reflect that
        security = deep_analysis.get("security", {})
        if security and "https_rate" in security:
            https_rate = security["https_rate"]
            if https_rate == 0 and quality_score > 50:
                issues.append({
                    "type": "security_mismatch",
                    "issue": f"No HTTPS (0%) but quality_score is {quality_score:.1f}",
                    "severity": "warning"
                })

        return {
            "consistent": len(issues) == 0,
            "issues": issues
        }

    def _generate_quality_report(
        self,
        completeness: Dict[str, Any],
        validity: Dict[str, Any],
        consistency: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall quality report

        Quality Score calculation:
        - Completeness: 40% (how many metrics collected)
        - Validity: 40% (how many metrics are valid)
        - Consistency: 20% (no contradictions)
        """
        # Completeness score (0-100)
        completeness_score = completeness["coverage_percent"]

        # Validity score (0-100)
        if validity["total_metrics"] > 0:
            validity_score = (validity["valid_metrics"] / validity["total_metrics"]) * 100
        else:
            validity_score = 0

        # Consistency score (0-100)
        critical_issues = sum(1 for i in consistency["issues"] if i.get("severity") == "critical")
        warning_issues = sum(1 for i in consistency["issues"] if i.get("severity") == "warning")

        if critical_issues > 0:
            consistency_score = 0
        elif warning_issues > 0:
            consistency_score = max(0, 100 - (warning_issues * 20))
        else:
            consistency_score = 100

        # Overall quality score
        quality_score = (
            completeness_score * 0.4 +
            validity_score * 0.4 +
            consistency_score * 0.2
        )

        return {
            "quality_score": quality_score,
            "completeness_score": completeness_score,
            "validity_score": validity_score,
            "consistency_score": consistency_score,
            "breakdown": {
                "completeness": f"{completeness['total_collected']}/{completeness['total_expected']} metrics",
                "validity": f"{validity['valid_metrics']}/{validity['total_metrics']} valid",
                "consistency": f"{len(consistency['issues'])} issues"
            }
        }

    def _determine_status(self, quality_report: Dict[str, Any]) -> str:
        """Determine validation status based on quality score

        - passed: quality_score >= 80
        - warning: 60 <= quality_score < 80
        - failed: quality_score < 60
        """
        quality_score = quality_report["quality_score"]

        if quality_score >= 80:
            return "passed"
        elif quality_score >= 60:
            return "warning"
        else:
            return "failed"


# Example usage
async def example_usage():
    """Example of how to use CI QA Validator"""

    validator = CIQAValidator(
        agent_id="ci-qa-validator",
        database_url="sqlite+aiosqlite:///./data/meai.db",
        vault_path="./obsidian/ci-qa-validator"
    )

    # Mock analysis result
    analysis_result = {
        "name": "Test Competitor",
        "url": "https://example.com",
        "pages_analyzed": 50,
        "deep_analysis": {
            "quality_score": 75.5,
            "seo_coverage": {
                "title": "50/50",
                "description": "45/50",
                "h1": "48/50"
            },
            "schema_coverage": "30/50",
            "cwv": {
                "score": 65.0,
                "avg_lcp": 2.8,
                "avg_cls": 0.15
            },
            "mobile": {
                "score": 80.0
            },
            "accessibility": {
                "score": 70.0
            },
            "security": {
                "score": 85.0,
                "https_rate": 100.0
            }
        }
    }

    task = Task(
        task_id="test-qa-validation",
        subtask_id="test-qa-validation-1",
        action="validate_analysis",
        payload={"analysis_result": analysis_result},
        priority=1,
        created_at=datetime.now()
    )

    result = await validator.execute_task(task)

    print(f"\n✅ Validation completed:")
    print(f"  Status: {result.result['validation_status']}")
    print(f"  Quality Score: {result.result['quality_report']['quality_score']:.1f}/100")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
