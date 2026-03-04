import { useAppContext } from '../../context/AppContext'
import { formatINR, formatNumber, pnlClass } from '../../utils/formatters'
import { fetchApi } from '../../hooks/useApi'

export default function PositionsTable() {
  const { state, refreshData } = useAppContext()
  const positions = state.positions || []

  async function handleClose(positionId) {
    if (!window.confirm('Close this position at market price?')) return
    try {
      await fetchApi(`/api/positions/${positionId}/close`, { method: 'POST' })
      refreshData()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div style={{ padding: '0' }}>
      <div style={{ padding: '8px 12px', fontWeight: 700, fontSize: '14px', color: '#374151', borderBottom: '2px solid #e5e7eb', background: '#fff' }}>
        Open Positions ({positions.length})
      </div>
      {positions.length === 0 ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>
          No open positions
        </div>
      ) : (
        <div style={{ overflow: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Rem</th>
                <th>Entry</th>
                <th>LTP</th>
                <th>Unrealized P&L</th>
                <th>Realized P&L</th>
                <th>Targets</th>
                <th>Stop Loss</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.display_name}</td>
                  <td>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: p.side === 'BUY' ? '#dcfce7' : '#fef2f2',
                      color: p.side === 'BUY' ? '#16a34a' : '#dc2626',
                    }}>
                      {p.side}
                    </span>
                  </td>
                  <td>{p.quantity}</td>
                  <td>{p.remaining_qty}</td>
                  <td>{formatNumber(p.entry_price)}</td>
                  <td style={{ fontWeight: 600 }}>{formatNumber(p.current_price)}</td>
                  <td className={pnlClass(p.unrealized_pnl)} style={{ fontWeight: 600 }}>
                    {formatINR(p.unrealized_pnl)}
                  </td>
                  <td className={pnlClass(p.realized_pnl)}>
                    {formatINR(p.realized_pnl)}
                  </td>
                  <td>
                    <TargetIndicators position={p} />
                  </td>
                  <td>
                    <SLIndicators position={p} />
                  </td>
                  <td>
                    <button
                      onClick={() => handleClose(p.id)}
                      style={{ padding: '2px 8px', fontSize: '11px' }}
                      className="danger"
                    >
                      Close
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function TargetIndicators({ position }) {
  const targets = [
    { label: 'T1', price: position.target1_price, qty: position.target1_qty, hit: position.target1_hit },
    { label: 'T2', price: position.target2_price, qty: position.target2_qty, hit: position.target2_hit },
    { label: 'T3', price: position.target3_price, qty: position.target3_qty, hit: position.target3_hit },
  ].filter(t => t.price != null)

  if (targets.length === 0) return <span style={{ color: '#9ca3af' }}>-</span>

  return (
    <div style={{ display: 'flex', gap: '3px' }}>
      {targets.map(t => (
        <span
          key={t.label}
          title={`${t.label}: ${formatNumber(t.price)} (${t.qty} qty)`}
          style={{
            padding: '1px 4px',
            borderRadius: '2px',
            fontSize: '10px',
            fontWeight: 600,
            background: t.hit ? '#16a34a' : '#e5e7eb',
            color: t.hit ? '#fff' : '#6b7280',
          }}
        >
          {t.label}
        </span>
      ))}
    </div>
  )
}

function SLIndicators({ position }) {
  if (position.sl_mode === 'TRAILING') {
    return (
      <span
        title={`Trailing SL: ${formatNumber(position.trailing_sl_current)} (High: ${formatNumber(position.trailing_sl_high)}, Points: ${position.trailing_sl_points})`}
        style={{
          padding: '1px 4px',
          borderRadius: '2px',
          fontSize: '10px',
          fontWeight: 600,
          background: '#fef2f2',
          color: '#dc2626',
        }}
      >
        TSL: {formatNumber(position.trailing_sl_current)}
      </span>
    )
  }

  const sls = [
    { label: 'SL1', price: position.sl1_price, qty: position.sl1_qty, hit: position.sl1_hit },
    { label: 'SL2', price: position.sl2_price, qty: position.sl2_qty, hit: position.sl2_hit },
    { label: 'SL3', price: position.sl3_price, qty: position.sl3_qty, hit: position.sl3_hit },
  ].filter(s => s.price != null)

  if (sls.length === 0) return <span style={{ color: '#9ca3af' }}>-</span>

  return (
    <div style={{ display: 'flex', gap: '3px' }}>
      {sls.map(s => (
        <span
          key={s.label}
          title={`${s.label}: ${formatNumber(s.price)} (${s.qty} qty)`}
          style={{
            padding: '1px 4px',
            borderRadius: '2px',
            fontSize: '10px',
            fontWeight: 600,
            background: s.hit ? '#dc2626' : '#e5e7eb',
            color: s.hit ? '#fff' : '#6b7280',
          }}
        >
          {s.label}
        </span>
      ))}
    </div>
  )
}
