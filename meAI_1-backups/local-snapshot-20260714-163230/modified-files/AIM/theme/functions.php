<?php
// AIM Theme — functions.php

// AIM Pro endpoints (fallback, session report)
$aim_pro_endpoints = __DIR__ . '/aim-pro-endpoints.php';
if (file_exists($aim_pro_endpoints)) {
    require_once $aim_pro_endpoints;
}

// Remove WordPress emoji cruft
remove_action('wp_head', 'print_emoji_detection_script', 7);
remove_action('wp_print_styles', 'print_emoji_styles');

add_action('after_setup_theme', function () {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('custom-logo');
    add_theme_support('html5', ['search-form', 'comment-form', 'comment-list']);
});

// ═══════════════════════════════════════════════
// Custom Post Type: Research
// ═══════════════════════════════════════════════
add_action('init', function () {
    register_post_type('research', [
        'labels' => [
            'name'          => 'Исследования',
            'singular_name' => 'Исследование',
            'add_new'       => 'Добавить исследование',
            'add_new_item'  => 'Добавить новое исследование',
            'edit_item'     => 'Редактировать исследование',
            'view_item'     => 'Смотреть исследование',
            'search_items'  => 'Искать исследования',
            'not_found'     => 'Исследования не найдены',
        ],
        'public'       => true,
        'has_archive'  => true,
        'rewrite'      => ['slug' => 'research'],
        'supports'     => ['title', 'editor', 'thumbnail', 'excerpt', 'custom-fields'],
        'show_in_rest' => true,
        'menu_icon'    => 'dashicons-analytics',
        'taxonomies'   => ['research_niche'],
    ]);

    register_taxonomy('research_niche', 'research', [
        'labels' => [
            'name'          => 'Ниши',
            'singular_name' => 'Ниша',
            'search_items'  => 'Искать ниши',
            'all_items'     => 'Все ниши',
            'edit_item'     => 'Редактировать нишу',
            'add_new_item'  => 'Добавить нишу',
        ],
        'hierarchical' => true,
        'show_in_rest' => true,
        'rewrite'      => ['slug' => 'research-niche'],
    ]);
});

add_action('init', function () {
    register_post_meta('research', 'research_date', [
        'type'         => 'string',
        'description'  => 'Дата исследования',
        'single'       => true,
        'show_in_rest' => true,
    ]);
    register_post_meta('research', 'company_name', [
        'type'         => 'string',
        'description'  => 'Название компании',
        'single'       => true,
        'show_in_rest' => true,
    ]);
    register_post_meta('research', 'company_website', [
        'type'         => 'string',
        'description'  => 'URL сайта компании',
        'single'       => true,
        'show_in_rest' => true,
    ]);
});

// Force front-page.php for homepage
add_filter('template_include', function ($template) {
    if (is_front_page()) {
        $front_page = get_template_directory() . '/front-page.php';
        if (file_exists($front_page)) {
            return $front_page;
        }
    }
    return $template;
}, 99);

add_action('wp_enqueue_scripts', function () {
    // Only load theme styles on frontend, not in admin
    if (!is_admin()) {
        $version = wp_get_theme()->get('Version');

        wp_enqueue_style('aim-tailwind', get_template_directory_uri() . '/tailwind-gen.css', [], $version);
        wp_enqueue_style('aim-theme', get_template_directory_uri() . '/theme.css', ['aim-tailwind'], $version);
        wp_enqueue_style('aim-chat', get_template_directory_uri() . '/assets/js/chat-bundle.css', [], $version);
    }

    $version = wp_get_theme()->get('Version');

    wp_deregister_script('react');
    wp_deregister_script('react-dom');
    wp_enqueue_script('react', 'https://unpkg.com/react@18/umd/react.production.min.js', [], '18', true);
    wp_enqueue_script('react-dom', 'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js', ['react'], '18', true);
    wp_enqueue_script('aim-chat', get_template_directory_uri() . '/assets/js/chat-bundle.js', ['react', 'react-dom'], $version, true);

    wp_localize_script('aim-chat', 'aimConfig', [
        'hermesApiUrl' => defined('HERMES_API_URL') ? HERMES_API_URL : 'http://localhost:8000',
    ]);
});

// Completely disable admin bar on frontend
add_filter('show_admin_bar', '__return_false');

// Add inline CSS to hide admin bar artifacts on frontend only
add_action('wp_head', function () {
    echo '<style>
        html { margin-top: 0 !important; }
        #wpadminbar { display: none !important; }
    </style>';
});

// Hide WordPress admin bar menu on frontend
add_action('wp_head', function () {
    if (is_admin_bar_showing()) {
        echo '<style>
            #wpadminbar #wp-admin-bar-menu-toggle { display: none !important; }
            #wpadminbar .menupop .ab-sub-wrapper { display: none !important; }
            #wpadminbar:hover .menupop .ab-sub-wrapper { display: none !important; }
        </style>';
    }
}, 100);



add_action('rest_api_init', function () {
    register_rest_route('aim/v1', '/chat/stream', [
        'methods'  => 'POST',
        'callback' => 'aim_proxy_chat_stream',
        'permission_callback' => '__return_true',
    ]);
    register_rest_route('aim/v1', '/chat', [
        'methods'  => 'POST',
        'callback' => 'aim_proxy_chat',
        'permission_callback' => '__return_true',
    ]);
    register_rest_route('aim/v1', '/chat-debug/stream', [
        'methods'  => 'POST',
        'callback' => 'aim_chat_debug_stream',
        'permission_callback' => '__return_true',
    ]);
});

function aim_proxy_chat_stream($request) {
    $body = $request->get_body();
    $hermes_url = (defined('HERMES_API_URL') ? HERMES_API_URL : 'http://localhost:8000') . '/api/chat/stream';

    // ── Disable all output buffering for SSE streaming ──────────────
    while (ob_get_level()) { ob_end_flush(); }
    ob_implicit_flush(true);
    header('Cache-Control: no-cache');
    header('Connection: keep-alive');
    header('X-Accel-Buffering: no');

    $ch = curl_init($hermes_url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . (defined('HERMES_API_KEY') ? HERMES_API_KEY : ''),
        ],
        CURLOPT_RETURNTRANSFER => false,
        CURLOPT_WRITEFUNCTION  => function ($ch, $data) {
            echo $data;
            flush();
            return strlen($data);
        },
        CURLOPT_HEADERFUNCTION => function ($ch, $header) {
            if (stripos($header, 'Content-Type:') !== false) {
                header(trim($header));
            }
            return strlen($header);
        },
        CURLOPT_TIMEOUT        => 1200,  // 20 минут — соответствует Hermes _SSE_DEADLINE
    ]);

    curl_exec($ch);
    curl_close($ch);
    die();
}

function aim_proxy_chat($request) {
    $body = $request->get_body();
    $hermes_url = (defined('HERMES_API_URL') ? HERMES_API_URL : 'http://localhost:8000') . '/api/chat';

    $ch = curl_init($hermes_url);
    curl_setopt_array($ch, [
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $body,
        CURLOPT_HTTPHEADER     => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . (defined('HERMES_API_KEY') ? HERMES_API_KEY : ''),
        ],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 30,
    ]);

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    status_header($http_code);
    header('Content-Type: application/json');
    echo $response;
    die();
}

// ═══════════════════════════════════════════════
// DEBUG: Mock Chat Stream Endpoint
// ═══════════════════════════════════════════════
function aim_chat_debug_stream($request) {
    $params = $request->get_json_params();
    $scenario = sanitize_text_field($params['scenario'] ?? 'short-success');
    
    $mock_file = get_template_directory() . "/chat-debug/src/mock/{$scenario}.json";
    
    if (!file_exists($mock_file)) {
        status_header(404);
        header('Content-Type: text/event-stream');
        header('Cache-Control: no-cache');
        echo "data: " . json_encode(['type' => 'error', 'message' => 'Scenario not found: ' . $scenario]) . "\n\n";
        flush();
        die();
    }
    
    $json_data = file_get_contents($mock_file);
    $data = json_decode($json_data, true);
    
    if (!$data || !isset($data['events'])) {
        status_header(500);
        header('Content-Type: text/event-stream');
        header('Cache-Control: no-cache');
        echo "data: " . json_encode(['type' => 'error', 'message' => 'Invalid scenario format']) . "\n\n";
        flush();
        die();
    }
    
    // Disable all output buffering for SSE streaming
    while (ob_get_level()) { ob_end_flush(); }
    ob_implicit_flush(true);
    
    header('Content-Type: text/event-stream');
    header('Cache-Control: no-cache');
    header('Connection: keep-alive');
    header('X-Accel-Buffering: no');
    
    // Stream events with delays
    foreach ($data['events'] as $event) {
        $delay_ms = isset($event['delay']) ? intval($event['delay']) : 100;
        
        // Sleep for the specified delay
        usleep($delay_ms * 1000);
        
        // Remove delay from event before sending
        unset($event['delay']);
        
        // Send SSE formatted event
        echo "data: " . json_encode($event) . "\n\n";
        flush();
        
        // Check if connection is still alive
        if (connection_aborted()) {
            break;
        }
    }
    
    die();
}

add_action('admin_menu', function () {
    add_options_page('AIM Настройки', 'AIM', 'manage_options', 'aim-settings', function () {
        ?>
        <div class="wrap">
            <h1>Настройки AIM</h1>
            <form method="post" action="options.php">
                <?php settings_fields('aim_settings'); ?>
                <table class="form-table">
                    <tr>
                        <th><label for="aim_founder_bio">Био основателя</label></th>
                        <td><textarea name="aim_founder_bio" id="aim_founder_bio" rows="4" cols="50" class="large-text"><?php echo esc_textarea(get_option('aim_founder_bio', '')); ?></textarea></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
        </div>
        <?php
    });
});

add_action('admin_init', function () {
    register_setting('aim_settings', 'aim_founder_bio');
    register_setting('aim_settings', 'aim_trust_logos');
});

// ═══════════════════════════════════════════════
// REST API: Contact Form Endpoint
// ═══════════════════════════════════════════════
add_action('rest_api_init', function () {
    register_rest_route('aim/v1', '/contact', [
        'methods'  => 'POST',
        'callback' => 'aim_handle_contact_form',
        'permission_callback' => '__return_true',
    ]);
});

function aim_handle_contact_form($request) {
    $params = $request->get_json_params();

    // Validation
    if (empty($params['name']) || empty($params['email']) || empty($params['message'])) {
        return new WP_Error('missing_fields', 'Заполните все обязательные поля', ['status' => 400]);
    }

    if (!isset($params['consent_pd']) || $params['consent_pd'] !== true) {
        return new WP_Error('consent_required', 'Необходимо согласие на обработку персональных данных', ['status' => 400]);
    }

    if (!filter_var($params['email'], FILTER_VALIDATE_EMAIL)) {
        return new WP_Error('invalid_email', 'Некорректный email', ['status' => 400]);
    }

    // Sanitize
    $name    = sanitize_text_field($params['name']);
    $email   = sanitize_email($params['email']);
    $phone   = sanitize_text_field($params['phone'] ?? '');
    $message = sanitize_textarea_field($params['message']);

    // Send email to admin
    $to      = get_option('admin_email', 'hello@iamaim.ru');
    $subject = 'Новое сообщение с сайта: ' . $name;
    $body    = "Имя: {$name}\n";
    $body   .= "Email: {$email}\n";
    if ($phone) {
        $body .= "Телефон: {$phone}\n";
    }
    $body   .= "\nСообщение:\n{$message}\n\n";
    $body   .= "---\nСогласие на обработку ПД получено: Да\n";
    $body   .= "Дата: " . current_time('Y-m-d H:i:s') . "\n";

    $headers = ['Content-Type: text/plain; charset=UTF-8'];

    $sent = wp_mail($to, $subject, $body, $headers);

    if (!$sent) {
        return new WP_Error('mail_failed', 'Не удалось отправить сообщение', ['status' => 500]);
    }

    // Save to database (optional)
    global $wpdb;
    $table_name = $wpdb->prefix . 'aim_contacts';
    
    $wpdb->insert($table_name, [
        'name'       => $name,
        'email'      => $email,
        'phone'      => $phone,
        'message'    => $message,
        'consent_pd' => 1,
        'created_at' => current_time('mysql'),
    ]);

    return rest_ensure_response([
        'success' => true,
        'message' => 'Сообщение отправлено успешно',
    ]);
}

// Create contacts table on theme activation
register_activation_hook(__FILE__, 'aim_create_contacts_table');

function aim_create_contacts_table() {
    global $wpdb;
    $table_name = $wpdb->prefix . 'aim_contacts';
    $charset_collate = $wpdb->get_charset_collate();

    $sql = "CREATE TABLE IF NOT EXISTS $table_name (
        id bigint(20) NOT NULL AUTO_INCREMENT,
        name varchar(255) NOT NULL,
        email varchar(255) NOT NULL,
        phone varchar(50) DEFAULT NULL,
        message text NOT NULL,
        consent_pd tinyint(1) DEFAULT 1,
        created_at datetime DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    ) $charset_collate;";

    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    dbDelta($sql);
}


// ── Session Archive API ────────────────────────────────────────────────

add_action('rest_api_init', function () {
    register_rest_route('aim/v1', '/session/(?P<hash>[a-f0-9]{12})', [
        'methods'  => 'GET',
        'callback' => 'aim_get_session',
        'permission_callback' => '__return_true',
        'args' => [
            'hash' => [
                'required' => true,
                'validate_callback' => function($param) {
                    return preg_match('/^[a-f0-9]{12}$/', $param);
                }
            ],
            'format' => [
                'default' => 'html',
                'enum' => ['html', 'json', 'pdf']
            ]
        ]
    ]);
});

function aim_get_session($request) {
    $hash = $request->get_param('hash');
    $format = $request->get_param('format');
    $hermes_base = defined('HERMES_API_URL') ? HERMES_API_URL : 'http://localhost:8000';

    // Fetch session metadata
    $metadata_url = "{$hermes_base}/api/sessions/{$hash}";
    $ch = curl_init($metadata_url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_HTTPHEADER => ['Accept: application/json']
    ]);

    $metadata_response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200) {
        return new WP_Error('session_not_found', 'Сессия не найдена', ['status' => 404]);
    }

    $session_meta = json_decode($metadata_response, true);
    if (!$session_meta) {
        return new WP_Error('invalid_session', 'Некорректные данные сессии', ['status' => 500]);
    }

    // Fetch conversation markdown if available
    $conversation_md = '';
    if ($session_meta['available_files']['conversation_md'] ?? false) {
        $conv_url = "{$hermes_base}/api/sessions/{$hash}/conversation";
        $ch = curl_init($conv_url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
        ]);
        $conversation_md = curl_exec($ch);
        curl_close($ch);
    }

    // Fetch prescan data if available
    $prescan_data = null;
    if ($session_meta['available_files']['prescan_data'] ?? false) {
        $prescan_url = "{$hermes_base}/api/sessions/{$hash}/prescan-data.json";
        $ch = curl_init($prescan_url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 10,
        ]);
        $prescan_response = curl_exec($ch);
        curl_close($ch);
        if ($prescan_response) {
            $prescan_data = json_decode($prescan_response, true);
        }
    }

    $session_data = [
        'metadata' => $session_meta['metadata'],
        'conversation_markdown' => $conversation_md,
        'prescan_data' => $prescan_data,
    ];

    // Return based on format
    switch ($format) {
        case 'json':
            return rest_ensure_response($session_data);

        case 'pdf':
            return aim_generate_session_pdf($session_data, $hash);

        case 'html':
        default:
            return aim_render_session_html($session_data, $hash);
    }
}

function aim_render_session_html($session_data, $hash) {
    $metadata = $session_data['metadata'] ?? [];
    $conversation = $session_data['conversation_markdown'] ?? '';
    $prescan = $session_data['prescan_data'] ?? null;

    $client_name = $metadata['client_name'] ?? 'Клиент';
    $created_at = $metadata['created_at'] ?? '';

    ob_start();
    ?>
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Сессия <?php echo esc_html($hash); ?> — <?php echo esc_html($client_name); ?></title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #1a1a1a;
                background: #f5f5f5;
                padding: 2rem;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                padding: 3rem;
            }
            .header {
                border-bottom: 2px solid #eee;
                padding-bottom: 1.5rem;
                margin-bottom: 2rem;
            }
            h1 {
                font-size: 2rem;
                margin-bottom: 0.5rem;
                color: #2c3e50;
            }
            .meta {
                color: #666;
                font-size: 0.9rem;
            }
            .actions {
                margin: 1.5rem 0;
                display: flex;
                gap: 1rem;
            }
            .btn {
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.2s;
            }
            .btn-primary {
                background: #3498db;
                color: white;
            }
            .btn-primary:hover {
                background: #2980b9;
            }
            .conversation {
                margin-top: 2rem;
                line-height: 1.8;
            }
            .conversation h2 {
                margin-top: 2rem;
                margin-bottom: 1rem;
                color: #2c3e50;
            }
            .conversation p {
                margin-bottom: 1rem;
            }
            .conversation code {
                background: #f5f5f5;
                padding: 0.2rem 0.4rem;
                border-radius: 4px;
                font-size: 0.9em;
            }
            .prescan-summary {
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                padding: 1.5rem;
                margin: 2rem 0;
                border-radius: 4px;
            }
            @media print {
                body { background: white; padding: 0; }
                .container { box-shadow: none; }
                .actions { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><?php echo esc_html($client_name); ?></h1>
                <div class="meta">
                    <strong>Сессия:</strong> <?php echo esc_html($hash); ?><br>
                    <strong>Дата:</strong> <?php echo esc_html($created_at); ?>
                </div>
            </div>

            <div class="actions">
                <a href="<?php echo esc_url(rest_url("aim/v1/session/{$hash}?format=pdf")); ?>"
                   class="btn btn-primary">
                    📄 Скачать PDF
                </a>
                <a href="javascript:window.print()" class="btn btn-primary">
                    🖨️ Печать
                </a>
            </div>

            <?php if ($prescan): ?>
            <div class="prescan-summary">
                <h3>📊 Результаты разведки</h3>
                <p>
                    <strong>Специализация:</strong> <?php echo esc_html($prescan['specialization'] ?? 'Не указано'); ?><br>
                    <strong>Город:</strong> <?php echo esc_html($prescan['city'] ?? 'Не указано'); ?><br>
                    <?php if (isset($prescan['revenue_year'])): ?>
                    <strong>Оборот:</strong> <?php echo number_format($prescan['revenue_year'], 0, ',', ' '); ?> ₽
                    <?php endif; ?>
                </p>
            </div>
            <?php endif; ?>

            <div class="conversation">
                <?php
                // Convert markdown to HTML (простая реализация)
                $html = $conversation;
                $html = preg_replace('/^### (.+)$/m', '<h3>$1</h3>', $html);
                $html = preg_replace('/^## (.+)$/m', '<h2>$1</h2>', $html);
                $html = preg_replace('/\*\*(.+?)\*\*/s', '<strong>$1</strong>', $html);
                $html = nl2br($html);
                echo wp_kses_post($html);
                ?>
            </div>
        </div>
    </body>
    </html>
    <?php
    $html = ob_get_clean();

    // Return as HTML response
    header('Content-Type: text/html; charset=UTF-8');
    echo $html;
    exit;
}

function aim_generate_session_pdf($session_data, $hash) {
    // For PDF generation, we'll use wkhtmltopdf via Hermes
    // For now, return a simple text response suggesting to print from HTML
    return new WP_Error(
        'pdf_not_implemented',
        'PDF генерация в разработке. Используйте кнопку "Печать" в HTML версии или сохраните как PDF через браузер.',
        ['status' => 501]
    );
}

// Run table creation on theme switch
add_action('after_switch_theme', 'aim_create_contacts_table');
