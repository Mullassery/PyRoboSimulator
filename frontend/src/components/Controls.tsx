import React from 'react'
import '../styles/Controls.css'

interface ControlsProps {
  playing: boolean
  speed: number
  cameraMode: 'free' | 'topdown' | 'follow'
  onPlayPause: () => void
  onSpeedChange: (speed: number) => void
  onCameraChange: (mode: 'free' | 'topdown' | 'follow') => void
}

export default function Controls({
  playing,
  speed,
  cameraMode,
  onPlayPause,
  onSpeedChange,
  onCameraChange,
}: ControlsProps) {
  return (
    <div className="controls">
      <div className="control-section">
        <label>Playback</label>
        <div className="button-group">
          <button
            className={`btn ${playing ? 'active' : ''}`}
            onClick={onPlayPause}
          >
            {playing ? 'Pause' : 'Play'}
          </button>
        </div>
      </div>

      <div className="control-section">
        <label>Speed</label>
        <div className="speed-controls">
          <button
            className="btn"
            onClick={() => onSpeedChange(0.5)}
            disabled={speed === 0.5}
          >
            0.5x
          </button>
          <button
            className="btn"
            onClick={() => onSpeedChange(1.0)}
            disabled={speed === 1.0}
          >
            1x
          </button>
          <button
            className="btn"
            onClick={() => onSpeedChange(2.0)}
            disabled={speed === 2.0}
          >
            2x
          </button>
          <button
            className="btn"
            onClick={() => onSpeedChange(4.0)}
            disabled={speed === 4.0}
          >
            4x
          </button>
        </div>
      </div>

      <div className="control-section">
        <label>Camera</label>
        <div className="button-group">
          <button
            className={`btn ${cameraMode === 'free' ? 'active' : ''}`}
            onClick={() => onCameraChange('free')}
          >
            Free
          </button>
          <button
            className={`btn ${cameraMode === 'topdown' ? 'active' : ''}`}
            onClick={() => onCameraChange('topdown')}
          >
            Top-Down
          </button>
          <button
            className={`btn ${cameraMode === 'follow' ? 'active' : ''}`}
            onClick={() => onCameraChange('follow')}
          >
            Follow
          </button>
        </div>
      </div>

      <div className="control-section">
        <label>Settings</label>
        <div className="settings">
          <label>
            <input type="checkbox" />
            Show Sensor Data
          </label>
          <label>
            <input type="checkbox" />
            Show Lidar
          </label>
          <label>
            <input type="checkbox" />
            Show Collisions
          </label>
        </div>
      </div>
    </div>
  )
}
