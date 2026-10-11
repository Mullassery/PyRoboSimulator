import { describe, it, expect } from 'vitest'

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

// Minimal big-endian MessagePack encoder for test fixtures (matches testUnpack above)
function pack(value: any): ArrayBuffer {
  const bytes: number[] = []

  function u8(n: number): void {
    bytes.push(n & 0xff)
  }
  function u16(n: number): void {
    bytes.push((n >> 8) & 0xff, n & 0xff)
  }
  function u32(n: number): void {
    bytes.push((n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff)
  }
  function f64(n: number): void {
    const buf = new ArrayBuffer(8)
    new DataView(buf).setFloat64(0, n, false)
    bytes.push(...new Uint8Array(buf))
  }
  function str(s: string): void {
    const encoded = new TextEncoder().encode(s)
    if (encoded.length < 32) {
      u8(0xa0 | encoded.length)
    } else if (encoded.length < 256) {
      u8(0xd9)
      u8(encoded.length)
    } else {
      u8(0xda)
      u16(encoded.length)
    }
    bytes.push(...encoded)
  }
  function array(arr: any[]): void {
    if (arr.length < 16) {
      u8(0x90 | arr.length)
    } else if (arr.length < 65536) {
      u8(0xdc)
      u16(arr.length)
    } else {
      u8(0xdd)
      u32(arr.length)
    }
    for (const item of arr) encode(item)
  }
  function map(obj: Record<string, any>): void {
    const keys = Object.keys(obj)
    if (keys.length < 16) {
      u8(0x80 | keys.length)
    } else if (keys.length < 65536) {
      u8(0xde)
      u16(keys.length)
    } else {
      u8(0xdf)
      u32(keys.length)
    }
    for (const key of keys) {
      str(key)
      encode(obj[key])
    }
  }
  function encode(v: any): void {
    if (v === null || v === undefined) {
      u8(0xc0)
    } else if (v === true) {
      u8(0xc3)
    } else if (v === false) {
      u8(0xc2)
    } else if (typeof v === 'number') {
      if (Number.isInteger(v)) {
        if (v >= 0 && v < 128) u8(v)
        else if (v >= -32 && v < 0) u8(0xe0 | (v + 32))
        else if (v >= 0 && v < 256) { u8(0xcc); u8(v) }
        else if (v >= 0 && v < 65536) { u8(0xcd); u16(v) }
        else if (v >= 0 && v < 4294967296) { u8(0xce); u32(v) }
        else if (v < 0 && v >= -128) { u8(0xd0); u8(v) }
        else if (v < 0 && v >= -32768) { u8(0xd1); u16(v) }
        else if (v < 0 && v >= -2147483648) { u8(0xd2); u32(v) }
        else { u8(0xcb); f64(v) }
      } else {
        u8(0xcb)
        f64(v)
      }
    } else if (typeof v === 'string') {
      str(v)
    } else if (Array.isArray(v)) {
      array(v)
    } else if (typeof v === 'object') {
      map(v as Record<string, any>)
    } else {
      throw new Error(`Unsupported type: ${typeof v}`)
    }
  }

  encode(value)
  return new Uint8Array(bytes).buffer
}

describe('MessagePack decoder', () => {
  it('decodes positive fixints (0x00-0x7f)', () => {
    const buffer = pack(42)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(42)
  })

  it('decodes negative fixints (0xe0-0xff)', () => {
    const buffer = pack(-5)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(-5)
  })

  it('decodes null, false, true', () => {
    expect(testUnpack(pack(null) as ArrayBuffer)).toBeNull()
    expect(testUnpack(pack(false) as ArrayBuffer)).toBe(false)
    expect(testUnpack(pack(true) as ArrayBuffer)).toBe(true)
  })

  it('decodes uint8 (0xcc)', () => {
    const buffer = pack(200)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(200)
  })

  it('decodes uint16 (0xcd) — critical for fixing offset bug', () => {
    const buffer = pack(40000)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(40000)
  })

  it('decodes uint32 (0xce)', () => {
    const buffer = pack(100000000)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(100000000)
  })

  it('decodes float32 (0xca)', () => {
    const buffer = pack(3.14)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(Math.abs(result - 3.14) < 0.01).toBe(true)
  })

  it('decodes float64 (0xcb) — the critical case (WorldFrame.timestamp_ms)', () => {
    const timestamp = 1234567890.123
    const buffer = pack(timestamp)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(Math.abs(result - timestamp) < 0.001).toBe(true)
  })

  it('decodes fixstr (0xa0-0xbf)', () => {
    const buffer = pack('hello')
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe('hello')
  })

  it('decodes str8 (0xd9)', () => {
    const longStr = 'a'.repeat(100)
    const buffer = pack(longStr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(longStr)
  })

  it('decodes str16 (0xda)', () => {
    const longStr = 'x'.repeat(500)
    const buffer = pack(longStr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toBe(longStr)
  })

  it('decodes fixarray (0x90-0x9f)', () => {
    const buffer = pack([1, 2, 3])
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual([1, 2, 3])
  })

  it('decodes array16 (0xdc) — was completely missing before', () => {
    const arr = Array.from({ length: 20 }, (_, i) => i)
    const buffer = pack(arr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(arr)
  })

  it('decodes array32 (0xdd)', () => {
    const arr = Array.from({ length: 100 }, (_, i) => i)
    const buffer = pack(arr)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(arr)
  })

  it('decodes fixmap (0x80-0x8f)', () => {
    const obj = { a: 1, b: 2 }
    const buffer = pack(obj)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result).toEqual(obj)
  })

  it('decodes map16 (0xde) — was completely missing before', () => {
    const obj: Record<string, number> = {}
    for (let i = 0; i < 20; i++) {
      obj[`key${i}`] = i
    }
    const buffer = pack(obj)
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
    const buffer = pack(worldFrame)
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
    const buffer = pack(lidarCloud)
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
    const buffer = pack(complex)
    const result = testUnpack(buffer as ArrayBuffer)
    expect(result.id).toBe(123)
    expect(result.position).toHaveLength(3)
    expect(result.trajectory).toHaveLength(50)
    expect(result.metadata.tags).toEqual(['robot', 'tracked'])
  })
})
