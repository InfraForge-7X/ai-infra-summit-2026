import { render, screen, waitForElementToBeRemoved, within } from '@testing-library/react'
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

    // EDGE, not LOCAL: the demo workload requires a GPU and LOCAL has none, so
    // a reroute to LOCAL would contradict the ranking shown beneath it.
    expect(container.querySelector('[data-target]')).toHaveAttribute('data-target', 'edge')
  })
})

describe('demo controls drawer', () => {
  // Closing runs an exit animation, so the drawer leaves on the next frame
  // rather than vanishing — the assertion has to wait for it.
  it('closes on Escape', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /demo control/i }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    await waitForElementToBeRemoved(() => screen.queryByRole('dialog'))
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

describe('decision detail drawer', () => {
  it('shows the raw payloads behind the decision', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /see decision/i }))
    const drawer = await screen.findByRole('dialog', { name: /decision detail/i })

    expect(within(drawer).getByText('RoutingDecision')).toBeInTheDocument()
    expect(within(drawer).getByText('WorkloadProfile sent')).toBeInTheDocument()
  })

  // This used to assert that the drawer said no candidate ranking existed.
  // #21 added one, so the assertion is now the opposite: the per-dimension
  // breakdown behind each score is here, keyed by whatever the engine sent.
  it('shows the per-dimension score breakdown for each scored candidate', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /see decision/i }))
    const drawer = await screen.findByRole('dialog', { name: /decision detail/i })

    expect(within(drawer).getByText(/score breakdown/i)).toBeInTheDocument()
    expect(within(drawer).getByText('CLOUD')).toBeInTheDocument()
    expect(within(drawer).getByText('EDGE')).toBeInTheDocument()
    // LOCAL is ineligible in this scenario: never scored, so no dimensions.
    expect(within(drawer).queryByText('LOCAL')).not.toBeInTheDocument()
  })
})

describe('workload form', () => {
  it('sends the profile and reflects it back on the page', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /change workload/i }))
    const drawer = await screen.findByRole('dialog', { name: /^workload$/i })

    await user.clear(within(drawer).getByLabelText(/task id/i))
    await user.type(within(drawer).getByLabelText(/task id/i), 'task-042')
    await user.click(within(drawer).getByRole('button', { name: /route this workload/i }))

    // The full task_id, matching what the decision drawer shows in the raw
    // payload — not a tidied fragment of it.
    expect(screen.getByText('task-042')).toBeInTheDocument()
  })

  // §29.2: the routing core is workload-agnostic. Speech has no frames, so
  // fps is null on the contract and must not render as 0.
  it('renders an em dash for fps when a speech workload is selected', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /change workload/i }))
    const drawer = await screen.findByRole('dialog', { name: /^workload$/i })

    await user.click(within(drawer).getByRole('combobox', { name: /workload type/i }))
    await user.click(within(drawer).getByRole('option', { name: 'speech' }))
    await user.click(within(drawer).getByRole('button', { name: /route this workload/i }))

    // Scoped to the execution card on purpose. An em dash now appears in the
    // candidate ranking too, where it means "never scored" rather than "no
    // frames" — two different absences that must not be asserted as one.
    const fps = screen.getByText('Frames per second').closest('div')
    expect(within(fps).getByText('—')).toBeInTheDocument()
  })

  it('does not offer the legacy workload type', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /change workload/i }))
    const drawer = await screen.findByRole('dialog', { name: /^workload$/i })
    await user.click(within(drawer).getByRole('combobox', { name: /workload type/i }))

    expect(within(drawer).getByRole('option', { name: 'real_time_video' })).toBeInTheDocument()
    expect(within(drawer).queryByRole('option', { name: 'video_inference' })).not.toBeInTheDocument()
  })

  // Replacing a native <select> means re-implementing what it gave for free.
  it('is operable from the keyboard alone', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /change workload/i }))
    const drawer = await screen.findByRole('dialog', { name: /^workload$/i })
    const combobox = within(drawer).getByRole('combobox', { name: /privacy/i })

    combobox.focus()
    await user.keyboard('{ArrowDown}')
    expect(combobox).toHaveAttribute('aria-expanded', 'true')

    await user.keyboard('{ArrowDown}{Enter}')
    expect(combobox).toHaveTextContent('sensitive')
    expect(combobox).toHaveAttribute('aria-expanded', 'false')
  })

  // Inside a drawer, Escape on an open menu must close the menu only. Closing
  // the whole drawer would throw away everything typed into the form.
  it('closes only the menu on Escape, not the drawer behind it', async () => {
    const user = userEvent.setup()
    render(<App />)

    await user.click(screen.getByRole('button', { name: /change workload/i }))
    const drawer = await screen.findByRole('dialog', { name: /^workload$/i })
    const combobox = within(drawer).getByRole('combobox', { name: /priority/i })

    await user.click(combobox)
    expect(combobox).toHaveAttribute('aria-expanded', 'true')

    await user.keyboard('{Escape}')
    expect(combobox).toHaveAttribute('aria-expanded', 'false')
    expect(screen.getByRole('dialog', { name: /^workload$/i })).toBeInTheDocument()
  })
})

describe('optional provider adapters', () => {
  // §29.5 — sponsor integrations are capabilities, not dependencies. The tag
  // says where execution happens; it must not appear on targets without an
  // adapter, and it changes no routing behaviour.
  it('labels only the target that has an adapter', () => {
    render(<App />)
    const adapters = screen.getAllByText(/via SiMa\.ai/i)
    expect(adapters).toHaveLength(1)
  })
})
