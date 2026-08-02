import React from 'react'
import { PresetStorage } from '../services/presetManager'
import PresetButtons from './PresetButtons'
import '../styles/Controls.css'

interface VisibilityLayers {
  agents: boolean
  obstacles: boolean
  trajectories: boolean
  grid: boolean
  bounds: boolean
}

interface ControlsProps {
  playing: boolean
  speed: number
  cameraMode: 'free' | 'topdown' | 'follow'
  visibleLayers: VisibilityLayers
  presets?: PresetStorage
  onPlayPause: () => void
  onSpeedChange: (speed: number) => void
  onCameraChange: (mode: 'free' | 'topdown' | 'follow') => void
  onLayerToggle: (layer: keyof VisibilityLayers, visible: boolean) => void
  onApplyPreset?: (presetName: string) => void
  onSavePreset?: (name: string) => boolean
  onDeletePreset?: (name: string) => void
  onExportPresets?: () => string
  onImportPresets?: (json: string) => boolean
  onResetToDefaults?: () => void
}

export default function Controls({
  playing,
  speed,
  cameraMode,
  visibleLayers,
  presets,
  onPlayPause,
  onSpeedChange,
  onCameraChange,
  onLayerToggle,
  onApplyPreset,
  onSavePreset,
  onDeletePreset,
  onExportPresets,
  onImportPresets,
  onResetToDefaults,
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
        <label>Layers</label>
        <div className="settings">
          <label>
            <input
              type="checkbox"
              checked={visibleLayers.agents}
              onChange={(e) => onLayerToggle('agents', e.target.checked)}
            />
            Agents
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleLayers.obstacles}
              onChange={(e) => onLayerToggle('obstacles', e.target.checked)}
            />
            Obstacles
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleLayers.trajectories}
              onChange={(e) => onLayerToggle('trajectories', e.target.checked)}
            />
            Trajectories
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleLayers.grid}
              onChange={(e) => onLayerToggle('grid', e.target.checked)}
            />
            Grid
          </label>
          <label>
            <input
              type="checkbox"
              checked={visibleLayers.bounds}
              onChange={(e) => onLayerToggle('bounds', e.target.checked)}
            />
            World Bounds
          </label>
        </div>
      </div>

      {presets && onApplyPreset && (
        <PresetButtons
          presets={presets}
          onApplyPreset={onApplyPreset}
          onSavePreset={onSavePreset || (() => false)}
          onDeletePreset={onDeletePreset || (() => {})}
          onExportPresets={onExportPresets || (() => '')}
          onImportPresets={onImportPresets || (() => false)}
          onResetToDefaults={onResetToDefaults || (() => {})}
        />
      )}
    </div>
  )
}
