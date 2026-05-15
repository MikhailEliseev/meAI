'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Search } from 'lucide-react'
import { cn } from '../../lib/utils'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '../ui/command'

interface SearchResult {
  id: string
  title: string
  description: string
  category: string
  href: string
  snippet?: string
}

export function SearchDialog() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const router = useRouter()

  // Open dialog with Cmd+K or Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  // Perform search with debounce
  useEffect(() => {
    if (!query) {
      setResults([])
      return
    }

    const timer = setTimeout(() => {
      // Import search index dynamically
      import('../../lib/search').then(({ getSearchIndex }) => {
        const index = getSearchIndex()
        const searchResults = index.search(query)
        setResults(searchResults)
        setSelectedIndex(0)
      })
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter' && results[selectedIndex]) {
        e.preventDefault()
        router.push(results[selectedIndex].href)
        setOpen(false)
      }
    },
    [results, selectedIndex, router]
  )

  // Group results by category
  const groupedResults = results.reduce((acc, result) => {
    if (!acc[result.category]) {
      acc[result.category] = []
    }
    acc[result.category].push(result)
    return acc
  }, {} as Record<string, SearchResult[]>)

  // Highlight search term in text
  const highlightMatch = (text: string, query: string) => {
    if (!query) return text

    const regex = new RegExp(`(${query})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-200 dark:bg-yellow-800">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput
        placeholder="Search documentation..."
        value={query}
        onValueChange={setQuery}
        onKeyDown={handleKeyDown}
      />
      <CommandList>
        {results.length === 0 && query && (
          <CommandEmpty>No results found.</CommandEmpty>
        )}

        {Object.entries(groupedResults).map(([category, items]) => (
          <CommandGroup
            key={category}
            heading={category.charAt(0).toUpperCase() + category.slice(1)}
          >
            {items.map((result, index) => {
              const globalIndex = results.indexOf(result)
              const isSelected = globalIndex === selectedIndex

              return (
                <CommandItem
                  key={result.id}
                  value={result.id}
                  onSelect={() => {
                    router.push(result.href)
                    setOpen(false)
                  }}
                  className={cn(isSelected && 'bg-accent')}
                  data-highlighted={isSelected}
                  role="option"
                >
                  <div className="flex flex-col gap-1">
                    <div className="font-medium">
                      {highlightMatch(result.title, query)}
                    </div>
                    {result.description && (
                      <div className="text-sm text-muted-foreground">
                        {highlightMatch(result.description, query)}
                      </div>
                    )}
                    {result.snippet && (
                      <div className="text-xs text-muted-foreground">
                        {highlightMatch(result.snippet, query)}
                      </div>
                    )}
                  </div>
                </CommandItem>
              )
            })}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  )
}
