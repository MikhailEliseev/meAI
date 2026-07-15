<!-- Hermes Chat Inline - Fully Scoped + AIM Pro Phase Tracker -->

<?php
// AIM Pro extension (phase tracker + report preview + fallback form)
// DISABLED Phase 7 — phase tracker banner removed, presale wording hidden
// $pro_path = __DIR__ . '/chat-inline-pro.php';
// if (file_exists($pro_path)) {
//     include $pro_path;
// }
?>
<meta charset="utf-8">
<!-- FingerprintJS CDN -->
    <script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@3/dist/fp.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js"></script>

<style>
/* === SCOPED CHAT STYLES === */
        /* === DUAL THEME SYSTEM === */
        .hermes-chat-scope {
            --bg: #ffffff;
            --surface: #ffffff;
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
            --surface: #161616;
            --glass-bg: #0f0f0f;
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
            background: transparent !important;
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
            width: 88vw;
            max-width: 1400px;
            height: 85vh;
            max-height: 85vh;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            background: var(--glass-bg);
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

        /* Markdown: headings */
        .message-bubble h1,.message-bubble h2,.message-bubble h3,
        .message-bubble h4,.message-bubble h5,.message-bubble h6 {
            margin: 16px 0 8px 0;
            font-weight: 600;
            color: var(--text);
            line-height: 1.3;
        }
        .message-bubble h1 { font-size: 1.3em; }
        .message-bubble h2 { font-size: 1.2em; }
        .message-bubble h3 { font-size: 1.1em; }
        .message-bubble h1:first-child,.message-bubble h2:first-child,
        .message-bubble h3:first-child { margin-top: 0; }

        /* Markdown: code blocks */
        .message-bubble pre {
            background: rgba(0,0,0,0.25);
            border-radius: 10px;
            padding: 14px 16px;
            overflow-x: auto;
            margin: 10px 0;
            font-size: 13px;
            line-height: 1.5;
        }
        .message-bubble pre code {
            background: none;
            padding: 0;
            border-radius: 0;
            font-size: inherit;
        }

        /* Markdown: inline code */
        .message-bubble code {
            background: rgba(0,0,0,0.15);
            padding: 2px 6px;
            border-radius: 5px;
            font-size: 0.9em;
            font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
        }

        /* Markdown: blockquotes */
        .message-bubble blockquote {
            border-left: 3px solid var(--accent);
            margin: 10px 0;
            padding: 8px 16px;
            color: var(--text-secondary);
            font-style: italic;
        }
        .message-bubble blockquote p { margin: 4px 0; }

        /* Markdown: tables */
        .message-bubble table {
            border-collapse: collapse;
            width: 100%;
            margin: 12px 0;
            font-size: 14px;
        }
        .message-bubble th,.message-bubble td {
            border: 1px solid rgba(128,128,128,0.2);
            padding: 8px 12px;
            text-align: left;
        }
        .message-bubble th {
            background: rgba(0,0,0,0.08);
            font-weight: 600;
        }

        /* Markdown: horizontal rule */
        .message-bubble hr {
            border: none;
            border-top: 1px solid rgba(128,128,128,0.2);
            margin: 16px 0;
        }

        /* Markdown: images */
        .message-bubble img {
            max-width: 100%;
            border-radius: 10px;
            margin: 8px 0;
        }

        /* Markdown: task lists (checkboxes) */
        .message-bubble input[type="checkbox"] {
            margin-right: 6px;
            accent-color: var(--accent);
        }

        /* Markdown: strikethrough */
        .message-bubble del,.message-bubble s {
            opacity: 0.6;
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
            align-items: center;
            gap: 10px;
            padding: 16px 20px;
            background: var(--surface);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-left: 3px solid var(--accent);
            border-radius: 20px;
            border-bottom-left-radius: 6px;
            max-width: 75%;
            min-height: 52px;
            transition: opacity 0.4s ease, transform 0.4s ease;
        }

        .typing-indicator .typing-spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid var(--glass-border);
            border-top-color: var(--accent);
            border-radius: 50%;
            flex-shrink: 0;
            animation: typing-spin 0.7s linear infinite;
        }

        @keyframes typing-spin {
            to { transform: rotate(360deg); }
        }

        .typing-indicator.fading-out {
            opacity: 0;
            transform: translateY(-8px);
        }

        .progress-text {
            color: var(--text);
            font-size: 15px;
            line-height: 1.7;
            font-weight: 500;
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


        /* === SUGGESTION BUTTONS === */
        .suggestions-container {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 4px 0 8px 0;
            animation: suggestionsFadeIn 0.4s ease-out;
        }
        @keyframes suggestionsFadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        .suggestion-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            border: 1px solid var(--accent-soft);
            border-radius: 20px;
            background: transparent;
            color: var(--accent);
            font-family: 'Jost', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.25s ease;
            white-space: nowrap;
            line-height: 1.3;
        }
        .suggestion-btn:hover {
            background: var(--accent);
            color: var(--bg);
            border-color: var(--accent);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px var(--shadow);
        }
        .suggestion-btn:active {
            transform: translateY(0);
            box-shadow: none;
        }
        .suggestion-btn .btn-icon { font-size: 14px; opacity: 0.8; }
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
        /* marked.js config */
        marked.setOptions({ breaks: true, gfm: true, headerIds: false, mangle: false });

        const HERMES_API = '/api/chat/stream';
        let sessionId = localStorage.getItem('hermes_session') || generateSessionId();
        let messages = JSON.parse(localStorage.getItem('hermes_messages') || '[]');
        let isProcessing = false;
        let pendingMessages = [];
        let activeSuggestions = [];

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
            // 1. Extract [REPORT_READY] blocks → render as cards
            const reportPattern = /\[REPORT_READY\]\s*([\s\S]*?)\s*\[\/REPORT_READY\]/g;
            let reportCards = [];
            let cleaned = text.replace(reportPattern, (match, jsonStr) => {
                try {
                    const data = JSON.parse(jsonStr);
                    reportCards.push(renderReportCard(data));
                    return `%%REPORT_CARD_${reportCards.length - 1}%%`;
                } catch (e) { return match; }
            });

            // 2. marked.parse() → HTML
            let html = marked.parse(cleaned);

            // 3. DOMPurify sanitize (XSS protection)
            html = DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ['p','br','strong','b','em','i','del','s','a','ul','ol','li',
                               'h1','h2','h3','h4','h5','h6','blockquote','pre','code',
                               'table','thead','tbody','tr','th','td','hr','sup','sub',
                               'div','span','img','input'],
                ALLOWED_ATTR: ['href','target','rel','src','alt','class','id','type','checked','disabled'],
            });

            // 4. Restore report cards
            html = html.replace(/%%REPORT_CARD_(\d+)%%/g, (m, idx) => reportCards[parseInt(idx)] || '');

            return html;
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

            if (activeSuggestions.length > 0) {
                var icons = {
                    'run_ci_analysis': '\u{1F50D}', 'run_smi_mentions': '\u{1F4F0}',
                    'run_review_platforms': '\u2B50', 'run_instagram_content': '\u{1F4F8}',
                    'run_seo_audit': '\u{1F3AF}', 'run_pagespeed': '\u26A1',
                    'run_ads_intelligence': '\u{1F4CA}'
                };
                var html = '<div class="suggestions-container">';
                for (var j = 0; j < activeSuggestions.length; j++) {
                    var b = activeSuggestions[j];
                    var ic = icons[b.tool] || '\u{1F4CC}';
                    html += '<button class="suggestion-btn" onclick="handleSuggestionClick(' + j + ')">';
                    html += '<span class="btn-icon">' + ic + '</span>' + b.label + '</button>';
                }
                html += '</div>';
                container.innerHTML += html;
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
                    <span class="typing-spinner"></span>
                    <span class="progress-text">Запускаю анализ…</span>
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


        function handleSuggestionClick(idx) {
            var btn = activeSuggestions[idx];
            if (!btn) return;
            var label = btn.label;
            activeSuggestions = [];
            renderMessages();
            var input = document.getElementById('message-input');
            if (!input) return;
            var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            ns.call(input, label);
            input.dispatchEvent(new Event('input', { bubbles: true }));
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const sendBtn = document.getElementById('send-btn');
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');

            const text = input.value.trim();
            if (!text) return;

            input.value = '';
            activeSuggestions = [];

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

            // Update session date tracking
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
                                    // AIM Pro: track phase for visual tracker
                                    if (window.aimProTrackPhase) {
                                        window.aimProTrackPhase(data.stage || data.tool || '', data.message);
                                    }
                                }

                                // AIM Pro: detect report URL in finish event or final text
                                if (data.type === 'finish') {
                                    if (window.aimProFinish && window.aimProFinish(data)) {
                                        // Returning true means we already showed report preview
                                    }
                                }

                                // Handle suggestions — show action buttons
                                if (data.type === 'suggestions' && data.buttons && data.buttons.length > 0) {
                                    activeSuggestions = data.buttons;
                                    renderMessages();
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
                                        var lastRenderedLen = -1;  // только перерендериваем если текст изменился
                                        rafId = requestAnimationFrame(function loop() {
                                            if (assistantMessage.length !== lastRenderedLen) {
                                                lastRenderedLen = assistantMessage.length;
                                                try {
                                                    streamSpan.innerHTML = DOMPurify.sanitize(marked.parse(assistantMessage));
                                                } catch(e) {
                                                    streamSpan.textContent = assistantMessage;
                                                }
                                            }
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

                    // AIM Pro: detect report URL in final message and show preview
                    if (window.aimProShowReport) {
                        // URL formats: https://iamaim.ru/abc123 or iamaim.ru/abc123
                        const urlMatch = assistantMessage.match(/(?:https?:\/\/)?(?:www\.)?iamaim\.ru\/([a-z0-9-]{6,})/i);
                        if (urlMatch) {
                            const slug = urlMatch[1];
                            const fullUrl = 'https://iamaim.ru/' + slug;
                            // Extract clinic name from text (best effort)
                            const titleMatch = assistantMessage.match(/(?:Клиника|Клиники|Центр|Институт)\s+[«"]?([А-Яа-яA-Za-z0-9\-\s]{3,40})[»"]?/);
                            const clinicName = titleMatch ? titleMatch[1].trim() : 'Разведка пресейла';
                            // Extract basic stats from message
                            const stats = [];
                            const revMatch = assistantMessage.match(/(\d+(?:[.,]\d+)?)\s*(млн|млрд|тыс\.?)\s*₽?/i);
                            if (revMatch) stats.push({ value: revMatch[1] + ' ' + revMatch[2], label: 'Выручка' });
                            const compMatch = assistantMessage.match(/(\d+)\s*конкурент/i);
                            if (compMatch) stats.push({ value: compMatch[1], label: 'Конкурентов' });
                            const rev2Match = assistantMessage.match(/(\d+)\s*отзыв/i);
                            if (rev2Match) stats.push({ value: rev2Match[1], label: 'Отзывов' });
                            window.aimProShowReport({
                                url: fullUrl,
                                title: clinicName + ' — Разведка AIM',
                                client: 'Готово к просмотру',
                                stats: stats,
                            });
                        }
                    }
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

        // Static greeting — clean, no "агентство", honest about AI nature
        (function loadStaticGreeting() {
            if (messages.length > 0) return;

            const greeting = 'Здравствуйте! Я AI-ассистент AIM — делаю предварительную разведку по вашей клинике. Пришлите ссылку на ваш сайт, и я покажу, как вы выглядите на рынке относительно конкурентов.';
            const firstBubble = document.querySelector('.message.assistant .message-bubble');
            if (firstBubble) {
                firstBubble.innerHTML = parseMarkdown(greeting);
            }
            messages.push({ role: 'assistant', content: greeting, timestamp: Date.now() });
            try { localStorage.setItem('hermes_messages', JSON.stringify(messages)); } catch {}
        })();
    
    // Bridge: allow front-page hero to send URL into the chat
    window.aimChatSend = function(url) {
        var input = document.getElementById('message-input');
        if (!input || !url) return;
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(input, url);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        if (typeof sendMessage === 'function') {
            sendMessage();
        }
    };
    </script></body>
</script>
