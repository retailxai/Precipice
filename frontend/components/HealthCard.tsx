'use client'

import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchHealth() {
  const response = await fetch(`${API_BASE}/api/health/summary`)
  if (!response.ok) {
    throw new Error('Failed to fetch health data')
  }
  return response.json()
}

export function HealthCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-sm text-red-700">
          Error loading health data
        </div>
      </div>
    )
  }

  const health = data || {
    status: 'unknown',
    database: 'unknown',
    redis: 'unknown',
    workers: 'unknown',
    queue_depth: 0,
    rate_limits: { remaining: 0, reset_at: '' },
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600'
      case 'unhealthy':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✓'
      case 'unhealthy':
        return '✗'
      default:
        return '?'
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${getStatusColor(health.database)}`}>
              {getStatusIcon(health.database)}
            </div>
            <div className="text-sm text-gray-500">Database</div>
            <div className="text-xs text-gray-400 capitalize">{health.database}</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getStatusColor(health.redis)}`}>
              {getStatusIcon(health.redis)}
            </div>
            <div className="text-sm text-gray-500">Redis</div>
            <div className="text-xs text-gray-400 capitalize">{health.redis}</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getStatusColor(health.workers)}`}>
              {getStatusIcon(health.workers)}
            </div>
            <div className="text-sm text-gray-500">Workers</div>
            <div className="text-xs text-gray-400 capitalize">{health.workers}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{health.queue_depth}</div>
            <div className="text-sm text-gray-500">Queue Depth</div>
            <div className="text-xs text-gray-400">Pending jobs</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate Limits</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-500">Remaining Requests</div>
            <div className="text-2xl font-bold text-blue-600">
              {health.rate_limits?.remaining || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Reset Time</div>
            <div className="text-sm text-gray-900">
              {health.rate_limits?.reset_at 
                ? new Date(health.rate_limits.reset_at).toLocaleString()
                : 'Unknown'
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
