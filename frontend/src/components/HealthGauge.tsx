import { useReducedMotion, motion } from 'framer-motion'
import styles from './HealthGauge.module.css'

interface HealthGaugeProps {
  value: number
}

function colorFor(value: number): string {
  if (value >= 70) return 'var(--color-normal)'
  if (value >= 40) return 'var(--color-attention)'
  return 'var(--color-alert)'
}

export function HealthGauge({ value }: HealthGaugeProps) {
  const reduceMotion = useReducedMotion()
  const clamped = Math.max(0, Math.min(100, value))
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - clamped / 100)
  const color = colorFor(clamped)

  return (
    <div className={styles.wrapper}>
      <svg viewBox="0 0 170 170" className={styles.svg} role="img" aria-label={`Índice de saúde: ${clamped.toFixed(0)} de 100`}>
        <circle cx="85" cy="85" r={radius} className={styles.track} />
        <motion.circle
          cx="85"
          cy="85"
          r={radius}
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          initial={reduceMotion ? { strokeDashoffset: offset } : { strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: reduceMotion ? 0 : 0.8, ease: 'easeOut' }}
          transform="rotate(-90 85 85)"
        />
      </svg>
      <div className={styles.value}>
        <span className={styles.number}>{clamped.toFixed(0)}</span>
        <span className={styles.unit}>/ 100</span>
      </div>
    </div>
  )
}
