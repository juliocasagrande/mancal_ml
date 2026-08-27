import { useId, useState, type ReactNode } from 'react'
import { Table2 } from 'lucide-react'
import styles from './ChartWithFallback.module.css'

interface Column {
  key: string
  label: string
}

interface ChartWithFallbackProps {
  title: string
  columns: Column[]
  rows: Array<Record<string, string | number>>
  children: ReactNode
}

/** Todo gráfico Recharts fica dentro deste wrapper: alterna para uma
 * tabela equivalente, exigida pela Seção 16 do blueprint como alternativa
 * acessível ("gráficos com descrição textual ou tabela alternativa"). */
export function ChartWithFallback({ title, columns, rows, children }: ChartWithFallbackProps) {
  const [showTable, setShowTable] = useState(false)
  const regionId = useId()

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.toggle}
          aria-pressed={showTable}
          aria-controls={regionId}
          onClick={() => setShowTable((s) => !s)}
        >
          <Table2 size={14} aria-hidden="true" />
          {showTable ? 'Ver gráfico' : 'Ver como tabela'}
        </button>
      </div>
      <div id={regionId}>
        {showTable ? (
          <div className={styles.tableScroll}>
            <table>
              <caption className="visually-hidden">{title}</caption>
              <thead>
                <tr>
                  {columns.map((c) => (
                    <th key={c.key} scope="col">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    {columns.map((c) => (
                      <td key={c.key}>{row[c.key]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  )
}
