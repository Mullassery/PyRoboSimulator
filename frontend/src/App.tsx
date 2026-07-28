import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { useWebSocket } from './hooks/useWebSocket'
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

  const simulationId = new URLSearchParams(window.location.search).get('id') || '1'
  const { frame, isConnected, sendCommand } = useWebSocket(simulationId)

  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(1.0)
  const [cameraMode, setCameraMode] = useState<'free' | 'topdown' | 'follow'>('free')
  const [selectedAgent, setSelectedAgent] = useState<number | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const [visibleLayers, setVisibleLayers] = useState({
    agents: true,
    obstacles: true,
    trajectories: true,
    grid: true,
    bounds: true,
  })

  // Initialize Three.js scene
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

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate)
      renderer.render(scene, camera)
    }
    animate()

    // Handle window resize
    const handleResize = () => {
      const newWidth = canvasRef.current?.clientWidth || width
      const newHeight = canvasRef.current?.clientHeight || height
      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()
      renderer.setSize(newWidth, newHeight)
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
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
      if (showTrajectories && agent.traj && agent.traj.length > 1) {
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
          onPlayPause={handlePlayPause}
          onSpeedChange={handleSpeedChange}
          onCameraChange={handleCameraChange}
          onLayerToggle={(layer, visible) =>
            setVisibleLayers({ ...visibleLayers, [layer]: visible })
          }
        />

        <div className="bottom-panel">
          <div className="event-log-wrapper">
            <EventLog events={events} />
          </div>

          {selectedAgent !== null && (
            <div className="sensor-panel-wrapper">
              <SensorPanel
                agentId={selectedAgent}
                sensorData={frame?.sensors?.[selectedAgent] || null}
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
