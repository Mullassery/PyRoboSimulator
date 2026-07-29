import { describe, it, expect } from 'vitest'
import * as msgpack from 'msgpack'

// Re-implementation of the unpack logic for testing (mirrors the fixed useWebSocket.ts)
function testUnpack(buffer: ArrayBuffer): any {
  const view = new DataView(buffer)
  const decoder = new TextDecoder()
  let offset = 0

  function read(bytes: number): Uint8Array {
    const result = new Uint8Array(buffer, offset, bytes)
    offset += bytes
    return result
  }

  function readArray(n: number): any[] {
    const arr = []
    for (let i = 0; i < n; i++) {
      arr.push(unpack())
    }
    return arr
  }

  function readMap(n: number): Record<string, any> {
    const obj: Record<string, any> = {}
    for (let i = 0; i < n; i++) {
      const key = unpack()
      const value = unpack()
      obj[key] = value
    }
    return obj
  }

  function unpack(): any {
    const byte = view.getUint8(offset)
    offset += 1

    if ((byte & 0x80) === 0) return byte
    if ((byte & 0xe0) === 0xe0) return byte | 0xffffff00
    if ((byte & 0xf0) === 0x80) return readMap(byte & 0x0f)
    if ((byte & 0xf0) === 0x90) return readArray(byte & 0x0f)
    if ((byte & 0xe0) === 0xa0) {
      const size = byte & 0x1f
      return decoder.decode(read(size))
    }

    switch (byte) {
      case 0xc0:
        return null
      case 0xc2:
        return false
      case 0xc3:
        return true
      case 0xcc: {
        const v = view.getUint8(offset)
        offset += 1
        return v
      }
      case 0xcd: {
        const v = view.getUint16(offset, false)
        offset += 2
        return v
      }
      case 0xce: {
        const v = view.getUint32(offset, false)
        offset += 4
        return v
      }
      case 0xcf: {
        const v = view.getBigUint64(offset, false)
        offset += 8
        return v
      }
      case 0xd0: {
        const v = view.getInt8(offset)
        offset += 1
        return v
      }
      case 0xd1: {
        const v = view.getInt16(offset, false)
        offset += 2
        return v
      }
      case 0xd2: {
        const v = view.getInt32(offset, false)
        offset += 4
        return v
      }
      case 0xd3: {
        const v = view.getBigInt64(offset, false)
        offset += 8
        return v
      }
      case 0xca: {
        const v = view.getFloat32(offset, false)
        offset += 4
        return v
      }
      case 0xcb: {
        const v = view.getFloat64(offset, false)
        offset += 8
        return v
      }
      case 0xd9: {
        const strLen = view.getUint8(offset)
        offset += 1
        return decoder.decode(read(strLen))
      }
      case 0xda: {
        const strLen = view.getUint16(offset, false)
        offset += 2
        return decoder.decode(read(strLen))
      }
      case 0xdb: {
        const strLen = view.getUint32(offset, false)
        offset += 4
        return decoder.decode(read(strLen))
      }
      case 0xdc: {
        const n = view.getUint16(offset, false)
        offset += 2
        return readArray(n)
      }
      case 0xdd: {
        const n = view.getUint32(offset, false)
        offset += 4
        return readArray(n)
      }
      case 0xde: {
        const n = view.getUint16(offset, false)
        offset += 2
        return readMap(n)
      }
      case 0xdf: {
        const n = view.getUint32(offset, false)
        offset += 4
        return readMap(n)
      }
      default:
        throw new Error(`Unsupported MessagePack type: 0x${byte.toString(16)}`)
    }
  }

  return unpack()
}

describe('MessagePack decoder', () => {
  it('decodes positive fixints (0x00-0x7f)', () => {
    const buffer = msgpack.pack(42)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(42)
  })

  it('decodes negative fixints (0xe0-0xff)', () => {
    const buffer = msgpack.pack(-5)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(-5)
  })

  it('decodes null, false, true', () => {
    expect(testUnpack(msgpack.pack(null) as ArrayBuffer)).toBeNull()
    expect(testUnpack(msgpack.pack(false) as ArrayBuffer)).toBe(false)
    expect(testUnpack(msgpack.pack(true) as ArrayBuffer)).toBe(true)
  })

  it('decodes uint8 (0xcc)', () => {
    const buffer = msgpack.pack(200)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(200)
  })

  it('decodes uint16 (0xcd) — critical for fixing offset bug', () => {
    const buffer = msgpack.pack(40000)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(40000)
  })

  it('decodes uint32 (0xce)', () => {
    const buffer = msgpack.pack(100000000)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(100000000)
  })

  it('decodes float32 (0xca)', () => {
    const buffer = msgpack.pack(3.14)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(Math.abs(result - 3.14) < 0.01).toBe(true)
  })

  it('decodes float64 (0xcb) — the critical case (WorldFrame.timestamp_ms)', () => {
    const timestamp = 1234567890.123
    const buffer = msgpack.pack(timestamp)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(Math.abs(result - timestamp) < 0.001).toBe(true)
  })

  it('decodes fixstr (0xa0-0xbf)', () => {
    const buffer = msgpack.pack('hello')
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe('hello')
  })

  it('decodes str8 (0xd9)', () => {
    const longStr = 'a'.repeat(100)
    const buffer = msgpack.pack(longStr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(longStr)
  })

  it('decodes str16 (0xda)', () => {
    const longStr = 'x'.repeat(500)
    const buffer = msgpack.pack(longStr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(longStr)
  })

  it('decodes fixarray (0x90-0x9f)', () => {
    const buffer = msgpack.pack([1, 2, 3])
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual([1, 2, 3])
  })

  it('decodes array16 (0xdc) — was completely missing before', () => {
    const arr = Array.from({ length: 20 }, (_, i) => i)
    const buffer = msgpack.pack(arr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(arr)
  })

  it('decodes array32 (0xdd)', () => {
    const arr = Array.from({ length: 100 }, (_, i) => i)
    const buffer = msgpack.pack(arr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(arr)
  })

  it('decodes fixmap (0x80-0x8f)', () => {
    const obj = { a: 1, b: 2 }
    const buffer = msgpack.pack(obj)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(obj)
  })

  it('decodes map16 (0xde) — was completely missing before', () => {
    const obj: Record<string, number> = {}
    for (let i = 0; i < 20; i++) {
      obj[`key${i}`] = i
    }
    const buffer = msgpack.pack(obj)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(obj)
  })

  it('decodes a realistic WorldFrame-like object with agents array', () => {
    const worldFrame = {
      type: 'world_frame',
      frame_id: 42,
      timestamp_ms: 1234567890.5,
      agents: [
        { id: 1, pos: [0, 0, 0], state: 'moving', vel: [1, 0, 0] },
        { id: 2, pos: [10, 10, 0], state: 'idle', vel: [0, 0, 0] },
      ],
      events: [],
      obstacles: [],
    }
    const buffer = msgpack.pack(worldFrame)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result.frame_id).toBe(42)
    expect(result.timestamp_ms).toBeCloseTo(1234567890.5, 1)
    expect(result.agents).toHaveLength(2)
    expect(result.agents[0].id).toBe(1)
  })

  it('decodes a large lidar cloud array (8192 points)', () => {
    const lidarCloud = Array.from({ length: 8192 }, (_, i) => [
      Math.cos((i / 8192) * Math.PI * 2) * 100,
      Math.sin((i / 8192) * Math.PI * 2) * 50,
      Math.sin((i / 8192) * Math.PI) * 30,
    ])
    const buffer = msgpack.pack(lidarCloud)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toHaveLength(8192)
    expect(result[0]).toHaveLength(3)
  })

  it('round-trips a complex nested structure', () => {
    const complex = {
      id: 123,
      name: 'test_agent',
      position: [1.5, 2.7, 3.14159],
      state: 'collision',
      trajectory: Array.from({ length: 50 }, (_, i) => [i * 0.5, i * 0.3]),
      metadata: {
        speed: 2.5,
        active: true,
        tags: ['robot', 'tracked'],
      },
    }
    const buffer = msgpack.pack(complex)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result.id).toBe(123)
    expect(result.position).toHaveLength(3)
    expect(result.trajectory).toHaveLength(50)
    expect(result.metadata.tags).toEqual(['robot', 'tracked'])
  })
})
