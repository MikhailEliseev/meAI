import { notFound } from 'next/navigation'
import { Metadata } from 'next'
import fs from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { MDXRemote } from 'next-mdx-remote/rsc'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

const components = {
  Button,
  Card,
  Input,
  Label,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Separator,
}

interface DocPageProps {
  params: {
    slug: string[]
  }
}

async function getDocFromParams(params: DocPageProps['params']) {
  const slug = params.slug?.join('/') || ''
  const filePath = path.join(process.cwd(), 'content/docs', `${slug}.mdx`)

  if (!fs.existsSync(filePath)) {
    return null
  }

  const fileContent = fs.readFileSync(filePath, 'utf8')
  const { data, content } = matter(fileContent)

  return {
    frontmatter: data,
    content,
  }
}

export async function generateMetadata({
  params,
}: DocPageProps): Promise<Metadata> {
  const doc = await getDocFromParams(params)

  if (!doc) {
    return {}
  }

  return {
    title: doc.frontmatter.title,
    description: doc.frontmatter.description,
  }
}

export async function generateStaticParams() {
  const contentDir = path.join(process.cwd(), 'content/docs')

  function getFiles(dir: string, basePath = ''): string[][] {
    const files = fs.readdirSync(dir)
    const paths: string[][] = []

    for (const file of files) {
      const filePath = path.join(dir, file)
      const stat = fs.statSync(filePath)

      if (stat.isDirectory()) {
        paths.push(...getFiles(filePath, path.join(basePath, file)))
      } else if (file.endsWith('.mdx')) {
        const slug = path.join(basePath, file.replace(/\.mdx$/, ''))
        paths.push(slug.split(path.sep))
      }
    }

    return paths
  }

  return getFiles(contentDir).map((slug) => ({ slug }))
}

export default async function DocPage({ params }: DocPageProps) {
  const doc = await getDocFromParams(params)

  if (!doc) {
    notFound()
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="scroll-m-20 text-4xl font-bold tracking-tight">
          {doc.frontmatter.title}
        </h1>
        {doc.frontmatter.description && (
          <p className="text-lg text-muted-foreground">
            {doc.frontmatter.description}
          </p>
        )}
      </div>

      <Separator />

      <div className="prose prose-slate dark:prose-invert max-w-none">
        <MDXRemote source={doc.content} components={components} />
      </div>
    </div>
  )
}
