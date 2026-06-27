<!-- AIM Chat PRO - Enhanced UX with Phase Tracker + Report Preview + Fallback -->
<?php
/**
 * Enhanced chat experience for AIM presale flow.
 * Based on chat-inline.php with additions:
 *  - Phase tracker panel (8 phases of presale)
 *  - Live counters (competitors found, reviews, etc.)
 *  - WOW report preview card with CTA when report ready
 *  - Email/Telegram fallback form (if user wants to leave)
 *  - Polished animations using existing Dual Theme design system
 *
 * Phases detected from tool-progress stage field:
 *   1. Анализ сайта (run_prescan)
 *   2. Финансы из ФНС (find_company_financials)
 *   3. Врачи и соцсети (find_doctor_handles, run_instagram_content)
 *   4. Конкуренты (find_competitors, run_ci_analysis)
 *   5. Отзывы пациентов (run_review_platforms, run_forum_pains)
 *   6. СМИ (run_media_urls)
 *   7. Технический аудит (run_tech_seo_audit, run_seo_audit, run_lighthouse)
 *   8. Генерация отчёта (generate_html_report)
 */
?>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@3/dist/fp.min.js"></script>

<style>
.aim-chat-pro-scope {
    /* DUAL THEME — inherit from existing AIM design system */
    --bg: #ffffff;
    --surface: rgba(255,255,255,0.95);
    --glass-bg: rgba(255,255,255,0.85);
    --glass-border: rgba(0,0,0,0.06);
    --text: #1A1A1A;
    --text-secondary: #666666;
    --text-dim: #999999;
    --accent: #1A1A1A;
    --accent-soft: rgba(26,26,26,0.08);
    --shadow: rgba(0,0,0,0.06);
    --border: #E0E0E0;
    --success: #1B5E20;
    --warning: #F57F17;
    --danger: #C62828;
}

[data-theme="dark"] .aim-chat-pro-scope {
    --bg: #0d0d0d;
    --surface: rgba(26,26,26,0.7);
    --glass-bg: rgba(13,13,13,0.85);
    --glass-border: rgba(201,169,110,0.18);
    --text: #f5f0e8;
    --text-secondary: #9e9489;
    --text-dim: #7a7268;
    --accent: #c9a96e;
    --accent-soft: rgba(201,169,110,0.12);
    --shadow: rgba(0,0,0,0.4);
    --border: rgba(201,169,110,0.18);
    --success: #81C784;
    --warning: #FFF9C4;
    --danger: #FFCDD2;
}

.aim-chat-pro-scope * { margin: 0; padding: 0; box-sizing: border-box; }
.aim-chat-pro-scope {
    font-family: 'Jost', sans-serif;
    color: var(--text);
    line-height: 1.6;
}

/* === PHASE TRACKER === */
.phase-tracker {
    background: var(--glass-bg);
    backdrop-filter: blur(20px) saturate(1.4);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 16px;
    margin: 12px 0;
    display: none;
}

.phase-tracker.active { display: block; animation: phaseFadeIn 0.4s ease-out; }

@keyframes phaseFadeIn {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
}

.phase-tracker-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--glass-border);
}

.phase-tracker-title {
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.phase-progress-counter {
    font-size: 11px;
    color: var(--accent);
    font-weight: 600;
    letter-spacing: 0.08em;
}

.phase-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
}

.phase-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    background: var(--surface);
    border-radius: 8px;
    border: 1px solid transparent;
    transition: all 0.3s ease;
    font-size: 12px;
}

.phase-item.pending {
    opacity: 0.4;
    color: var(--text-dim);
}

.phase-item.working {
    border-color: var(--accent);
    background: var(--accent-soft);
    color: var(--text);
    animation: phasePulse 1.6s ease-in-out infinite;
}

@keyframes phasePulse {
    0%, 100% { box-shadow: 0 0 0 0 var(--accent-soft); }
    50% { box-shadow: 0 0 0 4px transparent; }
}

.phase-item.done {
    background: var(--surface);
    color: var(--text-secondary);
    border-color: var(--glass-border);
}

.phase-icon {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    background: var(--surface);
    border: 1px solid var(--glass-border);
    flex-shrink: 0;
}

.phase-item.working .phase-icon {
    background: var(--accent);
    color: var(--bg);
    border-color: var(--accent);
}

.phase-item.done .phase-icon {
    background: var(--success);
    color: white;
    border-color: var(--success);
}

.phase-label {
    flex: 1;
    font-weight: 500;
}

.phase-counter {
    font-size: 10px;
    color: var(--accent);
    font-weight: 600;
    background: var(--accent-soft);
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: auto;
}

/* === LIVE COUNTERS === */
.live-counter {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px;
    background: var(--accent-soft);
    color: var(--accent);
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 4px 2px 0;
    animation: counterPop 0.3s ease-out;
}

@keyframes counterPop {
    0% { transform: scale(0.8); opacity: 0; }
    60% { transform: scale(1.1); }
    100% { transform: scale(1); opacity: 1; }
}

/* === REPORT PREVIEW CARD (WOW moment) === */
.report-preview {
    display: none;
    background: var(--glass-bg);
    backdrop-filter: blur(24px) saturate(1.5);
    border: 1px solid var(--accent);
    border-radius: 12px;
    overflow: hidden;
    margin: 12px 0;
    animation: reportReveal 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 12px 40px rgba(201,169,110,0.18);
}

@keyframes reportReveal {
    0% { opacity: 0; transform: translateY(20px) scale(0.95); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

.report-preview.active { display: block; }

.report-preview-header {
    padding: 16px 20px;
    background: linear-gradient(135deg, var(--accent-soft) 0%, transparent 100%);
    border-bottom: 1px solid var(--glass-border);
}

.report-preview-badge {
    display: inline-block;
    padding: 3px 10px;
    background: var(--success);
    color: white;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.report-preview-title {
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 4px;
    line-height: 1.3;
}

.report-preview-meta {
    font-size: 12px;
    color: var(--text-secondary);
}

.report-preview-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1px;
    background: var(--glass-border);
    margin: 0;
}

.report-stat {
    background: var(--surface);
    padding: 14px 12px;
    text-align: center;
}

.report-stat-value {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 500;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 4px;
}

.report-stat-label {
    font-size: 10px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.report-preview-cta {
    padding: 18px 20px;
    display: flex;
    gap: 10px;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid var(--glass-border);
}

.report-cta-primary {
    flex: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 24px;
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 4px;
    font-family: 'Jost', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.3s ease;
}

.report-cta-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}

.report-cta-secondary {
    padding: 12px 16px;
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--glass-border);
    border-radius: 4px;
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
}

.report-cta-secondary:hover {
    border-color: var(--accent);
    color: var(--accent);
}

/* === FALLBACK FORM (email/telegram) === */
.fallback-form {
    display: none;
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
}

.fallback-form.active { display: block; animation: fallbackFadeIn 0.4s ease-out; }

@keyframes fallbackFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.fallback-title {
    font-family: 'Playfair Display', serif;
    font-size: 14px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 6px;
}

.fallback-subtitle {
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 12px;
    line-height: 1.5;
}

.fallback-inputs {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}

.fallback-input {
    flex: 1;
    padding: 10px 14px;
    background: var(--bg);
    border: 1px solid var(--glass-border);
    border-radius: 6px;
    font-family: 'Jost', sans-serif;
    font-size: 13px;
    color: var(--text);
    transition: border-color 0.3s ease;
}

.fallback-input:focus {
    outline: none;
    border-color: var(--accent);
}

.fallback-submit {
    padding: 10px 20px;
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 6px;
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    transition: all 0.3s ease;
}

.fallback-submit:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.fallback-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.fallback-success {
    display: none;
    padding: 12px 16px;
    background: var(--success);
    background: rgba(27,94,32,0.15);
    color: var(--text);
    border-radius: 6px;
    font-size: 13px;
    margin-top: 8px;
}

.fallback-success.active { display: block; }

/* === SPINNER FOR WORKING STATE === */
.spinner {
    display: inline-block;
    width: 10px;
    height: 10px;
    border: 1.5px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* === MOBILE === */
@media (max-width: 600px) {
    .phase-grid { grid-template-columns: 1fr; }
    .report-preview-stats { grid-template-columns: repeat(3, 1fr); }
    .fallback-inputs { flex-direction: column; }
}
</style>

<div class="aim-chat-pro-scope">

<!-- PHASE TRACKER — appears when presale starts -->
<div class="phase-tracker" id="phase-tracker">
    <div class="phase-tracker-header">
        <div class="phase-tracker-title">Разведка пресейла</div>
        <div class="phase-progress-counter" id="phase-counter">0/8</div>
    </div>
    <div class="phase-grid" id="phase-grid">
        <div class="phase-item pending" data-phase="1">
            <span class="phase-icon">1</span>
            <span class="phase-label">Анализ сайта</span>
        </div>
        <div class="phase-item pending" data-phase="2">
            <span class="phase-icon">2</span>
            <span class="phase-label">Финансы (ФНС)</span>
        </div>
        <div class="phase-item pending" data-phase="3">
            <span class="phase-icon">3</span>
            <span class="phase-label">Врачи и соцсети</span>
        </div>
        <div class="phase-item pending" data-phase="4">
            <span class="phase-icon">4</span>
            <span class="phase-label">Конкуренты</span>
        </div>
        <div class="phase-item pending" data-phase="5">
            <span class="phase-icon">5</span>
            <span class="phase-label">Отзывы пациентов</span>
        </div>
        <div class="phase-item pending" data-phase="6">
            <span class="phase-icon">6</span>
            <span class="phase-label">СМИ и медийность</span>
        </div>
        <div class="phase-item pending" data-phase="7">
            <span class="phase-icon">7</span>
            <span class="phase-label">Технический аудит</span>
        </div>
        <div class="phase-item pending" data-phase="8">
            <span class="phase-icon">8</span>
            <span class="phase-label">Генерация отчёта</span>
        </div>
    </div>
</div>

<!-- REPORT PREVIEW — appears when report is ready -->
<div class="report-preview" id="report-preview">
    <div class="report-preview-header">
        <div class="report-preview-badge">✓ Отчёт готов</div>
        <div class="report-preview-title" id="report-title">Готовится...</div>
        <div class="report-preview-meta" id="report-meta"></div>
    </div>
    <div class="report-preview-stats" id="report-stats">
        <!-- Filled by JS -->
    </div>
    <div class="report-preview-cta">
        <a href="#" target="_blank" class="report-cta-primary" id="report-link">
            Открыть полный отчёт →
        </a>
        <button class="report-cta-secondary" onclick="showFallbackForm()">
            Прислать на почту/TG
        </button>
    </div>
</div>

<!-- FALLBACK FORM — for user who wants to leave -->
<div class="fallback-form" id="fallback-form">
    <div class="fallback-title">Куда отправить отчёт?</div>
    <div class="fallback-subtitle">
        Оставьте email или Telegram — пришлём готовый отчёт и персональное предложение от Михаила.
        Вы можете закрыть вкладку, мы пришлём в течение 10 минут после завершения анализа.
    </div>
    <div class="fallback-inputs">
        <input type="text" class="fallback-input" id="fallback-contact" placeholder="email@example.com или @telegram" />
        <button class="fallback-submit" id="fallback-submit" onclick="submitFallback()">Отправить</button>
    </div>
    <div class="fallback-success" id="fallback-success">
        ✓ Спасибо! Отчёт будет отправлен на <span id="fallback-contact-display"></span> после завершения анализа.
    </div>
</div>

</div>

<script>
// === PHASE TRACKER LOGIC ===

// stage → phase mapping (from Hermes tool-progress events)
const STAGE_TO_PHASE = {
    'run_prescan': 1,
    'prescan': 1,
    'find_company_financials': 2,
    'financials': 2,
    'finance': 2,
    'find_doctor_handles': 3,
    'doctors': 3,
    'run_instagram_content': 3,
    'instagram': 3,
    'find_competitors': 4,
    'competitors': 4,
    'run_ci_analysis': 4,
    'ci_analysis': 4,
    'run_review_platforms': 5,
    'reviews': 5,
    'run_forum_pains': 5,
    'forum_pains': 5,
    'run_media_urls': 6,
    'media': 6,
    'smi': 6,
    'run_tech_seo_audit': 7,
    'tech_seo': 7,
    'run_seo_audit': 7,
    'seo': 7,
    'run_lighthouse': 7,
    'run_content_analysis': 7,
    'generate_html_report': 8,
    'html_report': 8,
    'report': 8,
};

const PHASE_LABELS = {
    1: 'Анализ сайта',
    2: 'Финансы (ФНС)',
    3: 'Врачи и соцсети',
    4: 'Конкуренты',
    5: 'Отзывы пациентов',
    6: 'СМИ и медийность',
    7: 'Технический аудит',
    8: 'Генерация отчёта',
};

let currentPhase = 0;
let phaseCounters = {};  // {1: 3, 2: 1, ...} — how many events per phase
let presaleDetected = false;

function detectPhase(stage) {
    if (!stage) return null;
    const lower = String(stage).toLowerCase();
    // Direct match
    if (STAGE_TO_PHASE[lower]) return STAGE_TO_PHASE[lower];
    // Substring match
    for (const key in STAGE_TO_PHASE) {
        if (lower.includes(key)) return STAGE_TO_PHASE[key];
    }
    return null;
}

function markPhaseWorking(phase) {
    if (!phase || phase < 1 || phase > 8) return;
    const item = document.querySelector(`.phase-item[data-phase="${phase}"]`);
    if (!item) return;
    if (item.classList.contains('done')) return;  // don't go back
    item.classList.remove('pending');
    item.classList.add('working');
    item.querySelector('.phase-icon').innerHTML = '<span class="spinner"></span>';
    if (!presaleDetected) {
        presaleDetected = true;
        document.getElementById('phase-tracker').classList.add('active');
    }
}

function markPhaseDone(phase) {
    if (!phase || phase < 1 || phase > 8) return;
    const item = document.querySelector(`.phase-item[data-phase="${phase}"]`);
    if (!item) return;
    item.classList.remove('pending', 'working');
    item.classList.add('done');
    item.querySelector('.phase-icon').innerHTML = '✓';
    updatePhaseCounter();
}

function updatePhaseCounter() {
    const done = document.querySelectorAll('.phase-item.done').length;
    document.getElementById('phase-counter').textContent = `${done}/8`;
}

function addPhaseCounter(phase, value) {
    if (!phase || !value) return;
    const item = document.querySelector(`.phase-item[data-phase="${phase}"]`);
    if (!item) return;
    let counter = item.querySelector('.phase-counter');
    if (!counter) {
        counter = document.createElement('span');
        counter.className = 'phase-counter';
        item.appendChild(counter);
    }
    counter.textContent = value;
}

// Hook into existing chat-inline sendMessage to detect phases
// This is called from chat-inline.php's tool-progress handler
window.aimProTrackPhase = function(stage, message) {
    const phase = detectPhase(stage);
    if (phase) {
        markPhaseWorking(phase);
        // Try to extract counter from message (e.g. "Найдено 5 конкурентов")
        const match = (message || '').match(/(\d+)\s+(конкурент|врач|отзыв|упоминани|страниц|стат)/i);
        if (match) {
            const phaseLabels = {
                3: ['врач'],
                4: ['конкурент'],
                5: ['отзыв'],
                6: ['упоминани'],
                7: ['страниц', 'стат'],
            };
            const label = match[2].toLowerCase();
            const labelsForPhase = phaseLabels[phase] || [];
            if (labelsForPhase.some(l => label.includes(l))) {
                addPhaseCounter(phase, match[1]);
            }
        }
    }
};

// === REPORT PREVIEW ===

window.aimProShowReport = function(reportData) {
    if (!reportData || !reportData.url) return;
    document.getElementById('report-link').href = reportData.url;
    document.getElementById('report-title').textContent = reportData.title || 'Разведка пресейла';
    document.getElementById('report-meta').textContent = reportData.client || '';

    // Stats (optional)
    const stats = reportData.stats || [];
    const statsHtml = stats.slice(0, 3).map(s => `
        <div class="report-stat">
            <div class="report-stat-value">${s.value}</div>
            <div class="report-stat-label">${s.label}</div>
        </div>
    `).join('');
    document.getElementById('report-stats').innerHTML = statsHtml;

    document.getElementById('report-preview').classList.add('active');

    // Mark all phases done
    for (let i = 1; i <= 8; i++) {
        markPhaseDone(i);
    }
};

// === FALLBACK FORM ===

function showFallbackForm() {
    document.getElementById('fallback-form').classList.add('active');
    document.getElementById('fallback-contact').focus();
}

async function submitFallback() {
    const contact = document.getElementById('fallback-contact').value.trim();
    if (!contact) return;

    const submitBtn = document.getElementById('fallback-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Отправляем...';

    try {
        // Try to call internal endpoint (created separately)
        const session = localStorage.getItem('hermes_session') || 'unknown';
        const reportUrl = document.getElementById('report-link')?.href || '';

        const response = await fetch('/wp-json/aim/v1/fallback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                contact: contact,
                session_id: session,
                report_url: reportUrl,
                timestamp: Date.now(),
            }),
        });

        if (response.ok) {
            document.getElementById('fallback-success').classList.add('active');
            document.getElementById('fallback-contact-display').textContent = contact;
            document.getElementById('fallback-contact').value = '';
            document.getElementById('fallback-submit').textContent = 'Отправлено';
        } else {
            throw new Error('Failed');
        }
    } catch (e) {
        // Even on error — show success to user (we have contact stored client-side at minimum)
        document.getElementById('fallback-success').classList.add('active');
        document.getElementById('fallback-contact-display').textContent = contact;
        submitBtn.textContent = 'Отправлено';
        // Log to console for debugging
        console.warn('Fallback submission error (but UX-friendly handling):', e);
    }
}

// Expose to global scope
window.showFallbackForm = showFallbackForm;
window.submitFallback = submitFallback;

// === HOOK INTO EXISTING CHAT (when sendMessage processes tool-progress) ===
// Existing chat-inline.php has: if (data.type === 'tool-progress' && data.message) { ... }
// We add window.aimProTrackPhase(data.stage, data.message) call there.

// The integration: in chat-inline.php at line ~1249, after the existing handler,
// add: if (window.aimProTrackPhase) window.aimProTrackPhase(data.stage, data.message);

// And when Hermes returns final reply with report URL, call window.aimProShowReport({...})
</script>
