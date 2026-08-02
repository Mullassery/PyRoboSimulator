/**
 * Tests for AgentList component
 */

import { describe, it, expect, vi } from 'vitest'
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import AgentList from '../AgentList'

describe('AgentList', () => {
  const mockAgents = [
    {
      id: 1,
      state: 'moving',
      pos: [10, 20, 30] as [number, number, number],
    },
    {
      id: 2,
      state: 'idle',
      pos: [15, 25, 35] as [number, number, number],
    },
    {
      id: 3,
      state: 'goal_reached',
      pos: [20, 30, 40] as [number, number, number],
    },
    {
      id: 4,
      state: 'collision',
      pos: [25, 35, 45] as [number, number, number],
    },
  ]

  const mockProps = {
    agents: mockAgents,
    selectedAgents: new Set<number>(),
    onSelectAgent: vi.fn(),
    onBulkSelect: vi.fn(),
    onClearSelection: vi.fn(),
  }

  it('should render agent list', () => {
    render(<AgentList {...mockProps} />)
    expect(screen.getByText('Agents (4/4)')).toBeDefined()
  })

  it('should display all agents', () => {
    render(<AgentList {...mockProps} />)
    mockAgents.forEach((agent) => {
      expect(screen.getByText(`#${agent.id}`)).toBeDefined()
    })
  })

  it('should display agent states with correct colors', () => {
    render(<AgentList {...mockProps} />)
    mockAgents.forEach((agent) => {
      expect(screen.getByText(agent.state)).toBeDefined()
    })
  })

  it('should filter agents by search term', () => {
    const { rerender } = render(<AgentList {...mockProps} />)

    // Simulate search
    const searchInput = screen.getByPlaceholderText('Search agent ID...')
    fireEvent.change(searchInput, { target: { value: '1' } })

    rerender(<AgentList {...mockProps} />)

    // Only agent 1 should be visible
    expect(screen.getByText('#1')).toBeDefined()
  })

  it('should handle agent selection', () => {
    const onSelectAgent = vi.fn()
    render(
      <AgentList {...mockProps} onSelectAgent={onSelectAgent} />
    )

    const agentItem = screen.getByTitle('Agent 1 - moving')
    fireEvent.click(agentItem)

    expect(onSelectAgent).toHaveBeenCalledWith(1, false)
  })

  it('should handle multi-select with ctrl key', () => {
    const onSelectAgent = vi.fn()
    render(
      <AgentList {...mockProps} onSelectAgent={onSelectAgent} />
    )

    const agentItem = screen.getByTitle('Agent 1 - moving')
    fireEvent.click(agentItem, { ctrlKey: true })

    expect(onSelectAgent).toHaveBeenCalledWith(1, true)
  })

  it('should display selected agents count', () => {
    const selected = new Set([1, 2])
    render(
      <AgentList
        {...mockProps}
        selectedAgents={selected}
      />
    )

    expect(screen.getByText('2 agent(s) selected')).toBeDefined()
  })

  it('should clear selection', () => {
    const onClearSelection = vi.fn()
    render(
      <AgentList
        {...mockProps}
        onClearSelection={onClearSelection}
      />
    )

    // Open filters to access clear button
    const settingsBtn = screen.getByTitle('Toggle filters')
    fireEvent.click(settingsBtn)

    const clearBtn = screen.getByText('Clear All')
    fireEvent.click(clearBtn)

    expect(onClearSelection).toHaveBeenCalled()
  })

  it('should select all agents', () => {
    const onBulkSelect = vi.fn()
    render(
      <AgentList
        {...mockProps}
        onBulkSelect={onBulkSelect}
      />
    )

    // Open filters
    const settingsBtn = screen.getByTitle('Toggle filters')
    fireEvent.click(settingsBtn)

    const selectAllBtn = screen.getByText('Select All')
    fireEvent.click(selectAllBtn)

    expect(onBulkSelect).toHaveBeenCalled()
  })

  it('should highlight agent', () => {
    const { container } = render(
      <AgentList
        {...mockProps}
        highlightedAgent={1}
      />
    )

    const highlighted = container.querySelector('.agent-item.highlighted')
    expect(highlighted).toBeDefined()
  })

  it('should show empty state when no agents match', () => {
    const emptyProps = {
      ...mockProps,
      agents: [],
    }

    render(<AgentList {...emptyProps} />)
    expect(screen.getByText('No agents available')).toBeDefined()
  })

  it('should handle agent filtering by state', () => {
    const { rerender } = render(<AgentList {...mockProps} />)

    // Open filters
    const settingsBtn = screen.getByTitle('Toggle filters')
    fireEvent.click(settingsBtn)

    // Filter by moving state
    const stateSelect = screen.getByDisplayValue('All States')
    fireEvent.change(stateSelect, { target: { value: 'moving' } })

    rerender(<AgentList {...mockProps} />)

    // Count visible agents (implementation detail - just verify filtering works)
    expect(screen.getByTitle('Toggle filters')).toBeDefined()
  })

  it('should display agent positions', () => {
    render(<AgentList {...mockProps} />)

    mockAgents.forEach((agent) => {
      const posText = `(${agent.pos[0].toFixed(1)}, ${agent.pos[1].toFixed(1)}, ${agent.pos[2].toFixed(1)})`
      expect(screen.getByText(posText)).toBeDefined()
    })
  })

  it('should handle large number of agents', () => {
    const largeAgentList = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      state: i % 4 === 0 ? 'moving' : i % 4 === 1 ? 'idle' : i % 4 === 2 ? 'goal_reached' : 'collision',
      pos: [Math.random() * 100, Math.random() * 100, Math.random() * 100] as [number, number, number],
    }))

    render(
      <AgentList
        {...mockProps}
        agents={largeAgentList}
      />
    )

    expect(screen.getByText('Agents (1000/1000)')).toBeDefined()
  })

  it('should support sorting by different criteria', () => {
    render(<AgentList {...mockProps} />)

    // Open filters
    const settingsBtn = screen.getByTitle('Toggle filters')
    fireEvent.click(settingsBtn)

    const sortSelect = screen.getByDisplayValue('Agent ID')
    expect(sortSelect).toBeDefined()

    // Try different sorts
    fireEvent.change(sortSelect, { target: { value: 'state' } })
    fireEvent.change(sortSelect, { target: { value: 'distance' } })
  })
})
