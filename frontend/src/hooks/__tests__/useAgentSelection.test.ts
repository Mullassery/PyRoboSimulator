/**
 * Tests for useAgentSelection hook
 */

import { renderHook, act } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useAgentSelection } from '../useAgentSelection'

describe('useAgentSelection', () => {
  it('should initialize with empty selection', () => {
    const { result } = renderHook(() => useAgentSelection())
    expect(result.current.selectedAgents.size).toBe(0)
  })

  it('should toggle single agent in single-select mode', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.toggleAgent(1, false)
    })

    expect(result.current.selectedAgents.has(1)).toBe(true)
    expect(result.current.selectedAgents.size).toBe(1)
  })

  it('should deselect agent in single-select mode', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.toggleAgent(1, false)
    })

    expect(result.current.selectedAgents.has(1)).toBe(true)

    act(() => {
      result.current.toggleAgent(1, false)
    })

    expect(result.current.selectedAgents.has(1)).toBe(false)
  })

  it('should replace selection in single-select mode', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.toggleAgent(1, false)
    })

    expect(result.current.selectedAgents.has(1)).toBe(true)

    act(() => {
      result.current.toggleAgent(2, false)
    })

    expect(result.current.selectedAgents.has(1)).toBe(false)
    expect(result.current.selectedAgents.has(2)).toBe(true)
    expect(result.current.selectedAgents.size).toBe(1)
  })

  it('should handle multi-select', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.toggleAgent(1, true)
      result.current.toggleAgent(2, true)
      result.current.toggleAgent(3, true)
    })

    expect(result.current.selectedAgents.has(1)).toBe(true)
    expect(result.current.selectedAgents.has(2)).toBe(true)
    expect(result.current.selectedAgents.has(3)).toBe(true)
    expect(result.current.selectedAgents.size).toBe(3)
  })

  it('should deselect in multi-select mode', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.toggleAgent(1, true)
      result.current.toggleAgent(2, true)
    })

    expect(result.current.selectedAgents.size).toBe(2)

    act(() => {
      result.current.toggleAgent(1, true)
    })

    expect(result.current.selectedAgents.has(1)).toBe(false)
    expect(result.current.selectedAgents.has(2)).toBe(true)
    expect(result.current.selectedAgents.size).toBe(1)
  })

  it('should select multiple agents at once', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.selectAgents([1, 2, 3, 4, 5])
    })

    expect(result.current.selectedAgents.size).toBe(5)
    [1, 2, 3, 4, 5].forEach((id) => {
      expect(result.current.selectedAgents.has(id)).toBe(true)
    })
  })

  it('should clear selection', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.selectAgents([1, 2, 3])
    })

    expect(result.current.selectedAgents.size).toBe(3)

    act(() => {
      result.current.clearSelection()
    })

    expect(result.current.selectedAgents.size).toBe(0)
  })

  it('should select all agents', () => {
    const { result } = renderHook(() => useAgentSelection())

    const allAgents = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    act(() => {
      result.current.selectAll(allAgents)
    })

    expect(result.current.selectedAgents.size).toBe(10)
    allAgents.forEach((id) => {
      expect(result.current.selectedAgents.has(id)).toBe(true)
    })
  })

  it('should handle large selection', () => {
    const { result } = renderHook(() => useAgentSelection())

    const largeSelection = Array.from({ length: 1000 }, (_, i) => i + 1)

    act(() => {
      result.current.selectAgents(largeSelection)
    })

    expect(result.current.selectedAgents.size).toBe(1000)
  })

  it('should replace selection with selectAgents', () => {
    const { result } = renderHook(() => useAgentSelection())

    act(() => {
      result.current.selectAgents([1, 2, 3])
    })

    expect(result.current.selectedAgents.size).toBe(3)

    act(() => {
      result.current.selectAgents([4, 5])
    })

    expect(result.current.selectedAgents.size).toBe(2)
    expect(result.current.selectedAgents.has(1)).toBe(false)
    expect(result.current.selectedAgents.has(4)).toBe(true)
  })

  it('should maintain selection immutability', () => {
    const { result } = renderHook(() => useAgentSelection())

    const initialSelection = result.current.selectedAgents

    act(() => {
      result.current.toggleAgent(1, true)
    })

    expect(result.current.selectedAgents).not.toBe(initialSelection)
  })
})
