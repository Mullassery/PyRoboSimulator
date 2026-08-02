/**
 * Camera View Preset Manager
 * Handles saving, loading, and managing camera view presets using localStorage
 */

export interface CameraPreset {
  name: string
  position: [number, number, number]
  target: [number, number, number]
  transitionDuration?: number
}

export interface PresetStorage {
  [key: string]: CameraPreset
}

const STORAGE_KEY = 'pyrobosim_camera_presets'

// Default presets
const DEFAULT_PRESETS: PresetStorage = {
  top: {
    name: 'Top View',
    position: [0, 300, 0.1],
    target: [0, 0, 0],
    transitionDuration: 1000,
  },
  front: {
    name: 'Front View',
    position: [0, 100, 300],
    target: [0, 0, 0],
    transitionDuration: 1000,
  },
  side: {
    name: 'Side View',
    position: [300, 100, 0],
    target: [0, 0, 0],
    transitionDuration: 1000,
  },
  isometric: {
    name: 'Isometric View',
    position: [200, 200, 200],
    target: [0, 0, 0],
    transitionDuration: 1000,
  },
  aerial: {
    name: 'Aerial View',
    position: [150, 250, 150],
    target: [0, 0, 0],
    transitionDuration: 1000,
  },
}

export class PresetManager {
  /**
   * Load all presets from localStorage
   */
  static loadPresets(): PresetStorage {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load presets from localStorage:', error)
    }
    return { ...DEFAULT_PRESETS }
  }

  /**
   * Save presets to localStorage
   */
  static savePresets(presets: PresetStorage): void {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(presets))
    } catch (error) {
      console.error('Failed to save presets to localStorage:', error)
    }
  }

  /**
   * Save a new preset or update existing one
   */
  static savePreset(name: string, preset: CameraPreset): void {
    const presets = this.loadPresets()
    presets[name] = preset
    this.savePresets(presets)
  }

  /**
   * Delete a preset
   */
  static deletePreset(name: string): void {
    const presets = this.loadPresets()
    delete presets[name]
    this.savePresets(presets)
  }

  /**
   * Get a specific preset
   */
  static getPreset(name: string): CameraPreset | null {
    const presets = this.loadPresets()
    return presets[name] || null
  }

  /**
   * Get all presets
   */
  static getAllPresets(): PresetStorage {
    return this.loadPresets()
  }

  /**
   * Reset to default presets
   */
  static resetToDefaults(): void {
    this.savePresets({ ...DEFAULT_PRESETS })
  }

  /**
   * Export presets as JSON string
   */
  static exportPresetsAsJSON(): string {
    const presets = this.loadPresets()
    return JSON.stringify(presets, null, 2)
  }

  /**
   * Import presets from JSON string
   */
  static importPresetsFromJSON(jsonString: string): boolean {
    try {
      const imported = JSON.parse(jsonString) as PresetStorage
      this.savePresets(imported)
      return true
    } catch (error) {
      console.error('Failed to import presets:', error)
      return false
    }
  }
}
