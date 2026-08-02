/**
 * Agent List Component with Search and Filtering
 * Allows searching, filtering, and selecting agents
 */

import React, { useMemo, useState } from 'react'
import '../styles/AgentList.css'

interface Agent {
  id: number
  state: string
  pos: [number, number, number]
}

interface AgentListProps {
  agents: Agent[]
  selectedAgents: Set<number>
  onSelectAgent: (agentId: number, multiSelect: boolean) => void
  onBulkSelect: (agentIds: number[]) => void
  onClearSelection: () => void
  highlightedAgent?: number | null
}

type StateFilter = 'all' | 'moving' | 'idle' | 'goal_reached' | 'collision'

export default function AgentList({
  agents,
  selectedAgents,
  onSelectAgent,
  onBulkSelect,
  onClearSelection,
  highlightedAgent,
}: AgentListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [stateFilter, setStateFilter] = useState<StateFilter>('all')
  const [sortBy, setSortBy] = useState<'id' | 'state' | 'distance'>('id')
  const [showFilters, setShowFilters] = useState(false)

  // Filter and search agents
  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      // Search filter
      if (searchTerm && !agent.id.toString().includes(searchTerm)) {
        return false
      }

      // State filter
      if (stateFilter !== 'all' && agent.state !== stateFilter) {
        return false
      }

      return true
    })
  }, [agents, searchTerm, stateFilter])

  // Sort agents
  const sortedAgents = useMemo(() => {
    const sorted = [...filteredAgents]
    switch (sortBy) {
      case 'id':
        sorted.sort((a, b) => a.id - b.id)
        break
      case 'state':
        sorted.sort((a, b) => a.state.localeCompare(b.state))
        break
      case 'distance':
        sorted.sort((a, b) => {
          const distA = Math.sqrt(a.pos[0] ** 2 + a.pos[1] ** 2 + a.pos[2] ** 2)
          const distB = Math.sqrt(b.pos[0] ** 2 + b.pos[1] ** 2 + b.pos[2] ** 2)
          return distA - distB
        })
        break
    }
    return sorted
  }, [filteredAgents, sortBy])

  const getStateColor = (state: string): string => {
    switch (state) {
      case 'moving':
        return '#3a7fbd'
      case 'idle':
        return '#666'
      case 'goal_reached':
        return '#7abf1d'
      case 'collision':
        return '#ff6b6b'
      default:
        return '#a0a0a0'
    }
  }

  const handleSelectAll = () => {
    const allIds = sortedAgents.map((a) => a.id)
    onBulkSelect(allIds)
  }

  return (
    <div className="agent-list">
      <div className="agent-list-header">
        <h3>Agents ({filteredAgents.length}/{agents.length})</h3>
        <button
          className="btn-icon"
          onClick={() => setShowFilters(!showFilters)}
          title="Toggle filters"
        >
          ⚙
        </button>
      </div>

      {/* Search Bar */}
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search agent ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        {searchTerm && (
          <button
            className="btn-small"
            onClick={() => setSearchTerm('')}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="filters-panel">
          <div className="filter-group">
            <label>State Filter</label>
            <select
              value={stateFilter}
              onChange={(e) => setStateFilter(e.target.value as StateFilter)}
              className="filter-select"
            >
              <option value="all">All States</option>
              <option value="moving">Moving</option>
              <option value="idle">Idle</option>
              <option value="goal_reached">Goal Reached</option>
              <option value="collision">Collision</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'id' | 'state' | 'distance')}
              className="filter-select"
            >
              <option value="id">Agent ID</option>
              <option value="state">State</option>
              <option value="distance">Distance</option>
            </select>
          </div>

          <div className="filter-actions">
            <button className="btn-small" onClick={handleSelectAll}>
              Select All
            </button>
            <button className="btn-small secondary" onClick={onClearSelection}>
              Clear All
            </button>
          </div>
        </div>
      )}

      {/* Agent List */}
      <div className="agents-container">
        {sortedAgents.length === 0 ? (
          <div className="empty-state">
            {searchTerm ? 'No agents match your search' : 'No agents available'}
          </div>
        ) : (
          <div className="agents-grid">
            {sortedAgents.map((agent) => (
              <div
                key={agent.id}
                className={`agent-item ${
                  selectedAgents.has(agent.id) ? 'selected' : ''
                } ${highlightedAgent === agent.id ? 'highlighted' : ''}`}
                onClick={(e) => {
                  const isMultiSelect = e.ctrlKey || e.metaKey
                  onSelectAgent(agent.id, isMultiSelect)
                }}
                onDoubleClick={() => onSelectAgent(agent.id, false)}
                title={`Agent ${agent.id} - ${agent.state}`}
              >
                <div className="agent-id">#{agent.id}</div>
                <div
                  className="agent-state"
                  style={{ color: getStateColor(agent.state) }}
                >
                  {agent.state}
                </div>
                <div className="agent-pos">
                  ({agent.pos[0].toFixed(1)}, {agent.pos[1].toFixed(1)}, {agent.pos[2].toFixed(1)})
                </div>
                {selectedAgents.has(agent.id) && (
                  <div className="agent-selected-indicator">✓</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selection Info */}
      {selectedAgents.size > 0 && (
        <div className="selection-info">
          <span>{selectedAgents.size} agent(s) selected</span>
          <button
            className="btn-small secondary"
            onClick={() => {
              const selected = Array.from(selectedAgents)
              const json = JSON.stringify(selected)
              navigator.clipboard.writeText(json)
            }}
            title="Copy selected agent IDs"
          >
            Copy IDs
          </button>
        </div>
      )}
    </div>
  )
}
