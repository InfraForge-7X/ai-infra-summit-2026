import { Settings01Icon, Timer01Icon } from '@hugeicons/core-free-icons'
import { useEffect, useState } from 'react'

import { Button, Icon } from './ui/ui.jsx'
import styles from './TopBar.module.css'

/**
 * Brand, elapsed clock, demo controls.
 *
 * The clock is the one thing on the page that changes every second, and
 * General Sans has proportional digits, so its width is reserved.
 *
 * @param {object} props
 * @param {() => void} [props.onOpenDemoControls]
 */
export default function TopBar({ onOpenDemoControls }) {
  const [clock, setClock] = useState(() => new Date().toLocaleTimeString('en-GB'))

  useEffect(() => {
    const id = setInterval(() => setClock(new Date().toLocaleTimeString('en-GB')), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <header className={styles.bar}>
      <div className={styles.inner}>
        <p className={styles.brand}>
          AFRI-EDGE <span className={styles.crumb}>› routing control</span>
        </p>

        <div className={styles.actions}>
          {/* Icon first, like every other icon-and-label pairing on the page. */}
          <span className={styles.clock}>
            <Icon icon={Timer01Icon} size={16} />
            <span className="is-live" style={{ '--live-width': '8ch' }}>
              {clock}
            </span>
          </span>
          <Button small onClick={onOpenDemoControls}>
            <Icon icon={Settings01Icon} size={16} />
            Demo controls
          </Button>
        </div>
      </div>
    </header>
  )
}
