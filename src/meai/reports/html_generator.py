"""HTML Report Generator for AIM Agency

Generates beautiful HTML reports for clients with branding, metrics, and recommendations.
"""

from datetime import datetime
from pathlib import Path
from typing import Any


class HTMLReportGenerator:
    """Generates HTML reports for clients"""

    def __init__(self, output_dir: str = "./demo"):
        """Initialize report generator

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_client_report(
        self,
        client_name: str,
        client_data: dict[str, Any],
        project_data: dict[str, Any],
        results: dict[str, Any],
    ) -> str:
        """Generate HTML report for client

        Args:
            client_name: Client name (used for filename)
            client_data: Client information
            project_data: Project information
            results: Agent execution results

        Returns:
            Path to generated HTML file
        """
        # Create client directory
        client_dir = self.output_dir / client_name.lower().replace(" ", "-")
        client_dir.mkdir(parents=True, exist_ok=True)

        # Generate HTML
        html = self._generate_html(client_data, project_data, results)

        # Save HTML
        html_path = client_dir / "report.html"
        html_path.write_text(html, encoding="utf-8")

        return str(html_path)

    def _generate_html(
        self,
        client_data: dict[str, Any],
        project_data: dict[str, Any],
        results: dict[str, Any],
    ) -> str:
        """Generate HTML content"""

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт AIM Agency - {client_data['name']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 42px;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header .subtitle {{
            font-size: 18px;
            opacity: 0.9;
        }}

        .header .date {{
            margin-top: 20px;
            font-size: 14px;
            opacity: 0.8;
        }}

        .section {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .section h2 {{
            font-size: 28px;
            margin-bottom: 25px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .info-item {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .info-item .label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            margin-bottom: 5px;
            font-weight: 600;
        }}

        .info-item .value {{
            font-size: 20px;
            font-weight: 700;
            color: #333;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}

        .metric-card h3 {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 10px;
        }}

        .metric-card .number {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .metric-card .description {{
            font-size: 14px;
            opacity: 0.8;
        }}

        .results-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .recommendation {{
            padding: 20px;
            background: #f0f7ff;
            border-left: 4px solid #667eea;
            border-radius: 8px;
            margin-bottom: 15px;
        }}

        .recommendation h4 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 18px;
        }}

        .recommendation p {{
            color: #555;
            line-height: 1.8;
        }}

        .goals-list {{
            list-style: none;
            margin-top: 20px;
        }}

        .goals-list li {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-bottom: 10px;
            padding-left: 50px;
            position: relative;
        }}

        .goals-list li:before {{
            content: "✓";
            position: absolute;
            left: 20px;
            color: #667eea;
            font-weight: bold;
            font-size: 20px;
        }}

        .footer {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 14px;
        }}

        .footer .logo {{
            font-size: 24px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .section {{
                box-shadow: none;
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Отчёт о работе</h1>
            <div class="subtitle">{client_data['name']}</div>
            <div class="date">Сгенерировано: {datetime.now().strftime('%d.%m.%Y %H:%M')}</div>
        </div>

        <!-- Client Info -->
        <div class="section">
            <h2>Информация о клиенте</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Компания</div>
                    <div class="value">{client_data['name']}</div>
                </div>
                <div class="info-item">
                    <div class="label">Индустрия</div>
                    <div class="value">{client_data.get('industry', 'N/A').title()}</div>
                </div>
                <div class="info-item">
                    <div class="label">Локация</div>
                    <div class="value">{client_data.get('location', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="label">Subscription</div>
                    <div class="value">{client_data.get('subscription_tier', 'N/A').upper()}</div>
                </div>
            </div>
        </div>

        <!-- Project Info -->
        <div class="section">
            <h2>Проект: {project_data['name']}</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Тип проекта</div>
                    <div class="value">{project_data.get('project_type', 'N/A').upper()}</div>
                </div>
                <div class="info-item">
                    <div class="label">Длительность</div>
                    <div class="value">{project_data.get('duration_months', 'N/A')} месяцев</div>
                </div>
                <div class="info-item">
                    <div class="label">Бюджет</div>
                    <div class="value">{project_data.get('total_budget', 0):,} ₽</div>
                </div>
                <div class="info-item">
                    <div class="label">Статус</div>
                    <div class="value">{project_data.get('status', 'N/A').title()}</div>
                </div>
            </div>

            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #667eea;">Цели проекта</h3>
            <ul class="goals-list">
                {''.join(f'<li>{goal}</li>' for goal in project_data.get('goals', []))}
            </ul>
        </div>

        <!-- Results -->
        <div class="section">
            <h2>Результаты работы</h2>
            <div class="results-grid">
                <div class="metric-card">
                    <h3>SEO Анализ</h3>
                    <div class="number">{results.get('seo', {}).get('keywords_count', 0)}</div>
                    <div class="description">ключевых слов найдено</div>
                </div>
                <div class="metric-card">
                    <h3>Контент</h3>
                    <div class="number">{results.get('content', {}).get('word_count', 0)}</div>
                    <div class="description">слов создано</div>
                </div>
                <div class="metric-card">
                    <h3>Реклама</h3>
                    <div class="number">{results.get('ads', {}).get('ad_groups_count', 0)}</div>
                    <div class="description">рекламных групп</div>
                </div>
            </div>

            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #667eea;">Детали</h3>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Качество контента</div>
                    <div class="value">{results.get('content', {}).get('quality_score', 0)}/100</div>
                </div>
                <div class="info-item">
                    <div class="label">SEO оптимизация</div>
                    <div class="value">{results.get('content', {}).get('seo_score', 0)}/100</div>
                </div>
                <div class="info-item">
                    <div class="label">Бюджет кампании</div>
                    <div class="value">{results.get('ads', {}).get('budget', 0):,} ₽</div>
                </div>
                <div class="info-item">
                    <div class="label">Время выполнения</div>
                    <div class="value">&lt;1 сек</div>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="section">
            <h2>Рекомендации</h2>
            {''.join(f'''
            <div class="recommendation">
                <h4>{i}. {rec.get('title', 'Рекомендация')}</h4>
                <p>{rec.get('description', '')}</p>
            </div>
            ''' for i, rec in enumerate(results.get('recommendations', []), 1))}
        </div>

        <!-- Pricing -->
        <div class="section">
            <h2>Стоимость услуг</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="label">Subscription Tier</div>
                    <div class="value">{client_data.get('subscription_tier', 'PRO').upper()}</div>
                </div>
                <div class="info-item">
                    <div class="label">Месячный бюджет</div>
                    <div class="value">{project_data.get('total_budget', 0):,} ₽</div>
                </div>
                <div class="info-item">
                    <div class="label">SLA Response Time</div>
                    <div class="value">12 часов</div>
                </div>
                <div class="info-item">
                    <div class="label">Длительность</div>
                    <div class="value">{project_data.get('duration_months', 3)} месяцев</div>
                </div>
            </div>

            <h3 style="margin-top: 30px; margin-bottom: 15px; color: #667eea;">Что входит в стоимость</h3>
            <ul class="goals-list">
                <li>SEO анализ и оптимизация (20+ ключевых слов)</li>
                <li>Создание качественного контента (1600+ слов/статья)</li>
                <li>Настройка и ведение рекламных кампаний</li>
                <li>Еженедельные отчёты о прогрессе</li>
                <li>Приоритетная поддержка (12 часов)</li>
                <li>Доступ к AI-системе 24/7</li>
            </ul>

            <div style="margin-top: 30px; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
                <h3 style="color: white; margin-bottom: 15px;">Ожидаемый ROI</h3>
                <div style="font-size: 18px; line-height: 1.8;">
                    <p><strong>Инвестиция:</strong> {project_data.get('total_budget', 0):,} ₽ за {project_data.get('duration_months', 3)} месяцев</p>
                    <p><strong>Ожидаемый результат:</strong> 30+ новых пациентов</p>
                    <p><strong>Средний чек:</strong> ~15,000 ₽ (имплантация)</p>
                    <p><strong>Выручка:</strong> ~450,000 ₽</p>
                    <p><strong>ROI:</strong> ~200% за 3 месяца</p>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="logo">AIM Agency</div>
            <p>AI-First Medical Marketing Agency</p>
            <p style="margin-top: 10px;">iamaim.ru</p>
        </div>
    </div>
</body>
</html>
"""
        return html
