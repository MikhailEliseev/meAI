# AIM Agency Frontend - Performance Optimization Guide

## Performance Targets (Lighthouse)

- **Performance:** ≥90
- **Accessibility:** ≥95
- **Best Practices:** ≥95
- **SEO:** ≥95

## Optimizations Implemented

### 1. Image Optimization
- **Next.js Image Component:** Automatic optimization, lazy loading, responsive images
- **Formats:** AVIF (primary), WebP (fallback), PNG/JPEG (legacy)
- **Device Sizes:** 640, 750, 828, 1080, 1200, 1920, 2048, 3840
- **Image Sizes:** 16, 32, 48, 64, 96, 128, 256, 384

### 2. Font Optimization
- **Google Fonts:** Inter (body), Poppins (headings)
- **Subsets:** Latin, Cyrillic (for Russian content)
- **Display:** swap (prevents FOIT - Flash of Invisible Text)
- **Preload:** Automatic via Next.js font optimization

### 3. Code Splitting
- **Automatic:** Next.js App Router splits by route
- **Dynamic Imports:** Use for heavy components (charts, maps)
- **Bundle Analysis:** Run `npm run build` to analyze bundle size

### 4. Caching Strategy
- **Static Assets:** 1 year cache (fonts, images)
- **HTML:** No cache (always fresh)
- **API Routes:** Custom cache headers per endpoint

### 5. Security Headers
- **HSTS:** Strict-Transport-Security (HTTPS only)
- **XSS Protection:** X-XSS-Protection
- **Frame Options:** X-Frame-Options (prevent clickjacking)
- **Content Type:** X-Content-Type-Options (prevent MIME sniffing)
- **Referrer Policy:** strict-origin-when-cross-origin
- **Permissions Policy:** Disable unused browser features

### 6. SEO Optimization
- **Metadata:** Comprehensive title, description, keywords
- **Open Graph:** Facebook, LinkedIn sharing
- **Twitter Cards:** Twitter sharing
- **Structured Data:** Organization, WebSite, BreadcrumbList, FAQPage, Review
- **Sitemap:** Dynamic sitemap.xml generation
- **Robots.txt:** Search engine crawling rules
- **Canonical URLs:** Prevent duplicate content

### 7. Analytics
- **Yandex.Metrika:** Russian market analytics
- **Goals:** Form submissions, button clicks, scroll depth
- **Webvisor:** Session recordings (optional)
- **E-commerce:** Ready for transaction tracking

## Performance Checklist

### Before Production
- [ ] Compress all images (TinyPNG, Squoosh)
- [ ] Generate favicon set (favicon.ico, icon.svg, apple-touch-icon.png)
- [ ] Create OG image (1200x630px)
- [ ] Test on mobile devices (iOS Safari, Chrome Android)
- [ ] Run Lighthouse audit (target: all scores ≥90)
- [ ] Test with slow 3G network (Chrome DevTools)
- [ ] Verify Yandex.Metrika tracking
- [ ] Test reCAPTCHA on contact form
- [ ] Verify email delivery (SendGrid)

### Monitoring
- [ ] Set up Yandex.Metrika goals
- [ ] Monitor Core Web Vitals (LCP, FID, CLS)
- [ ] Track conversion rate (form submissions)
- [ ] Monitor error rate (Sentry or similar)
- [ ] Check uptime (UptimeRobot or similar)

## Core Web Vitals Targets

- **LCP (Largest Contentful Paint):** <2.5s
- **FID (First Input Delay):** <100ms
- **CLS (Cumulative Layout Shift):** <0.1

## Bundle Size Targets

- **First Load JS:** <200KB
- **Total Page Size:** <1MB
- **Time to Interactive:** <3s (3G)

## Commands

```bash
# Development
npm run dev

# Production build
npm run build

# Start production server
npm start

# Analyze bundle
npm run build && npx @next/bundle-analyzer

# Lighthouse audit
npx lighthouse https://iamaim.ru --view

# Test performance
npm run build && npm start
# Then open Chrome DevTools > Lighthouse
```

## Russian Market Specifics

### Yandex.Metrika Setup
1. Create account at https://metrika.yandex.ru
2. Add site: iamaim.ru
3. Copy Metrika ID
4. Add to `.env.local`: `NEXT_PUBLIC_YANDEX_METRIKA_ID=12345678`
5. Verify tracking in Yandex.Metrika dashboard

### Yandex Webmaster Setup
1. Register at https://webmaster.yandex.ru
2. Add site: iamaim.ru
3. Verify ownership (meta tag or DNS)
4. Submit sitemap: https://iamaim.ru/sitemap.xml
5. Monitor indexing status

## Future Optimizations

- [ ] Implement Service Worker (PWA)
- [ ] Add offline support
- [ ] Implement push notifications
- [ ] Add image CDN (Cloudflare, Cloudinary)
- [ ] Implement edge caching (Vercel Edge, Cloudflare Workers)
- [ ] Add A/B testing (Yandex.Metrika Experiments)
- [ ] Implement lazy loading for below-fold content
- [ ] Add prefetching for critical routes
