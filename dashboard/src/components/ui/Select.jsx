import { ArrowDown01Icon, Tick02Icon } from '@hugeicons/core-free-icons'
import { useEffect, useId, useRef, useState } from 'react'

import { Icon } from './ui.jsx'
import styles from './Select.module.css'

/**
 * Type-ahead matching, kept at module scope: it reads the clock, which is not
 * something to do inside a component body even on a path that only ever runs
 * from a keystroke.
 *
 * @param {{ buffer: string, at: number }} state  Mutated in place
 * @param {string} key
 * @param {{ value: string, label?: string }[]} options
 * @returns {number} Index of the first match, or -1
 */
function matchTypeahead(state, key, options) {
  const now = Date.now()
  state.buffer = now - state.at > 800 ? key : state.buffer + key
  state.at = now
  return options.findIndex((option) =>
    (option.label ?? option.value).toLowerCase().startsWith(state.buffer.toLowerCase()),
  )
}

/**
 * Listbox select.
 *
 * A native <select> renders the operating system's own menu, so the same build
 * looks like Windows on one machine and macOS on another — neither of which is
 * this design system. This replaces it with a menu built from the tokens:
 * selection marked with a tick rather than a highlight, so the chosen row reads
 * the same whether or not it is also hovered.
 *
 * Replacing a native control means re-implementing what it gave for free, so:
 * combobox/listbox roles, arrow keys, Home/End, type-ahead, Enter and Escape,
 * click-outside, and focus returning to the trigger on close.
 *
 * Escape stops here rather than bubbling — inside a Drawer it would otherwise
 * close the drawer as well as the menu, which is never what someone means.
 *
 * @param {object} props
 * @param {string} props.id
 * @param {string} props.value
 * @param {{ value: string, label?: string }[]} props.options
 * @param {(value: string) => void} props.onChange
 * @param {string} props.label  Accessible name, mirrors the visible <label>
 */
export default function Select({ id, value, options, onChange, label }) {
  const [open, setOpen] = useState(false)
  const [activeIndex, setActiveIndex] = useState(() =>
    Math.max(0, options.findIndex((option) => option.value === value)),
  )
  const rootRef = useRef(/** @type {HTMLDivElement | null} */ (null))
  const triggerRef = useRef(/** @type {HTMLButtonElement | null} */ (null))
  const listId = useId()
  const typeahead = useRef({ buffer: '', at: 0 })

  const selected = options.find((option) => option.value === value)

  useEffect(() => {
    if (!open) return undefined

    /** @param {MouseEvent} event */
    const onPointerDown = (event) => {
      if (!rootRef.current?.contains(/** @type {Node} */ (event.target))) setOpen(false)
    }
    document.addEventListener('mousedown', onPointerDown)
    return () => document.removeEventListener('mousedown', onPointerDown)
  }, [open])

  const close = ({ refocus = true } = {}) => {
    setOpen(false)
    if (refocus) triggerRef.current?.focus()
  }

  /** @param {number} index */
  const choose = (index) => {
    const option = options[index]
    if (!option) return
    onChange(option.value)
    setActiveIndex(index)
    close()
  }

  /** @param {React.KeyboardEvent} event */
  const onKeyDown = (event) => {
    const { key } = event

    if (!open) {
      if (key === 'ArrowDown' || key === 'ArrowUp' || key === 'Enter' || key === ' ') {
        event.preventDefault()
        setOpen(true)
      }
      return
    }

    if (key === 'Escape') {
      // Do not let the Drawer's own Escape handler see this.
      event.preventDefault()
      event.stopPropagation()
      close()
      return
    }

    if (key === 'Enter' || key === ' ') {
      event.preventDefault()
      choose(activeIndex)
      return
    }

    if (key === 'ArrowDown' || key === 'ArrowUp') {
      event.preventDefault()
      const step = key === 'ArrowDown' ? 1 : -1
      setActiveIndex((index) => (index + step + options.length) % options.length)
      return
    }

    if (key === 'Home' || key === 'End') {
      event.preventDefault()
      setActiveIndex(key === 'Home' ? 0 : options.length - 1)
      return
    }

    if (key === 'Tab') {
      close({ refocus: false })
      return
    }

    // Type-ahead, the one native behaviour people miss most.
    if (key.length === 1 && !event.metaKey && !event.ctrlKey) {
      const match = matchTypeahead(typeahead.current, key, options)
      if (match >= 0) setActiveIndex(match)
    }
  }

  return (
    <div className={styles.root} ref={rootRef} onKeyDown={onKeyDown}>
      <button
        type="button"
        id={id}
        ref={triggerRef}
        className={styles.trigger}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-haspopup="listbox"
        aria-label={label}
        onClick={() => setOpen((wasOpen) => !wasOpen)}
      >
        <span className={styles.value}>{selected?.label ?? selected?.value ?? ''}</span>
        <span className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`}>
          <Icon icon={ArrowDown01Icon} size={16} />
        </span>
      </button>

      {open ? (
        <ul className={styles.menu} id={listId} role="listbox" aria-label={label}>
          {options.map((option, index) => {
            const isSelected = option.value === value
            return (
              <li key={option.value} role="none">
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`${styles.option} ${index === activeIndex ? styles.active : ''}`}
                  onClick={() => choose(index)}
                  onMouseEnter={() => setActiveIndex(index)}
                  tabIndex={-1}
                >
                  <span className={styles.tick} aria-hidden="true">
                    {isSelected ? <Icon icon={Tick02Icon} size={14} /> : null}
                  </span>
                  {option.label ?? option.value}
                </button>
              </li>
            )
          })}
        </ul>
      ) : null}
    </div>
  )
}
