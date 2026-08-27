import { AlertTriangle, CircleHelp, Power, ShieldAlert, ShieldCheck } from 'lucide-react'
import type { MonitoringState } from '../api/types'
import styles from './StatusBadge.module.css'

const CONFIG: Record<MonitoringState, { label: string; className: string; Icon: typeof ShieldCheck }> = {
  normal: { label: 'Normal', className: styles.normal, Icon: ShieldCheck },
  attention: { label: 'Atenção', className: styles.attention, Icon: AlertTriangle },
  alert: { label: 'Alerta', className: styles.alert, Icon: ShieldAlert },
  insufficient_data: { label: 'Dados insuficientes', className: styles.neutral, Icon: CircleHelp },
  model_unavailable: { label: 'Modelo indisponível', className: styles.neutral, Icon: Power },
}

interface StatusBadgeProps {
  state: MonitoringState
  size?: 'sm' | 'md'
}

export function StatusBadge({ state, size = 'md' }: StatusBadgeProps) {
  const { label, className, Icon } = CONFIG[state]
  return (
    <span className={`${styles.badge} ${className} ${size === 'sm' ? styles.sm : ''}`}>
      <Icon aria-hidden="true" size={size === 'sm' ? 14 : 16} />
      <span>{label}</span>
    </span>
  )
}
