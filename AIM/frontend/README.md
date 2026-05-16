# AIM Agency Frontend

Landing page для привлечения клиентов медицинского маркетингового агентства.

## Технологии

- **Next.js 14** - React framework с App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Framer Motion** - Animations
- **React Hook Form** - Form handling
- **Jest + Testing Library** - Testing

## Russian Market Adaptation

Проект адаптирован под российский рынок:

- ✅ **ФЗ-152** вместо HIPAA (compliance)
- ✅ **Яндекс.Директ** вместо Google Ads (партнёрство)
- ✅ **Российские метрики** (трафик, пациенты, результаты)
- 🔄 **ЮKassa** вместо Helcim (payment - stub, Phase 12)
- 🔄 **Контур.Диадок** вместо DocuSign (signatures - stub, Phase 12)

## Установка

```bash
cd AIM/frontend
npm install
```

## Разработка

```bash
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000)

## Тестирование

```bash
# Запустить тесты
npm test

# Запустить с coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Сборка

```bash
npm run build
npm start
```

## Структура

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Landing page
│   └── globals.css        # Global styles
├── components/
│   └── landing/           # Landing page components
│       ├── HeroSection.tsx
│       └── TrustBadges.tsx
├── lib/
│   └── utils.ts           # Utility functions
├── __tests__/             # Tests
│   └── landing/
└── public/                # Static assets
```

## Phase 11 Progress

### Task 1.1: Hero Section ✅ COMPLETED
- [x] Hero component with trust badges
- [x] Headline and subheadline
- [x] Primary CTA button
- [x] Trust badges (ФЗ-152, Яндекс, клиенты, гарантия)
- [x] Mobile-responsive design
- [x] Accessibility (WCAG 2.1 AA)
- [x] Tests (10 test cases)

### Next Tasks
- [ ] Task 1.2: Social Proof Section (case studies, testimonials)
- [ ] Task 1.3: Process Visualization (3-step process)
- [ ] Task 1.4: FAQ Section
- [ ] Task 1.5: Contact Form (HIPAA-compliant)
- [ ] Task 1.6: Landing Page Integration

## Accessibility

- WCAG 2.1 AA compliant
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support
- Contrast ratio ≥4.5:1

## Performance

- Lighthouse score target: ≥90
- Page load: <2s (3G)
- Image optimization (AVIF/WebP)
- Code splitting
- CSS optimization
