import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import App from '../App.jsx'

/** Open the demo controls drawer and click one of its controls. */
async function selectControl(name) {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name: /demo control/i }))
  const drawer = await screen.findByRole('dialog')
  await user.click(within(drawer).getByRole('button', { name: new RegExp(name, 'i') }))
  return user
}

describe('failure states', () => {
  // §14 gives three error codes and they mean three different things to the
  // user. A 503 says your view is stale; a 422 says fix your input.
  it('keeps the last known state on screen for a 503, and marks how old it is', async () => {
    render(<App />)
    await selectControl('API 503')

    expect(screen.getByText(/503 —/)).toBeInTheDocument()
    expect(screen.getByText(/last update/i)).toBeInTheDocument()
    // The dashboard is still there — the numbers exist, they are just no
    // longer current.
    expect(screen.getByText('Routing score')).toBeInTheDocument()
  })

  it('clears the dashboard for a 422, because nothing was dispatched', async () => {
    render(<App />)
    await selectControl('API 422')

    expect(screen.getByText(/422 —/)).toBeInTheDocument()
    expect(screen.queryByText('Routing score')).not.toBeInTheDocument()
    expect(screen.queryByText(/last update/i)).not.toBeInTheDocument()
  })

  // §21: no eligible target is an explicit outcome, not a crash. It has to
  // name what to do next.
  it('treats a routing failure as a recorded outcome with a way forward', async () => {
    render(<App />)
    await selectControl('No eligible target')

    expect(screen.getByText(/no eligible target/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /route again/i })).toBeInTheDocument()
  })
})

describe('the live accent follows the decision', () => {
  it('re-tints the page when the workload moves to another target', async () => {
    const { container } = render(<App />)
    expect(container.querySelector('[data-target]')).toHaveAttribute('data-target', 'cloud')

    await selectControl('Reroute under pressure')

    expect(container.querySelector('[data-target]')).toHaveAttribute('data-target', 'local')
  })
})

describe('demo controls drawer', () => {
  it('closes on Escape', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /demo control/i }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('says on its face that it is not part of the product', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.click(screen.getByRole('button', { name: /demo control/i }))

    expect(screen.getByText(/not part of the product/i)).toBeInTheDocument()
  })
})

describe('baseline comparison', () => {
  it('claims no improvement until both runs are measured', async () => {
    render(<App />)
    expect(screen.getByText(/No improvement is claimed until both runs are measured/i)).toBeInTheDocument()

    await selectControl('Run static baseline')

    expect(screen.getByText('Static baseline vs adaptive')).toBeInTheDocument()
    expect(screen.getByText(/Demonstration values only/i)).toBeInTheDocument()
  })
})
