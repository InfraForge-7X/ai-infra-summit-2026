import { useEffect, useRef, useState } from 'react'

import styles from './Drawer.module.css'

/**
 * Right-anchored drawer with a scrim. Figma node 5808:16715 — 528px panel,
 * 500px content inside a 16px inset.
 *
 * Drawers are state, not routes. Opening one must not change the URL, because
 * the reroute has to stay visible behind it.
 *
 * Keyboard and focus behaviour is not in the design but is not optional:
 * Escape closes, focus moves to the panel on open and returns to whatever
 * opened it on close, and the page behind does not scroll.
 *
 * @param {object} props
 * @param {boolean} props.open
 * @param {() => void} props.onClose
 * @param {string} props.title
 * @param {string} [props.lede]
 * @param {React.ReactNode} props.children
 */
export default function Drawer({ open, onClose, title, lede, children }) {
  const [closing, setClosing] = useState(false)
  const panelRef = useRef(/** @type {HTMLDivElement | null} */ (null))
  const restoreTo = useRef(/** @type {Element | null} */ (null))
  const exitTimer = useRef(/** @type {ReturnType<typeof setTimeout> | undefined} */ (undefined))

  /*
   * Closing runs the exit animation first, then unmounts when it finishes.
   * Driven by the animation's own end event rather than a timer, so the two
   * can never drift apart. All dismissals — Escape, scrim, the close button —
   * go through here; a caller that flips `open` directly still closes, just
   * without the exit, which is right when the close is a side effect of
   * choosing something.
   */
  const finish = () => {
    clearTimeout(exitTimer.current)
    setClosing(false)
    onClose()
  }

  const requestClose = () => {
    setClosing(true)
    // Safety net: if the exit animation never fires — animations disabled at
    // the OS or browser level, an interrupted frame — the drawer must still
    // close. Waiting on animationend alone would leave it stuck open.
    clearTimeout(exitTimer.current)
    exitTimer.current = setTimeout(finish, 400)
  }

  const onAnimationEnd = () => {
    if (closing) finish()
  }

  useEffect(() => {
    if (!open) return undefined

    restoreTo.current = document.activeElement
    panelRef.current?.focus()

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    /** @param {KeyboardEvent} event */
    const onKeyDown = (event) => {
      if (event.key === 'Escape') requestClose()
    }
    document.addEventListener('keydown', onKeyDown)

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      clearTimeout(exitTimer.current)
      if (restoreTo.current instanceof HTMLElement) restoreTo.current.focus()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, onClose])

  if (!open) return null

  return (
    <>
      <div
        className={`${styles.scrim} ${closing ? styles.scrimOut : ''}`}
        onClick={requestClose}
        aria-hidden="true"
      />
      <div
        ref={panelRef}
        className={`${styles.panel} ${closing ? styles.panelOut : ''}`}
        onAnimationEnd={onAnimationEnd}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
      >
        <header className={styles.head}>
          <h2 className={styles.title}>{title}</h2>
          <button type="button" className={styles.close} onClick={requestClose} aria-label="Close">
            ×
          </button>
        </header>

        {lede ? <p className={styles.lede}>{lede}</p> : null}

        <div className={styles.body}>{children}</div>
      </div>
    </>
  )
}
