import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { Activity, FlaskConical, Gauge, ListTree, Radio } from 'lucide-react'
import { useModels, useMonitoringCurrent } from '../../api/hooks'
import { StatusBadge } from '../StatusBadge'
import styles from './AppShell.module.css'

const NAV_ITEMS = [
  { to: '/', label: 'Visão geral', Icon: Gauge, end: true },
  { to: '/sinais', label: 'Explorador de sinais', Icon: Activity },
  { to: '/laboratorio', label: 'Laboratório de modelos', Icon: FlaskConical },
  { to: '/explicabilidade', label: 'Explicabilidade', Icon: Radio },
  { to: '/linhagem', label: 'Linhagem e Model Card', Icon: ListTree },
]

export function AppShell({ children }: { children: ReactNode }) {
  const { data: models } = useModels()
  const activeModel = models?.find((m) => m.status === 'active')
  const { data: monitoring } = useMonitoringCurrent()

  return (
    <div className={styles.shell}>
      <a href="#conteudo-principal" className="skip-link">
        Pular para o conteúdo principal
      </a>

      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true">
            <span className={styles.brandMarkDiamond} />
          </span>
          <div>
            <div className={styles.brandTitle}>Mancal Guard</div>
            <div className={styles.brandSubtitle}>Mancal-guia · Unidade G1</div>
          </div>
        </div>
        <div className={styles.headerStatus}>
          {activeModel ? (
            <>
              <span className={styles.modelInfo}>
                Modelo ativo: <strong>{activeModel.name}</strong>
              </span>
              <StatusBadge state={monitoring?.state ?? 'insufficient_data'} size="sm" />
            </>
          ) : (
            <StatusBadge state="model_unavailable" size="sm" />
          )}
        </div>
      </header>

      <nav className={styles.nav} aria-label="Navegação principal">
        <ul>
          {NAV_ITEMS.map(({ to, label, Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <main id="conteudo-principal" className={styles.main} tabIndex={-1}>
        {children}
      </main>
    </div>
  )
}
