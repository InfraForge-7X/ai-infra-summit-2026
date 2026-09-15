import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * The live path, exercised without a backend.
 *
 * `USING_MOCK_DATA` is read at module load, so every test here stubs the
 * environment and then imports the modules fresh. These tests intentionally
 * cover only the confirmed POST /route contract. Unsupported read endpoints
 * are not polled until a backend contract exists.
 */

const DECISION = {
  task_id: 'task-900',
  target: 'edge',
  score: 0.71,
  reasons: ['Latency within requirement'],
  ranked_candidates: [
    { target: 'edge', eligible: true, disqualification_reasons: [], score: 0.71, score_breakdown: {} },
  ],
}

/** A fetch that answers by path, so a test only declares what it cares about. */
function fetchReturning(routes) {
  return vi.fn(async (url, init) => {
    const path = String(url).replace('http://afri-edge.test', '')
    const key = `${init?.method ?? 'GET'} ${path}`
    const handler = routes[key] ?? routes[path]
    if (!handler) return { ok: true, status: 200, json: async () => ({}) }
    return handler
  })
}

const ok = (body) => ({ ok: true, status: 200, json: async () => body })
const fail = (status, body) => ({ ok: false, status, json: async () => body })

async function loadHook() {
  vi.resetModules()
  vi.stubEnv('VITE_API_URL', 'http://afri-edge.test')
  return import('../hooks/useLiveDashboard.js')
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchReturning({}))
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.resetModules()
})

describe('live dashboard', () => {
  it('does not poll unsupported read endpoints', async () => {
    const fetchSpy = vi.fn(async () => ok([]))
    vi.stubGlobal('fetch', fetchSpy)
    const { useLiveDashboard } = await loadHook()

    const { result } = renderHook(() => useLiveDashboard())

    // Live mode is currently backed only by the confirmed POST /route contract.
    expect(result.current.loading).toBe(false)
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(result.current.states).toEqual({})
    expect(result.current.history).toEqual([])
    expect(result.current.execution).toBeNull()
  })

  it('routes a workload and keeps the decision the service returned', async () => {
    const fetchSpy = fetchReturning({ 'POST /route': ok(DECISION) })
    vi.stubGlobal('fetch', fetchSpy)
    const { useLiveDashboard } = await loadHook()

    const { result } = renderHook(() => useLiveDashboard())
    await act(async () => {
      await result.current.route({ task_id: 'task-900' })
    })

    expect(result.current.decision.target).toBe('edge')
    expect(result.current.decision.ranked_candidates).toHaveLength(1)
    expect(result.current.execution).toBeNull()
    expect(result.current.error).toBeNull()
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    expect(fetchSpy.mock.calls[0][1].method).toBe('POST')
  })

  it('keeps the last known decision on a 503', async () => {
    let routeResponse = ok(DECISION)
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url, init) => {
        if (init?.method === 'POST') return routeResponse
        return ok([])
      }),
    )
    const { useLiveDashboard } = await loadHook()

    const { result } = renderHook(() => useLiveDashboard())
    await act(async () => {
      await result.current.route({ task_id: 'task-900' })
    })
    expect(result.current.decision.target).toBe('edge')

    routeResponse = fail(503, { detail: 'Decision engine unreachable' })
    await act(async () => {
      await result.current.route({ task_id: 'task-900' })
    })

    // The last decision remains visible while the route service is unavailable.
    expect(result.current.error.status).toBe(503)
    expect(result.current.error.showsLastKnownState).toBe(true)
    expect(result.current.decision.target).toBe('edge')
  })

  it('clears the decision on a 422 and names the field that was rejected', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url, init) => {
        if (init?.method === 'POST') {
          return fail(422, {
            detail: [{ loc: ['body', 'latency_requirement'], msg: 'Input should be greater than 0' }],
          })
        }
        return ok([])
      }),
    )
    const { useLiveDashboard } = await loadHook()

    const { result } = renderHook(() => useLiveDashboard())
    await act(async () => {
      await result.current.route({ task_id: 'task-901' })
    })

    // Nothing was dispatched, so nothing may stay on screen claiming otherwise.
    expect(result.current.decision).toBeNull()
    expect(result.current.error.status).toBe(422)
    expect(result.current.error.body).toBe(
      'latency_requirement: Input should be greater than 0',
    )
  })

  it('treats an unreachable service as a 503 when routing', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const { useLiveDashboard } = await loadHook()

    const { result } = renderHook(() => useLiveDashboard())
    await act(async () => {
      await result.current.route({ task_id: 'task-902' })
    })

    expect(result.current.error).toBeTruthy()
    expect(result.current.error.status).toBe(503)
  })

  it('issues no requests at all in mock mode', async () => {
    const spy = vi.fn()
    vi.stubGlobal('fetch', spy)
    vi.resetModules()
    vi.stubEnv('VITE_API_URL', '')
    const { useLiveDashboard } = await import('../hooks/useLiveDashboard.js')

    const { result } = renderHook(() => useLiveDashboard())

    // Load-bearing: a demo machine with no backend must not be quietly
    // hammering an address that isn't there and swallowing the failures.
    expect(result.current).toBeNull()
    expect(spy).not.toHaveBeenCalled()
  })
})
