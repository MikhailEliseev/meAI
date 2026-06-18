<!-- Hermes Chat Inline - Fully Scoped -->

<meta charset="utf-8">
<!-- FingerprintJS CDN -->
    <script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@3/dist/fp.min.js"></script>

<style>
/* === SCOPED CHAT STYLES === */
        /* === DUAL THEME SYSTEM === */
        .hermes-chat-scope {
            --bg: #ffffff;
            --surface: rgba(255,255,255,0.95);
            --glass-bg: #ffffff;
            --glass-border: rgba(0,0,0,0.06);
            --text: #1A1A1A;
            --text-secondary: #666666;
            --text-dim: #999999;
            --accent: #1A1A1A;
            --accent-soft: rgba(26,26,26,0.08);
            --shadow: rgba(0,0,0,0.06);
        }

        [data-theme="dark"] .hermes-chat-scope {
            --bg: #0a0a0a;
            --surface: rgba(26,26,26,0.7);
            --glass-bg: rgba(20,20,20,0.5);
            --glass-border: rgba(201,169,110,.15);
            --text: #f5f0e8;
            --text-secondary: #9e9489;
            --text-dim: #7a7268;
            --accent: #c9a96e;
            --accent-soft: rgba(201,169,110,0.12);
            --shadow: rgba(0,0,0,0.4);
        }

        .hermes-chat-scope * { margin: 0; padding: 0; box-sizing: border-box; }

        .hermes-chat-scope {
            font-family: 'Jost', sans-serif;
            color: var(--text);
            transition: background .4s ease;
        }

        /* Chat Theme Toggle */
        .chat-theme-toggle {
            position: fixed;
            top: 24px;
            right: 24px;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            border: 1px solid var(--glass-border);
            background: var(--glass-bg);
            backdrop-filter: blur(20px) saturate(1.6);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all .3s ease;
            z-index: 100;
            box-shadow: 0 4px 16px var(--shadow);
        }

        .chat-theme-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px var(--shadow);
        }

        /* Chat Container */
        .chat-wrapper {
            width: 90vw;
            max-width: 1400px;
            height: 85vh;
            max-height: 85vh;
            margin: 0 20px;
            display: flex;
            flex-direction: column;
            background: var(--glass-bg);
            backdrop-filter: blur(40px) saturate(1.8);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            box-shadow: 0 20px 60px var(--shadow);
            overflow: hidden;
        }

        /* Header */
        .chat-header {
            padding: 24px 32px;
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }

        .header-info {
            flex: 1;
        }

        .header-title {
            font-family: 'Playfair Display', serif;
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 4px;
        }

        .header-status {
            font-size: 13px;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #22c55e;
            animation: pulse-dot 2s ease-in-out infinite;
        }

        .status-dot.thinking {
            background: var(--accent);
            animation: pulse-think 1.2s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes pulse-think {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.3); }
        }

        /* Messages */
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 32px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .message {
            display: flex;
            flex-direction: column;
            gap: 8px;
            animation: slideUp 0.4s ease-out;
        }

        .message.user {
            align-items: flex-end;
        }

        .message.assistant {
            align-items: flex-start;
        }

        @keyframes slideUp {
            0% { opacity: 0; transform: translateY(16px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        .message-bubble {
            max-width: 75%;
            padding: 16px 20px;
            border-radius: 20px;
            font-size: 15px;
            line-height: 1.7;
            word-wrap: break-word;
        }

        .message-bubble p {
            margin: 0 0 12px 0;
        }

        .message-bubble p:last-child {
            margin-bottom: 0;
        }

        .message-bubble strong {
            font-weight: 600;
        }

        .message-bubble ul, .message-bubble ol {
            margin: 8px 0;
            padding-left: 24px;
        }

        .message-bubble li {
            margin: 4px 0;
        }

        .message-bubble a {
            color: inherit;
            text-decoration: underline;
            opacity: 0.9;
        }

        .message-bubble a:hover {
            opacity: 1;
        }

        /* Report Ready Card */
        .report-ready-card {
            margin: 8px 0;
            padding: 24px 28px;
            background: linear-gradient(135deg, rgba(201,169,110,0.08) 0%, rgba(201,169,110,0.03) 100%);
            border: 1px solid var(--accent-soft);
            border-radius: 16px;
            position: relative;
            overflow: hidden;
        }

        .report-ready-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            opacity: 0.4;
        }

        .report-ready-icon {
            font-size: 32px;
            margin-bottom: 12px;
            display: block;
        }

        .report-ready-title {
            font-family: 'Playfair Display', serif;
            font-size: 18px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 8px;
        }

        .report-ready-summary {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 16px;
        }

        .report-ready-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: var(--accent);
            color: var(--bg);
            border-radius: 12px;
            font-size: 14px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.3s ease;
        }

        .report-ready-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 16px var(--shadow);
            opacity: 0.95;
            color: var(--bg);
            text-decoration: none;
        }

        .report-ready-meta {
            margin-top: 12px;
            font-size: 12px;
            color: var(--text-dim);
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }

        .report-ready-meta span {
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .message.assistant .message-bubble {
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-bottom-left-radius: 6px;
            color: var(--text);
        }

        .message.user .message-bubble {
            background: var(--accent);
            color: var(--bg);
            border-bottom-right-radius: 6px;
            box-shadow: 0 4px 12px var(--shadow);
        }

        /* Progress Bubble (permanent, Telegram-style) */
        .message.assistant-progress {
            align-items: flex-start;
        }

        .message.assistant-progress .message-bubble {
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-bottom-left-radius: 6px;
            color: var(--text-dim);
            font-size: 13px;
            line-height: 1.5;
            max-width: 70%;
            padding: 10px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .progress-dot {
            width: 7px;
            height: 7px;
            min-width: 7px;
            border-radius: 50%;
            background: var(--accent);
            opacity: 0.5;
            animation: progress-pulse 1.2s ease-in-out infinite;
        }

        .progress-dot.done {
            animation: none;
            opacity: 1;
        }

        @keyframes progress-pulse {
            0%, 100% { opacity: 0.3; transform: scale(0.9); }
            50% { opacity: 1; transform: scale(1.2); }
        }

        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            align-items: flex-start;
            padding: 16px 20px;
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            border-bottom-left-radius: 6px;
            max-width: 75%;
            min-height: 52px;
            transition: opacity 0.4s ease, transform 0.4s ease;
        }

        .typing-indicator.fading-out {
            opacity: 0;
            transform: translateY(-8px);
        }

        .progress-text {
            color: var(--text);
            font-size: 15px;
            line-height: 1.7;
            flex: 1;
            transition: opacity 0.3s ease;
        }

        .progress-text.updating {
            opacity: 0.5;
        }

        /* Blinking cursor while waiting for progress */
        .progress-text:empty::after {
            content: '';
            display: inline-block;
            width: 2px;
            height: 18px;
            background: var(--accent);
            margin-left: 2px;
            vertical-align: text-bottom;
            animation: cursor-blink 0.8s step-end infinite;
        }

        @keyframes cursor-blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0; }
        }

        /* Input Area */
        .input-container {
            padding: 24px 32px;
            border-top: 1px solid var(--glass-border);
            background: var(--surface);
            backdrop-filter: blur(20px);
        }

        .input-wrapper {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 14px 20px;
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            color: var(--text);
            font-family: 'Jost', sans-serif;
            font-size: 15px;
            transition: all .2s ease;
            outline: none;
        }

        .chat-input::placeholder {
            color: var(--text-dim);
        }

        .chat-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-soft);
        }

        .send-button {
            padding: 14px 24px;
            background: var(--accent);
            color: var(--bg);
            border: none;
            border-radius: 16px;
            font-family: 'Jost', sans-serif;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all .2s ease;
            white-space: nowrap;
        }

        .send-button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--shadow);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Scrollbar */
        .messages-container::-webkit-scrollbar {
            width: 6px;
        }

        .messages-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .messages-container::-webkit-scrollbar-thumb {
            background: var(--glass-border);
            border-radius: 3px;
        }

        .messages-container::-webkit-scrollbar-thumb:hover {
            background: var(--text-dim);
        }

        /* Empty State */
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 48px 24px;
        }

        .empty-state-icon {
            font-size: 64px;
            margin-bottom: 16px;
            opacity: 0.6;
        }

        .empty-state-title {
            font-family: 'Playfair Display', serif;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .empty-state-text {
            font-size: 15px;
            color: var(--text-secondary);
            max-width: 400px;
        }

        /* Consent Banner (ФЗ-152 Article 9 compliance) */
        .consent-banner {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 9999;
            background: var(--surface);
            backdrop-filter: blur(20px) saturate(1.6);
            border-top: 1px solid var(--glass-border);
            padding: 16px 32px;
            box-shadow: 0 -4px 24px var(--shadow);
            animation: slideUpBanner 0.4s ease-out;
        }

        .consent-banner.hidden {
            display: none;
        }

        @keyframes slideUpBanner {
            from {
                transform: translateY(100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .consent-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 24px;
        }

        .consent-content p {
            margin: 0;
            font-size: 14px;
            color: var(--text-secondary);
            flex: 1;
        }

        .consent-content a {
            color: var(--accent);
            text-decoration: underline;
        }

        .consent-accept {
            padding: 12px 24px;
            background: var(--accent);
            color: var(--bg);
            border: none;
            border-radius: 12px;
            font-family: 'Jost', sans-serif;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all .2s ease;
            white-space: nowrap;
        }

        .consent-accept:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--shadow);
        }

        /* === EXPANDABLE TABS === */
        .demo-tab-bar {
            display: inline-flex;
            align-items: center;
            gap: 0;
            padding: 2px;
            border-radius: 12px;
            border: 1px solid var(--glass-border);
            background: var(--surface);
        }

        .demo-tab {
            display: flex;
            align-items: center;
            gap: 0;
            padding: 3px 6px;
            border-radius: 10px;
            border: none;
            background: transparent;
            color: var(--text-dim);
            cursor: pointer;
            font-family: 'Jost', sans-serif;
            font-size: 11px;
            font-weight: 500;
            transition: gap .3s cubic-bezier(0.2, 0.65, 0.3, 0.9),
                        padding .3s cubic-bezier(0.2, 0.65, 0.3, 0.9),
                        background .2s,
                        color .2s,
                        box-shadow .2s;
        }

        .demo-tab:hover {
            color: var(--text);
            background: var(--accent-soft);
        }

        .demo-tab.active {
            gap: 7px;
            padding-left: 12px;
            padding-right: 12px;
            background: var(--bg);
            color: var(--text);
            box-shadow: 0 1px 3px var(--shadow);
        }

        [data-theme="dark"] .demo-tab.active {
            box-shadow: 0 1px 6px rgba(201,169,110,0.12);
        }

        .demo-tab-label {
            overflow: hidden;
            width: 0;
            opacity: 0;
            white-space: nowrap;
            transition: width .3s cubic-bezier(0.2, 0.65, 0.3, 0.9),
                        opacity .25s ease;
        }

        .demo-tab.active .demo-tab-label {
            width: auto;
            opacity: 1;
        }

        .tab-sep {
            width: 1px;
            height: 16px;
            background: var(--glass-border);
            margin: 0 2px;
            flex-shrink: 0;
        }

        .tab-dropdown {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 8px;
            min-width: 320px;
            max-height: 400px;
            overflow-y: auto;
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 12px;
            box-shadow: 0 8px 24px var(--shadow);
            display: none;
            z-index: 1000;
        }

        .tab-dropdown.active {
            display: block;
        }
</style>

<div class="hermes-chat-scope">

    <div class="chat-wrapper">
        <div class="chat-header">
            <div class="header-info">
                <div class="header-title">AIM</div>
                <div class="header-status">
                    <span class="status-dot" id="status-dot"></span>
                    <span id="status-text">Готов к работе</span>
                </div>
            </div>

            <div class="demo-tab-bar" id="session-tabs">
                <button class="demo-tab" id="tab-history" onclick="toggleHistoryDropdown()">
                    🕐
                    <span class="demo-tab-label">История сессий</span>
                </button>
                <div class="tab-sep"></div>
                <button class="demo-tab" id="tab-clear" onclick="confirmClearSessions()">
                    🗑️
                    <span class="demo-tab-label">Очистить</span>
                </button>
            </div>
        </div>

        <div class="tab-dropdown" id="history-dropdown">
            <div id="session-list">
                <!-- Динамически заполняется через renderHistoryDropdown() в Plan 30-03 -->
            </div>
        </div>

        <div class="messages-container" id="messages-container">
            <div class="message assistant" id="first-message"><div class="message-bubble">Пришлите URL вашего сайта и, если хотите, пару-тройку своих конкурентов. Я посмотрю, что можно сделать.</div></div>
        </div>

        <div class="input-container">
            <div class="input-wrapper">
                <input type="text" class="chat-input" id="message-input" placeholder="Напишите сообщение..." />
                <button class="send-button" id="send-btn" onclick="sendMessage()">Отправить</button>
            </div>
        </div>
    </div>

    <!-- Consent Banner (ФЗ-152 Article 9 compliance) -->
    <div class="consent-banner" id="consent-banner">
        <div class="consent-content">
            <p>Мы используем fingerprinting для идентификации сессий. Продолжая, вы соглашаетесь. <a href="#" onclick="return false;">Подробнее</a></p>
            <button class="consent-accept" onclick="acceptConsent()">Согласен</button>
        </div>
    </div>
</div>

<script>
        const HERMES_API = 'https://iamaim.ru/wp-json/aim/v1/chat/stream';
        let sessionId = localStorage.getItem('hermes_session') || generateSessionId();
        let messages = JSON.parse(localStorage.getItem('hermes_messages') || '[]');
        let isProcessing = false;
        let pendingMessages = [];

        function generateSessionId() {
            const id = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('hermes_session', id);
            return id;
        }

        // FingerprintJS integration (D-01: Open Source via jsDelivr CDN)
        async function initFingerprint() {
            try {
                // Check if fingerprint already exists
                const existingFingerprint = localStorage.getItem('hermes_fingerprint');
                if (existingFingerprint) {
                    return existingFingerprint;
                }

                // Generate new fingerprint
                const fp = await FingerprintJS.load();
                const result = await fp.get();
                const visitorId = result.visitorId;

                // Save to localStorage
                localStorage.setItem('hermes_fingerprint', visitorId);
                return visitorId;
            } catch (error) {
                console.error('FingerprintJS error:', error);
                // Fallback to session-based ID if FingerprintJS fails
                return null;
            }
        }

        // Simple Markdown parser
        // Render report-ready card from JSON data
        function renderReportCard(data) {
            const icon = '📄';
            const title = 'Отчёт готов';
            const summary = data.summary || 'Полный разбор сайта, конкурентов и рынка';
            const url = data.session_url || '#';
            const archivedAt = data.archived_at || '';

            return `
                <div class="report-ready-card">
                    <span class="report-ready-icon">${icon}</span>
                    <div class="report-ready-title">${title}</div>
                    <div class="report-ready-summary">${summary}</div>
                    <a href="${url}" target="_blank" class="report-ready-link">
                        <span>📋</span>
                        <span>Открыть полный отчёт</span>
                        <span>→</span>
                    </a>
                    ${archivedAt ? `<div class="report-ready-meta"><span>🕐 ${archivedAt}</span><span>🔗 Ссылка сохранится навсегда</span></div>` : ''}
                </div>
            `;
        }

        function parseMarkdown(text) {
            // Detect [REPORT_READY] blocks and render cards
            const reportPattern = /\[REPORT_READY\]\s*([\s\S]*?)\s*\[\/REPORT_READY\]/g;
            let reportCards = [];
            let processedText = text.replace(reportPattern, (match, jsonStr) => {
                try {
                    const data = JSON.parse(jsonStr);
                    reportCards.push(renderReportCard(data));
                    return `%%REPORT_CARD_${reportCards.length - 1}%%`;
                } catch (e) {
                    console.error('Failed to parse REPORT_READY JSON:', e);
                    return match;
                }
            });

            // Escape HTML (except report card placeholders)
            processedText = processedText.replace(/</g, '&lt;').replace(/>/g, '&gt;');

            // Bold: **text** or __text__
            processedText = processedText.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            processedText = processedText.replace(/__(.+?)__/g, '<strong>$1</strong>');

            // Links: [text](url)
            processedText = processedText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

            // Restore report cards (after escaping, before paragraph splitting)
            processedText = processedText.replace(/%%REPORT_CARD_(\d+)%%/g, (m, idx) => {
                return reportCards[parseInt(idx)] || '';
            });

            // Split into paragraphs and lists
            const blocks = processedText.split('\n\n');
            const formatted = blocks.map(block => {
                // Skip block if it's a report card (already rendered as full HTML)
                if (block.match(/class="report-ready-card"/)) {
                    return block;
                }

                // Unordered list
                if (block.match(/^[-*]\s/m)) {
                    const items = block.split('\n').map(line => {
                        const match = line.match(/^[-*]\s(.+)$/);
                        return match ? `<li>${match[1]}</li>` : '';
                    }).filter(x => x).join('');
                    return `<ul>${items}</ul>`;
                }

                // Ordered list
                if (block.match(/^\d+\.\s/m)) {
                    const items = block.split('\n').map(line => {
                        const match = line.match(/^\d+\.\s(.+)$/);
                        return match ? `<li>${match[1]}</li>` : '';
                    }).filter(x => x).join('');
                    return `<ol>${items}</ol>`;
                }

                // Single line breaks within paragraph
                const lines = block.split('\n').filter(l => l.trim());
                return lines.length > 0 ? `<p>${lines.join('<br>')}</p>` : '';
            }).filter(x => x).join('');

            return formatted || processedText;
        }

        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('aim-theme', next);
        }

        // Restore theme — handled by header.php inline script

        // Consent banner logic (ФЗ-152 Article 9)
        function acceptConsent() {
            try {
                localStorage.setItem('hermes_consent_fingerprint', 'true');
                document.getElementById('consent-banner').classList.add('hidden');
                initFingerprint();
            } catch (error) {
                console.error('Consent error:', error);
            }
        }

        // Check consent on page load
        window.addEventListener('DOMContentLoaded', () => {
            try {
                const consentGiven = localStorage.getItem('hermes_consent_fingerprint');
                if (consentGiven === 'true') {
                    document.getElementById('consent-banner').classList.add('hidden');
                    initFingerprint();
                }
                // If consent not given, banner is visible by default
            } catch (error) {
                console.error('Consent check error:', error);
            }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('history-dropdown');
            const tabHistory = document.getElementById('tab-history');

            if (dropdown && tabHistory &&
                !dropdown.contains(e.target) &&
                e.target !== tabHistory &&
                !tabHistory.contains(e.target)) {
                dropdown.classList.remove('active');
                tabHistory.classList.remove('active');
            }
        });

        // Timezone detection (D-05, D-06)
        function getUserTimezone() {
            return Intl.DateTimeFormat().resolvedOptions().timeZone;
        }

        // Calendar day 00:00-23:59 in user's timezone (D-05, D-06)
        function getCurrentDateISO() {
            return new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD format
        }

        // Session Archive with FIFO rotation (D-09, D-10 from CONTEXT.md)
        function archiveCurrentSession() {
            if (messages.length === 0) return; // No messages to archive

            try {
                const sessions = JSON.parse(localStorage.getItem('hermes_sessions') || '[]');
                const currentDate = getCurrentDateISO();
                const currentSessionId = localStorage.getItem('hermes_session');

                // Check if current session already archived
                const existingIndex = sessions.findIndex(s => s.sessionId === currentSessionId);
                if (existingIndex >= 0) {
                    // Update existing
                    sessions[existingIndex] = {
                        date: currentDate,
                        sessionId: currentSessionId,
                        messageCount: messages.length,
                        messages: messages
                    };
                } else {
                    // Add new session
                    sessions.push({
                        date: currentDate,
                        sessionId: currentSessionId,
                        messageCount: messages.length,
                        messages: messages
                    });

                    // FIFO rotation (D-10 from CONTEXT.md): max 3 sessions
                    if (sessions.length > 3) {
                        sessions.shift(); // Remove oldest
                    }
                }

                localStorage.setItem('hermes_sessions', JSON.stringify(sessions));
            } catch (e) {
                if (e.name === 'QuotaExceededError') {
                    console.warn('Cannot archive session: localStorage quota exceeded');
                } else {
                    console.error('Session archive error:', e);
                }
            }
        }

        // Format date for history display (T-02: Plan 30-03)
        function formatDate(isoDate) {
            const date = new Date(isoDate);
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);

            if (date.toDateString() === today.toDateString()) return 'Сегодня';
            if (date.toDateString() === yesterday.toDateString()) return 'Вчера';

            return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });
        }

        // Render history dropdown with archived sessions (T-02: Plan 30-03)
        function renderHistoryDropdown() {
            const sessions = JSON.parse(localStorage.getItem('hermes_sessions') || '[]');
            const listContainer = document.getElementById('session-list');

            if (sessions.length === 0) {
                listContainer.innerHTML = '<p style="color: var(--text-dim); font-size: 13px; text-align: center; padding: 20px;">Нет сохранённых сессий</p>';
                return;
            }

            // Sort by date descending (newest first)
            sessions.sort((a, b) => new Date(b.date) - new Date(a.date));

            listContainer.innerHTML = sessions.map((session) => `
                <div class="session-item" style="padding: 12px; border-bottom: 1px solid var(--glass-border);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 4px;">
                                ${formatDate(session.date)}
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary);">
                                ${session.messageCount} сообщений
                            </div>
                        </div>
                        <button onclick="loadSession('${session.sessionId}')"
                                style="padding: 8px 16px; background: var(--accent); color: var(--bg); border: none; border-radius: 12px; font-size: 13px; font-weight: 600; cursor: pointer; font-family: 'Jost', sans-serif; transition: all .2s ease;">
                            Загрузить
                        </button>
                    </div>
                </div>
            `).join('');
        }

        // Load archived session (T-02: Plan 30-03)
        function loadSession(sessionId) {
            const sessions = JSON.parse(localStorage.getItem('hermes_sessions') || '[]');
            const session = sessions.find(s => s.sessionId === sessionId);

            if (!session) {
                alert('Сессия не найдена');
                return;
            }

            // Restore session
            localStorage.setItem('hermes_session', session.sessionId);
            localStorage.setItem('hermes_messages', JSON.stringify(session.messages));

            // Reload page to apply
            location.reload();
        }

        // History dropdown toggle (T-02: Plan 30-03)
        function toggleHistoryDropdown() {
            const dropdown = document.getElementById('history-dropdown');
            const tab = document.getElementById('tab-history');
            const isActive = dropdown.classList.contains('active');

            if (isActive) {
                dropdown.classList.remove('active');
                tab.classList.remove('active');
            } else {
                // Render history before showing dropdown
                renderHistoryDropdown();
                dropdown.classList.add('active');
                tab.classList.add('active');
            }
        }

        // Clear all sessions with confirmation (T-03: Plan 30-03)
        function confirmClearSessions() {
            const confirmed = confirm(
                'Удалить все сессии и очистить историю?\n\n' +
                'Это действие нельзя отменить. Будут удалены:\n' +
                '- История сообщений (последние 3 дня)\n' +
                '- Текущая сессия\n' +
                '- Fingerprint данные\n' +
                '- Consent настройки'
            );

            if (!confirmed) return;

            try {
                // Clear all hermes_* keys
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('hermes_')) {
                        keysToRemove.push(key);
                    }
                }

                keysToRemove.forEach(key => localStorage.removeItem(key));

                // Reset globals
                sessionId = generateSessionId();
                messages = [];

                // Reload to show consent banner again
                location.reload();
            } catch (error) {
                console.error('Clear sessions error:', error);
                alert('Произошла ошибка при очистке. Попробуйте ещё раз.');
            }
        }

        // Daily limit check for soft escalation (D-03, D-04)
        function checkDailyLimit() {
            try {
                const lastDate = localStorage.getItem('hermes_last_session_date');
                const currentDate = getCurrentDateISO();
                const warningShown = sessionStorage.getItem('warning_shown');

                // Same day, not first session (messages exist), warning not shown yet
                if (lastDate === currentDate && messages.length > 0 && !warningShown) {
                    return true;
                }
                return false;
            } catch (error) {
                console.error('Daily limit check error:', error);
                return false; // Fail open, don't block user
            }
        }

        function renderMessages() {
            const container = document.getElementById('messages-container');
            const typingEl = document.getElementById('typing-indicator');

            if (messages.length === 0) {
                container.innerHTML = `<div class="message assistant"><div class="message-bubble">Пришлите URL вашего сайта и, если хотите, пару-тройку своих конкурентов. Я посмотрю, что можно сделать.</div></div>`;
            } else {
                container.innerHTML = messages.map(msg => `
                    <div class="message ${msg.role}">
                        <div class="message-bubble">${msg.role === 'assistant-progress' ? `<span class="progress-dot${msg.done ? ' done' : ''}"></span>${msg.content}` : (msg.role === 'assistant' ? parseMarkdown(msg.content) : msg.content)}</div>
                    </div>
                `).join('');
            }

            if (typingEl) container.appendChild(typingEl);
            container.scrollTop = container.scrollHeight;
        }

        function showTyping() {
            const container = document.getElementById('messages-container');
            const typing = document.createElement('div');
            typing.className = 'message assistant';
            typing.id = 'typing-indicator';
            typing.innerHTML = `
                <div class="typing-indicator">
                    <span class="progress-text">…</span>
                </div>
            `;
            container.appendChild(typing);
            container.scrollTop = container.scrollHeight;
        }

        let progressPhaseUntil = 0;

        async function hideTyping() {
            const typing = document.getElementById('typing-indicator');
            if (!typing) return;
            typing.classList.add('fading-out');
            await new Promise(r => setTimeout(r, 400));
            if (typing.parentNode) typing.remove();
        }

        // RAF-based streaming: create a live-updating bubble
        function createStreamingBubble() {
            const container = document.getElementById('messages-container');
            const bubble = document.createElement('div');
            bubble.className = 'message assistant';
            bubble.id = 'streaming-message';
            const inner = document.createElement('div');
            inner.className = 'message-bubble';
            const span = document.createElement('span');
            span.className = 'chat-bubble-content';
            span.setAttribute('data-streaming', 'true');
            inner.appendChild(span);
            bubble.appendChild(inner);
            container.appendChild(bubble);
            return span;
        }

        function removeStreamingBubble() {
            const el = document.getElementById('streaming-message');
            if (el && el.parentNode) el.remove();
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const sendBtn = document.getElementById('send-btn');
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');

            const text = input.value.trim();
            if (!text) return;

            input.value = '';

            // If already processing, accumulate messages
            if (isProcessing) {
                pendingMessages.push(text);

                // Show accumulated context in UI immediately
                messages.push({ role: 'user', content: text });
                renderMessages();

                statusText.textContent = `Уточнение добавлено (${pendingMessages.length})...`;
                return;
            }

            isProcessing = true;
            let seenProgress = new Set();
            let rafId = null;

            // Check daily limit and show soft escalation warning (D-03, D-04)
            if (checkDailyLimit()) {
                try {
                    // Add soft escalation message - request contact details
                    messages.push({
                        role: 'assistant',
                        content: `Вы уже использовали одну сессию сегодня. Для более глубокой работы оставьте свой контакт — Михаил свяжется с вами лично.

Напишите ваш телефон или Telegram, и Михаил вернётся к вам в ближайшее время.

Вы можете продолжить диалог здесь, но для детального анализа лучше связаться напрямую.`
                    });
                    sessionStorage.setItem('warning_shown', 'true');
                    renderMessages();
                } catch (error) {
                    console.error('Warning display error:', error);
                }
            }

            // Update session date tracking (D-05, D-06)
            try {
                const lastDate = localStorage.getItem('hermes_last_session_date');
                const currentDate = getCurrentDateISO();
                if (lastDate !== currentDate) {
                    localStorage.setItem('hermes_last_session_date', currentDate);
                }
            } catch (error) {
                console.error('Session date tracking error:', error);
            }

            // Disable input
            input.disabled = true;
            sendBtn.disabled = true;
            statusDot.classList.add('thinking');
            statusText.textContent = 'Обрабатываю запрос...';
            progressPhaseUntil = 0;

            // Add user message
            messages.push({ role: 'user', content: text });
            renderMessages();

            // Show typing
            showTyping();

            try {
                const response = await fetch(HERMES_API, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer hmr_anbjfKH_hqaZIU9Z2vaF8f0t-nrDJGlv-nWfEhRuxP4'
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: text
                    })
                });

                if (!response.ok) throw new Error('Network response was not ok');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let assistantMessage = '';
                let sseBuffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    sseBuffer += decoder.decode(value, {stream: true});
                    const lines = sseBuffer.split('\n\n');
                    sseBuffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));

                                if (data.type === 'tool-progress' && data.message) {
                                    progressPhaseUntil = Date.now() + 5000;
                                    // Add agent prefix to progress message
                                    const agentIcons = { 'FinanceAgent': '💰', 'SEOAgent': '🔍', 'MarketAgent': '🌐' };
                                    const agentPrefix = data.agent ? (agentIcons[data.agent] || '•') + ' ' + data.agent + ': ' : '';
                                    const displayMessage = agentPrefix + data.message;
                                    statusText.textContent = displayMessage;
                                    const typing = document.getElementById('typing-indicator');
                                    if (typing) {
                                        const progressText = typing.querySelector('.progress-text');
                                        if (progressText && progressText.textContent !== displayMessage) {
                                            progressText.classList.add('updating');
                                            progressText.textContent = displayMessage;
                                            await new Promise(r => requestAnimationFrame(r));
                                            progressText.classList.remove('updating');
                                        }
                                    }
                                    // Add permanent progress bubble (dedup on raw message, agent is visual only)
                                    if (!seenProgress.has(data.message) && !messages.some(m => m.role === 'assistant-progress' && m.content === displayMessage)) {
                                        seenProgress.add(data.message);
                                        messages.push({ role: 'assistant-progress', content: displayMessage, done: false });
                                        renderMessages();
                                    }
                                }

                                // Handle text streaming — RAF + textContent, no innerHTML flicker
                                if (data.type === 'text-delta' && data.textDelta) {
                                    if (!assistantMessage) {
                                        const wait = progressPhaseUntil - Date.now();
                                        if (wait > 0) await new Promise(r => setTimeout(r, wait));
                                        await hideTyping();
                                        // Stop pulsing dots on all progress messages
                                        let anyProgressDone = false;
                                        messages.forEach(m => { if (m.role === 'assistant-progress' && !m.done) { m.done = true; anyProgressDone = true; } });
                                        if (anyProgressDone) renderMessages();
                                        // Create streaming bubble and start RAF loop
                                        const streamSpan = createStreamingBubble();
                                        const scrollContainer = document.getElementById('messages-container');
                                        rafId = requestAnimationFrame(function loop() {
                                            streamSpan.textContent = assistantMessage;
                                            if (scrollContainer) scrollContainer.scrollTop = scrollContainer.scrollHeight;
                                            rafId = requestAnimationFrame(loop);
                                        });
                                    }
                                    assistantMessage += data.textDelta;
                                }
                            } catch (e) {
                                console.error('Parse error:', e);
                            }
                        }
                    }
                }

                // Stop RAF loop, remove streaming bubble, final render
                if (rafId) {
                    cancelAnimationFrame(rafId);
                    rafId = null;
                }
                removeStreamingBubble();
                // Push final assistant message and render ONCE with markdown parsing
                if (assistantMessage) {
                    messages.push({ role: 'assistant', content: assistantMessage });
                }
                renderMessages();

                localStorage.setItem('hermes_messages', JSON.stringify(messages));

                // Archive session after assistant response (T-01: Plan 30-03)
                archiveCurrentSession();

            } catch (error) {
                console.error('Error:', error);
                if (rafId) {
                    cancelAnimationFrame(rafId);
                    rafId = null;
                }
                removeStreamingBubble();
                await hideTyping();
                messages.push({ role: 'assistant', content: 'Извините, произошла ошибка. Попробуйте ещё раз.' });
                renderMessages();
            } finally {
                if (rafId) {
                    cancelAnimationFrame(rafId);
                    rafId = null;
                }
                isProcessing = false;
                input.disabled = false;
                sendBtn.disabled = false;
                statusDot.classList.remove('thinking');
                statusText.textContent = 'Готов к работе';
                input.focus();

                // Process accumulated pending messages as single combined message
                if (pendingMessages.length > 0) {
                    const combined = pendingMessages.join('\n\n');
                    pendingMessages = [];
                    input.value = combined;
                    // Wait a bit before sending to ensure clean state
                    setTimeout(() => sendMessage(), 200);
                }
            }
        }

        // Enter to send
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Initial render
        renderMessages();

        // Dynamic greeting — replace static "URL please" with Hermes' engaging opener
        (async function loadDynamicGreeting() {
            // Only on first visit — no saved messages
            if (messages.length > 0) return;

            try {
                const resp = await fetch('/wp-json/aim/v1/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: '__GREETING__', mode: 'PRESALE' }),
                });
                if (!resp.ok) return;
                const data = await resp.json();
                const greeting = data.reply || '';
                if (!greeting.trim()) return;

                // Replace static first message with dynamic greeting
                const firstMsg = document.getElementById('first-message');
                if (firstMsg) {
                    firstMsg.querySelector('.message-bubble').innerHTML = parseMarkdown(greeting);
                }

                // Save to localStorage so it persists across reloads
                messages.push({ role: 'assistant', content: greeting, timestamp: Date.now() });
                try { localStorage.setItem('hermes_messages', JSON.stringify(messages)); } catch {}
            } catch {
                // Silent fallback — static message stays
            }
        })();
    </script>
</body>
</script>
