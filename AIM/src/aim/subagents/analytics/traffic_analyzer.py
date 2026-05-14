"""
Traffic Analyzer - Website Traffic Analysis.

Analyzes website traffic patterns using Google Analytics 4 and Yandex Metrica.
Provides traffic sources breakdown, user behavior analysis, and conversion funnels.

Based on: GA4 Reporting API + Yandex Metrica API
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog


@dataclass
class TrafficSource:
    """Traffic source data."""

    source: str  # google, yandex, direct, referral, social
    sessions: int
    users: int
    pageviews: int
    bounce_rate: float
    avg_session_duration: float  # seconds


@dataclass
class UserBehavior:
    """User behavior metrics."""

    new_users: int
    returning_users: int
    total_users: int
    new_user_rate: float
    pages_per_session: float
    avg_session_duration: float


@dataclass
class ConversionFunnel:
    """Conversion funnel step."""

    step_name: str
    step_number: int
    users: int
    conversion_rate: float  # % from previous step
    drop_off_rate: float  # % dropped from previous step


@dataclass
class BounceAnalysis:
    """Bounce rate analysis."""

    overall_bounce_rate: float
    bounce_by_source: dict[str, float]
    high_bounce_pages: list[dict[str, Any]]
    low_bounce_pages: list[dict[str, Any]]


@dataclass
class SessionAnalysis:
    """Session duration analysis."""

    avg_duration: float  # seconds
    median_duration: float
    duration_by_source: dict[str, float]
    short_sessions: int  # < 30 seconds
    medium_sessions: int  # 30s - 3min
    long_sessions: int  # > 3min


@dataclass
class TrafficReport:
    """Complete traffic analysis report."""

    start_date: str
    end_date: str
    timestamp: str

    # Traffic sources
    traffic_sources: list[TrafficSource]
    total_sessions: int
    total_users: int
    total_pageviews: int

    # User behavior
    user_behavior: UserBehavior

    # Conversion funnel
    conversion_funnel: list[ConversionFunnel]
    overall_conversion_rate: float

    # Bounce analysis
    bounce_analysis: BounceAnalysis

    # Session analysis
    session_analysis: SessionAnalysis

    # Top insights
    insights: list[str]


class TrafficAnalyzer:
    """
    Traffic Analyzer.

    Analyzes website traffic patterns using Google Analytics 4
    and Yandex Metrica APIs.
    """

    def __init__(
        self,
        ga4_property_id: str | None = None,
        yandex_counter_id: str | None = None,
    ):
        """
        Initialize Traffic Analyzer.

        Args:
            ga4_property_id: Google Analytics 4 property ID
            yandex_counter_id: Yandex Metrica counter ID
        """
        self.logger = structlog.get_logger()
        self.ga4_property_id = ga4_property_id
        self.yandex_counter_id = yandex_counter_id

    async def analyze(
        self,
        start_date: str,  # YYYY-MM-DD
        end_date: str,  # YYYY-MM-DD
        source: str = "ga4",  # ga4, yandex, both
    ) -> TrafficReport:
        """
        Analyze traffic for date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            source: Data source (ga4, yandex, both)

        Returns:
            Complete traffic analysis report
        """
        self.logger.info(
            "traffic_analysis_start",
            start_date=start_date,
            end_date=end_date,
            source=source,
        )

        # Step 1: Fetch traffic sources
        traffic_sources = await self._fetch_traffic_sources(
            start_date,
            end_date,
            source,
        )

        # Step 2: Analyze user behavior
        user_behavior = await self._analyze_user_behavior(
            start_date,
            end_date,
            source,
        )

        # Step 3: Analyze conversion funnel
        conversion_funnel = await self._analyze_conversion_funnel(
            start_date,
            end_date,
            source,
        )

        # Step 4: Analyze bounce rate
        bounce_analysis = await self._analyze_bounce_rate(
            start_date,
            end_date,
            source,
        )

        # Step 5: Analyze session duration
        session_analysis = await self._analyze_session_duration(
            start_date,
            end_date,
            source,
        )

        # Step 6: Calculate totals
        total_sessions = sum(s.sessions for s in traffic_sources)
        total_users = sum(s.users for s in traffic_sources)
        total_pageviews = sum(s.pageviews for s in traffic_sources)

        # Step 7: Calculate overall conversion rate
        overall_conversion_rate = 0.0
        if conversion_funnel:
            last_step = conversion_funnel[-1]
            first_step = conversion_funnel[0]
            if first_step.users > 0:
                overall_conversion_rate = (last_step.users / first_step.users) * 100

        # Step 8: Generate insights
        insights = self._generate_insights(
            traffic_sources,
            user_behavior,
            bounce_analysis,
            session_analysis,
        )

        report = TrafficReport(
            start_date=start_date,
            end_date=end_date,
            timestamp=datetime.now().isoformat(),
            traffic_sources=traffic_sources,
            total_sessions=total_sessions,
            total_users=total_users,
            total_pageviews=total_pageviews,
            user_behavior=user_behavior,
            conversion_funnel=conversion_funnel,
            overall_conversion_rate=round(overall_conversion_rate, 2),
            bounce_analysis=bounce_analysis,
            session_analysis=session_analysis,
            insights=insights,
        )

        self.logger.info(
            "traffic_analysis_complete",
            total_sessions=total_sessions,
            total_users=total_users,
            conversion_rate=overall_conversion_rate,
        )

        return report

    async def _fetch_traffic_sources(
        self,
        start_date: str,
        end_date: str,
        source: str,
    ) -> list[TrafficSource]:
        """Fetch traffic sources breakdown."""
        # Mock data for now (real implementation would call GA4/Yandex API)
        sources = [
            TrafficSource(
                source="google",
                sessions=5000,
                users=4200,
                pageviews=15000,
                bounce_rate=45.5,
                avg_session_duration=180.0,
            ),
            TrafficSource(
                source="yandex",
                sessions=3000,
                users=2500,
                pageviews=9000,
                bounce_rate=50.2,
                avg_session_duration=150.0,
            ),
            TrafficSource(
                source="direct",
                sessions=2000,
                users=1800,
                pageviews=6000,
                bounce_rate=35.0,
                avg_session_duration=200.0,
            ),
            TrafficSource(
                source="referral",
                sessions=1000,
                users=900,
                pageviews=3000,
                bounce_rate=55.0,
                avg_session_duration=120.0,
            ),
            TrafficSource(
                source="social",
                sessions=500,
                users=450,
                pageviews=1500,
                bounce_rate=60.0,
                avg_session_duration=90.0,
            ),
        ]

        return sources

    async def _analyze_user_behavior(
        self,
        start_date: str,
        end_date: str,
        source: str,
    ) -> UserBehavior:
        """Analyze user behavior metrics."""
        # Mock data
        new_users = 7000
        returning_users = 2850
        total_users = new_users + returning_users

        return UserBehavior(
            new_users=new_users,
            returning_users=returning_users,
            total_users=total_users,
            new_user_rate=round((new_users / total_users) * 100, 2),
            pages_per_session=3.2,
            avg_session_duration=165.0,
        )

    async def _analyze_conversion_funnel(
        self,
        start_date: str,
        end_date: str,
        source: str,
    ) -> list[ConversionFunnel]:
        """Analyze conversion funnel."""
        # Mock data
        funnel = [
            ConversionFunnel(
                step_name="Landing Page",
                step_number=1,
                users=10000,
                conversion_rate=100.0,
                drop_off_rate=0.0,
            ),
            ConversionFunnel(
                step_name="Product Page",
                step_number=2,
                users=6000,
                conversion_rate=60.0,
                drop_off_rate=40.0,
            ),
            ConversionFunnel(
                step_name="Add to Cart",
                step_number=3,
                users=3000,
                conversion_rate=50.0,
                drop_off_rate=50.0,
            ),
            ConversionFunnel(
                step_name="Checkout",
                step_number=4,
                users=1500,
                conversion_rate=50.0,
                drop_off_rate=50.0,
            ),
            ConversionFunnel(
                step_name="Purchase",
                step_number=5,
                users=1000,
                conversion_rate=66.7,
                drop_off_rate=33.3,
            ),
        ]

        return funnel

    async def _analyze_bounce_rate(
        self,
        start_date: str,
        end_date: str,
        source: str,
    ) -> BounceAnalysis:
        """Analyze bounce rate."""
        # Mock data
        return BounceAnalysis(
            overall_bounce_rate=47.5,
            bounce_by_source={
                "google": 45.5,
                "yandex": 50.2,
                "direct": 35.0,
                "referral": 55.0,
                "social": 60.0,
            },
            high_bounce_pages=[
                {"page": "/blog/post-1", "bounce_rate": 75.0, "sessions": 500},
                {"page": "/promo", "bounce_rate": 70.0, "sessions": 300},
            ],
            low_bounce_pages=[
                {"page": "/products", "bounce_rate": 25.0, "sessions": 1000},
                {"page": "/services", "bounce_rate": 30.0, "sessions": 800},
            ],
        )

    async def _analyze_session_duration(
        self,
        start_date: str,
        end_date: str,
        source: str,
    ) -> SessionAnalysis:
        """Analyze session duration."""
        # Mock data
        return SessionAnalysis(
            avg_duration=165.0,
            median_duration=120.0,
            duration_by_source={
                "google": 180.0,
                "yandex": 150.0,
                "direct": 200.0,
                "referral": 120.0,
                "social": 90.0,
            },
            short_sessions=3000,
            medium_sessions=5000,
            long_sessions=2500,
        )

    def _generate_insights(
        self,
        traffic_sources: list[TrafficSource],
        user_behavior: UserBehavior,
        bounce_analysis: BounceAnalysis,
        session_analysis: SessionAnalysis,
    ) -> list[str]:
        """Generate actionable insights."""
        insights = []

        # Top traffic source
        if traffic_sources:
            top_source = max(traffic_sources, key=lambda x: x.sessions)
            insights.append(
                f"Основной источник трафика: {top_source.source} "
                f"({top_source.sessions:,} сессий, {top_source.sessions / sum(s.sessions for s in traffic_sources) * 100:.1f}%)"
            )

        # New vs returning users
        if user_behavior.new_user_rate > 70:
            insights.append(
                f"Высокая доля новых пользователей ({user_behavior.new_user_rate:.1f}%) - "
                "фокус на удержание"
            )
        elif user_behavior.new_user_rate < 30:
            insights.append(
                f"Низкая доля новых пользователей ({user_behavior.new_user_rate:.1f}%) - "
                "нужно привлечение"
            )

        # Bounce rate
        if bounce_analysis.overall_bounce_rate > 60:
            insights.append(
                f"Высокий показатель отказов ({bounce_analysis.overall_bounce_rate:.1f}%) - "
                "проверьте релевантность контента"
            )

        # Session duration
        if session_analysis.avg_duration < 60:
            insights.append(
                f"Короткая средняя длительность сессии ({session_analysis.avg_duration:.0f}s) - "
                "улучшите вовлечённость"
            )

        # High bounce pages
        if bounce_analysis.high_bounce_pages:
            page = bounce_analysis.high_bounce_pages[0]
            insights.append(
                f"Страница с высоким отказом: {page['page']} ({page['bounce_rate']:.1f}%)"
            )

        return insights


async def main():
    """Example usage."""
    analyzer = TrafficAnalyzer(
        ga4_property_id="123456789",
        yandex_counter_id="987654321",
    )

    # Analyze last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)

    report = await analyzer.analyze(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        source="ga4",
    )

    print(f"Traffic Report: {report.start_date} - {report.end_date}")
    print(f"Total Sessions: {report.total_sessions:,}")
    print(f"Total Users: {report.total_users:,}")
    print(f"Total Pageviews: {report.total_pageviews:,}")
    print(f"Overall Conversion Rate: {report.overall_conversion_rate:.2f}%")
    print()

    print("Top Traffic Sources:")
    for source in report.traffic_sources[:3]:
        print(f"  {source.source}: {source.sessions:,} sessions ({source.bounce_rate:.1f}% bounce)")

    print()
    print("Insights:")
    for insight in report.insights:
        print(f"  - {insight}")


if __name__ == "__main__":
    asyncio.run(main())


# ==============================================================================
# Added by Teacher Agent: traffic-analyzer
# ==============================================================================

import asyncio

async def execute(
        self, recompute_atoms: set[str] | None = None
    ) -> dict[str, Any]:
        """
        Executes atoms in the workflow, with selective recomputation.

        Args:
            recompute_atoms: Optional set of atom names to force recomputation,
                           regardless of cache status
        """
        self._is_rerun = True  # prevent duplicate re-registration
        try:
            # Clear caches and component producers, but not atoms
            self.cache.cache.clear()
            self._component_producers.clear()

            execution_order = self._get_execution_order()
            atoms_to_recompute = self._get_affected_atoms(recompute_atoms or set())

            logger.info(f"[DAG] Atoms to recompute {atoms_to_recompute=}")

            for atom_name in execution_order:
                if self._is_rerun and recompute_atoms and atom_name not in atoms_to_recompute:
                    logger.info(f"[DAG] Skipping atom (not affected) {atom_name=}")
                    continue

                atom = self.atoms[atom_name]
                if atom_name in atoms_to_recompute:
                    atom.force_recompute = True

                result = self._execute_atom(atom)
                self.context.set_result(atom_name, result)
                atom.force_recompute = False

                if result.status == AtomStatus.FAILED:
                    logger.error(f"[DAG] Execution halted due to failure {atom_name=}")
                    break

            return self.context.results
        finally:
            self._is_rerun = False

# ==============================================================================
# Added by Teacher Agent: traffic-analyzer
# ==============================================================================

import asyncio

async def execute(
        self, recompute_atoms: set[str] | None = None
    ) -> dict[str, Any]:
        """
        Executes atoms in the workflow, with selective recomputation.

        Args:
            recompute_atoms: Optional set of atom names to force recomputation,
                           regardless of cache status
        """
        self._is_rerun = True  # prevent duplicate re-registration
        try:
            # Clear caches and component producers, but not atoms
            self.cache.cache.clear()
            self._component_producers.clear()

            execution_order = self._get_execution_order()
            atoms_to_recompute = self._get_affected_atoms(recompute_atoms or set())

            logger.info(f"[DAG] Atoms to recompute {atoms_to_recompute=}")

            for atom_name in execution_order:
                if self._is_rerun and recompute_atoms and atom_name not in atoms_to_recompute:
                    logger.info(f"[DAG] Skipping atom (not affected) {atom_name=}")
                    continue

                atom = self.atoms[atom_name]
                if atom_name in atoms_to_recompute:
                    atom.force_recompute = True

                result = self._execute_atom(atom)
                self.context.set_result(atom_name, result)
                atom.force_recompute = False

                if result.status == AtomStatus.FAILED:
                    logger.error(f"[DAG] Execution halted due to failure {atom_name=}")
                    break

            return self.context.results
        finally:
            self._is_rerun = False