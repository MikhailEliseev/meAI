<?php
/**
 * Template Name: Chat Debug
 * Description: Debug версия чата с mock API для тестирования UI/UX
 */

// Энкью debug версии скриптов
add_action('wp_enqueue_scripts', function() {
    $version = wp_get_theme()->get('Version');
    
    // React и ReactDOM уже загружены глобально
    wp_enqueue_script('react', 'https://unpkg.com/react@18/umd/react.production.min.js', [], '18', true);
    wp_enqueue_script('react-dom', 'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js', ['react'], '18', true);
    
    // Debug chat bundle (v2 с mock данными)
    wp_enqueue_style('aim-chat-debug', get_template_directory_uri() . '/assets/js/chat-debug-bundle.css', [], $version);
    wp_enqueue_script('aim-chat-debug', get_template_directory_uri() . '/assets/js/chat-debug-bundle.js', ['react', 'react-dom'], $version, true);
}, 20);

?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Debug — <?php bloginfo('name'); ?></title>
    <?php wp_head(); ?>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        #chat-debug {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100vw;
            height: 100vh;
        }
    </style>
</head>
<body>
    <div id="chat-debug"></div>
    <?php wp_footer(); ?>
</body>
</html>
