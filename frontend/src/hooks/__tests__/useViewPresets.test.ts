/**
 * Tests for useViewPresets hook
 */

import { renderHook, act } from '@testing-library/react'
import * as THREE from 'three'
import { useViewPresets } from '../useViewPresets'
import { PresetManager } from '../../services/presetManager'

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

describe('useViewPresets', () => {
  let camera: THREE.PerspectiveCamera
  let cameraTarget: THREE.Vector3

  beforeEach(() => {
    localStorage.clear()
    PresetManager.resetToDefaults()
    camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000)
    camera.position.set(150, 150, 150)
    cameraTarget = new THREE.Vector3(0, 0, 0)
  })

  describe('applyPreset', () => {
    test('should apply a preset to the camera', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      act(() => {
        result.current.applyPreset('top')
      })

      setTimeout(() => {
        // Animation should complete
        expect(camera.position.y).toBeCloseTo(300, 0)
      }, 1100)
    })

    test('should return false for non-existent preset', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      act(() => {
        const success = result.current.applyPreset('nonexistent')
        expect(success).toBe(false)
      })
    })
  })

  describe('saveCurrentViewAsPreset', () => {
    test('should save current camera position as preset', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      camera.position.set(100, 200, 300)
      cameraTarget.set(10, 20, 30)

      act(() => {
        const success = result.current.saveCurrentViewAsPreset('mysave')
        expect(success).toBe(true)
      })

      const saved = PresetManager.getPreset('mysave')
      expect(saved?.position).toEqual([100, 200, 300])
      expect(saved?.target).toEqual([10, 20, 30])
    })

    test('should return false if camera is null', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera: null, cameraTarget })
      )

      act(() => {
        const success = result.current.saveCurrentViewAsPreset('test')
        expect(success).toBe(false)
      })
    })
  })

  describe('deletePreset', () => {
    test('should delete a preset', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      PresetManager.savePreset('todelete', {
        name: 'To Delete',
        position: [100, 100, 100],
        target: [0, 0, 0],
      })

      expect(PresetManager.getPreset('todelete')).not.toBeNull()

      act(() => {
        result.current.deletePreset('todelete')
      })

      expect(PresetManager.getPreset('todelete')).toBeNull()
    })
  })

  describe('exportPresets', () => {
    test('should export presets as JSON', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      let json: string
      act(() => {
        json = result.current.exportPresets()
      })

      const parsed = JSON.parse(json!)
      expect(parsed).toHaveProperty('top')
      expect(parsed).toHaveProperty('front')
    })
  })

  describe('importPresets', () => {
    test('should import presets from JSON', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      const newPresets = {
        custom: {
          name: 'Custom',
          position: [250, 250, 250],
          target: [0, 0, 0],
        },
      }

      let success: boolean
      act(() => {
        success = result.current.importPresets(JSON.stringify(newPresets))
      })

      expect(success!).toBe(true)
      expect(PresetManager.getPreset('custom')).toEqual(newPresets.custom)
    })

    test('should return false for invalid JSON', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      let success: boolean
      act(() => {
        success = result.current.importPresets('invalid json')
      })

      expect(success!).toBe(false)
    })
  })

  describe('resetToDefaults', () => {
    test('should reset presets to defaults', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      PresetManager.savePreset('custom', {
        name: 'Custom',
        position: [999, 999, 999],
        target: [0, 0, 0],
      })

      act(() => {
        result.current.resetToDefaults()
      })

      expect(result.current.presets).toHaveProperty('top')
      expect(result.current.presets).not.toHaveProperty('custom')
    })
  })

  describe('presets state', () => {
    test('should load presets on mount', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      expect(result.current.presets).toHaveProperty('top')
      expect(result.current.presets).toHaveProperty('front')
    })

    test('should update presets after save', () => {
      const { result } = renderHook(() =>
        useViewPresets({ camera, cameraTarget })
      )

      const initialCount = Object.keys(result.current.presets).length

      act(() => {
        result.current.saveCurrentViewAsPreset('newsave')
      })

      expect(Object.keys(result.current.presets).length).toBe(initialCount + 1)
    })
  })
})
