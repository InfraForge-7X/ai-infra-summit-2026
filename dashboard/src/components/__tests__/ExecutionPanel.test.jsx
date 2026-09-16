import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import ExecutionPanel from '../ExecutionPanel.jsx'
import { EM_DASH } from '../../lib/format.js'

/** @type {import('../../mocks/contracts.js').InfrastructureState} */
const targetState = {
  target: 'cloud',
  cpu_usage: 10,
  gpu_available: true,
  ram_usage: 31,
  queue: 0,
  latency_ms: 73,
  bandwidth_mbps: 940,
  packet_loss: 0,
  timestamp: new Date().toISOString(),
}

/** @param {number | null} fps */
const executionWith = (fps) => ({
  task_id: 'task-001',
  target: /** @type {const} */ ('cloud'),
  status: /** @type {const} */ ('running'),
  execution_time_ms: 82000,
  network_latency_ms: 73,
  fps,
})

describe('ExecutionPanel', () => {
  it('shows an em dash for a workload with no frames', () => {
    // A speech workload has no fps. Rendering 0 would assert a measurement
    // that was never taken.
    render(<ExecutionPanel execution={executionWith(null)} targetState={targetState} />)
    expect(screen.getByText(EM_DASH)).toBeInTheDocument()
  })

  it('shows the value for a video workload', () => {
    render(<ExecutionPanel execution={executionWith(17)} targetState={targetState} />)
    expect(screen.getByText('17')).toBeInTheDocument()
    expect(screen.queryByText(EM_DASH)).not.toBeInTheDocument()
  })

  it('renders the execution status as a label, not a raw enum value', () => {
    render(<ExecutionPanel execution={executionWith(17)} targetState={targetState} />)
    expect(screen.getByText('Executing')).toBeInTheDocument()
    expect(screen.queryByText('running')).not.toBeInTheDocument()
  })
})
