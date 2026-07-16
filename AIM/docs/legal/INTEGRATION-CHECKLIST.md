# Финальный чек-лист интеграции юридических документов

**Дата:** 13 июня 2026 г.  
**Статус:** ✅ Документы готовы к публикации на 100%

---

## ✅ Что готово

### Документы (7 файлов)
- ✅ privacy-policy.md — Политика обработки ПД (152-ФЗ)
- ✅ terms-of-service.md — Пользовательское соглашение
- ✅ confidentiality.md — Политика конфиденциальности
- ✅ consent-form.md — Форма согласия (бумажная + цифровая)
- ✅ requisites.md — Реквизиты с шаблонами
- ✅ README.md — Инструкции по интеграции
- ✅ SUMMARY.md — Итоговый отчёт

### Реквизиты (полностью заполнены)
- ✅ ИНН: 501109473258
- ✅ ОГРНИП: 314501125900011
- ✅ Дата регистрации: 16.09.2014
- ✅ КПП: 773501001
- ✅ Банк: ОАО "АЛЬФА-БАНК" г. Москва
- ✅ Р/с: 40802810502470000130
- ✅ К/с: 30101810200000000593
- ✅ БИК: 044525593
- ✅ Адрес: Московская область, РФ (безопасный формат)

---

## 🚀 План интеграции на сайт (Next.js)

### Шаг 1: Создать страницы (10 минут)

```bash
cd AIM/frontend

# Создать папки
mkdir -p app/privacy-policy
mkdir -p app/terms-of-service
mkdir -p app/confidentiality
mkdir -p app/requisites
```

### Шаг 2: Создать компоненты страниц (20 минут)

**Пример: app/privacy-policy/page.tsx**
```tsx
import fs from 'fs';
import path from 'path';
import ReactMarkdown from 'react-markdown';

export const metadata = {
  title: 'Политика обработки персональных данных | AIM Agency',
  description: 'Политика обработки персональных данных в соответствии с 152-ФЗ',
};

export default function PrivacyPolicy() {
  const markdown = fs.readFileSync(
    path.join(process.cwd(), '../docs/legal/privacy-policy.md'),
    'utf8'
  );
  
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <article className="prose prose-lg prose-slate mx-auto">
        <ReactMarkdown>{markdown}</ReactMarkdown>
      </article>
    </div>
  );
}
```

Повторить для:
- `app/terms-of-service/page.tsx`
- `app/confidentiality/page.tsx`
- `app/requisites/page.tsx`

### Шаг 3: Обновить Footer (15 минут)

**components/Footer.tsx**
```tsx
export default function Footer() {
  return (
    <footer className="bg-slate-900 text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* О компании */}
          <div>
            <h4 className="text-lg font-semibold mb-4">AIM Agency</h4>
            <p className="text-slate-400 text-sm">
              AI-first маркетинговое агентство для медицинских клиник
            </p>
          </div>
          
          {/* Контакты */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Контакты</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="mailto:info@iamaim.ru" className="text-slate-400 hover:text-white">
                  info@iamaim.ru
                </a>
              </li>
              <li>
                <a href="https://iamaim.ru" className="text-slate-400 hover:text-white">
                  iamaim.ru
                </a>
              </li>
            </ul>
          </div>
          
          {/* Документы */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Документы</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="/terms-of-service" className="text-slate-400 hover:text-white">
                  Пользовательское соглашение
                </a>
              </li>
              <li>
                <a href="/privacy-policy" className="text-slate-400 hover:text-white">
                  Политика обработки ПД
                </a>
              </li>
              <li>
                <a href="/confidentiality" className="text-slate-400 hover:text-white">
                  Политика конфиденциальности
                </a>
              </li>
            </ul>
          </div>
          
          {/* Реквизиты */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Реквизиты</h4>
            <div className="text-slate-400 text-sm space-y-1">
              <p className="font-medium text-white">ИП Елисеев М.С.</p>
              <p>ИНН: 501109473258</p>
              <p>ОГРНИП: 314501125900011</p>
              <p>Московская область, РФ</p>
            </div>
          </div>
          
        </div>
        
        {/* Copyright */}
        <div className="mt-8 pt-8 border-t border-slate-800 text-center text-sm text-slate-400">
          <p>© 2026 AIM Agency. Все права защищены.</p>
        </div>
      </div>
    </footer>
  );
}
```

### Шаг 4: Добавить checkbox согласия в формы (15 минут)

**Пример для формы обратной связи:**
```tsx
'use client';

import { useState } from 'react';

export default function ContactForm() {
  const [consent, setConsent] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!consent) {
      alert('Необходимо согласие на обработку персональных данных');
      return;
    }
    
    // Отправка формы
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Поля формы */}
      <input type="text" name="name" placeholder="Имя" required />
      <input type="email" name="email" placeholder="Email" required />
      <textarea name="message" placeholder="Сообщение" required />
      
      {/* Checkbox согласия */}
      <label className="flex items-start gap-2 text-sm">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          required
          className="mt-1"
        />
        <span>
          Согласен с{' '}
          <a 
            href="/privacy-policy" 
            target="_blank" 
            className="text-blue-600 hover:underline"
          >
            обработкой персональных данных
          </a>
        </span>
      </label>
      
      <button 
        type="submit" 
        disabled={!consent}
        className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        Отправить
      </button>
    </form>
  );
}
```

### Шаг 5: Обновить sitemap.xml (5 минут)

**public/sitemap.xml**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  
  <url>
    <loc>https://iamaim.ru/</loc>
    <priority>1.0</priority>
    <changefreq>weekly</changefreq>
  </url>
  
  <url>
    <loc>https://iamaim.ru/privacy-policy</loc>
    <priority>0.5</priority>
    <changefreq>monthly</changefreq>
  </url>
  
  <url>
    <loc>https://iamaim.ru/terms-of-service</loc>
    <priority>0.5</priority>
    <changefreq>monthly</changefreq>
  </url>
  
  <url>
    <loc>https://iamaim.ru/confidentiality</loc>
    <priority>0.5</priority>
    <changefreq>monthly</changefreq>
  </url>
  
  <url>
    <loc>https://iamaim.ru/requisites</loc>
    <priority>0.3</priority>
    <changefreq>yearly</changefreq>
  </url>
  
</urlset>
```

### Шаг 6: Установить зависимости (если нужно)

```bash
cd AIM/frontend
npm install react-markdown remark-gfm
```

### Шаг 7: Стилизация страниц (опционально)

**Если используете Tailwind CSS с prose:**
```bash
npm install @tailwindcss/typography
```

**tailwind.config.js:**
```js
module.exports = {
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
```

---

## 📝 Чек-лист перед публикацией

### Документы
- [x] Все реквизиты проверены и актуальны
- [x] Email info@iamaim.ru существует и работает
- [x] Даты обновления актуальны (13 июня 2026)
- [x] Все ссылки между документами корректны

### Интеграция
- [ ] Созданы все страницы (privacy-policy, terms-of-service, confidentiality, requisites)
- [ ] Footer обновлён с реквизитами и ссылками
- [ ] Checkbox согласия добавлен во все формы
- [ ] Sitemap.xml обновлён
- [ ] Протестированы все ссылки
- [ ] Проверена мобильная версия

### SEO
- [ ] Мета-теги для юридических страниц
- [ ] robots.txt настроен
- [ ] Canonical URLs указаны

### Юридическое
- [ ] Документы соответствуют 152-ФЗ
- [ ] Процедура обработки запросов на удаление данных
- [ ] Email для обращений субъектов ПД работает

---

## ⏱️ Оценка времени

| Этап | Время |
|------|-------|
| Создание страниц | 10 мин |
| Компоненты страниц | 20 мин |
| Обновление Footer | 15 мин |
| Checkbox в формы | 15 мин |
| Sitemap | 5 мин |
| Тестирование | 15 мин |
| **ИТОГО** | **~1.5 часа** |

---

## 🎯 После публикации

### В течение недели
- [ ] Протестировать отправку форм с checkbox
- [ ] Проверить отображение на всех устройствах
- [ ] Убедиться, что все ссылки работают

### В течение месяца
- [ ] Назначить ответственного за обработку ПД (можете сами)
- [ ] Создать процедуру обработки запросов субъектов ПД
- [ ] Подготовить шаблоны ответов на типовые запросы

---

## 📞 Контакты

**ИП Елисеев Михаил Сергеевич**  
ИНН: 501109473258  
ОГРНИП: 314501125900011  
Email: info@iamaim.ru

---

**Статус:** ✅ Готово к интеграции  
**Все файлы в:** AIM/docs/legal/
