/**
 * Camera View Preset Buttons Component
 * Provides quick access to saved camera view presets
 */

import React, { useState } from 'react'
import { PresetStorage } from '../services/presetManager'
import '../styles/PresetButtons.css'

interface PresetButtonsProps {
  presets: PresetStorage
  onApplyPreset: (presetName: string) => void
  onSavePreset: (name: string) => boolean
  onDeletePreset: (name: string) => void
  onExportPresets: () => string
  onImportPresets: (json: string) => boolean
  onResetToDefaults: () => void
}

export default function PresetButtons({
  presets,
  onApplyPreset,
  onSavePreset,
  onDeletePreset,
  onExportPresets,
  onImportPresets,
  onResetToDefaults,
}: PresetButtonsProps) {
  const [showMenu, setShowMenu] = useState(false)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [importJson, setImportJson] = useState('')

  const handleSavePreset = () => {
    if (saveName.trim()) {
      if (onSavePreset(saveName)) {
        setSaveName('')
        setShowSaveDialog(false)
      }
    }
  }

  const handleImportPresets = () => {
    if (importJson.trim()) {
      if (onImportPresets(importJson)) {
        setImportJson('')
        setShowImportDialog(false)
      } else {
        alert('Failed to import presets. Check JSON format.')
      }
    }
  }

  const handleExportPresets = () => {
    const json = onExportPresets()
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'camera-presets.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="preset-buttons">
      {/* Quick preset buttons */}
      <div className="quick-presets">
        {Object.entries(presets).slice(0, 5).map(([key, preset]) => (
          <button
            key={key}
            className="btn preset-btn"
            onClick={() => onApplyPreset(key)}
            title={`Apply ${preset.name}`}
          >
            {preset.name}
          </button>
        ))}
      </div>

      {/* More options menu */}
      <div className="preset-menu">
        <button
          className="btn menu-btn"
          onClick={() => setShowMenu(!showMenu)}
          title="More preset options"
        >
          ⋮
        </button>

        {showMenu && (
          <div className="dropdown-menu">
            <button
              className="menu-item"
              onClick={() => {
                setShowSaveDialog(true)
                setShowMenu(false)
              }}
            >
              Save Current View
            </button>
            <button
              className="menu-item"
              onClick={() => {
                setShowImportDialog(true)
                setShowMenu(false)
              }}
            >
              Import Presets
            </button>
            <button
              className="menu-item"
              onClick={() => {
                handleExportPresets()
                setShowMenu(false)
              }}
            >
              Export Presets
            </button>
            <button
              className="menu-item danger"
              onClick={() => {
                if (window.confirm('Reset to default presets?')) {
                  onResetToDefaults()
                  setShowMenu(false)
                }
              }}
            >
              Reset to Defaults
            </button>
          </div>
        )}
      </div>

      {/* Save preset dialog */}
      {showSaveDialog && (
        <div className="modal-overlay" onClick={() => setShowSaveDialog(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Save Current View as Preset</h3>
            <input
              type="text"
              placeholder="Enter preset name"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSavePreset()}
              autoFocus
            />
            <div className="modal-buttons">
              <button className="btn" onClick={handleSavePreset}>
                Save
              </button>
              <button
                className="btn secondary"
                onClick={() => {
                  setSaveName('')
                  setShowSaveDialog(false)
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import presets dialog */}
      {showImportDialog && (
        <div className="modal-overlay" onClick={() => setShowImportDialog(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Import Presets</h3>
            <textarea
              placeholder="Paste JSON here"
              value={importJson}
              onChange={(e) => setImportJson(e.target.value)}
              rows={10}
            />
            <div className="modal-buttons">
              <button className="btn" onClick={handleImportPresets}>
                Import
              </button>
              <button
                className="btn secondary"
                onClick={() => {
                  setImportJson('')
                  setShowImportDialog(false)
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
