import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test-utils'
import { OverviewPage } from './OverviewPage'

const ALERT = {
  id: 'alert-1',
  prediction_run_id: 'pred-1',
  severity: 'alert' as const,
  reason: 'Score acima do limiar',
  acknowledged: false,
  acknowledged_at: null,
  notes: null,
  window_start: '2020-10-11T00:00:00Z',
  window_end: '2020-10-11T06:00:00Z',
}

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } })
}

function mockFetch() {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input.toString()
    if (url.includes('/api/monitoring/current')) {
      return jsonResponse({
        state: 'normal',
        health_index: 82,
        anomaly_score: 1.2,
        threshold: 3.5,
        window_start: '2020-10-11T00:00:00Z',
        window_end: '2020-10-11T06:00:00Z',
        model_name: 'lstm_autoencoder',
        model_id: 'model-1',
        feature_contributions: {},
      })
    }
    if (url.includes('/api/alerts')) {
      return jsonResponse([ALERT])
    }
    if (url.includes('/api/datasets') && url.includes('/quality')) {
      return jsonResponse({ status: 'success', row_count: 100, pipeline_version: 'v1', quality_report: {} })
    }
    if (url.includes('/api/datasets')) {
      return jsonResponse([{ id: 'dataset-1', name: 'Dataset', source_url: '', license: '', version: 'v1', time_start: null, time_end: null, metadata: {} }])
    }
    return jsonResponse({})
  })
}

describe('OverviewPage', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch())
  })

  it('renders the health state and pending alert once loaded', async () => {
    renderWithProviders(<OverviewPage />)

    await waitFor(() => expect(screen.getByText('Score acima do limiar')).toBeInTheDocument())
    expect(screen.getByText('82')).toBeInTheDocument()
  })

  it('acknowledges an alert on button click', async () => {
    const user = userEvent.setup()
    renderWithProviders(<OverviewPage />)

    await waitFor(() => expect(screen.getByText('Score acima do limiar')).toBeInTheDocument())
    await user.click(screen.getByRole('button', { name: /reconhecer/i }))

    await waitFor(() => {
      const calls = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls as Array<[RequestInfo | URL, RequestInit | undefined]>
      expect(calls.some(([input, init]) => String(input).includes('/api/alerts/alert-1') && init?.method === 'PATCH')).toBe(true)
    })
  })
})
