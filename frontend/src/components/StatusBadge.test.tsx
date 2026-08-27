import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from './StatusBadge'
import type { MonitoringState } from '../api/types'

const STATES: MonitoringState[] = ['normal', 'attention', 'alert', 'insufficient_data', 'model_unavailable']

describe('StatusBadge', () => {
  it('gives each state a unique, non-empty text label (not color alone)', () => {
    const labels = STATES.map((state) => {
      const { container, unmount } = render(<StatusBadge state={state} />)
      const text = container.textContent
      unmount()
      return text
    })
    for (const text of labels) {
      expect(text).toBeTruthy()
    }
    expect(new Set(labels).size).toBe(STATES.length)
  })
})
