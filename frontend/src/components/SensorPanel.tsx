import React, { useState, useEffect, useRef } from 'react'
import '../styles/SensorPanel.css'

interface SensorData {
  rgb?: string
  depth?: string
  lidar?: Array<[number, number, number]>
  thermal?: string
}

interface DepthHeatmapProps {
  depthData: string
}

// Depth heatmap renderer component
function DepthHeatmap({ depthData }: DepthHeatmapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current || !depthData) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    try {
      // Decode base64 depth data
      const binaryString = atob(depthData)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }

      // Convert to float32
      const depthArray = new Float32Array(bytes.buffer)

      // Create image data for canvas
      const imageData = ctx.createImageData(512, 512)
      const data = imageData.data

      // Render depth as heatmap (red=near, blue=far)
      for (let i = 0; i < depthArray.length; i++) {
        const depth = depthArray[i] / 300  // Normalize to 0-1
        const pixelIdx = i * 4

        // Color gradient: red (near) -> yellow -> blue (far)
        if (depth < 0.5) {
          // Red to yellow
          data[pixelIdx] = 255  // R
          data[pixelIdx + 1] = Math.floor(depth * 510)  // G
          data[pixelIdx + 2] = 0  // B
        } else {
          // Yellow to blue
          data[pixelIdx] = Math.floor((1 - depth) * 510)  // R
          data[pixelIdx + 1] = Math.floor((1 - depth) * 510)  // G
          data[pixelIdx + 2] = Math.floor((depth - 0.5) * 510)  // B
        }
        data[pixelIdx + 3] = 255  // Alpha
      }

      ctx.putImageData(imageData, 0, 0)
    } catch (error) {
      console.error('Error rendering depth heatmap:', error)
    }
  }, [depthData])

  return <canvas ref={canvasRef} className="depth-canvas" width={512} height={512} />
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
            <div className="sensor-controls">
              <label>
                Depth Range:
                <input type="range" min="0" max="300" defaultValue="300" />
                <span>0-300m</span>
              </label>
            </div>
            <div className="sensor-feed">
              {sensorData?.depth ? (
                <DepthHeatmap depthData={sensorData.depth} />
              ) : (
                <p>Depth sensor data not available</p>
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
