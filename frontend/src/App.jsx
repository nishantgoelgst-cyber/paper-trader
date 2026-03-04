import { useAppContext } from './context/AppContext'
import AccountSummary from './components/Dashboard/AccountSummary'
import PositionsTable from './components/Positions/PositionsTable'
import OrderForm from './components/OrderEntry/OrderForm'
import PendingTable from './components/PendingOrders/PendingTable'
import TradeTable from './components/TradeHistory/TradeTable'
import './App.css'

function App() {
  const { state } = useAppContext()

  if (state.loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
        Loading...
      </div>
    )
  }

  return (
    <div className="app-layout">
      {/* Notification toast */}
      {state.notification && (
        <div className="notification">
          {state.notification.message}
        </div>
      )}

      {/* Left Panel: Account Summary */}
      <div className="panel left-panel">
        <AccountSummary />
      </div>

      {/* Center Panel: Pending Orders + Open Positions */}
      <div className="panel center-panel">
        <div className="status-bar">
          <span className={`ws-indicator ${state.wsConnected ? 'connected' : 'disconnected'}`} />
          {state.wsConnected ? 'Live' : 'Reconnecting...'}
        </div>
        <PendingTable />
        <PositionsTable />
      </div>

      {/* Right Panel: Order Entry */}
      <div className="panel right-panel">
        <OrderForm />
      </div>

      {/* Bottom Panel: Trade History */}
      <div className="panel bottom-panel">
        <TradeTable />
      </div>
    </div>
  )
}

export default App
