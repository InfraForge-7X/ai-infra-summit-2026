import { describe, expect, it } from 'vitest'
import { detailFrom, toApiError, USING_MOCK_DATA } from '../api/client.js'

describe('toApiError', () => {
  it('keeps the last known state on a 503 and discards it on 422 and 500', () => {
    // This is the whole behavioural difference between the three, and it is
    // the thing a demo gets judged on: an unreachable service must not blank a
    // view that is still true, and a rejected workload must not leave a stale
    // decision on screen looking current.
    expect(toApiError(503).showsLastKnownState).toBe(true)
    expect(toApiError(422).showsLastKnownState).toBe(false)
    expect(toApiError(500).showsLastKnownState).toBe(false)
  })

  it('maps an unrecognised status to the 500 wording rather than inventing one', () => {
    const error = toApiError(418)
    expect(error.status).toBe(500)
    expect(error.showsLastKnownState).toBe(false)
  })

  it('prefers the server explanation over the canned one', () => {
    expect(toApiError(422, 'latency_requirement: must be greater than 0').body).toBe(
      'latency_requirement: must be greater than 0',
    )
  })

  it('falls back to the canned wording when the server explains nothing', () => {
    expect(toApiError(422, '').body).toMatch(/could not accept this workload/)
  })
})

describe('detailFrom', () => {
  it('reads a FastAPI validation error and names the field that failed', () => {
    const body = {
      detail: [
        {
          loc: ['body', 'latency_requirement'],
          msg: 'Input should be greater than 0',
          type: 'greater_than',
        },
      ],
    }
    expect(detailFrom(body)).toBe('latency_requirement: Input should be greater than 0')
  })

  it('joins multiple validation failures', () => {
    const body = {
      detail: [
        { loc: ['body', 'input_size'], msg: 'Input should be greater than 0' },
        { loc: ['body', 'model'], msg: 'String should have at least 1 character' },
      ],
    }
    expect(detailFrom(body)).toBe(
      'input_size: Input should be greater than 0. model: String should have at least 1 character',
    )
  })

  it('reads a plain HTTPException detail string', () => {
    expect(detailFrom({ detail: 'No eligible target' })).toBe('No eligible target')
  })

  it('returns nothing for a body it does not recognise, rather than [object Object]', () => {
    expect(detailFrom({ error: 'nope' })).toBe('')
    expect(detailFrom(null)).toBe('')
    expect(detailFrom('a string')).toBe('')
  })
})

describe('mock mode', () => {
  it('is on when no API address is configured', () => {
    // The guarantee is that there is no third state: with VITE_API_URL unset
    // the app cannot believe it is live. If this ever fails, the demo can ship
    // claiming measured results it does not have.
    expect(USING_MOCK_DATA).toBe(true)
  })
})
