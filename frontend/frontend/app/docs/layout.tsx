import { Metadata } from 'next'
import { Sidebar } from '@/components/docs/Sidebar'
import { Breadcrumbs } from '@/components/docs/Breadcrumbs'

export const metadata: Metadata = {
  title: {
    default: 'Documentation',
    template: '%s | Documentation',
  },
  description: 'Comprehensive documentation for components, hooks, and guides',
}

const sidebarItems = [
  {
    title: 'Getting Started',
    items: [
      { title: 'Introduction', href: '/docs/introduction' },
      { title: 'Installation', href: '/docs/installation' },
      { title: 'Configuration', href: '/docs/configuration' },
    ],
  },
  {
    title: 'Components',
    items: [
      { title: 'Accordion', href: '/docs/components/accordion' },
      { title: 'Alert', href: '/docs/components/alert' },
      { title: 'Avatar', href: '/docs/components/avatar' },
      { title: 'Badge', href: '/docs/components/badge' },
      { title: 'Button', href: '/docs/components/button' },
      { title: 'Calendar', href: '/docs/components/calendar' },
      { title: 'Card', href: '/docs/components/card' },
      { title: 'Checkbox', href: '/docs/components/checkbox' },
      { title: 'Collapsible', href: '/docs/components/collapsible' },
      { title: 'Command', href: '/docs/components/command' },
      { title: 'Dialog', href: '/docs/components/dialog' },
      { title: 'Dropdown Menu', href: '/docs/components/dropdown-menu' },
      { title: 'Form', href: '/docs/components/form' },
      { title: 'Input', href: '/docs/components/input' },
      { title: 'Label', href: '/docs/components/label' },
      { title: 'Pagination', href: '/docs/components/pagination' },
      { title: 'Popover', href: '/docs/components/popover' },
      { title: 'Progress', href: '/docs/components/progress' },
      { title: 'Radio Group', href: '/docs/components/radio-group' },
      { title: 'Select', href: '/docs/components/select' },
      { title: 'Separator', href: '/docs/components/separator' },
      { title: 'Sheet', href: '/docs/components/sheet' },
      { title: 'Skeleton', href: '/docs/components/skeleton' },
      { title: 'Slider', href: '/docs/components/slider' },
      { title: 'Switch', href: '/docs/components/switch' },
      { title: 'Table', href: '/docs/components/table' },
      { title: 'Tabs', href: '/docs/components/tabs' },
      { title: 'Textarea', href: '/docs/components/textarea' },
      { title: 'Toast', href: '/docs/components/toast' },
      { title: 'Tooltip', href: '/docs/components/tooltip' },
    ],
  },
  {
    title: 'Hooks',
    items: [
      { title: 'useDebounce', href: '/docs/hooks/use-debounce' },
      { title: 'useLocalStorage', href: '/docs/hooks/use-local-storage' },
      { title: 'useMediaQuery', href: '/docs/hooks/use-media-query' },
      { title: 'useOnClickOutside', href: '/docs/hooks/use-on-click-outside' },
      { title: 'useToggle', href: '/docs/hooks/use-toggle' },
    ],
  },
  {
    title: 'Guides',
    items: [
      { title: 'Theming', href: '/docs/guides/theming' },
      { title: 'Dark Mode', href: '/docs/guides/dark-mode' },
      { title: 'Accessibility', href: '/docs/guides/accessibility' },
      { title: 'Forms', href: '/docs/guides/forms' },
      { title: 'Testing', href: '/docs/guides/testing' },
    ],
  },
]

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="container flex-1 items-start md:grid md:grid-cols-[220px_minmax(0,1fr)] md:gap-6 lg:grid-cols-[240px_minmax(0,1fr)] lg:gap-10">
      <Sidebar items={sidebarItems} />
      <main className="relative py-6 lg:gap-10 lg:py-8 xl:grid xl:grid-cols-[1fr_300px]">
        <div className="mx-auto w-full min-w-0">
          <Breadcrumbs className="mb-4" />
          {children}
        </div>
      </main>
    </div>
  )
}
