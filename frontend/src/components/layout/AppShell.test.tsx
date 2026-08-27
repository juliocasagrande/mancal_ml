import { beforeEach, describe, expect, it, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '../../test-utils'
import { AppShell } from './AppShell'

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } })),
  )
})

describe('AppShell', () => {
  it('has a skip link and every route is reachable via keyboard tab order', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <AppShell>
        <p>conteúdo da página</p>
      </AppShell>,
    )

    expect(screen.getByText('Pular para o conteúdo principal')).toBeInTheDocument()

    const expectedLabels = [
      'Visão geral',
      'Explorador de sinais',
      'Laboratório de modelos',
      'Explicabilidade',
      'Linhagem e Model Card',
    ]

    const focusedTexts: string[] = []
    for (let i = 0; i < expectedLabels.length + 2; i++) {
      await user.tab()
      focusedTexts.push(document.activeElement?.textContent ?? '')
    }

    for (const label of expectedLabels) {
      expect(focusedTexts.some((text) => text.includes(label))).toBe(true)
    }
  })
})
