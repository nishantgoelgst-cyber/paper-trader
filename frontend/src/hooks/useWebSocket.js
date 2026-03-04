import { useEffect, useRef } from 'react'

export function useWebSocket(dispatch) {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  useEffect(() => {
    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        dispatch({ type: 'WS_CONNECTED' })
      }

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          switch (msg.type) {
            case 'price_update':
              dispatch({ type: 'UPDATE_PRICES', payload: msg.data.prices })
              break
            case 'position_update':
              dispatch({ type: 'SET_POSITIONS', payload: msg.data.positions })
              break
            case 'trade_executed':
              dispatch({ type: 'TRADE_EXECUTED', payload: msg.data })
              break
          }
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        dispatch({ type: 'WS_DISCONNECTED' })
        reconnectTimer.current = setTimeout(connect, 3000)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [dispatch])
}
