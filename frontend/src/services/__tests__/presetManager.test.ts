/**
 * Tests for PresetManager
 */

import { PresetManager, CameraPreset } from '../presetManager'

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('PresetManager', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('loadPresets', () => {
    test('should load default presets when localStorage is empty', () => {
      const presets = PresetManager.loadPresets()
      expect(presets).toHaveProperty('top')
      expect(presets).toHaveProperty('front')
      expect(presets).toHaveProperty('side')
      expect(presets).toHaveProperty('isometric')
      expect(presets).toHaveProperty('aerial')
    })

    test('should load presets from localStorage if available', () => {
      const customPreset: CameraPreset = {
        name: 'Custom',
        position: [100, 100, 100] as [number, number, number],
        target: [0, 0, 0] as [number, number, number],
      }
      localStorage.setItem('pyrobosim_camera_presets', JSON.stringify({ custom: customPreset }))

      const presets = PresetManager.loadPresets()
      expect(presets.custom).toEqual(customPreset)
    })

    test('should handle invalid JSON gracefully', () => {
      localStorage.setItem('pyrobosim_camera_presets', 'invalid json')
      const presets = PresetManager.loadPresets()
      expect(presets).toHaveProperty('top')
    })
  })

  describe('savePresets', () => {
    test('should save presets to localStorage', () => {
      const presets: PresetStorage = {
        test: {
          name: 'Test',
          position: [100, 100, 100] as [number, number, number],
          target: [0, 0, 0] as [number, number, number],
        },
      }
      PresetManager.savePresets(presets)

      const retrieved = JSON.parse(localStorage.getItem('pyrobosim_camera_presets') || '{}')
      expect(retrieved.test).toEqual(presets.test)
    })
  })

  describe('savePreset', () => {
    test('should save a new preset', () => {
      const preset: CameraPreset = {
        name: 'New Preset',
        position: [50, 50, 50],
        target: [10, 10, 10],
      }
      PresetManager.savePreset('new', preset)

      const loaded = PresetManager.getPreset('new')
      expect(loaded).toEqual(preset)
    })

    test('should update existing preset', () => {
      const preset1: CameraPreset = {
        name: 'Preset 1',
        position: [100, 100, 100],
        target: [0, 0, 0],
      }
      PresetManager.savePreset('test', preset1)

      const preset2: CameraPreset = {
        name: 'Preset 2',
        position: [200, 200, 200],
        target: [0, 0, 0],
      }
      PresetManager.savePreset('test', preset2)

      const loaded = PresetManager.getPreset('test')
      expect(loaded).toEqual(preset2)
    })
  })

  describe('getPreset', () => {
    test('should return null for non-existent preset', () => {
      const preset = PresetManager.getPreset('nonexistent')
      expect(preset).toBeNull()
    })

    test('should return existing preset', () => {
      const original: CameraPreset = {
        name: 'Test',
        position: [100, 100, 100],
        target: [0, 0, 0],
      }
      PresetManager.savePreset('test', original)

      const retrieved = PresetManager.getPreset('test')
      expect(retrieved).toEqual(original)
    })
  })

  describe('deletePreset', () => {
    test('should delete a preset', () => {
      const preset: CameraPreset = {
        name: 'To Delete',
        position: [100, 100, 100],
        target: [0, 0, 0],
      }
      PresetManager.savePreset('todelete', preset)
      expect(PresetManager.getPreset('todelete')).not.toBeNull()

      PresetManager.deletePreset('todelete')
      expect(PresetManager.getPreset('todelete')).toBeNull()
    })
  })

  describe('resetToDefaults', () => {
    test('should reset to default presets', () => {
      const custom: CameraPreset = {
        name: 'Custom',
        position: [999, 999, 999],
        target: [0, 0, 0],
      }
      PresetManager.savePreset('custom', custom)

      PresetManager.resetToDefaults()
      const presets = PresetManager.loadPresets()

      expect(presets).toHaveProperty('top')
      expect(presets).toHaveProperty('front')
      expect(presets).not.toHaveProperty('custom')
    })
  })

  describe('exportPresetsAsJSON', () => {
    test('should export presets as valid JSON', () => {
      PresetManager.resetToDefaults()
      const json = PresetManager.exportPresetsAsJSON()
      const parsed = JSON.parse(json)

      expect(parsed).toHaveProperty('top')
      expect(parsed).toHaveProperty('front')
      expect(parsed.top.name).toBe('Top View')
    })
  })

  describe('importPresetsFromJSON', () => {
    test('should import presets from valid JSON', () => {
      const presetsToImport = {
        imported: {
          name: 'Imported',
          position: [150, 150, 150],
          target: [0, 0, 0],
        },
      }
      const json = JSON.stringify(presetsToImport)
      const success = PresetManager.importPresetsFromJSON(json)

      expect(success).toBe(true)
      expect(PresetManager.getPreset('imported')).toEqual(presetsToImport.imported)
    })

    test('should return false for invalid JSON', () => {
      const success = PresetManager.importPresetsFromJSON('invalid json')
      expect(success).toBe(false)
    })
  })

  describe('getAllPresets', () => {
    test('should return all presets', () => {
      PresetManager.resetToDefaults()
      const allPresets = PresetManager.getAllPresets()

      expect(Object.keys(allPresets).length).toBeGreaterThan(0)
      expect(allPresets).toHaveProperty('top')
      expect(allPresets).toHaveProperty('front')
    })
  })
})
