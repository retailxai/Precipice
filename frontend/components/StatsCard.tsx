'use client'

import { useQuery } from '@tanstack/react-query'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchStats() {
  const response = await fetch(`${API_BASE}/api/stats`)
  if (!response.ok) {
    throw new Error('Failed to fetch stats')
  }
  return response.json()
}

export function StatsCard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['stats'],
    queryFn: fetchStats,
  })

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-4 gap-4">
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
          Error loading statistics
        </div>
      </div>
    )
  }

  const stats = data?.stats || {
    totalDrafts: 0,
    publishedToday: 0,
    activeChannels: 0,
    lastUpdate: new Date().toISOString(),
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.totalDrafts}</div>
          <div className="text-sm text-gray-500">Total Drafts</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{stats.publishedToday}</div>
          <div className="text-sm text-gray-500">Published Today</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">{stats.activeChannels}</div>
          <div className="text-sm text-gray-500">Active Channels</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {new Date(stats.lastUpdate).toLocaleTimeString()}
          </div>
          <div className="text-sm text-gray-500">Last Update</div>
        </div>
      </div>
    </div>
  )
}
