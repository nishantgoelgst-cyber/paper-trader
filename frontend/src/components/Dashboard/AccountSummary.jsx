import { useState } from 'react'
import { useAppContext } from '../../context/AppContext'
import { formatINR, formatPct, pnlClass } from '../../utils/formatters'
import { fetchApi } from '../../hooks/useApi'

export default function AccountSummary() {
  const { state, refreshData } = useAppContext()
  const { account } = state
  const [addFundsAmount, setAddFundsAmount] = useState('')
  const [showAddFunds, setShowAddFunds] = useState(false)

  if (!account) return <div>Loading...</div>

  async function handleAddFunds() {
    const amount = parseFloat(addFundsAmount)
    if (!amount || amount <= 0) return
    try {
      await fetchApi('/api/account/add-funds', {
        method: 'POST',
        body: JSON.stringify({ amount }),
      })
      setAddFundsAmount('')
      setShowAddFunds(false)
      refreshData()
    } catch (err) {
      alert(err.message)
    }
  }

  async function handleReset() {
    if (!window.confirm('Reset account? This will delete all positions, orders, and trades.')) return
    try {
      await fetchApi('/api/account/reset', { method: 'POST' })
      refreshData()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div>
      <div className="panel-header">Account Summary</div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <StatRow label="Initial Capital" value={formatINR(account.initial_balance)} />
        <StatRow label="Cash Balance" value={formatINR(account.cash_balance)} />
        <StatRow label="Equity" value={formatINR(account.equity)} bold />

        <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb' }} />

        <StatRow label="Market Value" value={formatINR(account.market_value)} />
        <StatRow
          label="Unrealized P&L"
          value={formatINR(account.unrealized_pnl)}
          className={pnlClass(account.unrealized_pnl)}
        />
        <StatRow
          label="Realized P&L"
          value={formatINR(account.realized_pnl)}
          className={pnlClass(account.realized_pnl)}
        />

        <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb' }} />

        <StatRow
          label="Total P&L"
          value={formatINR(account.total_pnl)}
          className={pnlClass(account.total_pnl)}
          bold
        />
        <StatRow
          label="Total Return"
          value={formatPct(account.total_pnl_pct)}
          className={pnlClass(account.total_pnl_pct)}
        />
        <StatRow label="Open Positions" value={account.open_positions_count} />

        <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb' }} />

        <div style={{ display: 'flex', gap: '6px' }}>
          <button onClick={() => setShowAddFunds(!showAddFunds)} style={{ flex: 1 }}>
            Add Funds
          </button>
          <button onClick={handleReset} className="danger" style={{ flex: 1 }}>
            Reset
          </button>
        </div>

        {showAddFunds && (
          <div style={{ display: 'flex', gap: '6px' }}>
            <input
              type="number"
              placeholder="Amount"
              value={addFundsAmount}
              onChange={(e) => setAddFundsAmount(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="primary" onClick={handleAddFunds}>Add</button>
          </div>
        )}
      </div>
    </div>
  )
}

function StatRow({ label, value, className, bold }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: '#6b7280', fontSize: '12px' }}>{label}</span>
      <span
        className={className || ''}
        style={{ fontWeight: bold ? 700 : 500, fontSize: bold ? '14px' : '13px' }}
      >
        {value}
      </span>
    </div>
  )
}
