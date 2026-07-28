import React, { useState, useEffect } from 'react'
import '../styles/SensorPanel.css'

interface SensorData {
  rgb?: string
  depth?: string
  lidar?: Array<[number, number, number]>
  thermal?: string
}

interface SensorPanelProps {
  agentId: number
  sensorData?: SensorData | null
}

export default function SensorPanel({ agentId, sensorData }: SensorPanelProps) {
  const [rgbImage, setRgbImage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'rgb' | 'depth' | 'lidar' | 'thermal'>('rgb')

  useEffect(() => {
    if (sensorData?.rgb) {
      setRgbImage(`data:image/jpeg;base64,${sensorData.rgb}`)
    }
  }, [sensorData])

  return (
    <div className="sensor-panel">
      <h3>Agent {agentId} Sensors</h3>
      <div className="sensor-tabs-nav">
        <button
          className={`tab-btn ${activeTab === 'rgb' ? 'active' : ''}`}
          onClick={() => setActiveTab('rgb')}
        >
          RGB
        </button>
        <button
          className={`tab-btn ${activeTab === 'depth' ? 'active' : ''}`}
          onClick={() => setActiveTab('depth')}
        >
          Depth
        </button>
        <button
          className={`tab-btn ${activeTab === 'lidar' ? 'active' : ''}`}
          onClick={() => setActiveTab('lidar')}
        >
          Lidar
        </button>
        <button
          className={`tab-btn ${activeTab === 'thermal' ? 'active' : ''}`}
          onClick={() => setActiveTab('thermal')}
        >
          Thermal
        </button>
      </div>

      <div className="sensor-tabs">
        {activeTab === 'rgb' && (
          <div className="sensor-tab active">
            <h4>RGB Camera</h4>
            <div className="sensor-feed">
              {rgbImage ? (
                <img src={rgbImage} alt="RGB Camera Feed" className="sensor-image" />
              ) : (
                <p>No RGB data available</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'depth' && (
          <div className="sensor-tab active">
            <h4>Depth Sensor</h4>
            <div className="sensor-feed">
              {sensorData?.depth ? (
                <img
                  src={`data:image/png;base64,${sensorData.depth}`}
                  alt="Depth Sensor"
                  className="sensor-image"
                />
              ) : (
                <p>Depth sensor not yet implemented</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'lidar' && (
          <div className="sensor-tab active">
            <h4>Lidar</h4>
            <div className="sensor-feed">
              {sensorData?.lidar ? (
                <p>Lidar point cloud: {sensorData.lidar.length} points</p>
              ) : (
                <p>Lidar sensor not yet implemented</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'thermal' && (
          <div className="sensor-tab active">
            <h4>Thermal Camera</h4>
            <div className="sensor-feed">
              {sensorData?.thermal ? (
                <img
                  src={`data:image/png;base64,${sensorData.thermal}`}
                  alt="Thermal Camera"
                  className="sensor-image"
                />
              ) : (
                <p>Thermal sensor not yet implemented</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
