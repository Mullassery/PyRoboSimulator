import React from 'react'
import '../styles/SensorPanel.css'

interface SensorPanelProps {
  agentId: number
}

export default function SensorPanel({ agentId }: SensorPanelProps) {
  return (
    <div className="sensor-panel">
      <h3>Agent {agentId} Sensors</h3>
      <div className="sensor-tabs">
        <div className="sensor-tab">
          <h4>RGB Camera</h4>
          <div className="sensor-feed">
            <p>RGB feed would display here</p>
          </div>
        </div>

        <div className="sensor-tab">
          <h4>Depth Sensor</h4>
          <div className="sensor-feed">
            <p>Depth heatmap would display here</p>
          </div>
        </div>

        <div className="sensor-tab">
          <h4>Lidar</h4>
          <div className="sensor-feed">
            <p>Point cloud would display here</p>
          </div>
        </div>

        <div className="sensor-tab">
          <h4>Thermal</h4>
          <div className="sensor-feed">
            <p>Thermal false-color would display here</p>
          </div>
        </div>
      </div>
    </div>
  )
}
