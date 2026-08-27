import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StateBoundary } from './StateBoundary'

describe('StateBoundary', () => {
  it('shows a loading indicator while loading', () => {
    render(
      <StateBoundary isLoading isError={false}>
        <p>conteúdo</p>
      </StateBoundary>,
    )
    expect(screen.getByRole('status')).toBeInTheDocument()
    expect(screen.queryByText('conteúdo')).not.toBeInTheDocument()
  })

  it('shows an error message and retry button on error', () => {
    render(
      <StateBoundary isLoading={false} isError onRetry={() => {}}>
        <p>conteúdo</p>
      </StateBoundary>,
    )
    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /tentar novamente/i })).toBeInTheDocument()
  })

  it('shows the empty label when isEmpty is true', () => {
    render(
      <StateBoundary isLoading={false} isError={false} isEmpty emptyLabel="Nada por aqui">
        <p>conteúdo</p>
      </StateBoundary>,
    )
    expect(screen.getByText('Nada por aqui')).toBeInTheDocument()
  })

  it('renders children when loaded, without error, and not empty', () => {
    render(
      <StateBoundary isLoading={false} isError={false}>
        <p>conteúdo</p>
      </StateBoundary>,
    )
    expect(screen.getByText('conteúdo')).toBeInTheDocument()
  })
})
