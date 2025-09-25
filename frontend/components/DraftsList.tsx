'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { DraftCard } from './DraftCard'

interface Draft {
  id: number
  title: string
  slug: string
  summary: string
  status: string
  created_at: string
  updated_at: string
  tags: string[]
}

interface DraftsResponse {
  drafts: Draft[]
  total: number
  page: number
  size: number
  pages: number
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

async function fetchDrafts(): Promise<DraftsResponse> {
  const response = await fetch(`${API_BASE}/api/drafts`)
  if (!response.ok) {
    throw new Error('Failed to fetch drafts')
  }
  return response.json()
}

export function DraftsList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['drafts'],
    queryFn: fetchDrafts,
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Error loading drafts
            </h3>
            <div className="mt-2 text-sm text-red-700">
              {error instanceof Error ? error.message : 'Unknown error'}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!data || data.drafts.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">No drafts found</h3>
        <p className="mt-2 text-gray-500">Create your first draft to get started.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Drafts</h2>
        <div className="text-sm text-gray-500">
          {data.total} total • Page {data.page} of {data.pages}
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.drafts.map((draft) => (
          <DraftCard key={draft.id} draft={draft} />
        ))}
      </div>
    </div>
  )
}
