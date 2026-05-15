# Research Part 2: Automated Reporting Systems

**Date:** 2026-05-15  
**Focus:** Report generation, scheduling, and delivery automation  
**Budget:** N/A (GitHub + web search)

---

## Executive Summary

Исследовал production-ready решения для автоматизированной системы отчётности. Нашёл 3 топовых подхода:

1. **ReportLab + APScheduler** — простой, надёжный, без внешних зависимостей
2. **ZipReport + Celery** — enterprise-grade с HTML→PDF через headless browser
3. **SendGrid/Mailgun API** — для email delivery с tracking

**Рекомендация:** Комбинированный подход — ReportLab для PDF, APScheduler для scheduling, SendGrid для delivery.

---

## Top 3 GitHub Repositories

### 1. automated-weekly-marketing-report-builder ⭐⭐⭐⭐⭐

**URL:** https://github.com/jamous-max/automated-weekly-marketing-report-builder  
**Stars:** 0 (новый, но качественный)  
**Language:** Python  
**Last Updated:** 2026-03-02

**Что делает:**
- Загружает CSV с маркетинговыми данными
- Очищает и агрегирует метрики (impressions, clicks, CTR, conversions, revenue)
- Генерирует PDF отчёты с ReportLab
- Week-over-week сравнение с классификацией (Baseline, Growth, Decline, Stable)
- Risk level tagging (Low, Medium, High)
- History tracking (не обрабатывает дважды одну неделю)
- AI-powered executive summary (опционально)

**Архитектура:**
```
main.py (orchestrator)
  ↓
src/
├── loader.py          # CSV loading
├── cleaner.py         # Data cleaning
├── aggregator.py      # Metrics aggregation
├── comparison.py      # Week-over-week analysis
├── ai_summary.py      # Executive summary generation
├── pdf_report.py      # PDF generation (ReportLab)
├── summary_report.py  # TXT report generation
└── history_logger.py  # History tracking
```

**Ключевые паттерны:**

1. **History Tracking Pattern:**
```python
# history.csv хранит обработанные недели
if history_file.exists():
    history_df = pd.read_csv(history_file)
    processed_weeks = set(history_df["week_number"].astype(int))
else:
    processed_weeks = set()

# Пропускаем уже обработанные
for week in unique_weeks:
    if week in processed_weeks:
        print(f"Week {week} already processed — skipping.")
        continue
```

2. **Risk Classification Pattern:**
```python
# config.py
HIGH_RISK_REVENUE_DROP = 0.10  # 10% drop
MEDIUM_RISK_REVENUE_DROP = 0.05  # 5% drop

def classify_risk(revenue_change_pct):
    if revenue_change_pct <= -HIGH_RISK_REVENUE_DROP:
        return "High"
    elif revenue_change_pct <= -MEDIUM_RISK_REVENUE_DROP:
        return "Medium"
    else:
        return "Low"
```

3. **PDF Generation Pattern (ReportLab):**
```python
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf_report(totals_df, output_path, week_number, start_date, end_date, executive_summary):
    doc = SimpleDocTemplate(str(output_path))
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph("<b>Weekly Marketing Performance Report</b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Period info
    period_info = Paragraph(
        f"<b>Week {week_number}</b><br/>"
        f"Reporting Period: {start_date} - {end_date}",
        styles["Normal"],
    )
    elements.append(period_info)
    
    # Executive summary
    summary_lines = executive_summary.split("\n")
    for line in summary_lines:
        if line.startswith("Week Type:") or line.startswith("Risk Level:"):
            elements.append(Paragraph(f"<b>{line}</b>", styles["Normal"]))
        else:
            elements.append(Paragraph(line, styles["Normal"]))
    
    # Metrics table
    table_data = [["Metric", "Value"]]
    for _, row in totals_df.iterrows():
        table_data.append([row["metric"], f"{row['value']:,}"])
    
    table = Table(table_data, colWidths=[3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    
    doc.build(elements)
```

**Dependencies:**
```
pandas
reportlab
```

**Что взять:**
- ✅ History tracking pattern (не обрабатывать дважды)
- ✅ Risk classification (High/Medium/Low)
- ✅ Week-over-week comparison logic
- ✅ ReportLab PDF generation pattern
- ✅ Modular architecture (loader → cleaner → aggregator → report)

---

### 2. zipreport ⭐⭐⭐⭐

**URL:** https://github.com/zipreport/zipreport  
**Stars:** N/A (official library)  
**Language:** Python  
**Last Updated:** Active

**Что делает:**
- HTML → PDF через headless browser (zipreport-server)
- Jinja2 templating для отчётов
- PagedJS support (headers, footers, page numbers, TOC)
- Dynamic image embedding
- MIME email generation
- JavaScript support в отчётах

**Архитектура:**
```
zipreport/
├── zipreport.py       # Main API (ZipReport, MIMEReport)
├── report/
│   ├── job.py         # ReportJob, JobResult
│   ├── reportfile.py  # ReportFile (zpt format)
│   └── loader.py      # ReportFileLoader
├── processors/
│   ├── interface.py   # ProcessorInterface
│   ├── zipreport.py   # ZipReportProcessor (API client)
│   └── mime.py        # MIMEProcessor (email)
└── template/
    ├── jinjarender.py # Jinja2 rendering
    └── environment.py # Environment wrapper
```

**Ключевые паттерны:**

1. **Report Job Pattern:**
```python
from zipreport import ZipReport
from zipreport.report import ReportFileLoader

# Load template
zpt = ReportFileLoader.load("report.zpt")

# Create job
client = ZipReport("https://127.0.0.1:6543", "secretKey")
job = client.create_job(zpt)

# Configure job
job.set_page_size("A4")
job.set_margins("default")
job.set_landscape(False)

# Render with data
report_data = {
    'title': "Q1 Report",
    'metrics': [...],
}
result = client.render(job, report_data)

# Save PDF
if result.success:
    with open("output.pdf", 'wb') as f:
        f.write(result.report.read())
```

2. **PagedJS Support (Headers/Footers/TOC):**
```html
<!-- report.html -->
<style>
@page {
  size: A4;
  margin: 2cm;
  
  @top-center {
    content: "Company Report";
  }
  
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
  }
}
</style>

<div class="page-break">
  <h1>{{ title }}</h1>
  <table>
    {% for metric in metrics %}
    <tr>
      <td>{{ metric.name }}</td>
      <td>{{ metric.value }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
```

3. **MIME Email Generation:**
```python
from zipreport import MIMEReport

mime_report = MIMEReport()
job = mime_report.create_job(zpt)
result = mime_report.render(job, report_data)

# result.report is MIME message ready to send
```

**Dependencies:**
```
zipreport-lib>=2.0.0
jinja2>=3.1
zipreport-server (Docker container)
```

**Что взять:**
- ✅ HTML templating approach (более гибкий чем ReportLab)
- ✅ PagedJS для headers/footers/page numbers
- ✅ Job configuration pattern
- ⚠️ Требует zipreport-server (Docker) — сложнее деплоить

---

### 3. Weekly-Business-Report-Automation ⭐⭐⭐⭐

**URL:** https://github.com/jihanKamilah/Weekly-Business-Report-Automation  
**Stars:** N/A  
**Language:** Python  
**Last Updated:** 2026-04-13

**Что делает:**
- ETL pipeline для бизнес-отчётов
- Cutoff-based simulation (имитация weekly updates)
- PDF generation с matplotlib charts
- Email delivery через SMTP
- GitHub Actions automation

**Архитектура:**
```
extract.py          # Load datasets
  ↓
transform.py        # Data cleaning
  ↓
simulate.py         # Weekly cutoff simulation
  ↓
metrics.py          # Business metrics
  ↓
insight.py          # Insight generation
  ↓
report.py           # PDF with charts
  ↓
main.py             # Email automation
```

**Ключевые паттерны:**

1. **Cutoff-Based Simulation:**
```python
# Имитация weekly updates
def simulate_weekly_cutoff(df, cutoff_date):
    """Filter data up to cutoff date"""
    return df[df['date'] <= cutoff_date]

# State management
def update_state(next_cutoff):
    """Save next cutoff for next run"""
    with open('state.json', 'w') as f:
        json.dump({'next_cutoff': next_cutoff}, f)
```

2. **Charts in PDF (Matplotlib + ReportLab):**
```python
import matplotlib.pyplot as plt
from reportlab.platypus import Image

# Generate chart
fig, ax = plt.subplots()
ax.plot(dates, revenue)
plt.savefig('chart.png')

# Embed in PDF
elements.append(Image('chart.png', width=6*inch, height=4*inch))
```

3. **Email Automation (SMTP):**
```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(pdf_path, recipient):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = f"Weekly Report - {date}"
    
    # Attach PDF
    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={pdf_path}')
        msg.attach(part)
    
    # Send
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
```

4. **GitHub Actions Scheduling:**
```yaml
# .github/workflows/auto-report.yml
name: Weekly Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Generate report
        run: python main.py
      - name: Commit state
        run: |
          git config user.name "GitHub Actions"
          git add state.json
          git commit -m "Update state"
          git push
```

**Dependencies:**
```
pandas
matplotlib
reportlab
smtplib (built-in)
```

**Что взять:**
- ✅ Cutoff-based simulation (для тестирования)
- ✅ Charts in PDF pattern
- ✅ SMTP email delivery
- ✅ GitHub Actions scheduling example

---

## Scheduling Tools Comparison

### APScheduler vs Celery

| Feature | APScheduler | Celery Beat |
|---------|-------------|-------------|
| **Complexity** | Simple | Complex |
| **Setup** | Single process | Broker + Worker + Beat |
| **Persistence** | SQLAlchemy, Redis, MongoDB | Database (django-celery-beat) |
| **Distributed** | No | Yes |
| **Scalability** | Single machine | Multiple workers |
| **Use Case** | Simple scheduling | Complex workflows |
| **Dependencies** | Minimal | Redis/RabbitMQ required |

### APScheduler Example

```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

# Configure persistent job store
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

# Add cron job
scheduler.add_job(
    func=generate_weekly_report,
    trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
    id='weekly_report',
    replace_existing=True,
)

# Add interval job
scheduler.add_job(
    func=check_metrics,
    trigger='interval',
    hours=1,
    id='hourly_check',
)

scheduler.start()
```

### Celery Beat Example

```python
from celery import Celery
from celery.schedules import crontab

app = Celery('tasks', broker='redis://localhost:6379/0')

app.conf.beat_schedule = {
    'weekly-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(day_of_week='monday', hour=9, minute=0),
    },
    'hourly-check': {
        'task': 'tasks.check_metrics',
        'schedule': crontab(minute=0),  # Every hour
    },
}

@app.task
def generate_report():
    # Report generation logic
    pass
```

**Рекомендация:** APScheduler для нашего случая (проще, меньше зависимостей, достаточно функциональности).

---

## Email Delivery Solutions

### SendGrid vs Mailgun vs SMTP

| Feature | SendGrid | Mailgun | SMTP (Gmail) |
|---------|----------|---------|--------------|
| **Setup** | API key | API key | App password |
| **Tracking** | Opens, clicks, bounces | Opens, clicks, bounces | No |
| **Deliverability** | Excellent | Excellent | Good |
| **Cost** | Free: 100/day, Paid: $19.95/mo | Free: 5000/mo, Paid: $35/mo | Free |
| **Rate Limits** | High | High | Low (500/day) |
| **Templates** | Yes | Yes | No |
| **Webhooks** | Yes | Yes | No |

### SendGrid Example

```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

def send_report_email(recipient, pdf_path, report_date):
    message = Mail(
        from_email='reports@iamaim.ru',
        to_emails=recipient,
        subject=f'Weekly Report - {report_date}',
        html_content=f'''
        <h2>Weekly Marketing Report</h2>
        <p>Please find attached your weekly report for {report_date}.</p>
        <p>Key highlights:</p>
        <ul>
            <li>Revenue: +15% vs last week</li>
            <li>Conversions: 234 (+12%)</li>
            <li>CTR: 3.2% (+0.5%)</li>
        </ul>
        '''
    )
    
    # Attach PDF
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    encoded = base64.b64encode(data).decode()
    attachment = Attachment(
        FileContent(encoded),
        FileName('weekly_report.pdf'),
        FileType('application/pdf'),
        Disposition('attachment')
    )
    message.attachment = attachment
    
    # Send
    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    response = sg.send(message)
    
    return response.status_code == 202
```

### Mailgun Example

```python
import requests

def send_report_mailgun(recipient, pdf_path, report_date):
    return requests.post(
        "https://api.mailgun.net/v3/iamaim.ru/messages",
        auth=("api", os.environ.get('MAILGUN_API_KEY')),
        files=[("attachment", ("report.pdf", open(pdf_path, "rb")))],
        data={
            "from": "Reports <reports@iamaim.ru>",
            "to": recipient,
            "subject": f"Weekly Report - {report_date}",
            "html": "<h2>Your weekly report is attached</h2>",
            "o:tracking": "yes",
            "o:tracking-opens": "yes",
            "o:tracking-clicks": "yes",
        }
    )
```

**Рекомендация:** SendGrid (лучший баланс цена/функциональность, отличная документация).

---

## Implementation Recommendations

### Architecture

```
Reporting System
├── Report Generator
│   ├── Data Collector (fetch metrics from DB)
│   ├── Data Processor (aggregate, calculate)
│   ├── Report Builder (ReportLab PDF)
│   └── Chart Generator (matplotlib)
├── Scheduler (APScheduler)
│   ├── Job Store (SQLite)
│   ├── Cron Triggers
│   └── Interval Triggers
├── Delivery Service
│   ├── SendGrid Client
│   ├── Email Templates
│   └── Attachment Handler
└── History Tracker
    ├── Processed Reports Log
    └── Delivery Status Log
```

### Tech Stack

**Core:**
- `pandas>=2.0.0` — data processing
- `reportlab>=4.0.0` — PDF generation
- `matplotlib>=3.7.0` — charts
- `jinja2>=3.1.0` — templating

**Scheduling:**
- `apscheduler>=3.10.0` — job scheduling
- `sqlalchemy>=2.0.0` — job persistence

**Email:**
- `sendgrid>=6.11.0` — email delivery
- `python-dotenv>=1.0.0` — config management

**Optional:**
- `zipreport-lib>=2.0.0` — если нужен HTML→PDF
- `weasyprint>=60.0` — альтернатива zipreport

### Code Structure

```
AIM/src/aim/reporting/
├── __init__.py
├── generator.py          # Report generation logic
│   ├── ReportGenerator
│   ├── DataCollector
│   ├── DataProcessor
│   └── ChartGenerator
├── builder.py            # PDF building (ReportLab)
│   ├── PDFBuilder
│   ├── TableBuilder
│   └── ChartEmbedder
├── scheduler.py          # APScheduler integration
│   ├── ReportScheduler
│   ├── JobManager
│   └── TriggerFactory
├── delivery.py           # Email delivery (SendGrid)
│   ├── EmailDelivery
│   ├── AttachmentHandler
│   └── TemplateRenderer
├── history.py            # History tracking
│   ├── HistoryTracker
│   └── DeliveryLog
└── templates/
    ├── weekly_report.html
    ├── monthly_report.html
    └── executive_summary.html
```

### Example Usage

```python
from AIM.src.aim.reporting import ReportGenerator, ReportScheduler, EmailDelivery

# Initialize components
generator = ReportGenerator(db_session)
scheduler = ReportScheduler(jobstore_url='sqlite:///jobs.db')
delivery = EmailDelivery(sendgrid_api_key=os.getenv('SENDGRID_API_KEY'))

# Define report job
def generate_weekly_report():
    # Collect data
    data = generator.collect_weekly_data()
    
    # Generate PDF
    pdf_path = generator.build_pdf(
        data=data,
        template='weekly_report',
        output_path=f'reports/weekly_{date.today()}.pdf'
    )
    
    # Send email
    delivery.send_report(
        recipients=['client@example.com'],
        pdf_path=pdf_path,
        subject=f'Weekly Report - {date.today()}',
        template='weekly_email'
    )
    
    # Log history
    generator.log_delivery(pdf_path, recipients)

# Schedule job
scheduler.add_job(
    func=generate_weekly_report,
    trigger='cron',
    day_of_week='mon',
    hour=9,
    minute=0,
    id='weekly_report',
)

scheduler.start()
```

---

## Key Patterns to Implement

### 1. History Tracking Pattern

```python
class HistoryTracker:
    def __init__(self, db_session):
        self.db = db_session
    
    def is_processed(self, report_id: str) -> bool:
        """Check if report already generated"""
        return self.db.query(ReportHistory).filter_by(report_id=report_id).first() is not None
    
    def mark_processed(self, report_id: str, pdf_path: str, recipients: list):
        """Mark report as processed"""
        history = ReportHistory(
            report_id=report_id,
            pdf_path=pdf_path,
            recipients=json.dumps(recipients),
            generated_at=datetime.utcnow(),
        )
        self.db.add(history)
        self.db.commit()
```

### 2. Risk Classification Pattern

```python
class RiskClassifier:
    HIGH_RISK_THRESHOLD = 0.10  # 10% drop
    MEDIUM_RISK_THRESHOLD = 0.05  # 5% drop
    
    def classify(self, current: float, previous: float) -> str:
        """Classify risk level based on change"""
        change_pct = (current - previous) / previous if previous > 0 else 0
        
        if change_pct <= -self.HIGH_RISK_THRESHOLD:
            return "High"
        elif change_pct <= -self.MEDIUM_RISK_THRESHOLD:
            return "Medium"
        else:
            return "Low"
```

### 3. Retry Pattern (Email Delivery)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class EmailDelivery:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def send_email(self, recipient: str, pdf_path: str):
        """Send email with retry logic"""
        try:
            response = self.sendgrid_client.send(message)
            if response.status_code != 202:
                raise Exception(f"SendGrid error: {response.status_code}")
            return True
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            raise
```

### 4. Template Rendering Pattern

```python
from jinja2 import Environment, FileSystemLoader

class TemplateRenderer:
    def __init__(self, templates_dir: str):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
    
    def render_email(self, template_name: str, data: dict) -> str:
        """Render email template"""
        template = self.env.get_template(f'{template_name}.html')
        return template.render(**data)
    
    def render_pdf_html(self, template_name: str, data: dict) -> str:
        """Render PDF template"""
        template = self.env.get_template(f'{template_name}.html')
        return template.render(**data)
```

---

## Cost Analysis

### SendGrid Pricing

| Plan | Price | Emails/Month | Features |
|------|-------|--------------|----------|
| Free | $0 | 100/day (3,000/mo) | Basic sending |
| Essentials | $19.95/mo | 50,000 | Email API, Templates |
| Pro | $89.95/mo | 100,000 | Advanced stats, Dedicated IP |

**Estimate for AIM:**
- 50 clients × 4 reports/month = 200 emails/month
- Free tier sufficient for MVP
- Upgrade to Essentials when > 100 emails/day

### Mailgun Pricing

| Plan | Price | Emails/Month | Features |
|------|-------|--------------|----------|
| Trial | $0 | 5,000 | Full features |
| Foundation | $35/mo | 50,000 | Email validation |
| Growth | $80/mo | 100,000 | Dedicated IP |

**Estimate for AIM:**
- Free tier sufficient for MVP (5,000/month)
- Upgrade to Foundation at scale

### Infrastructure Costs

**APScheduler + SQLite:**
- $0 (runs in-process)
- No external dependencies
- Suitable for single-server deployment

**Celery + Redis:**
- Redis: $10-30/mo (managed service)
- Additional complexity
- Only needed for distributed deployment

**Recommendation:** Start with APScheduler, migrate to Celery if needed.

---

## Security Considerations

### API Keys Management

```python
# .env
SENDGRID_API_KEY=SG.xxx
MAILGUN_API_KEY=key-xxx

# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    sendgrid_api_key: str
    mailgun_api_key: str
    
    class Config:
        env_file = '.env'

settings = Settings()
```

### PDF Security

```python
from reportlab.lib.pdfencrypt import StandardEncryption

# Encrypt PDF
encrypt = StandardEncryption(
    userPassword='client_password',
    ownerPassword='admin_password',
    canPrint=1,
    canModify=0,
    canCopy=0,
)

doc = SimpleDocTemplate('report.pdf', encrypt=encrypt)
```

### Email Security

- Use DKIM signing (SendGrid/Mailgun handle this)
- SPF records for domain
- DMARC policy
- TLS for SMTP connections

---

## Testing Strategy

### Unit Tests

```python
def test_report_generation():
    generator = ReportGenerator(mock_db)
    data = generator.collect_weekly_data()
    assert len(data) > 0
    
    pdf_path = generator.build_pdf(data, 'weekly_report')
    assert os.path.exists(pdf_path)

def test_risk_classification():
    classifier = RiskClassifier()
    assert classifier.classify(90, 100) == "High"  # 10% drop
    assert classifier.classify(95, 100) == "Medium"  # 5% drop
    assert classifier.classify(100, 100) == "Low"  # No change
```

### Integration Tests

```python
def test_email_delivery():
    delivery = EmailDelivery(api_key='test_key')
    result = delivery.send_email(
        recipient='test@example.com',
        pdf_path='test_report.pdf'
    )
    assert result is True

def test_scheduler():
    scheduler = ReportScheduler()
    job_id = scheduler.add_job(
        func=mock_report_generation,
        trigger='interval',
        seconds=10,
    )
    assert scheduler.get_job(job_id) is not None
```

---

## Migration Path

### Phase 1: MVP (Week 1-2)
- ✅ ReportLab PDF generation
- ✅ Basic email delivery (SMTP)
- ✅ Manual triggering

### Phase 2: Automation (Week 3-4)
- ✅ APScheduler integration
- ✅ Cron-based scheduling
- ✅ History tracking

### Phase 3: Enhancement (Week 5-6)
- ✅ SendGrid integration
- ✅ Email templates
- ✅ Delivery tracking

### Phase 4: Scale (Week 7-8)
- ✅ Charts in PDF
- ✅ Risk classification
- ✅ Multi-client support

---

## Conclusion

**Recommended Stack:**
- **PDF Generation:** ReportLab (simple, reliable)
- **Scheduling:** APScheduler (no external dependencies)
- **Email Delivery:** SendGrid (best features/price ratio)
- **Persistence:** SQLite (APScheduler job store)

**Why not Celery?**
- Overkill for our use case
- Requires Redis/RabbitMQ
- More complex deployment
- APScheduler sufficient for single-server

**Why not ZipReport?**
- Requires Docker container (zipreport-server)
- More complex setup
- ReportLab sufficient for our needs
- Consider for future if need HTML→PDF

**Next Steps:**
1. Implement ReportGenerator with ReportLab
2. Add APScheduler for weekly/monthly reports
3. Integrate SendGrid for email delivery
4. Add history tracking to prevent duplicates
5. Implement risk classification for insights

**Estimated Timeline:** 2-3 weeks for full implementation.
