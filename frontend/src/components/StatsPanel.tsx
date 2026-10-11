/**
 * Real-Time Statistics Panel Component
 * Displays live simulation statistics with mini charts
 */

import React from 'react'
import '../styles/StatsPanel.css'

interface AgentStateDistribution {
  moving: number
  idle: number
  goal_reached: number
  collision: number
  other: number
}

interface EventRates {
  collisions_per_sec: number
  goals_reached_per_sec: number
  state_changes_per_sec: number
}

export interface StatisticsData {
  timestamp_ms: number
  active_agents: number
  total_agents: number
  agent_state_distribution: AgentStateDistribution
  event_rates: EventRates
  uptime_seconds: number
  fps: number
}

interface StatsPanelProps {
  stats: StatisticsData | null
  enabled?: boolean
}

interface MiniChartProps {
  title: string
  value: number
  unit?: string
  max?: number
  color?: string
  decimals?: number
}

function MiniChart({ title, value, unit = '', max = 100, color = '#3a7fbd', decimals = 1 }: MiniChartProps) {
  const percentage = Math.min((value / max) * 100, 100)

  return (
    <div className="mini-chart">
      <div className="chart-header">
        <span className="chart-title">{title}</span>
        <span className="chart-value">
          {value.toFixed(decimals)}{unit}
        </span>
      </div>
      <div className="chart-bar-container">
        <div
          className="chart-bar"
          style={{
            width: `${percentage}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  )
}

interface StatBoxProps {
  label: string
  value: number | string
  unit?: string
  color?: string
  decimals?: number
}

function StatBox({ label, value, unit = '', color = '#e0e0e0', decimals = 1 }: StatBoxProps) {
  return (
    <div className="stat-box">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>
        {typeof value === 'number' ? value.toFixed(decimals) : value}
        {unit && <span className="stat-unit">{unit}</span>}
      </div>
    </div>
  )
}

export default function StatsPanel({ stats, enabled = true }: StatsPanelProps) {
  if (!enabled || !stats) {
    return null
  }

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const totalAgents = stats.agent_state_distribution.moving
    + stats.agent_state_distribution.idle
    + stats.agent_state_distribution.goal_reached
    + stats.agent_state_distribution.collision
    + stats.agent_state_distribution.other

  const cpuHealthColor = stats.fps >= 50 ? '#7abf1d' : stats.fps >= 30 ? '#ffa500' : '#ff6b6b'

  return (
    <div className="stats-panel">
      <div className="stats-header">
        <h3>Simulation Statistics</h3>
      </div>

      {/* Core Metrics */}
      <div className="stats-section">
        <div className="stats-grid">
          <StatBox
            label="Active Agents"
            value={stats.active_agents}
            unit=""
            color="#3a7fbd"
            decimals={0}
          />
          <StatBox
            label="FPS"
            value={stats.fps}
            unit=""
            color={cpuHealthColor}
          />
          <StatBox
            label="Uptime"
            value={formatUptime(stats.uptime_seconds)}
            color="#e0e0e0"
          />
        </div>
      </div>

      {/* Agent State Distribution */}
      <div className="stats-section">
        <div className="section-title">Agent State Distribution</div>
        <div className="state-distribution">
          {stats.agent_state_distribution.moving > 0 && (
            <MiniChart
              title="Moving"
              value={stats.agent_state_distribution.moving}
              max={totalAgents || 100}
              color="#3a7fbd"
              decimals={0}
            />
          )}
          {stats.agent_state_distribution.idle > 0 && (
            <MiniChart
              title="Idle"
              value={stats.agent_state_distribution.idle}
              max={totalAgents || 100}
              color="#666"
              decimals={0}
            />
          )}
          {stats.agent_state_distribution.goal_reached > 0 && (
            <MiniChart
              title="Goal Reached"
              value={stats.agent_state_distribution.goal_reached}
              max={totalAgents || 100}
              color="#7abf1d"
              decimals={0}
            />
          )}
          {stats.agent_state_distribution.collision > 0 && (
            <MiniChart
              title="Collision"
              value={stats.agent_state_distribution.collision}
              max={totalAgents || 100}
              color="#ff6b6b"
              decimals={0}
            />
          )}
          {stats.agent_state_distribution.other > 0 && (
            <MiniChart
              title="Other"
              value={stats.agent_state_distribution.other}
              max={totalAgents || 100}
              color="#ffa500"
              decimals={0}
            />
          )}
        </div>
      </div>

      {/* Event Rates */}
      <div className="stats-section">
        <div className="section-title">Event Rates</div>
        <div className="event-rates">
          <StatBox
            label="Collisions/sec"
            value={stats.event_rates.collisions_per_sec}
            color="#ff6b6b"
          />
          <StatBox
            label="Goals/sec"
            value={stats.event_rates.goals_reached_per_sec}
            color="#7abf1d"
          />
          <StatBox
            label="State Changes/sec"
            value={stats.event_rates.state_changes_per_sec}
            color="#5a9fdd"
          />
        </div>
      </div>

      {/* State Pie Chart (as CSS pie) */}
      {totalAgents > 0 && (
        <div className="stats-section">
          <div className="section-title">State Distribution Pie</div>
          <div className="pie-chart">
            {stats.agent_state_distribution.moving > 0 && (
              <div
                className="pie-slice"
                style={{
                  '--percentage': `${(stats.agent_state_distribution.moving / totalAgents) * 100}%`,
                  '--color': '#3a7fbd',
                } as React.CSSProperties}
                title={`Moving: ${stats.agent_state_distribution.moving}`}
              />
            )}
            {stats.agent_state_distribution.idle > 0 && (
              <div
                className="pie-slice"
                style={{
                  '--percentage': `${(stats.agent_state_distribution.idle / totalAgents) * 100}%`,
                  '--color': '#666',
                } as React.CSSProperties}
                title={`Idle: ${stats.agent_state_distribution.idle}`}
              />
            )}
            {stats.agent_state_distribution.goal_reached > 0 && (
              <div
                className="pie-slice"
                style={{
                  '--percentage': `${(stats.agent_state_distribution.goal_reached / totalAgents) * 100}%`,
                  '--color': '#7abf1d',
                } as React.CSSProperties}
                title={`Goal Reached: ${stats.agent_state_distribution.goal_reached}`}
              />
            )}
            {stats.agent_state_distribution.collision > 0 && (
              <div
                className="pie-slice"
                style={{
                  '--percentage': `${(stats.agent_state_distribution.collision / totalAgents) * 100}%`,
                  '--color': '#ff6b6b',
                } as React.CSSProperties}
                title={`Collision: ${stats.agent_state_distribution.collision}`}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
