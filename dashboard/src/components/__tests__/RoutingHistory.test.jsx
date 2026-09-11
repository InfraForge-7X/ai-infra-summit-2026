import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import RoutingHistory from '../RoutingHistory.jsx'

/** @param {Partial<import('../../mocks/fixtures.js').RoutingEvent>} overrides */
const event = (overrides) => ({
  id: 'ev-1',
  time: '03:20:52',
  kind: /** @type {const} */ ('decision'),
  target: /** @type {const} */ ('cloud'),
  score: 0.65,
  reason: 'Latency within requirement',
  ...overrides,
})

describe('RoutingHistory', () => {
  it('invites the first event when empty rather than showing a blank card', () => {
    render(<RoutingHistory events={[]} />)
    expect(screen.getByText(/land here in order/i)).toBeInTheDocument()
  })

  it('reads a reroute as a move between two targets', () => {
    render(<RoutingHistory events={[event({ kind: 'reroute', from: 'cloud', target: 'local' })]} />)
    expect(screen.getByText(/CLOUD/)).toBeInTheDocument()
    expect(screen.getByText('LOCAL')).toBeInTheDocument()
  })

  // The hold is the evidence that the switching policy is real. If it read the
  // same as a reroute, it would claim a move that never happened.
  it('distinguishes a hold from a reroute', () => {
    render(<RoutingHistory events={[event({ kind: 'hold', reason: 'Gain below switching threshold' })]} />)
    expect(screen.getByText(/Held on/i)).toBeInTheDocument()
    expect(screen.queryByText(/→/)).not.toBeInTheDocument()
  })

  it('states a failure without attaching a score to it', () => {
    render(
      <RoutingHistory
        events={[event({ kind: 'failure', score: 0, reason: 'Every environment failed a hard constraint' })]}
      />,
    )
    expect(screen.getByText('Routing failed')).toBeInTheDocument()
    expect(screen.queryByText(/Score/)).not.toBeInTheDocument()
  })

  it('says the shape is provisional, since src/shared has no event model', () => {
    render(<RoutingHistory events={[event({})]} />)
    expect(screen.getByText(/no contract yet/i)).toBeInTheDocument()
  })
})
