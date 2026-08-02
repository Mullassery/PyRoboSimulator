import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { useWebSocket } from './hooks/useWebSocket'
import { useViewPresets } from './hooks/useViewPresets'
import Controls from './components/Controls'
import SensorPanel from './components/SensorPanel'
import EventLog from './components/EventLog'
import './App.css'

interface Agent {
  id: number
  pos: [number, number, number]
  rot: [number, number, number]
  vel: [number, number, number]
  state: string
  traj?: Array<[number, number]>
}

interface Event {
  id: number
  type: string
  agent_id: number
  pos: [number, number, number]
  data?: Record<string, any>
}

interface SensorData {
  rgb?: string
  depth?: string
  lidar?: Array<[number, number, number]>
  thermal?: string
}

interface Obstacle {
  id: number
  pos: [number, number, number]
  size: [number, number, number]
  type: string
}

interface WorldFrame {
  type: string
  frame_id: number
  timestamp_ms: number
  agents: Agent[]
  events: Event[]
  sensors?: Record<string, SensorData>
  obstacles?: Obstacle[]
}

function App() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const sceneRef = useRef<THREE.Scene | null>(null)
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null)
  const agentMeshesRef = useRef<Map<number, THREE.Mesh>>(new Map())
  const obstaclesMeshesRef = useRef<Map<number, THREE.Mesh>>(new Map())
  const trajectoryLinesRef = useRef<Map<number, THREE.LineSegments>>(new Map())
  const gridHelperRef = useRef<THREE.GridHelper | null>(null)
  const boundingBoxRef = useRef<THREE.BoxHelper | null>(null)
  const obstaclesInitializedRef = useRef(false)
  const cameraRef = useRef<THREE.PerspectiveCamera | THREE.OrthographicCamera | null>(null)
  const cameraTargetRef = useRef(new THREE.Vector3(0, 0, 0))
  const cameraControlsRef = useRef({ x: 0, y: 0, z: 0 })
  const cameraModeRef = useRef<'free' | 'topdown' | 'follow'>('free')
  const rafIdRef = useRef<number | null>(null)

  const simulationId = new URLSearchParams(window.location.search).get('id') || '1'
  const { frame, isConnected, sendCommand } = useWebSocket(simulationId)

  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(1.0)
  const [cameraMode, setCameraMode] = useState<'free' | 'topdown' | 'follow'>('free')
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<number>>(new Set())
  const [primarySelectedAgent, setPrimarySelectedAgent] = useState<number | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [visibleLayers, setVisibleLayers] = useState({
    agents: true,
    obstacles: true,
    trajectories: true,
    grid: true,
    bounds: true,
  })

  // Initialize view presets hook (will be configured after camera is created)
  const viewPresetsConfig = {
    camera: cameraRef.current,
    cameraTarget: cameraTargetRef.current,
  }
  const viewPresets = useViewPresets(viewPresetsConfig)

  // Sync cameraModeRef with cameraMode state (for updateFreeCamera closure)
  useEffect(() => {
    cameraModeRef.current = cameraMode
  }, [cameraMode])

  // Initialize Three.js scene (mount once)
  useEffect(() => {
    if (!canvasRef.current) return

    const width = canvasRef.current.clientWidth
    const height = canvasRef.current.clientHeight

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x1a1a1a)
    sceneRef.current = scene

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 10000)
    camera.position.set(150, 150, 150)
    camera.lookAt(0, 0, 0)
    cameraRef.current = camera

    // Renderer
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current, antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(window.devicePixelRatio)
    rendererRef.current = renderer

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(100, 100, 100)
    scene.add(directionalLight)

    // Grid
    const gridHelper = new THREE.GridHelper(500, 50, 0x444444, 0x222222)
    scene.add(gridHelper)
    gridHelperRef.current = gridHelper

    // World bounds
    const boundingBox = new THREE.BoxHelper(
      new THREE.Box3(
        new THREE.Vector3(-250, -250, -10),
        new THREE.Vector3(250, 250, 10)
      )
    )
    scene.add(boundingBox)
    boundingBoxRef.current = boundingBox

    // Animation loop — reads cameraRef.current every frame (not closed-over camera)
    const animate = () => {
      rafIdRef.current = requestAnimationFrame(animate)
      if (cameraRef.current) {
        renderer.render(scene, cameraRef.current)
      }
    }
    animate()

    // Handle window resize
    const handleResize = () => {
      const newWidth = canvasRef.current?.clientWidth || width
      const newHeight = canvasRef.current?.clientHeight || height
      if (cameraRef.current instanceof THREE.PerspectiveCamera) {
        cameraRef.current.aspect = newWidth / newHeight
        cameraRef.current.updateProjectionMatrix()
      } else if (cameraRef.current instanceof THREE.OrthographicCamera) {
        const scale = newWidth / newHeight
        cameraRef.current.left = -500 * scale
        cameraRef.current.right = 500 * scale
        cameraRef.current.updateProjectionMatrix()
      }
      renderer.setSize(newWidth, newHeight)
    }

    // Keyboard controls for free camera
    const keys: Record<string, boolean> = {}
    const handleKeyDown = (e: KeyboardEvent) => {
      keys[e.key.toLowerCase()] = true
    }
    const handleKeyUp = (e: KeyboardEvent) => {
      keys[e.key.toLowerCase()] = false
    }

    const updateFreeCamera = () => {
      if (!cameraRef.current || cameraModeRef.current !== 'free') return
      const speed = 2

      if (keys['w']) cameraControlsRef.current.z -= speed
      if (keys['s']) cameraControlsRef.current.z += speed
      if (keys['a']) cameraControlsRef.current.x -= speed
      if (keys['d']) cameraControlsRef.current.x += speed
      if (keys['q']) cameraControlsRef.current.y -= speed
      if (keys['e']) cameraControlsRef.current.y += speed

      const cam = cameraRef.current as THREE.PerspectiveCamera
      cam.position.x += cameraControlsRef.current.x * 0.1
      cam.position.y += cameraControlsRef.current.y * 0.1
      cam.position.z += cameraControlsRef.current.z * 0.1
      cameraControlsRef.current = { x: 0, y: 0, z: 0 }
      cam.lookAt(cameraTargetRef.current)
    }

    // Handle click-to-select (raycasting against agent meshes)
    const handleCanvasClick = (e: MouseEvent) => {
      if (!(cameraRef.current && sceneRef.current)) return

      const canvas = canvasRef.current!
      const rect = canvas.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      const y = -((e.clientY - rect.top) / rect.height) * 2 + 1

      const raycaster = new THREE.Raycaster()
      raycaster.setFromCamera(new THREE.Vector2(x, y), cameraRef.current)

      const agents = Array.from(agentMeshesRef.current.values())
      const intersects = raycaster.intersectObjects(agents)

      if (intersects.length > 0) {
        const clicked = intersects[0].object as THREE.Mesh
        const clickedAgentId = clicked.userData.agentId as number

        if (e.shiftKey || e.ctrlKey || e.metaKey) {
          // Multi-select: toggle membership
          if (selectedAgentIds.has(clickedAgentId)) {
            selectedAgentIds.delete(clickedAgentId)
          } else {
            selectedAgentIds.add(clickedAgentId)
          }
          setSelectedAgentIds(new Set(selectedAgentIds))
        } else {
          // Single select: replace or clear
          if (selectedAgentIds.size === 1 && selectedAgentIds.has(clickedAgentId)) {
            setSelectedAgentIds(new Set())
            setPrimarySelectedAgent(null)
          } else {
            setSelectedAgentIds(new Set([clickedAgentId]))
            setPrimarySelectedAgent(clickedAgentId)
          }
        }
      } else {
        // Click empty space: clear selection
        setSelectedAgentIds(new Set())
        setPrimarySelectedAgent(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)
    window.addEventListener('resize', handleResize)
    canvasRef.current.addEventListener('click', handleCanvasClick)

    const cameraUpdateInterval = setInterval(updateFreeCamera, 16)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
      window.removeEventListener('resize', handleResize)
      canvasRef.current?.removeEventListener('click', handleCanvasClick)
      clearInterval(cameraUpdateInterval)
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current)
      }
    }
  }, [])

  // Update layer visibility
  useEffect(() => {
    if (!sceneRef.current) return

    if (gridHelperRef.current) {
      gridHelperRef.current.visible = visibleLayers.grid
    }
    if (boundingBoxRef.current) {
      boundingBoxRef.current.visible = visibleLayers.bounds
    }

    agentMeshesRef.current.forEach((mesh) => {
      mesh.visible = visibleLayers.agents
    })

    obstaclesMeshesRef.current.forEach((mesh) => {
      mesh.visible = visibleLayers.obstacles
    })

    trajectoryLinesRef.current.forEach((line) => {
      line.visible = visibleLayers.trajectories
    })
  }, [visibleLayers])

  // Update camera based on mode
  useEffect(() => {
    if (!cameraRef.current || !sceneRef.current || !frame) return

    const frameData = frame as WorldFrame

    switch (cameraMode) {
      case 'topdown': {
        if (!(cameraRef.current instanceof THREE.OrthographicCamera)) {
          const ortho = new THREE.OrthographicCamera(-500, 500, -500, 500, 0.1, 10000)
          ortho.position.set(0, 500, 0)
          ortho.lookAt(0, 0, 0)
          if (cameraRef.current instanceof THREE.PerspectiveCamera) {
            sceneRef.current.remove(cameraRef.current)
          }
          sceneRef.current.add(ortho)
          cameraRef.current = ortho
        }
        break
      }

      case 'follow': {
        if (cameraRef.current instanceof THREE.PerspectiveCamera) {
          const agentToFollow =
            primarySelectedAgent !== null ? primarySelectedAgent : frameData.agents[0]?.id
          const agent = frameData.agents.find((a) => a.id === agentToFollow)

          if (agent) {
            const offset = 30
            cameraRef.current.position.set(
              agent.pos[0] + offset,
              agent.pos[1] + offset,
              agent.pos[2] + offset
            )
            cameraTargetRef.current.set(agent.pos[0], agent.pos[1], agent.pos[2])
            cameraRef.current.lookAt(cameraTargetRef.current)
          }
        }
        break
      }

      case 'free':
      default: {
        if (cameraRef.current instanceof THREE.OrthographicCamera) {
          const width = canvasRef.current?.clientWidth || 800
          const height = canvasRef.current?.clientHeight || 600
          const persp = new THREE.PerspectiveCamera(75, width / height, 0.1, 10000)
          persp.position.set(150, 150, 150)
          persp.lookAt(0, 0, 0)
          sceneRef.current.remove(cameraRef.current)
          sceneRef.current.add(persp)
          cameraRef.current = persp
        }
        break
      }
    }
  }, [cameraMode, primarySelectedAgent, frame])

  // Update scene with frame data
  useEffect(() => {
    if (!frame || !sceneRef.current) return

    const frameData = frame as WorldFrame

    // Initialize obstacles (one-time)
    if (!obstaclesInitializedRef.current && frameData.obstacles) {
      frameData.obstacles.forEach((obstacle: Obstacle) => {
        const geometry = new THREE.BoxGeometry(obstacle.size[0], obstacle.size[1], obstacle.size[2])
        const material = new THREE.MeshPhongMaterial({
          color: 0x666666,
          shininess: 30,
        })
        const mesh = new THREE.Mesh(geometry, material)
        mesh.position.set(obstacle.pos[0], obstacle.pos[1], obstacle.pos[2])
        mesh.userData.obstacleId = obstacle.id
        sceneRef.current!.add(mesh)
        obstaclesMeshesRef.current.set(obstacle.id, mesh)
      })
      obstaclesInitializedRef.current = true
    }

    // Update agents and trajectories
    frameData.agents.forEach((agent: Agent) => {
      let mesh = agentMeshesRef.current.get(agent.id)

      if (!mesh) {
        // Create new agent sphere
        const geometry = new THREE.SphereGeometry(5, 8, 8)
        const material = new THREE.MeshPhongMaterial({
          color: getAgentColor(agent.state),
        })
        mesh = new THREE.Mesh(geometry, material)
        mesh.userData.agentId = agent.id
        sceneRef.current!.add(mesh)
        agentMeshesRef.current.set(agent.id, mesh)
      }

      // Update position and color
      mesh.position.set(agent.pos[0], agent.pos[1], agent.pos[2])
      ;(mesh.material as THREE.MeshPhongMaterial).color.set(getAgentColor(agent.state))

      // Update trajectory if available and enabled
      if (visibleLayers.trajectories && agent.traj && agent.traj.length > 1) {
        let line = trajectoryLinesRef.current.get(agent.id)

        if (!line) {
          const geometry = new THREE.BufferGeometry()
          const material = new THREE.LineBasicMaterial({
            color: getAgentColor(agent.state),
            linewidth: 1,
            transparent: true,
            opacity: 0.6,
          })
          line = new THREE.LineSegments(geometry, material)
          sceneRef.current!.add(line)
          trajectoryLinesRef.current.set(agent.id, line)
        }

        const positions = new Float32Array(agent.traj.length * 3)
        for (let i = 0; i < agent.traj.length; i++) {
          positions[i * 3] = agent.traj[i][0]
          positions[i * 3 + 1] = agent.traj[i][1]
          positions[i * 3 + 2] = 0.1
        }

        ;(line.geometry as THREE.BufferGeometry).dispose()
        line.geometry = new THREE.BufferGeometry()
        line.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
        ;(line.material as THREE.LineBasicMaterial).color.set(getAgentColor(agent.state))
      }
    })

    // Add new events
    setEvents((prev) => [...prev, ...frameData.events].slice(-50)) // Keep last 50 events

    // Remove agents that are no longer in the frame
    const currentAgentIds = new Set(frameData.agents.map((a) => a.id))
    agentMeshesRef.current.forEach((mesh, agentId) => {
      if (!currentAgentIds.has(agentId)) {
        sceneRef.current?.remove(mesh)
        agentMeshesRef.current.delete(agentId)

        // Also remove trajectory
        const line = trajectoryLinesRef.current.get(agentId)
        if (line) {
          sceneRef.current?.remove(line)
          line.geometry.dispose()
          ;(line.material as THREE.LineBasicMaterial).dispose()
          trajectoryLinesRef.current.delete(agentId)
        }
      }
    })
  }, [frame])

  const handlePlayPause = () => {
    const newState = !playing
    setPlaying(newState)
    sendCommand({
      type: newState ? 'play' : 'pause',
      payload: {},
    })
  }

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed)
    sendCommand({
      type: 'speed',
      payload: { speed: newSpeed },
    })
  }

  const handleCameraChange = (mode: 'free' | 'topdown' | 'follow') => {
    setCameraMode(mode)
    sendCommand({
      type: 'camera',
      payload: { camera: mode },
    })
  }

  return (
    <div className="app-container">
      <div className="canvas-wrapper">
        <canvas ref={canvasRef} className="viewport" />
      </div>

      <div className="ui-panel">
        <div className="header">
          <h1>PyRoboSimulator</h1>
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        <Controls
          playing={playing}
          speed={speed}
          cameraMode={cameraMode}
          visibleLayers={visibleLayers}
          presets={viewPresets.presets}
          onPlayPause={handlePlayPause}
          onSpeedChange={handleSpeedChange}
          onCameraChange={handleCameraChange}
          onLayerToggle={(layer, visible) =>
            setVisibleLayers({ ...visibleLayers, [layer]: visible })
          }
          onApplyPreset={viewPresets.applyPreset}
          onSavePreset={viewPresets.saveCurrentViewAsPreset}
          onDeletePreset={viewPresets.deletePreset}
          onExportPresets={viewPresets.exportPresets}
          onImportPresets={viewPresets.importPresets}
          onResetToDefaults={viewPresets.resetToDefaults}
        />

        <div className="bottom-panel">
          <div className="event-log-wrapper">
            <EventLog events={events} />
          </div>

          {primarySelectedAgent !== null && (
            <div className="sensor-panel-wrapper">
              <SensorPanel
                agentId={primarySelectedAgent}
                sensorData={frame?.sensors?.[primarySelectedAgent] || null}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function getAgentColor(state: string): number {
  switch (state) {
    case 'moving':
      return 0x00ff00 // Green
    case 'idle':
      return 0x0099ff // Blue
    case 'goal_reached':
      return 0xffff00 // Yellow
    case 'collision':
      return 0xff0000 // Red
    default:
      return 0xffffff // White
  }
}

export default App
