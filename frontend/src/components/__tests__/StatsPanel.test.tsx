/**
 * Tests for StatsPanel component
 */

import { describe, it, expect } from 'vitest'
import React from 'react'
import { render, screen } from '@testing-library/react'
import StatsPanel, { StatisticsData } from '../StatsPanel'

describe('StatsPanel', () => {
  const mockStats: StatisticsData = {
    timestamp_ms: 1000,
    active_agents: 50,
    total_agents: 100,
    agent_state_distribution: {
      moving: 25,
      idle: 15,
      goal_reached: 8,
      collision: 2,
      other: 0,
    },
    event_rates: {
      collisions_per_sec: 0.5,
      goals_reached_per_sec: 1.2,
      state_changes_per_sec: 2.3,
    },
    uptime_seconds: 123.45,
    fps: 60.0,
  }

  it('should render when enabled and stats provided', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    expect(screen.getByText('Simulation Statistics')).toBeDefined()
    expect(screen.getByText('Active Agents')).toBeDefined()
  })

  it('should not render when disabled', () => {
    const { container } = render(<StatsPanel stats={mockStats} enabled={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('should not render when stats is null', () => {
    const { container } = render(<StatsPanel stats={null} enabled={true} />)
    expect(container.firstChild).toBeNull()
  })

  it('should display active agent count', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    expect(screen.getByText('50')).toBeDefined()
  })

  it('should format uptime correctly', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    // 123.45 seconds = 00:02:03
    expect(screen.getByText(/00:02:03/)).toBeDefined()
  })

  it('should display FPS', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    expect(screen.getByText(/60.0/)).toBeDefined()
  })

  it('should display agent state distribution', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    expect(screen.getByText('Moving')).toBeDefined()
    expect(screen.getByText('Idle')).toBeDefined()
    expect(screen.getByText('Goal Reached')).toBeDefined()
    expect(screen.getByText('Collision')).toBeDefined()
  })

  it('should display event rates', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)
    expect(screen.getByText('Collisions/sec')).toBeDefined()
    expect(screen.getByText('Goals/sec')).toBeDefined()
    expect(screen.getByText('State Changes/sec')).toBeDefined()
  })

  it('should handle zero agents gracefully', () => {
    const zeroStats: StatisticsData = {
      ...mockStats,
      active_agents: 0,
      agent_state_distribution: {
        moving: 0,
        idle: 0,
        goal_reached: 0,
        collision: 0,
        other: 0,
      },
    }

    render(<StatsPanel stats={zeroStats} enabled={true} />)
    expect(screen.getByText('0')).toBeDefined()
  })

  it('should handle high FPS correctly', () => {
    const highFpsStats: StatisticsData = {
      ...mockStats,
      fps: 144.0,
    }

    render(<StatsPanel stats={highFpsStats} enabled={true} />)
    const fpsElements = screen.getAllByText(/144/)
    expect(fpsElements.length).toBeGreaterThan(0)
  })

  it('should handle low FPS correctly', () => {
    const lowFpsStats: StatisticsData = {
      ...mockStats,
      fps: 15.0,
    }

    render(<StatsPanel stats={lowFpsStats} enabled={true} />)
    const fpsElements = screen.getAllByText(/15/)
    expect(fpsElements.length).toBeGreaterThan(0)
  })

  it('should display all non-zero state distributions', () => {
    render(<StatsPanel stats={mockStats} enabled={true} />)

    // Check that all states are displayed
    const distributionTitle = screen.getByText('Agent State Distribution')
    expect(distributionTitle).toBeDefined()
  })

  it('should handle very long uptimes', () => {
    const longUptimeStats: StatisticsData = {
      ...mockStats,
      uptime_seconds: 3661.5, // 1 hour, 1 minute, 1.5 seconds
    }

    render(<StatsPanel stats={longUptimeStats} enabled={true} />)
    expect(screen.getByText(/01:01:01/)).toBeDefined()
  })

  it('should handle collision-heavy scenario', () => {
    const collisionStats: StatisticsData = {
      ...mockStats,
      agent_state_distribution: {
        moving: 5,
        idle: 5,
        goal_reached: 10,
        collision: 30,
        other: 0,
      },
      event_rates: {
        collisions_per_sec: 5.0,
        goals_reached_per_sec: 0.1,
        state_changes_per_sec: 1.0,
      },
    }

    render(<StatsPanel stats={collisionStats} enabled={true} />)
    expect(screen.getByText(/5.0/)).toBeDefined() // Collisions/sec
  })

  it('should handle decimal values in event rates', () => {
    const decimalStats: StatisticsData = {
      ...mockStats,
      event_rates: {
        collisions_per_sec: 0.123,
        goals_reached_per_sec: 0.456,
        state_changes_per_sec: 0.789,
      },
    }

    render(<StatsPanel stats={decimalStats} enabled={true} />)
    const eventRatesSection = screen.getByText('Event Rates')
    expect(eventRatesSection).toBeDefined()
  })
})
