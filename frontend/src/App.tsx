import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { OverviewPage } from './pages/OverviewPage'
import { SignalExplorerPage } from './pages/SignalExplorerPage'
import { ModelLabPage } from './pages/ModelLabPage'
import { ExplainabilityPage } from './pages/ExplainabilityPage'
import { LineagePage } from './pages/LineagePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 15_000,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/sinais" element={<SignalExplorerPage />} />
            <Route path="/laboratorio" element={<ModelLabPage />} />
            <Route path="/explicabilidade" element={<ExplainabilityPage />} />
            <Route path="/linhagem" element={<LineagePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
