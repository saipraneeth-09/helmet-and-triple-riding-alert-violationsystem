'use client'

import { useState } from 'react'
import { HelmetDetector } from '../components/HelmetDetector'
import { AlertLog } from '../components/AlertLog'

export default function Home() {
  const [alerts, setAlerts] = useState<string[]>([])

  const addAlert = (message: string) => {
    setAlerts(prev => [...prev, message])
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-8">Helmet Detection System</h1>
      <div className="w-full max-w-3xl">
        <HelmetDetector onAlert={addAlert} />
        <AlertLog alerts={alerts} />
      </div>
    </main>
  )
}

