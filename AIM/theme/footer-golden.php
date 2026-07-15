</main>

<!-- ═══════════════════════════════════════════════ -->
<!-- FROST OVERLAY (shared across all pages) -->
<!-- ═══════════════════════════════════════════════ -->
<div class="frost-overlay" id="frost-overlay" onclick="closeChat()"></div>

<!-- ═══════════════════════════════════════════════ -->
<!-- CHAT (shared across all pages) -->
<!-- ═══════════════════════════════════════════════ -->
<div class="chat-emerge-container" id="chat-emerge">
  <button class="chat-emerge-close" onclick="closeChat()" aria-label="Закрыть чат">✕</button>
  <div id="hermes-chat" class="chat-wrapper"><?php include get_template_directory() . "/chat-inline.php"; ?></div>
</div>

<!-- ═══════════════════════════════════════════════ -->
<!-- FLOATING CHAT BUTTON (hidden on front page) -->
<!-- ═══════════════════════════════════════════════ -->
<button class="floating-chat-btn" id="floatingChatBtn" onclick="openChatDirect()" aria-label="AIM Ассистент">
  <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
  </svg>
  <span>AIM Ассистент</span>
</button>

<style>
.floating-chat-btn {
  position: fixed;
  bottom: 32px;
  right: 32px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--accent, #1A1A1A);
  color: white;
  border: none;
  border-radius: 50px;
  font-family: var(--font-body, 'Jost', sans-serif);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 1000;
}
.floating-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}
.floating-chat-btn svg {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}
@media (max-width: 768px) {
  .floating-chat-btn span { display: none; }
  .floating-chat-btn {
    width: 56px; height: 56px; padding: 16px;
    justify-content: center; bottom: 24px; right: 24px;
  }
}
</style>

<script>
(function() {
  var chatOpen = false;

  // Defines openChatDirect only if not already set by front-page.php
  window.openChatDirect = window.openChatDirect || function() {
    window.openChat();
  };

  // Defines openChat only if not already set by front-page.php
  window.openChat = window.openChat || function() {
    if (chatOpen) return;
    chatOpen = true;

    var frost = document.getElementById('frost-overlay');
    var chat  = document.getElementById('chat-emerge');
    var btn   = document.getElementById('floatingChatBtn');

    if (btn) btn.style.display = 'none';
    if (frost) frost.classList.add('active');
    if (chat) chat.classList.add('active');

    // Render messages from localStorage when opening chat
    if (typeof renderMessages === 'function') {
      renderMessages();
    }
  };

  // Defines closeChat only if not already set by front-page.php
  window.closeChat = window.closeChat || function() {
    if (!chatOpen) return;
    chatOpen = false;

    var frost = document.getElementById('frost-overlay');
    var chat  = document.getElementById('chat-emerge');
    var btn   = document.getElementById('floatingChatBtn');

    if (chat) chat.classList.remove('active');
    setTimeout(function() {
      if (frost) frost.classList.remove('active');
      if (btn) btn.style.display = 'flex';
    }, 300);
  };

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && chatOpen) window.closeChat();
  });

})();
</script>

<footer class="site-footer">
	<div class="footer-inner">
		<div class="footer-brand">
			<a href="/" class="footer-logo no-underline" aria-label="AIM" style="font-family: 'Playfair Display', serif;">
				<span class="text-3xl text-ink" style="font-weight:400;letter-spacing:-.02em;">AIM</span>
			</a>
			<p class="footer-tagline">AI-first маркетинг в медицине</p>
			<p class="footer-copy">&copy; <?php echo date('Y'); ?> AIM</p>
			<p class="footer-requisites">
				<strong>ИП Елисеев М.С.</strong><br>
				ИНН: 501109473258<br>
				ОГРНИП: 314501125900011
			</p>
		</div>
		<div class="footer-nav">
			<h4 class="footer-heading">Навигация</h4>
			<a href="/prices/">Цены</a>
			<a href="/research/">Исследования</a>
			<a href="/blog/">Блог</a>
			<a href="/philosophy/">Смысл</a>
			<a href="/contact/">Контакты</a>
		</div>
		<div class="footer-legal">
			<h4 class="footer-heading">Документы</h4>
			<a href="/privacy-policy/">Политика обработки ПД</a>
			<a href="/terms-of-service/">Пользовательское соглашение</a>
			<a href="/confidentiality/">Конфиденциальность</a>
			<a href="/requisites/">Реквизиты</a>
		</div>
		<div class="footer-contacts">
			<h4 class="footer-heading">Связь</h4>
			<a href="mailto:hello@iamaim.ru">hello@iamaim.ru</a>
			<a href="https://t.me/mikhaileliseev" target="_blank" rel="noopener">Telegram: @mikhaileliseev</a>
			<a href="tel:+79684757766">+7 968 475-77-66</a>
		</div>
	</div>
</footer>

<style>
.site-footer {
	border-top: 1px solid var(--border, rgba(0,0,0,.08));
	padding: 64px 24px 40px;
	margin-top: 96px;
}
.footer-inner {
	max-width: 1100px;
	margin: 0 auto;
	display: grid;
	grid-template-columns: 2fr 1fr 1fr 1fr;
	gap: 48px;
}
.footer-logo {
	display: inline-block;
	color: var(--text, #1a1a1a);
	text-decoration: none;
	transition: opacity .2s;
	margin-bottom: 16px;
}
.footer-logo:hover { opacity: .75; }
.footer-tagline {
	font-family: 'Jost', sans-serif;
	font-size: .85rem;
	color: var(--text-secondary, #6b6b6b);
	margin: 0 0 8px;
	line-height: 1.5;
}
.footer-copy {
	font-family: 'Jost', sans-serif;
	font-size: .8rem;
	color: var(--text-secondary, #6b6b6b);
	margin: 0;
}
.footer-requisites {
	font-family: 'Jost', sans-serif;
	font-size: .75rem;
	color: var(--text-secondary, #6b6b6b);
	margin: 16px 0 0;
	line-height: 1.6;
}
.footer-requisites strong {
	color: var(--text, #1a1a1a);
	font-weight: 600;
}
.footer-heading {
	font-family: 'Jost', sans-serif;
	font-size: .75rem;
	font-weight: 600;
	letter-spacing: .08em;
	text-transform: uppercase;
	color: var(--text, #1a1a1a);
	margin: 0 0 16px;
}
.footer-nav, .footer-legal, .footer-contacts {
	display: flex;
	flex-direction: column;
	gap: 10px;
}
.footer-nav a, .footer-legal a, .footer-contacts a {
	font-family: 'Jost', sans-serif;
	font-size: .9rem;
	color: var(--text-secondary, #6b6b6b);
	text-decoration: none;
	transition: color .2s;
	line-height: 1.5;
}
.footer-nav a:hover, .footer-legal a:hover, .footer-contacts a:hover {
	color: var(--text, #1a1a1a);
}

[data-theme="dark"] .footer-logo { color: var(--text, #f5f0e8); }
[data-theme="dark"] .footer-requisites strong { color: var(--text, #f5f0e8); }

@media (max-width: 768px) {
	.site-footer { padding: 48px 20px 32px; margin-top: 64px; }
	.footer-inner { grid-template-columns: 1fr; gap: 36px; }
}
</style>
<?php wp_footer(); ?>
<!-- Yandex.Metrika counter -->
<script type="text/javascript">
   (function(m,e,t,r,i,k,a){
       m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
       m[i].l=1*new Date();
       for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
       k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
   })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=109826942', 'ym');

   ym(109826942, 'init', {
       clickmap:true,
       trackLinks:true,
       accurateTrackBounce:true,
       webvisor:true,
       ecommerce:"dataLayer",
       ssr:true,
       referrer: document.referrer,
       url: location.href
   });
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/109826942" style="position:absolute; left:-9999px;" alt="" /></div></noscript>
<!-- /Yandex.Metrika counter -->
</body>
</html>