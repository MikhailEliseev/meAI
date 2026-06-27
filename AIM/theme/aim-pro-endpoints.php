<?php
/**
 * AIM Pro Endpoints — added to functions.php via include
 *
 * Endpoints:
 *   POST /wp-json/aim/v1/fallback
 *     { contact: "email@example.com|@telegram", session_id: "...", report_url: "..." }
 *     → stores in DB + sends notification to Michael's Telegram
 *
 *   GET  /wp-json/aim/v1/session-report/<session_id>
 *     → returns latest report_url + title for session (for resume after reload)
 */

if (!defined('ABSPATH')) exit;

add_action('rest_api_init', function () {
    register_rest_route('aim/v1', '/fallback', [
        'methods'  => 'POST',
        'callback' => 'aim_pro_handle_fallback',
        'permission_callback' => '__return_true',
    ]);

    register_rest_route('aim/v1', '/session-report/(?P<session_id>[a-zA-Z0-9_-]+)', [
        'methods'  => 'GET',
        'callback' => 'aim_pro_get_session_report',
        'permission_callback' => '__return_true',
    ]);
});

function aim_pro_handle_fallback($request) {
    $params = $request->get_json_params();

    $contact = trim(isset($params['contact']) ? $params['contact'] : '');
    $session_id = sanitize_text_field(isset($params['session_id']) ? $params['session_id'] : '');
    $report_url = esc_url_raw(isset($params['report_url']) ? $params['report_url'] : '');
    $timestamp = intval(isset($params['timestamp']) ? $params['timestamp'] : time());

    if (empty($contact)) {
        return new WP_REST_Response(['ok' => false, 'error' => 'contact required'], 400);
    }

    // Detect contact type
    $is_email = filter_var($contact, FILTER_VALIDATE_EMAIL);
    $is_telegram = (strpos($contact, '@') === 0) || (strpos(strtolower($contact), 't.me/') !== false);
    $contact_type = $is_email ? 'email' : ($is_telegram ? 'telegram' : 'other');

    // Store in DB (use wp_options as simple key-value, prefix with aim_fallback_)
    $record = [
        'contact' => $contact,
        'type' => $contact_type,
        'session_id' => $session_id,
        'report_url' => $report_url,
        'timestamp' => $timestamp,
        'created_at' => current_time('mysql'),
        'ip' => isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '',
        'user_agent' => substr(isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '', 0, 255),
    ];

    // Save to options (auto-incrementing list, max 100 entries)
    $fallbacks = get_option('aim_fallback_requests', []);
    if (!is_array($fallbacks)) $fallbacks = [];
    $fallbacks[] = $record;
    if (count($fallbacks) > 100) {
        $fallbacks = array_slice($fallbacks, -100);
    }
    update_option('aim_fallback_requests', $fallbacks, false);

    // Send notification to Michael's Telegram (if configured)
    $admin_tg_chat = get_option('aim_telegram_admin_chat_id', '');
    $bot_token = getenv('TELEGRAM_BOT_TOKEN') ?: (defined('TELEGRAM_BOT_TOKEN') ? TELEGRAM_BOT_TOKEN : '');

    if ($admin_tg_chat && $bot_token) {
        $type_emoji = $contact_type === 'email' ? '📧' : ($contact_type === 'telegram' ? '💬' : '👤');
        $message = sprintf(
            "%s *Новый запрос на fallback*\n\n*Контакт:* %s\n*Тип:* %s\n*Session:* %s\n*Отчёт:* %s\n*Время:* %s",
            $type_emoji,
            $contact,
            $contact_type,
            $session_id,
            $report_url ?: '(не сгенерирован)',
            current_time('Y-m-d H:i:s')
        );

        // Async Telegram send via wp_remote_post (non-blocking on success)
        $tg_url = "https://api.telegram.org/bot{$bot_token}/sendMessage";
        wp_remote_post($tg_url, [
            'timeout' => 5,
            'body' => [
                'chat_id' => $admin_tg_chat,
                'text' => $message,
                'parse_mode' => 'Markdown',
            ],
        ]);
    }

    // Send email notification to admin (always)
    $admin_email = get_option('admin_email', 'hello@iamaim.ru');
    $subject = "[AIM Fallback] {$contact_type}: {$contact}";
    $body = "Новый запрос на отправку отчёта после пресейла:\n\n";
    $body .= "Контакт: {$contact}\n";
    $body .= "Тип: {$contact_type}\n";
    $body .= "Session ID: {$session_id}\n";
    $body .= "URL отчёта: {$report_url}\n";
    $body .= "Время: " . current_time('Y-m-d H:i:s') . "\n";
    $body .= "IP: " . (isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : '-') . "\n";
    wp_mail($admin_email, $subject, $body);

    // If contact is email AND report_url is set, send the report to user immediately
    // (Best-effort; if not yet ready, admin will manually send later)
    if ($is_email && !empty($report_url)) {
        $user_subject = 'Ваш отчёт AIM — ' . get_bloginfo('name');
        $user_body = "Здравствуйте!\n\n";
        $user_body .= "Ваш персональный отчёт пресейла готов:\n";
        $user_body .= $report_url . "\n\n";
        $user_body .= "Если ссылка не открывается — напишите в ответ на это письмо.\n\n";
        $user_body .= "— Команда AIM\n";
        $user_body .= get_bloginfo('url');
        wp_mail($contact, $user_subject, $user_body);
    }

    return new WP_REST_Response([
        'ok' => true,
        'type' => $contact_type,
        'message' => 'Запрос сохранён. Отчёт будет отправлен после завершения анализа.',
    ], 200);
}

function aim_pro_get_session_report($request) {
    $session_id = sanitize_text_field($request['session_id']);

    if (empty($session_id)) {
        return new WP_REST_Response(['ok' => false, 'error' => 'session_id required'], 400);
    }

    // Check Hermes for session data via internal HTTP
    $hermes_url = (defined('HERMES_API_URL') ? HERMES_API_URL : 'http://localhost:8000');
    $url = $hermes_url . '/api/session/' . urlencode(substr($session_id, 0, 12)) . '/report';

    $response = wp_remote_get($url, ['timeout' => 5]);

    if (is_wp_error($response)) {
        return new WP_REST_Response(['ok' => false, 'error' => 'session not found'], 404);
    }

    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);

    return new WP_REST_Response($data, 200);
}
