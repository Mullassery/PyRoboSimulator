/**
 * React hook for managing camera view presets
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import * as THREE from 'three'
import { PresetManager, CameraPreset, PresetStorage } from '../services/presetManager'

interface UseViewPresetsOptions {
  camera: THREE.PerspectiveCamera | THREE.OrthographicCamera | null
  cameraTarget: THREE.Vector3
}

interface AnimationState {
  isAnimating: boolean
  startTime: number
  duration: number
  startPos: THREE.Vector3
  startTarget: THREE.Vector3
  endPos: THREE.Vector3
  endTarget: THREE.Vector3
}

export function useViewPresets({ camera, cameraTarget }: UseViewPresetsOptions) {
  const [presets, setPresets] = useState<PresetStorage>(PresetManager.loadPresets())
  const animationRef = useRef<AnimationState | null>(null)
  const rafIdRef = useRef<number | null>(null)

  // Load presets on mount
  useEffect(() => {
    setPresets(PresetManager.loadPresets())
  }, [])

  // Animation loop
  useEffect(() => {
    if (!camera) return

    const animate = () => {
      if (animationRef.current && animationRef.current.isAnimating) {
        const now = Date.now()
        const elapsed = now - animationRef.current.startTime
        const progress = Math.min(elapsed / animationRef.current.duration, 1)

        // Easing function (ease-in-out)
        const easeProgress = progress < 0.5
          ? 2 * progress * progress
          : -1 + (4 - 2 * progress) * progress

        // Interpolate position
        const newPos = new THREE.Vector3(
          animationRef.current.startPos.x + (animationRef.current.endPos.x - animationRef.current.startPos.x) * easeProgress,
          animationRef.current.startPos.y + (animationRef.current.endPos.y - animationRef.current.startPos.y) * easeProgress,
          animationRef.current.startPos.z + (animationRef.current.endPos.z - animationRef.current.startPos.z) * easeProgress,
        )

        // Interpolate target
        const newTarget = new THREE.Vector3(
          animationRef.current.startTarget.x + (animationRef.current.endTarget.x - animationRef.current.startTarget.x) * easeProgress,
          animationRef.current.startTarget.y + (animationRef.current.endTarget.y - animationRef.current.startTarget.y) * easeProgress,
          animationRef.current.startTarget.z + (animationRef.current.endTarget.z - animationRef.current.startTarget.z) * easeProgress,
        )

        camera.position.copy(newPos)
        cameraTarget.copy(newTarget)

        if (camera instanceof THREE.PerspectiveCamera || camera instanceof THREE.OrthographicCamera) {
          camera.lookAt(newTarget)
        }

        if (progress >= 1) {
          animationRef.current.isAnimating = false
        } else {
          rafIdRef.current = requestAnimationFrame(animate)
        }
      }
    }

    if (animationRef.current?.isAnimating) {
      rafIdRef.current = requestAnimationFrame(animate)
    }

    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current)
    }
  }, [camera, cameraTarget])

  const applyPreset = useCallback((presetName: string) => {
    if (!camera) return false

    const preset = PresetManager.getPreset(presetName)
    if (!preset) {
      console.error(`Preset "${presetName}" not found`)
      return false
    }

    const duration = preset.transitionDuration || 1000

    // Start animation
    animationRef.current = {
      isAnimating: true,
      startTime: Date.now(),
      duration,
      startPos: camera.position.clone(),
      startTarget: cameraTarget.clone(),
      endPos: new THREE.Vector3(...preset.position),
      endTarget: new THREE.Vector3(...preset.target),
    }

    return true
  }, [camera, cameraTarget])

  const saveCurrentViewAsPreset = useCallback((name: string) => {
    if (!camera) return false

    const preset: CameraPreset = {
      name,
      position: [camera.position.x, camera.position.y, camera.position.z],
      target: [cameraTarget.x, cameraTarget.y, cameraTarget.z],
    }

    PresetManager.savePreset(name, preset)
    setPresets(PresetManager.loadPresets())
    return true
  }, [camera, cameraTarget])

  const deletePreset = useCallback((name: string) => {
    PresetManager.deletePreset(name)
    setPresets(PresetManager.loadPresets())
  }, [])

  const exportPresets = useCallback(() => {
    return PresetManager.exportPresetsAsJSON()
  }, [])

  const importPresets = useCallback((jsonString: string) => {
    const success = PresetManager.importPresetsFromJSON(jsonString)
    if (success) {
      setPresets(PresetManager.loadPresets())
    }
    return success
  }, [])

  const resetToDefaults = useCallback(() => {
    PresetManager.resetToDefaults()
    setPresets(PresetManager.loadPresets())
  }, [])

  return {
    presets,
    applyPreset,
    saveCurrentViewAsPreset,
    deletePreset,
    exportPresets,
    importPresets,
    resetToDefaults,
  }
}
