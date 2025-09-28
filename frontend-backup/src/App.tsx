import { useEffect, useState } from 'react'
import './App.css'
import { getHealth } from './lib/api'

function App() {
  const [status, setStatus] = useState<string>('loading...')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then((res) => setStatus(res.status))
      .catch((e) => setError(String(e)))
  }, [])

  return (
    <div style={{ padding: 24, fontFamily: 'system-ui, sans-serif' }}>
      <h1>MHacks Rental AI</h1>
      <p>Backend health: {error ? `error: ${error}` : status}</p>
      <p style={{ marginTop: 16 }}>
        Update <code>frontend/.env</code> to point <code>VITE_API_BASE</code> at your backend if needed.
      </p>
    </div>
  )
}

export default App
