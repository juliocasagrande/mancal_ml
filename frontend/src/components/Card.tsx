import type { ReactNode } from 'react'
import styles from './Card.module.css'

interface CardProps {
  title?: string
  description?: string
  children: ReactNode
  className?: string
}

export function Card({ title, description, children, className }: CardProps) {
  return (
    <section className={`${styles.card} ${className ?? ''}`} aria-label={title}>
      {title && <h2 className={styles.title}>{title}</h2>}
      {description && <p className={styles.description}>{description}</p>}
      <div className={styles.body}>{children}</div>
    </section>
  )
}
