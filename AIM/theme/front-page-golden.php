bash: warning: setlocale: LC_ALL: cannot change locale (ru_RU.UTF-8)
<?php get_header(); ?>

<!-- Water Ripples Background -->
<div class="water-ripples" aria-hidden="true">
  <?php for ($i = 1; $i <= 7; $i++): ?>
  <div class="ripple-origin ripple-origin-<?php echo $i; ?>">
    <?php for ($r = 1; $r <= 2; $r++): ?>
    <div class="ripple-ring"></div>
    <?php endfor; ?>
  </div>
  <?php endfor; ?>
</div>

<!-- ═══════════════════════════════════════════════ -->
<!-- HERO PREMIUM -->
<!-- ═══════════════════════════════════════════════ -->
<section class="hero-premium" id="hero-premium">

  <div class="hero-bg-image" aria-hidden="true"></div>
  <div class="hero-bg-overlay"></div>
  <div class="hero-premium-content" id="hero-content">
    <div class="sec-tag">AI-first маркетинг в медицине</div>
    <h1 class="hero-title-ds">
      <span>I am AIM</span><span class="marquee-container">
        <span class="marquee-wrapper">
          <span class="marquee-inner" style="--count: 9; --speed: 1;">
            <span class="marquee-item" style="--index: 0; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">oney</span>
            <span class="marquee-item" style="--index: 1; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">ethodology</span>
            <span class="marquee-item" style="--index: 2; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">argin</span>
            <span class="marquee-item" style="--index: 3; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">onitoring</span>
            <span class="marquee-item" style="--index: 4; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">etrics</span>
            <span class="marquee-item" style="--index: 5; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">anagement</span>
            <span class="marquee-item" style="--index: 6; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">edicine</span>
            <span class="marquee-item" style="--index: 7; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">arketing</span>
            <span class="marquee-item" style="--index: 8; --origin: calc((var(--count) - var(--index)) * 100%); --destination: calc((var(--index) + 1) * -100%); --duration: calc(var(--speed) * 9s); --delay: calc((var(--duration) / var(--count)) * var(--index) - var(--duration)); translate: 0 var(--origin); animation: slide-vertical var(--duration) var(--delay) infinite linear;">odeling</span>
          </span>
        </span>
      </span>
    </h1>
    <p class="hero-subtitle-ds">Вас привел сюда AI. Если он привел Вас, то приведет пациентов в Вашу клинику</p>

    <div class="hero-input-card" id="hero-input-card">
      <input
        type="text"
        class="glass-input"
        id="site-url-input"
        placeholder="Введите адрес сайта вашей клиники"
        autocomplete="url"
        inputmode="url"
      >
      <button class="btn-primary" id="hero-submit-btn" onclick="openChat()">
        Начать диалог
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
        </svg>
      </button>
    </div>
  </div>
</section>



<!-- ═══════════════════════════════════════════════ -->
<!-- PAGE CONTENT (below fold) -->
<!-- ═══════════════════════════════════════════════ -->
<div class="page-content-frost" id="page-content">

  <!-- ═══════════════════════════════════════════════ -->
  <!-- PHILOSOPHY: Why Trust AIM -->
  <!-- ═══════════════════════════════════════════════ -->
  <section class="sec-section" style="padding-top: 30px;">
    <div class="max-w-5xl mx-auto px-4">
      <div class="text-center mb-16">
        <div class="sec-tag" style="margin-bottom: 16px;">Почему нам доверяют</div>
        <h2 class="sec-heading">Три правила, которым мы следуем</h2>
        <p class="sec-subtitle">Мы не делаем маркетинг как все. Мы строим системы, которые работают на данных, AI и вашей реальности.</p>
      </div>

      <div class="grid-3-glass">
        <!-- Rule 1: Data -->
        <div class="glass-panel">
          <div class="rule-number">01</div>
          <h3 class="rule-title">Что делает система</h3>
          <p class="rule-desc">Системы AIM используют самые передовые AI-модели — от генерации контента до сложных аналитических задач. Мы обеспечиваем стабильный поток пациентов в клинику: анализируем рынок, конкурентов, отзывы и рекламу, чтобы вы получали предсказуемый результат.</p>
        </div>

        <!-- Rule 2: AI -->
        <div class="glass-panel">
          <div class="rule-number">02</div>
          <h3 class="rule-title">AI снижает человеческий фактор</h3>
          <p class="rule-desc">Люди устают. AI — нет. Берёт на себя рутину: сбор данных, анализ сайтов конкурентов, проверку отзывов, подготовку отчётов. Пока AI делает тяжёлую работу, специалисты AIM фокусируются на стратегии и результате. Человек принимает решения, AI — обеспечивает данными.</p>
        </div>

        <!-- Rule 3: Flexibility -->
        <div class="glass-panel">
          <div class="rule-number">03</div>
          <h3 class="rule-title">Гибкость под ваш бизнес</h3>
          <p class="rule-desc">Каждая клиника уникальна. Мы строим систему под вас: анализируем ваши данные, ставим измеримые задачи, тестируем гипотезы быстрее конкурентов, реагируем на изменения рынка первыми. Нет универсальных решений. Есть то, что работает у вас.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Founder Hero -->
  <section class="founder-hero">
    <div class="founder-grid">
      <div class="founder-text-col">
        <p class="founder-bio"><?php echo wp_kses_post(get_option('aim_founder_bio', 'Основатель AIM. Специализируюсь на медицинском маркетинге и AI-автоматизации. Помогаю частным клиникам находить пациентов через data-driven-подход и AI-инструменты.')); ?></p>
        <a href="#" class="founder-more" onclick="event.preventDefault();window.dataLayer=window.dataLayer||[];dataLayer.push({event:'founder_modal'});if(typeof ym!=='undefined')ym(109826942,'reachGoal','founder_modal');openModal('founderModal');">Подробнее</a>
      </div>

      <div class="founder-image-area">
        <div class="founder-circle" aria-hidden="true"></div>
        <img src="<?php echo get_template_directory_uri(); ?>/../../uploads/2026/06/mikhail-eliseev.png" alt="Михаил Елисеев" class="founder-photo-img" loading="lazy">
      </div>

      <div class="founder-name-col">
        <h2>Михаил<br>Елисеев</h2>
      </div>
    </div>

    <div class="founder-footer">
      <div class="founder-contacts">
        <a href="https://t.me/mikhaileliseev" target="_blank" rel="noopener noreferrer" class="founder-contact-link" onclick="window.dataLayer=window.dataLayer||[];dataLayer.push({event:'telegram_click'});if(typeof ym!=='undefined')ym(109826942,'reachGoal','telegram_click');">
          <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18 1.897-.962 6.502-1.359 8.627-.168.9-.5 1.201-.82 1.23-.697.064-1.226-.461-1.901-.903-1.056-.692-1.653-1.123-2.678-1.799-1.185-.781-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.015-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.139-5.062 3.345-.479.329-.913.489-1.302.481-.428-.009-1.252-.242-1.865-.442-.751-.244-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.831-2.529 6.998-3.015 3.333-1.386 4.025-1.627 4.476-1.635.099-.002.321.023.465.141.119.098.152.228.168.334.016.106.036.344.02.531z"/></svg>
          <span>@mikhaileliseev</span>
        </a>
        <a href="tel:+79684757766" class="founder-contact-link" onclick="window.dataLayer=window.dataLayer||[];dataLayer.push({event:'phone_click'});if(typeof ym!=='undefined')ym(109826942,'reachGoal','phone_click');">
          <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
          <span>+7 968 475-77-66</span>
        </a>
      </div>
    </div>
  </section>


  <!-- ═══════════════════════════════════════════════ -->
  <!-- CTA -->
  <!-- ═══════════════════════════════════════════════ -->
  <section class="sec-section">
    <div class="max-w-4xl mx-auto px-4">
      <div class="glass-cta">
        <h2>Ассистент AIM</h2>
        <p>Запустите ассистента — он проанализирует ваш сайт, изучит конкурентов и покажет, где вы теряете пациентов. Глубокий анализ может занять до часа, но оно того стоит.</p>
        <button class="btn-primary" onclick="openChatDirect()">
          Начать диалог
          <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6"/>
          </svg>
        </button>
      </div>
    </div>
  </section>

</div>

<script>
(function() {
  function normalizeUrl(raw) {
    var u = raw.trim();
    if (!u) return '';
    if (!/^https?:\/\//i.test(u)) u = 'https://' + u;
    return u;
  }

  function shake(el) {
    el.style.transition = 'transform .1s ease';
    el.style.transform = 'translateX(-8px)';
    setTimeout(function(){ el.style.transform = 'translateX(8px)'; }, 100);
    setTimeout(function(){ el.style.transform = 'translateX(-4px)'; }, 200);
    setTimeout(function(){ el.style.transform = 'translateX(0)'; }, 300);
  }

  function goal(id) {
    window.dataLayer = window.dataLayer || [];
    dataLayer.push({ event: id });
    if (typeof ym !== 'undefined') ym(109826942, 'reachGoal', id);
  }

  // ═══ CHAT ═══
  var chatOpen = false;

  window.openChatDirect = function() {
    if (chatOpen) return;
    chatOpen = true;
    goal('cta_bottom_start');
    var frost = document.getElementById('frost-overlay');
    var chat  = document.getElementById('chat-emerge');
    var page  = document.getElementById('page-content');
    var btn   = document.getElementById('floatingChatBtn');
    if (btn) btn.style.display = 'none';

    if (frost) frost.classList.add('active');
    setTimeout(function(){
      if (page) page.classList.add('frosted');
      if (chat) chat.classList.add('active');
    }, 100);
    setTimeout(function(){ goal('chat_opened'); }, 600);
  };

  window.openChat = function() {
    if (chatOpen) return;
    var input = document.getElementById('site-url-input');
    var hero  = document.getElementById('hero-content');
    var frost = document.getElementById('frost-overlay');
    var chat  = document.getElementById('chat-emerge');
    var page  = document.getElementById('page-content');
    var card  = document.getElementById('hero-input-card');
    var url = normalizeUrl(input.value);
    if (!url || url === 'https://') {
      goal('hero_start_empty');
      shake(card);
      input.focus();
      return;
    }
    goal('hero_start');
    chatOpen = true;

    hero.classList.add('fading');
    var btn = document.getElementById('floatingChatBtn');
    if (btn) btn.style.display = 'none';
    setTimeout(function(){ frost.classList.add('active'); }, 200);
    setTimeout(function(){ page.classList.add('frosted'); }, 400);
    setTimeout(function(){ chat.classList.add('active'); }, 500);
    setTimeout(function(){ goal('chat_opened'); }, 600);
    setTimeout(function() {
      if (typeof window.aimChatSend === 'function') {
        window.aimChatSend(url);
      }
    }, 1100);
  };

  window.closeChat = function() {
    if (!chatOpen) return;
    var hero  = document.getElementById('hero-content');
    var frost = document.getElementById('frost-overlay');
    var chat  = document.getElementById('chat-emerge');
    var page  = document.getElementById('page-content');
    chat.classList.remove('active');
    var btn = document.getElementById('floatingChatBtn');
    setTimeout(function(){
      frost.classList.remove('active');
      page.classList.remove('frosted');
    }, 300);
    setTimeout(function(){
      hero.classList.remove('fading');
      chatOpen = false;
      if (btn) btn.style.display = 'flex';
    }, 500);
  };

  var siteInput = document.getElementById('site-url-input');
  if (siteInput) {
    siteInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') window.openChat();
    });
  }

  // ═══ UNIFIED KEYDOWN (Escape) ═══
  document.addEventListener('keydown', function(e) {
    if (e.key !== 'Escape') return;
    if (chatOpen) { window.closeChat(); return; }
    var activeModal = document.querySelector('.modal-overlay.active');
    if (activeModal) {
      activeModal.classList.remove('active');
      document.body.style.overflow = '';
    }
  });

  // ═══ SCROLL EFFECTS ═══
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var heroContent = document.getElementById('hero-content');
    var heroBg = document.querySelector('.hero-bg-image');
    var heroOverlay = document.querySelector('.hero-bg-overlay');

    var textCol = document.querySelector('.founder-text-col');
    var nameCol = document.querySelector('.founder-name-col');
    var founderFooter = document.querySelector('.founder-footer');

    var heroTicking = false;
    var founderTicking = false;
    var founderTransitionsKilled = false;

    function killFounderTransitions() {
      if (founderTransitionsKilled) return;
      founderTransitionsKilled = true;
      [textCol, nameCol, founderFooter].forEach(function(el) {
        if (el) el.style.transition = 'none';
      });
    }

    function updateHero() {
      if (!heroContent && !heroBg) { heroTicking = false; return; }
      var scrollY = window.scrollY || window.pageYOffset;
      var heroH = window.innerHeight;
      if (heroH <= 0) { heroTicking = false; return; }
      var progress = Math.max(0, Math.min(1, scrollY / (heroH * 0.5)));
      var t = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
      var opacity = (1 - t).toFixed(3);
      var bgBlurPx = (t * 32).toFixed(1);
      if (heroContent) {
        heroContent.style.opacity = opacity;
        heroContent.style.filter = 'blur(' + (t * 20).toFixed(1) + 'px)';
        heroContent.style.transform = 'translateY(' + (t * -32).toFixed(1) + 'px) scale(' + (1 - t * 0.05).toFixed(3) + ')';
      }
      if (heroBg) {
        heroBg.style.filter = 'blur(' + bgBlurPx + 'px)';
        heroBg.style.opacity = opacity;
      }
      if (heroOverlay) {
        heroOverlay.style.opacity = opacity;
      }
      heroTicking = false;
    }

    function updateFounder() {
      var founderSection = document.querySelector('.founder-hero');
      if (!founderSection) { founderTicking = false; return; }
      killFounderTransitions();
      var rect = founderSection.getBoundingClientRect();
      var windowH = window.innerHeight;
      var enterEnd   = windowH * 0.82;
      var enterRange = windowH * 0.30;
      var exitStart  = windowH * 0.28;
      var exitRange  = windowH * 0.30;
      var enterProgress = Math.max(0, Math.min(1, (enterEnd - rect.top) / enterRange));
      var exitProgress  = Math.max(0, Math.min(1, (exitStart - rect.top) / exitRange));
      var opacity = Math.min(enterProgress, 1 - exitProgress);
      var shift   = (1 - opacity) * -24;
      if (textCol) {
        textCol.style.opacity = opacity.toFixed(3);
        textCol.style.transform = 'translateY(' + shift.toFixed(1) + 'px)';
      }
      if (nameCol) {
        nameCol.style.opacity = opacity.toFixed(3);
        nameCol.style.transform = 'translateY(' + shift.toFixed(1) + 'px)';
      }
      if (founderFooter) {
        founderFooter.style.opacity = opacity.toFixed(3);
        founderFooter.style.transform = 'translateY(' + shift.toFixed(1) + 'px)';
      }
      founderTicking = false;
    }

    // Shared scroll listener
    var scroll50 = false, scroll75 = false;
    window.addEventListener('scroll', function() {
      if (!heroTicking) {
        requestAnimationFrame(updateHero);
        heroTicking = true;
      }
      if (!founderTicking) {
        requestAnimationFrame(updateFounder);
        founderTicking = true;
      }
      if (typeof ym !== 'undefined') {
        var pct = (window.scrollY + window.innerHeight) / document.body.scrollHeight;
        if (!scroll50 && pct >= 0.5) { scroll50 = true; window.dataLayer=window.dataLayer||[]; dataLayer.push({event:'scroll_50'}); ym(109826942, 'reachGoal', 'scroll_50'); }
        if (!scroll75 && pct >= 0.75) { scroll75 = true; window.dataLayer=window.dataLayer||[]; dataLayer.push({event:'scroll_75'}); ym(109826942, 'reachGoal', 'scroll_75'); }
      }
    }, { passive: true });

    updateHero();
    updateFounder();

    // Founder IntersectionObserver
    var founderSection = document.querySelector('.founder-hero');
    if (founderSection) {
      var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
          if (entry.isIntersecting) {
            founderSection.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15 });
      observer.observe(founderSection);
    }
  }
})();
</script>


<!-- ═══════════════════════════════════════════════ -->
<!-- MODAL WINDOWS -->
<!-- ═══════════════════════════════════════════════ -->

<!-- Founder Bio Modal -->
<div class="modal-overlay" id="founderModal">
  <div class="modal-dialog">
    <button class="modal-close" onclick="closeModal('founderModal')" aria-label="Закрыть">✕</button>
    <div class="modal-content">
      <h1>Михаил Елисеев</h1>
      <p class="founder-subtitle">Основатель и CEO</p>

      <p>
        С 2005 года строю маркетинговые системы, которые работают. Начинал с SEO, когда это ещё не было мейнстримом. В 2014 основал собственное агентство.
      </p>
      <p>
        С 2016 по 2025 год руководил отделом маркетинга в Институте пластической хирургии и косметологии (ИПХиК) и клиниках «Ланцетъ» — выстраивал стратегию, управлял командой, масштабировал бизнес.
      </p>
      <p>
        С 2020 по 2025 год — операционный директор РОПРЭХ (Российское общество пластических, реконструктивных и эстетических хирургов). Организовывал профессиональные мероприятия, координировал работу отраслевого сообщества.
      </p>
      <p>
        С 2025 года работаю в AIM и развиваю маркетинг с применением нейросетей. Беру проекты в медицине — от небольших клиник до крупных сетей с оборотом более миллиарда рублей.
      </p>
      <p>
        Верю в цифры и AI.
      </p>
    </div>
  </div>
</div>

<script>
function openModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  var modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    closeModal(e.target.id);
  }
});
</script>
<?php get_footer(); ?>
