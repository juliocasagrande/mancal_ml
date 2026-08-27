import type { ReactNode } from 'react'
import { AlertOctagon, Inbox, Loader2 } from 'lucide-react'
import { ApiError } from '../api/client'
import styles from './StateBoundary.module.css'

interface StateBoundaryProps {
  isLoading: boolean
  isError: boolean
  error?: unknown
  isEmpty?: boolean
  emptyLabel?: string
  loadingLabel?: string
  onRetry?: () => void
  children: ReactNode
}

/** Wrapper único para loading/erro/vazio — Seção 16 do blueprint exige que
 * toda página trate esses estados; nenhuma página os implementa solto. */
export function StateBoundary({
  isLoading,
  isError,
  error,
  isEmpty = false,
  emptyLabel = 'Sem dados para exibir.',
  loadingLabel = 'Carregando…',
  onRetry,
  children,
}: StateBoundaryProps) {
  if (isLoading) {
    return (
      <div className={styles.state} role="status" aria-live="polite">
        <Loader2 className={styles.spinner} aria-hidden="true" size={22} />
        <span>{loadingLabel}</span>
      </div>
    )
  }

  if (isError) {
    const message = error instanceof ApiError ? error.message : 'Não foi possível carregar os dados.'
    return (
      <div className={styles.state} role="alert">
        <AlertOctagon aria-hidden="true" size={22} />
        <span>{message}</span>
        {onRetry && (
          <button type="button" className={styles.retryButton} onClick={onRetry}>
            Tentar novamente
          </button>
        )}
      </div>
    )
  }

  if (isEmpty) {
    return (
      <div className={styles.state}>
        <Inbox aria-hidden="true" size={22} />
        <span>{emptyLabel}</span>
      </div>
    )
  }

  return <>{children}</>
}
