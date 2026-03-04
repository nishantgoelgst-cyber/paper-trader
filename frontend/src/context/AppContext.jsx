import { createContext, useContext, useReducer, useEffect, useCallback } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { fetchApi } from '../hooks/useApi'

const AppContext = createContext()

const initialState = {
  account: null,
  positions: [],
  pendingOrders: [],
  trades: [],
  prices: {},
  wsConnected: false,
  loading: true,
  error: null,
  notification: null,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_ACCOUNT':
      return { ...state, account: action.payload }
    case 'SET_POSITIONS':
      return { ...state, positions: action.payload || [] }
    case 'SET_PENDING_ORDERS':
      return { ...state, pendingOrders: action.payload || [] }
    case 'SET_TRADES':
      return { ...state, trades: action.payload || [] }
    case 'UPDATE_PRICES':
      return { ...state, prices: { ...state.prices, ...action.payload } }
    case 'TRADE_EXECUTED':
      return {
        ...state,
        notification: action.payload,
      }
    case 'CLEAR_NOTIFICATION':
      return { ...state, notification: null }
    case 'WS_CONNECTED':
      return { ...state, wsConnected: true }
    case 'WS_DISCONNECTED':
      return { ...state, wsConnected: false }
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    default:
      return state
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  useWebSocket(dispatch)

  const refreshData = useCallback(async () => {
    try {
      const [account, positions, pendingOrders, trades] = await Promise.all([
        fetchApi('/api/account'),
        fetchApi('/api/positions?status=OPEN'),
        fetchApi('/api/orders?status=PENDING'),
        fetchApi('/api/trades'),
      ])
      dispatch({ type: 'SET_ACCOUNT', payload: account })
      dispatch({ type: 'SET_POSITIONS', payload: positions })
      dispatch({ type: 'SET_PENDING_ORDERS', payload: pendingOrders })
      dispatch({ type: 'SET_TRADES', payload: trades })
      dispatch({ type: 'SET_LOADING', payload: false })
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: err.message })
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  // Initial data load
  useEffect(() => {
    refreshData()
  }, [refreshData])

  // Re-fetch when trade is executed or WS reconnects
  useEffect(() => {
    if (state.notification) {
      refreshData()
      const timer = setTimeout(() => dispatch({ type: 'CLEAR_NOTIFICATION' }), 5000)
      return () => clearTimeout(timer)
    }
  }, [state.notification, refreshData])

  return (
    <AppContext.Provider value={{ state, dispatch, refreshData }}>
      {children}
    </AppContext.Provider>
  )
}

export function useAppContext() {
  return useContext(AppContext)
}
