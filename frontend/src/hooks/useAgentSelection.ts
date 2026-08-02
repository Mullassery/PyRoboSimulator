/**
 * Hook for managing agent selection state.
 */

import { useState, useCallback } from 'react'

export function useAgentSelection() {
  const [selectedAgents, setSelectedAgents] = useState<Set<number>>(new Set())

  const toggleAgent = useCallback((agentId: number, multiSelect: boolean) => {
    setSelectedAgents((prev) => {
      const newSet = new Set(prev)

      if (!multiSelect) {
        // Single select mode - replace entire selection
        if (newSet.has(agentId) && newSet.size === 1) {
          // Deselect if it's the only selected agent
          newSet.delete(agentId)
        } else {
          // Replace with single agent
          newSet.clear()
          newSet.add(agentId)
        }
      } else {
        // Multi-select mode - toggle this agent
        if (newSet.has(agentId)) {
          newSet.delete(agentId)
        } else {
          newSet.add(agentId)
        }
      }

      return newSet
    })
  }, [])

  const selectAgents = useCallback((agentIds: number[]) => {
    setSelectedAgents(new Set(agentIds))
  }, [])

  const clearSelection = useCallback(() => {
    setSelectedAgents(new Set())
  }, [])

  const selectAll = useCallback((agentIds: number[]) => {
    setSelectedAgents(new Set(agentIds))
  }, [])

  return {
    selectedAgents,
    toggleAgent,
    selectAgents,
    selectAll,
    clearSelection,
  }
}
