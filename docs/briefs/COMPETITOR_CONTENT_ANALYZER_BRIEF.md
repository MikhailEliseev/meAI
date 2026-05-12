# Бриф: Competitor Content Analyzer

**Дата:** 2026-05-12  
**Приоритет:** P1  
**Родительский Magister:** SEO Magister

## Назначение

Глубокий SEO-анализ контента конкурентов для понимания почему они ранжируются выше и как улучшить наш контент.

**Ключевой инсайт:** Тексты — ключевой фактор ранжирования. Анализируем не только SEO-факторы, но и качество текста, AI-детекцию, конверсионные фреймворки.

## Контекст и специфика

**Предметная область:** Медицинский маркетинг (iamaim.ru)

**Специфические требования:**
- E-E-A-T scoring для медицинского контента (критично для YMYL)
- AI-детекция текста (написан человеком или AI, как это влияет на ранжирование)
- Compliance с медицинскими требованиями

**Проблемы, которые решает:**
1. Почему конкуренты ранжируются выше?
2. Какие SEO-факторы они используют лучше?
3. Как написаны их тексты (структура, качество, фреймворки)?
4. Есть ли признаки AI-генерации в их контенте?
5. Какие технические SEO-факторы влияют на позиции?

## Два возможных подхода

**Вариант 1 (выбран):** Один агент с двумя режимами анализа
- SEO-анализ (структура, ключевые слова, технические факторы)
- Content Quality анализ (копирайтинг, фреймворки, AI-детекция)

**Вариант 2:** Два отдельных агента
- Competitor Content Analyzer (SEO-фокус)
- Content Quality Analyzer (копирайтинг-фокус, входит в Competitive Intelligence)

**Решение:** Начинаем с одного агента, можем разделить позже если нужно.

## Интеграции

**Входные данные:**
- `competitor_url` (URL страницы конкурента для анализа)
- `client_url` (наш URL для сравнения, опционально)
- `analysis_mode` (seo | content_quality | full)

**Выходные данные:**
- Детальный отчёт с анализом
- Сравнение с нашим контентом (если client_url указан)
- Конкретные рекомендации по улучшению
- Scoring по каждому фактору

**Связанные агенты:**
- Content Gap Analysis Agent (для поиска пробелов в контенте)
- Keyword Research Agent (для анализа ключевых слов)
- Technical SEO Auditor (для технических факторов, если будет отдельный)

**Внешние API (если нужны):**
- Ahrefs API (backlinks, domain rating)
- SEMrush API (keyword positions, traffic estimates)
- Screaming Frog (technical SEO crawling)
- Playwright (web scraping для JS-heavy сайтов)

**Бесплатные инструменты (из skills):**
- SEO skills (seo-content, seo-technical, seo-page)
- Playwright MCP (browser automation)
- AI detection tools (если есть в MCP)

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Ключевые слова и их вхождение:**
   - Оптимальная плотность ключевых слов (keyword density)
   - Вхождение в title, meta description, H1-H6
   - LSI keywords (семантически связанные слова)
   - Keyword stuffing detection (переспам)

2. **E-E-A-T для медицинского контента:**
   - Experience (опыт автора)
   - Expertise (экспертность)
   - Authoritativeness (авторитетность)
   - Trustworthiness (доверие)
   - Как это влияет на ранжирование YMYL-контента

3. **AI-детекция текста:**
   - Признаки AI-генерации (GPT, Claude, etc.)
   - Как AI-контент ранжируется в Google (2024-2026 данные)
   - Методы детекции (статистические, ML-модели)
   - Корреляция AI-контент ↔ позиции в поиске

4. **Технические SEO-факторы:**
   - Core Web Vitals (LCP, FID, CLS)
   - Mobile-friendliness
   - Page speed
   - Structured data (schema.org)
   - Internal linking structure
   - URL structure
   - Canonical tags, hreflang

5. **Структура и качество текста:**
   - Readability (Flesch Reading Ease, Flesch-Kincaid Grade)
   - Структура (H1-H6 иерархия)
   - Длина контента (word count)
   - Paragraph length
   - Sentence length
   - Use of lists, tables, images

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Конверсионные фреймворки:**
   - AIDA (Attention, Interest, Desire, Action)
   - PAS (Problem, Agitate, Solution)
   - FAB (Features, Advantages, Benefits)
   - Как фреймворк влияет на конверсию и косвенно на ранжирование (через поведенческие факторы)

2. **Backlink profile:**
   - Количество и качество обратных ссылок
   - Anchor text distribution
   - Referring domains
   - Domain authority/rating

3. **Content freshness:**
   - Дата публикации
   - Дата последнего обновления
   - Частота обновлений

4. **Multimedia elements:**
   - Images (alt text, file names, optimization)
   - Videos (YouTube embeds, native video)
   - Infographics
   - Interactive elements

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. **Social signals:**
   - Shares, likes, comments
   - Social media presence

2. **Brand mentions:**
   - Branded vs non-branded traffic
   - Brand authority signals

3. **User engagement metrics:**
   - Bounce rate (если доступно)
   - Time on page
   - Pages per session

## Дополнительные материалы

**Интервью:** Этот файл  
**Связанные спецификации:**
- Content Gap Analysis Agent
- Keyword Research Agent
- SEO Magister

**TODO из других агентов:**
- Интеграция с Content Gap Analysis для автоматического поиска пробелов
- Интеграция с Keyword Research для анализа ключевых слов конкурентов

## Ключевые вопросы для исследования

1. **Какая оптимальная плотность ключевых слов в 2026?** (Google guidelines)
2. **Как Google детектирует AI-контент?** (официальные заявления + исследования)
3. **Какие E-E-A-T сигналы наиболее важны для медицинского контента?**
4. **Какие технические SEO-факторы имеют наибольший вес в ранжировании?**
5. **Есть ли корреляция между конверсионными фреймворками и ранжированием?**
6. **Какие бесплатные инструменты лучше всего подходят для анализа контента конкурентов?**

## Метрики успеха агента

**Точность анализа:**
- Precision > 90% (правильно определённые факторы)
- Recall > 85% (не пропущенные факторы)

**Полезность рекомендаций:**
- Actionable recommendations (конкретные шаги, не общие советы)
- Prioritized by impact (сначала факторы с наибольшим влиянием)

**Скорость:**
- Quick analysis (1 страница): < 2 минуты
- Deep analysis (1 страница): < 5 минут
- Competitor comparison (2-5 сайтов): < 10 минут
