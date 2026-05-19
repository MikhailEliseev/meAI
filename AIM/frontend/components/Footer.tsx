import Link from "next/link";

const footerColumns = [
  {
    title: "Услуги",
    links: [
      { href: "/services#seo", label: "SEO-продвижение" },
      { href: "/services#ads", label: "Яндекс.Директ" },
      { href: "/services#content", label: "Контент-маркетинг" },
      { href: "/services#analytics", label: "AI-аналитика" },
    ],
  },
  {
    title: "Компания",
    links: [
      { href: "/about", label: "О нас" },
      { href: "/case-studies", label: "Кейсы" },
      { href: "/blog", label: "Блог" },
      { href: "/contact", label: "Контакты" },
    ],
  },
  {
    title: "Клиентам",
    links: [
      { href: "/privacy-policy", label: "Политика конфиденциальности" },
      { href: "/privacy-policy#cookies", label: "Cookie-файлы" },
      { href: "/privacy-policy#data", label: "Обработка данных (ФЗ-152)" },
      { href: "/contact", label: "Поддержка" },
    ],
  },
];

export function Footer() {
  return (
    <footer
      className="bg-gray-900 text-gray-300 pt-16 pb-8 px-4"
      role="contentinfo"
    >
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-12">
          {footerColumns.map((col) => (
            <div key={col.title}>
              <h4 className="font-heading text-white font-semibold text-sm uppercase tracking-wider mb-4">
                {col.title}
              </h4>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-sm text-gray-400 hover:text-white transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Contacts column */}
          <div>
            <h4 className="font-heading text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Контакты
            </h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li>
                <a
                  href="mailto:hello@iamaim.ru"
                  className="hover:text-white transition-colors"
                >
                  hello@iamaim.ru
                </a>
              </li>
              <li>
                <a
                  href="tel:+79991234567"
                  className="hover:text-white transition-colors"
                >
                  +7 999 123-45-67
                </a>
              </li>
              <li>
                <a
                  href="https://t.me/aimagency"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  Telegram
                </a>
              </li>
              <li>
                <a
                  href="https://vk.com/aimagency"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  VK
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-gray-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 bg-primary-600 text-white rounded flex items-center justify-center text-[10px] font-extrabold">
              AIM
            </span>
            <p className="text-sm text-gray-500">
              &copy; {new Date().getFullYear()} AIM Agency. Все права защищены.
            </p>
          </div>
          <p className="text-xs text-gray-500">
            AI-first медицинское маркетинговое агентство
          </p>
        </div>
      </div>
    </footer>
  );
}
