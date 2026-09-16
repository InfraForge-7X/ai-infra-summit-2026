import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * The live path, exercised without a backend.
 *
 * `USING_MOCK_DATA` is read at module load, so every test here stubs the
 * environment and then imports the modules fresh. These tests intentionally
 * cover only the confirmed POST /route contract. Unsupported read endpoints
 * are not polled until a backend contract exists.
 */
