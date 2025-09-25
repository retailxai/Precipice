/**
 * Dashboard component tests
 */

import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Dashboard } from '@/components/Dashboard'

// Mock the child components
jest.mock('@/components/DraftsList', () => ({
  DraftsList: () => <div data-testid="drafts-list">Drafts List</div>
}))

jest.mock('@/components/HealthCard', () => ({
  HealthCard: () => <div data-testid="health-card">Health Card</div>
}))

jest.mock('@/components/StatsCard', () => ({
  StatsCard: () => <div data-testid="stats-card">Stats Card</div>
}))

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
})

describe('Dashboard', () => {
  it('renders the dashboard header', () => {
    const queryClient = createTestQueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    expect(screen.getByText('RetailXAI Dashboard')).toBeInTheDocument()
  })

  it('renders navigation tabs', () => {
    const queryClient = createTestQueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    expect(screen.getByText('Drafts')).toBeInTheDocument()
    expect(screen.getByText('Health')).toBeInTheDocument()
  })

  it('shows drafts tab by default', () => {
    const queryClient = createTestQueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    expect(screen.getByTestId('drafts-list')).toBeInTheDocument()
    expect(screen.getByTestId('stats-card')).toBeInTheDocument()
  })

  it('switches to health tab when clicked', () => {
    const queryClient = createTestQueryClient()
    
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    const healthTab = screen.getByText('Health')
    healthTab.click()
    
    expect(screen.getByTestId('health-card')).toBeInTheDocument()
  })
})
