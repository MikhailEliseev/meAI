import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowRight, Book, Code, Layers, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Documentation',
  description: 'Comprehensive documentation for components, hooks, and guides',
}

const categories = [
  {
    title: 'Components',
    description: 'UI components built with Radix UI and Tailwind CSS',
    icon: Layers,
    href: '/docs/components',
    count: 30,
  },
  {
    title: 'Hooks',
    description: 'Custom React hooks for common patterns',
    icon: Code,
    href: '/docs/hooks',
    count: 10,
  },
  {
    title: 'Guides',
    description: 'Step-by-step guides and best practices',
    icon: Book,
    href: '/docs/guides',
    count: 15,
  },
  {
    title: 'Examples',
    description: 'Real-world examples and use cases',
    icon: Zap,
    href: '/docs/examples',
    count: 20,
  },
]

const popularDocs = [
  { title: 'Button', href: '/docs/components/button', category: 'Components' },
  { title: 'Form', href: '/docs/components/form', category: 'Components' },
  { title: 'Dialog', href: '/docs/components/dialog', category: 'Components' },
  { title: 'Table', href: '/docs/components/table', category: 'Components' },
  { title: 'useDebounce', href: '/docs/hooks/use-debounce', category: 'Hooks' },
  { title: 'Getting Started', href: '/docs/guides/getting-started', category: 'Guides' },
]

export default function DocsPage() {
  return (
    <div className="container py-8 md:py-12 lg:py-16">
      <div className="mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
            Documentation
          </h1>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
            Everything you need to build modern web applications. Components, hooks, guides, and examples.
          </p>
        </div>

        {/* Categories Grid */}
        <div className="mb-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {categories.map((category) => {
            const Icon = category.icon
            return (
              <Link key={category.href} href={category.href}>
                <Card className="h-full transition-colors hover:bg-accent">
                  <CardHeader>
                    <div className="mb-2 flex items-center justify-between">
                      <Icon className="h-8 w-8 text-primary" />
                      <span className="text-sm text-muted-foreground">
                        {category.count} items
                      </span>
                    </div>
                    <CardTitle>{category.title}</CardTitle>
                    <CardDescription>{category.description}</CardDescription>
                  </CardHeader>
                </Card>
              </Link>
            )
          })}
        </div>

        {/* Popular Documentation */}
        <div className="mb-16">
          <h2 className="mb-6 text-2xl font-bold">Popular Documentation</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {popularDocs.map((doc) => (
              <Link key={doc.href} href={doc.href}>
                <Card className="h-full transition-colors hover:bg-accent">
                  <CardHeader>
                    <div className="mb-2 text-xs text-muted-foreground">
                      {doc.category}
                    </div>
                    <CardTitle className="flex items-center justify-between text-lg">
                      {doc.title}
                      <ArrowRight className="h-4 w-4" />
                    </CardTitle>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        {/* Quick Start */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Start</CardTitle>
            <CardDescription>
              Get started with our documentation in minutes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h3 className="font-semibold">1. Search Documentation</h3>
              <p className="text-sm text-muted-foreground">
                Press <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
                  <span className="text-xs">⌘</span>K
                </kbd> to open the search dialog and find what you need instantly.
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold">2. Browse Categories</h3>
              <p className="text-sm text-muted-foreground">
                Explore components, hooks, and guides organized by category.
              </p>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold">3. Copy & Paste</h3>
              <p className="text-sm text-muted-foreground">
                All examples are ready to use. Just copy the code and paste it into your project.
              </p>
            </div>
            <div className="flex gap-4 pt-4">
              <Button asChild>
                <Link href="/docs/guides/getting-started">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/docs/components">Browse Components</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
