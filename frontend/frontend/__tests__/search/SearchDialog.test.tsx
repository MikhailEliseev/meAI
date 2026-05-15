import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchDialog } from '../../components/search/SearchDialog'
import { vi } from 'vitest'

// Mock search index
const mockSearchIndex = {
  search: vi.fn(),
}

vi.mock('../../lib/search', () => ({
  getSearchIndex: () => mockSearchIndex,
}))

describe('SearchDialog', () => {
  beforeEach(() => {
    mockSearchIndex.search.mockClear()
  })

  describe('Keyboard Shortcuts', () => {
    it('opens on Cmd+K', () => {
      render(<SearchDialog />)

      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      expect(screen.getByPlaceholderText(/search documentation/i)).toBeInTheDocument()
    })

    it('opens on Ctrl+K', () => {
      render(<SearchDialog />)

      fireEvent.keyDown(document, { key: 'k', ctrlKey: true })

      expect(screen.getByPlaceholderText(/search documentation/i)).toBeInTheDocument()
    })

    it('closes on Escape', async () => {
      render(<SearchDialog />)

      // Open dialog
      fireEvent.keyDown(document, { key: 'k', metaKey: true })
      expect(screen.getByPlaceholderText(/search documentation/i)).toBeInTheDocument()

      // Close dialog
      fireEvent.keyDown(document, { key: 'Escape' })

      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/search documentation/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Search Functionality', () => {
    it('performs search on input', async () => {
      const mockResults = [
        {
          id: '1',
          title: 'Button Component',
          description: 'A button component',
          category: 'components',
          href: '/docs/components/button',
        },
      ]

      mockSearchIndex.search.mockReturnValue(mockResults)

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'button')

      await waitFor(() => {
        expect(mockSearchIndex.search).toHaveBeenCalledWith('button')
        expect(screen.getByText('Button Component')).toBeInTheDocument()
      })
    })

    it('shows no results message', async () => {
      mockSearchIndex.search.mockReturnValue([])

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'nonexistent')

      await waitFor(() => {
        expect(screen.getByText(/no results found/i)).toBeInTheDocument()
      })
    })

    it('debounces search input', async () => {
      vi.useFakeTimers()

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'but')

      // Should not search immediately
      expect(mockSearchIndex.search).not.toHaveBeenCalled()

      // Fast-forward time
      vi.advanceTimersByTime(300)

      await waitFor(() => {
        expect(mockSearchIndex.search).toHaveBeenCalledWith('but')
      })

      vi.useRealTimers()
    })
  })

  describe('Keyboard Navigation', () => {
    const mockResults = [
      {
        id: '1',
        title: 'Button',
        description: 'Button component',
        category: 'components',
        href: '/docs/components/button',
      },
      {
        id: '2',
        title: 'Input',
        description: 'Input component',
        category: 'components',
        href: '/docs/components/input',
      },
      {
        id: '3',
        title: 'Card',
        description: 'Card component',
        category: 'components',
        href: '/docs/components/card',
      },
    ]

    beforeEach(() => {
      mockSearchIndex.search.mockReturnValue(mockResults)
    })

    it('navigates down with ArrowDown', async () => {
      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'component')

      await waitFor(() => {
        expect(screen.getByText('Button')).toBeInTheDocument()
      })

      // Press ArrowDown
      fireEvent.keyDown(input, { key: 'ArrowDown' })

      // First result should be highlighted
      const firstResult = screen.getByText('Button').closest('[role="option"]')
      expect(firstResult).toHaveAttribute('data-highlighted', 'true')
    })

    it('navigates up with ArrowUp', async () => {
      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'component')

      await waitFor(() => {
        expect(screen.getByText('Button')).toBeInTheDocument()
      })

      // Navigate down twice
      fireEvent.keyDown(input, { key: 'ArrowDown' })
      fireEvent.keyDown(input, { key: 'ArrowDown' })

      // Navigate up once
      fireEvent.keyDown(input, { key: 'ArrowUp' })

      // First result should be highlighted
      const firstResult = screen.getByText('Button').closest('[role="option"]')
      expect(firstResult).toHaveAttribute('data-highlighted', 'true')
    })

    it('selects result with Enter', async () => {
      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)

      mockSearchIndex.search.mockReturnValue([
        {
          id: '1',
          title: 'Button',
          description: 'A button component',
          category: 'components',
          href: '/docs/components/button',
        },
      ])

      await userEvent.type(input, 'button')

      await waitFor(() => {
        expect(screen.getByText('Button')).toBeInTheDocument()
      })

      // Press Enter to select first result
      fireEvent.keyDown(input, { key: 'Enter' })

      // Dialog should close
      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/search documentation/i)).not.toBeInTheDocument()
      })
    })
  })

  describe('Match Highlighting', () => {
    it('highlights search term in results', async () => {
      const mockResults = [
        {
          id: '1',
          title: 'Button Component',
          description: 'A button component for user interactions',
          category: 'components',
          href: '/docs/components/button',
        },
      ]

      mockSearchIndex.search.mockReturnValue(mockResults)

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'button')

      await waitFor(() => {
        const highlighted = screen.getAllByText(/button/i)
        expect(highlighted.length).toBeGreaterThan(0)
      })
    })
  })

  describe('Snippet Generation', () => {
    it('shows content snippet in results', async () => {
      const mockResults = [
        {
          id: '1',
          title: 'Button',
          description: 'Button component',
          category: 'components',
          href: '/docs/components/button',
          snippet: 'A button component for triggering actions...',
        },
      ]

      mockSearchIndex.search.mockReturnValue(mockResults)

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'button')

      await waitFor(() => {
        expect(screen.getByText(/A button component for triggering actions/i)).toBeInTheDocument()
      })
    })
  })

  describe('Categories', () => {
    it('groups results by category', async () => {
      const mockResults = [
        {
          id: '1',
          title: 'Button',
          description: 'Button component',
          category: 'components',
          href: '/docs/components/button',
        },
        {
          id: '2',
          title: 'useDebounce',
          description: 'Debounce hook',
          category: 'hooks',
          href: '/docs/hooks/use-debounce',
        },
      ]

      mockSearchIndex.search.mockReturnValue(mockResults)

      render(<SearchDialog />)
      fireEvent.keyDown(document, { key: 'k', metaKey: true })

      const input = screen.getByPlaceholderText(/search documentation/i)
      await userEvent.type(input, 'component')

      await waitFor(() => {
        expect(screen.getByText('Components')).toBeInTheDocument()
        expect(screen.getByText('Hooks')).toBeInTheDocument()
      })
    })
  })
})
