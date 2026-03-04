import { useAppContext } from '../../context/AppContext'
import { formatINR, formatNumber, formatTime, pnlClass } from '../../utils/formatters'

export default function TradeTable() {
  const { state } = useAppContext()
  const trades = state.trades || []

  return (
    <div>
      <div style={{ padding: '8px 12px', fontWeight: 700, fontSize: '14px', color: '#374151', borderBottom: '2px solid #e5e7eb', background: '#fff' }}>
        Trade History ({trades.length})
      </div>
      {trades.length === 0 ? (
        <div style={{ padding: '24px', textAlign: 'center', color: '#9ca3af' }}>
          No trades yet
        </div>
      ) : (
        <div style={{ overflow: 'auto', maxHeight: '240px' }}>
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Brokerage</th>
                <th>P&L</th>
                <th>Trigger</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontSize: '11px', color: '#6b7280' }}>{formatTime(t.created_at)}</td>
                  <td style={{ fontWeight: 600 }}>{t.symbol.replace('.NS', '').replace('.BO', '')}</td>
                  <td>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: t.side === 'BUY' ? '#dcfce7' : '#fef2f2',
                      color: t.side === 'BUY' ? '#16a34a' : '#dc2626',
                    }}>
                      {t.side}
                    </span>
                  </td>
                  <td>{t.quantity}</td>
                  <td>{formatNumber(t.price)}</td>
                  <td style={{ fontSize: '11px', color: '#6b7280' }}>{formatINR(t.brokerage)}</td>
                  <td className={pnlClass(t.pnl)} style={{ fontWeight: 600 }}>
                    {t.pnl != null ? formatINR(t.pnl) : '-'}
                  </td>
                  <td>
                    <span style={{
                      padding: '2px 6px',
                      borderRadius: '3px',
                      fontSize: '10px',
                      fontWeight: 600,
                      background: '#f3f4f6',
                      color: '#4b5563',
                    }}>
                      {t.trigger_type || 'MANUAL'}
                    </span>
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
