'use client'

import { useState } from 'react'
import { DraftsList } from './DraftsList'
import { HealthCard } from './HealthCard'
import { StatsCard } from './StatsCard'

export function Dashboard() {
  const [activeTab, setActiveTab] = useState('drafts')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">RetailXAI Dashboard</h1>
            </div>
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('drafts')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'drafts'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Drafts
              </button>
              <button
                onClick={() => setActiveTab('health')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === 'health'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Health
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'drafts' && (
          <div className="space-y-6">
            <StatsCard />
            <DraftsList />
          </div>
        )}
        
        {activeTab === 'health' && (
          <div className="space-y-6">
            <HealthCard />
          </div>
        )}
      </main>
    </div>
  )
}
