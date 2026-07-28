import { useEffect, useRef, useState } from 'react'

interface ControlCommand {
  type: string
  payload: Record<string, any>
}

export function useWebSocket(simulationId: string) {
  const wsRef = useRef<WebSocket | null>(null)
  const [frame, setFrame] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/simulations/${simulationId}/stream`

    const ws = new WebSocket(wsUrl)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        // Deserialize MessagePack frame
        const data = event.data
        const frameData = unpackMessagePack(data)
        setFrame(frameData)
      } catch (error) {
        console.error('Error processing frame:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
      setIsConnected(false)
    }

    wsRef.current = ws

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [simulationId])

  const sendCommand = (command: ControlCommand) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(command))
    }
  }

  return {
    frame,
    isConnected,
    sendCommand,
  }
}

// Simple MessagePack decoder
function unpackMessagePack(buffer: ArrayBuffer): any {
  const view = new DataView(buffer)
  const decoder = new TextDecoder()
  let offset = 0

  function read(bytes: number): Uint8Array {
    const result = new Uint8Array(buffer, offset, bytes)
    offset += bytes
    return result
  }

  function unpack(): any {
    const byte = view.getUint8(offset++)

    // Positive fixint
    if ((byte & 0x80) === 0) {
      return byte
    }

    // Negative fixint
    if ((byte & 0xe0) === 0xe0) {
      return byte | 0xffffff00
    }

    // Fixmap
    if ((byte & 0xf0) === 0x80) {
      const size = byte & 0x0f
      const obj: Record<string, any> = {}
      for (let i = 0; i < size; i++) {
        const key = unpack()
        const value = unpack()
        obj[key] = value
      }
      return obj
    }

    // Fixarray
    if ((byte & 0xf0) === 0x90) {
      const size = byte & 0x0f
      const arr = []
      for (let i = 0; i < size; i++) {
        arr.push(unpack())
      }
      return arr
    }

    // Fixstr
    if ((byte & 0xe0) === 0xa0) {
      const size = byte & 0x1f
      const bytes = read(size)
      return decoder.decode(bytes)
    }

    switch (byte) {
      case 0xc0:
        return null
      case 0xc2:
        return false
      case 0xc3:
        return true
      case 0xcc:
        return view.getUint8(offset++)
      case 0xcd:
        return view.getUint16(offset++, false)
      case 0xce:
        return view.getUint32(offset++, false)
      case 0xcf:
        return view.getBigUint64(offset++, false)
      case 0xd0:
        return view.getInt8(offset++)
      case 0xd1:
        return view.getInt16(offset++, false)
      case 0xd2:
        return view.getInt32(offset++, false)
      case 0xd3:
        return view.getBigInt64(offset++, false)
      case 0xca:
        return view.getFloat32(offset++, false)
      case 0xcb:
        return view.getFloat64(offset++, false)
      case 0xd9:
        const strLen = view.getUint8(offset++)
        return decoder.decode(read(strLen))
      case 0xda:
        const strLen16 = view.getUint16(offset++, false)
        return decoder.decode(read(strLen16))
      case 0xdb:
        const strLen32 = view.getUint32(offset++, false)
        return decoder.decode(read(strLen32))
      default:
        throw new Error(`Unsupported MessagePack type: 0x${byte.toString(16)}`)
    }
  }

  return unpack()
}
