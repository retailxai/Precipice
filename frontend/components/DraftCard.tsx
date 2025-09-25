'use client'

import { useState } from 'react'
import { Draft } from '@/types/draft'

interface DraftCardProps {
  draft: Draft
}

export function DraftCard({ draft }: DraftCardProps) {
  const [isPublishing, setIsPublishing] = useState(false)

  const handlePublish = async (endpoint: string) => {
    setIsPublishing(true)
    try {
      const response = await fetch(`/api/drafts/${draft.id}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          endpoints: [endpoint],
        }),
      })
      
      if (!response.ok) {
        throw new Error('Failed to publish')
      }
      
      // Show success message
      alert(`Published to ${endpoint} successfully!`)
    } catch (error) {
      console.error('Publish error:', error)
      alert('Failed to publish. Please try again.')
    } finally {
      setIsPublishing(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800'
      case 'review':
        return 'bg-yellow-100 text-yellow-800'
      case 'approved':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
          {draft.title}
        </h3>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(draft.status)}`}>
          {draft.status}
        </span>
      </div>
      
      {draft.summary && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {draft.summary}
        </p>
      )}
      
      {draft.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {draft.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
      
      <div className="flex justify-between items-center text-xs text-gray-500 mb-4">
        <span>Created: {new Date(draft.created_at).toLocaleDateString()}</span>
        <span>Updated: {new Date(draft.updated_at).toLocaleDateString()}</span>
      </div>
      
      <div className="flex space-x-2">
        <button
          onClick={() => handlePublish('substack')}
          disabled={isPublishing}
          className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPublishing ? 'Publishing...' : 'Publish to Substack'}
        </button>
        <button
          onClick={() => handlePublish('linkedin')}
          disabled={isPublishing}
          className="flex-1 bg-blue-700 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPublishing ? 'Publishing...' : 'Publish to LinkedIn'}
        </button>
        <button
          onClick={() => handlePublish('twitter')}
          disabled={isPublishing}
          className="flex-1 bg-gray-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPublishing ? 'Publishing...' : 'Publish to Twitter'}
        </button>
      </div>
    </div>
  )
}
