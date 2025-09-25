/**
 * DraftCard component tests
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DraftCard } from '@/components/DraftCard'
import { Draft } from '@/types/draft'

// Mock fetch
const mockFetch = jest.fn()
global.fetch = mockFetch

const mockDraft: Draft = {
  id: 1,
  title: 'Test Draft',
  slug: 'test-draft',
  summary: 'A test draft for testing',
  status: 'draft',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  tags: ['test', 'example'],
  body_md: '# Test Content',
  body_html: '<h1>Test Content</h1>',
  author: 'testuser',
  source: 'manual',
  source_ref: 'test-ref',
  hero_image_url: 'https://example.com/image.jpg',
  scores: { readability: 0.8 },
  meta: { word_count: 100 }
}

describe('DraftCard', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('renders draft information', () => {
    render(<DraftCard draft={mockDraft} />)
    
    expect(screen.getByText('Test Draft')).toBeInTheDocument()
    expect(screen.getByText('A test draft for testing')).toBeInTheDocument()
    expect(screen.getByText('test')).toBeInTheDocument()
    expect(screen.getByText('example')).toBeInTheDocument()
  })

  it('shows draft status', () => {
    render(<DraftCard draft={mockDraft} />)
    
    expect(screen.getByText('draft')).toBeInTheDocument()
  })

  it('shows creation and update dates', () => {
    render(<DraftCard draft={mockDraft} />)
    
    expect(screen.getByText(/Created:/)).toBeInTheDocument()
    expect(screen.getByText(/Updated:/)).toBeInTheDocument()
  })

  it('renders publish buttons', () => {
    render(<DraftCard draft={mockDraft} />)
    
    expect(screen.getByText('Publish to Substack')).toBeInTheDocument()
    expect(screen.getByText('Publish to LinkedIn')).toBeInTheDocument()
    expect(screen.getByText('Publish to Twitter')).toBeInTheDocument()
  })

  it('handles publish to Substack', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Published successfully' })
    })

    render(<DraftCard draft={mockDraft} />)
    
    const publishButton = screen.getByText('Publish to Substack')
    fireEvent.click(publishButton)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/drafts/1/publish',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoints: ['substack'] })
        })
      )
    })
  })

  it('handles publish to LinkedIn', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Published successfully' })
    })

    render(<DraftCard draft={mockDraft} />)
    
    const publishButton = screen.getByText('Publish to LinkedIn')
    fireEvent.click(publishButton)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/drafts/1/publish',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoints: ['linkedin'] })
        })
      )
    })
  })

  it('handles publish to Twitter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ message: 'Published successfully' })
    })

    render(<DraftCard draft={mockDraft} />)
    
    const publishButton = screen.getByText('Publish to Twitter')
    fireEvent.click(publishButton)
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/drafts/1/publish',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ endpoints: ['twitter'] })
        })
      )
    })
  })

  it('shows loading state during publish', async () => {
    mockFetch.mockImplementationOnce(
      () => new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: async () => ({ message: 'Published successfully' })
      }), 100))
    )

    render(<DraftCard draft={mockDraft} />)
    
    const publishButton = screen.getByText('Publish to Substack')
    fireEvent.click(publishButton)
    
    expect(screen.getByText('Publishing...')).toBeInTheDocument()
    expect(publishButton).toBeDisabled()
  })

  it('handles publish failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    // Mock alert
    const mockAlert = jest.spyOn(window, 'alert').mockImplementation(() => {})

    render(<DraftCard draft={mockDraft} />)
    
    const publishButton = screen.getByText('Publish to Substack')
    fireEvent.click(publishButton)
    
    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith('Failed to publish. Please try again.')
    })

    mockAlert.mockRestore()
  })

  it('handles different draft statuses', () => {
    const publishedDraft = { ...mockDraft, status: 'published' as const }
    render(<DraftCard draft={publishedDraft} />)
    
    expect(screen.getByText('published')).toBeInTheDocument()
  })

  it('handles draft without summary', () => {
    const draftWithoutSummary = { ...mockDraft, summary: undefined }
    render(<DraftCard draft={draftWithoutSummary} />)
    
    expect(screen.getByText('Test Draft')).toBeInTheDocument()
    expect(screen.queryByText('A test draft for testing')).not.toBeInTheDocument()
  })

  it('handles draft without tags', () => {
    const draftWithoutTags = { ...mockDraft, tags: [] }
    render(<DraftCard draft={draftWithoutTags} />)
    
    expect(screen.getByText('Test Draft')).toBeInTheDocument()
    expect(screen.queryByText('test')).not.toBeInTheDocument()
  })
})
