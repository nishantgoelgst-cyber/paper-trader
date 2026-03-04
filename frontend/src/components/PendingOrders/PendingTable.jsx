import { useAppContext } from '../../context/AppContext'
import { formatNumber } from '../../utils/formatters'
import { fetchApi } from '../../hooks/useApi'

export default function PendingTable() {
  const { state, refreshData } = useAppContext()
  const pendingOrders = state.pendingOrders || []

  if (pendingOrders.length === 0) return null

  async function handleCancel(orderId) {
    if (!window.confirm('Cancel this GTT order?')) return
    try {
      await fetchApi(`/api/orders/${orderId}`, { method: 'DELETE' })
      refreshData()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <div>
      <div style={{ padding: '8px 12px', fontWeight: 700, fontSize: '13px', color: '#92400e', background: '#fef3c7', borderBottom: '1px solid #fde68a' }}>
        Pending GTT Orders ({pendingOrders.length})
      </div>
      <div style={{ overflow: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Side</th>
              <th>Qty</th>
              <th>Entry Zone</th>
              <th>Preferred</th>
              <th>Targets</th>
              <th>SL</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {pendingOrders.map((o) => (
              <tr key={o.id}>
                <td style={{ fontWeight: 600 }}>{o.display_name}</td>
                <td>
                  <span style={{
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontSize: '11px',
                    fontWeight: 600,
                    background: o.side === 'BUY' ? '#dcfce7' : '#fef2f2',
                    color: o.side === 'BUY' ? '#16a34a' : '#dc2626',
                  }}>
                    {o.side}
                  </span>
                </td>
                <td>{o.quantity}</td>
                <td>{formatNumber(o.entry_price_low)} - {formatNumber(o.entry_price_high)}</td>
                <td>{formatNumber(o.entry_price_preferred)}</td>
                <td style={{ fontSize: '11px' }}>
                  {[
                    o.target1_price && `T1:${formatNumber(o.target1_price)}(${o.target1_qty})`,
                    o.target2_price && `T2:${formatNumber(o.target2_price)}(${o.target2_qty})`,
                    o.target3_price && `T3:${formatNumber(o.target3_price)}(${o.target3_qty})`,
                  ].filter(Boolean).join(' ') || '-'}
                </td>
                <td style={{ fontSize: '11px' }}>
                  {o.sl_mode === 'TRAILING'
                    ? `Trail: ${o.trailing_sl_points}pts`
                    : [
                        o.sl1_price && `SL1:${formatNumber(o.sl1_price)}(${o.sl1_qty})`,
                        o.sl2_price && `SL2:${formatNumber(o.sl2_price)}(${o.sl2_qty})`,
                        o.sl3_price && `SL3:${formatNumber(o.sl3_price)}(${o.sl3_qty})`,
                      ].filter(Boolean).join(' ') || '-'
                  }
                </td>
                <td>
                  <button
                    onClick={() => handleCancel(o.id)}
                    style={{ padding: '2px 8px', fontSize: '11px' }}
                  >
                    Cancel
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
