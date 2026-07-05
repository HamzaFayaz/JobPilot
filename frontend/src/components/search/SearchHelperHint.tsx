import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getWorkerStatus } from '../../api/worker'

interface SearchHelperHintProps {
  onConnectedChange?: (connected: boolean) => void
}

export function SearchHelperHint({ onConnectedChange }: SearchHelperHintProps) {
  const [connected, setConnected] = useState<boolean | null>(null)

  useEffect(() => {
    let active = true

    const refresh = async () => {
      try {
        const status = await getWorkerStatus()
        if (!active) return
        setConnected(status.connected)
        onConnectedChange?.(status.connected)
      } catch {
        if (!active) return
        setConnected(false)
        onConnectedChange?.(false)
      }
    }

    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, 5000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [onConnectedChange])

  if (connected !== false) {
    return null
  }

  return (
    <p className="text-sm text-text-secondary">
      Connect Search Helper in{' '}
      <Link to="/settings" className="font-medium text-primary hover:underline">
        Settings
      </Link>{' '}
      to run browser search on this PC.
    </p>
  )
}
