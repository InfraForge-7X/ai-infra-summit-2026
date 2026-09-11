import { useEffect, useRef } from 'react'

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
  const panelRef = useRef(/** @type {HTMLDivElement | null} */ (null))
  const restoreTo = useRef(/** @type {Element | null} */ (null))

  useEffect(() => {
    if (!open) return undefined

    restoreTo.current = document.activeElement
    panelRef.current?.focus()

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    /** @param {KeyboardEvent} event */
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)

    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
      if (restoreTo.current instanceof HTMLElement) restoreTo.current.focus()
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <>
      <div className={styles.scrim} onClick={onClose} aria-hidden="true" />
      <div
        ref={panelRef}
        className={styles.panel}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
      >
        <header className={styles.head}>
          <h2 className={styles.title}>{title}</h2>
          <button type="button" className={styles.close} onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        {lede ? <p className={styles.lede}>{lede}</p> : null}

        <div className={styles.body}>{children}</div>
      </div>
    </>
  )
}
