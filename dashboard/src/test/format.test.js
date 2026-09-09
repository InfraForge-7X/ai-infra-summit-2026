import { describe, expect, it } from 'vitest'

import { asInt, asPercent, EM_DASH, isStale, timeAgo } from '../lib/format.js'

describe('numeric formatting', () => {
  // The contract says fps is `float | None`. A speech workload returns null,
  // and the spec is explicit: a missing reading and a zero reading are
  // different facts.
  it('renders a missing value as an em dash, not zero', () => {
    expect(asInt(null)).toBe(EM_DASH)
    expect(asInt(undefined)).toBe(EM_DASH)
    expect(asInt(Number.NaN)).toBe(EM_DASH)
  })

  it('renders an actual zero as zero', () => {
    expect(asInt(0)).toBe('0')
    expect(asPercent(0)).toBe('0%')
  })

  it('rounds rather than truncating', () => {
    expect(asInt(17.6)).toBe('18')
    expect(asPercent(27.4)).toBe('27%')
  })
})

describe('freshness', () => {
  const now = Date.UTC(2026, 8, 9, 12, 0, 0)
  const iso = (secondsAgo) => new Date(now - secondsAgo * 1000).toISOString()

  it('reports fresh state as just now', () => {
    expect(timeAgo(iso(0), now)).toBe('updated just now')
  })

  it('counts seconds while they are meaningful', () => {
    expect(timeAgo(iso(9), now)).toBe('updated 9s ago')
  })

  // §8 tracks freshness and a stale target loses confidence. The window is
  // the dashboard's own, since no contract carries eligibility.
  it('marks state older than the window as stale', () => {
    expect(isStale(iso(3), now)).toBe(false)
    expect(isStale(iso(20), now)).toBe(true)
  })

  it('treats an unparseable timestamp as stale rather than fresh', () => {
    expect(isStale('not-a-date', now)).toBe(true)
  })
})
