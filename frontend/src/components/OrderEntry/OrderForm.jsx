import { useState } from 'react'
import { useAppContext } from '../../context/AppContext'
import { fetchApi } from '../../hooks/useApi'
import { formatINR, formatNumber } from '../../utils/formatters'

const INITIAL_FORM = {
  symbol: '',
  side: 'BUY',
  orderType: 'GTT',
  quantity: '',
  entryLow: '',
  entryHigh: '',
  entryPreferred: '',
  t1Price: '', t1Qty: '',
  t2Price: '', t2Qty: '',
  t3Price: '', t3Qty: '',
  slMode: 'FIXED',
  sl1Price: '', sl1Qty: '',
  sl2Price: '', sl2Qty: '',
  sl3Price: '', sl3Qty: '',
  trailingSLPoints: '',
}

export default function OrderForm() {
  const { refreshData } = useAppContext()
  const [form, setForm] = useState(INITIAL_FORM)
  const [ltp, setLtp] = useState(null)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function set(field) {
    return (e) => setForm({ ...form, [field]: e.target.value })
  }

  async function lookupSymbol() {
    if (!form.symbol.trim()) return
    setSearching(true)
    setError('')
    try {
      const symbol = form.symbol.toUpperCase().trim()
      const fullSymbol = symbol.endsWith('.NS') || symbol.endsWith('.BO') ? symbol : `${symbol}.NS`
      const data = await fetchApi(`/api/price/${fullSymbol}`)
      setLtp(data.price)
      setForm({ ...form, symbol: fullSymbol })
    } catch (err) {
      setLtp(null)
      setError(`Symbol not found: ${form.symbol}`)
    }
    setSearching(false)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    const qty = parseInt(form.quantity)
    if (!qty || qty <= 0) {
      setError('Enter valid quantity')
      return
    }

    // Validate target quantities
    const t1Qty = parseInt(form.t1Qty) || 0
    const t2Qty = parseInt(form.t2Qty) || 0
    const t3Qty = parseInt(form.t3Qty) || 0
    const totalTargetQty = t1Qty + t2Qty + t3Qty
    if (totalTargetQty > 0 && totalTargetQty !== qty) {
      setError(`Target quantities (${totalTargetQty}) must equal order quantity (${qty})`)
      return
    }

    // Validate SL quantities
    if (form.slMode === 'FIXED') {
      const sl1Qty = parseInt(form.sl1Qty) || 0
      const sl2Qty = parseInt(form.sl2Qty) || 0
      const sl3Qty = parseInt(form.sl3Qty) || 0
      const totalSLQty = sl1Qty + sl2Qty + sl3Qty
      if (totalSLQty > 0 && totalSLQty !== qty) {
        setError(`SL quantities (${totalSLQty}) must equal order quantity (${qty})`)
        return
      }
    }

    const body = {
      symbol: form.symbol,
      side: form.side,
      order_type: form.orderType,
      quantity: qty,
    }

    if (form.orderType === 'GTT') {
      if (!form.entryLow || !form.entryHigh) {
        setError('GTT orders require entry price zone')
        return
      }
      body.entry_price_low = parseFloat(form.entryLow)
      body.entry_price_high = parseFloat(form.entryHigh)
      if (form.entryPreferred) body.entry_price_preferred = parseFloat(form.entryPreferred)
    }

    // Targets
    if (form.t1Price && form.t1Qty) body.target1 = { price: parseFloat(form.t1Price), qty: parseInt(form.t1Qty) }
    if (form.t2Price && form.t2Qty) body.target2 = { price: parseFloat(form.t2Price), qty: parseInt(form.t2Qty) }
    if (form.t3Price && form.t3Qty) body.target3 = { price: parseFloat(form.t3Price), qty: parseInt(form.t3Qty) }

    // Stop losses
    body.sl_mode = form.slMode
    if (form.slMode === 'FIXED') {
      if (form.sl1Price && form.sl1Qty) body.sl1 = { price: parseFloat(form.sl1Price), qty: parseInt(form.sl1Qty) }
      if (form.sl2Price && form.sl2Qty) body.sl2 = { price: parseFloat(form.sl2Price), qty: parseInt(form.sl2Qty) }
      if (form.sl3Price && form.sl3Qty) body.sl3 = { price: parseFloat(form.sl3Price), qty: parseInt(form.sl3Qty) }
    } else {
      if (!form.trailingSLPoints) {
        setError('Trailing SL requires points value')
        return
      }
      body.trailing_sl_points = parseFloat(form.trailingSLPoints)
    }

    setSubmitting(true)
    try {
      await fetchApi('/api/orders', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      setForm(INITIAL_FORM)
      setLtp(null)
      refreshData()
    } catch (err) {
      setError(err.message)
    }
    setSubmitting(false)
  }

  return (
    <div>
      <div className="panel-header">Place Order</div>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Symbol */}
        <div>
          <label style={labelStyle}>Symbol</label>
          <div style={{ display: 'flex', gap: '4px' }}>
            <input
              type="text"
              placeholder="e.g. RELIANCE"
              value={form.symbol}
              onChange={set('symbol')}
              onBlur={lookupSymbol}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), lookupSymbol())}
              style={{ flex: 1 }}
            />
            <button type="button" onClick={lookupSymbol} disabled={searching}>
              {searching ? '...' : 'Lookup'}
            </button>
          </div>
          {ltp && (
            <div style={{ marginTop: '4px', fontSize: '12px', color: '#16a34a', fontWeight: 600 }}>
              LTP: {formatINR(ltp)}
            </div>
          )}
        </div>

        {/* Side + Order Type */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Side</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                className={form.side === 'BUY' ? 'buy-btn' : ''}
                onClick={() => setForm({ ...form, side: 'BUY' })}
                style={{ flex: 1 }}
              >
                BUY
              </button>
              <button
                type="button"
                className={form.side === 'SELL' ? 'sell-btn' : ''}
                onClick={() => setForm({ ...form, side: 'SELL' })}
                style={{ flex: 1 }}
              >
                SELL
              </button>
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Type</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                className={form.orderType === 'GTT' ? 'primary' : ''}
                onClick={() => setForm({ ...form, orderType: 'GTT' })}
                style={{ flex: 1 }}
              >
                GTT
              </button>
              <button
                type="button"
                className={form.orderType === 'MARKET' ? 'primary' : ''}
                onClick={() => setForm({ ...form, orderType: 'MARKET' })}
                style={{ flex: 1 }}
              >
                Market
              </button>
            </div>
          </div>
        </div>

        {/* Quantity */}
        <div>
          <label style={labelStyle}>Quantity</label>
          <input type="number" placeholder="100" value={form.quantity} onChange={set('quantity')} min="1" />
        </div>

        {/* Entry Price Zone (GTT only) */}
        {form.orderType === 'GTT' && (
          <div style={{ background: '#f0f9ff', padding: '8px', borderRadius: '4px' }}>
            <label style={{ ...labelStyle, color: '#0369a1' }}>Entry Price Zone</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <input type="number" placeholder="Low" value={form.entryLow} onChange={set('entryLow')} step="0.05" />
              <input type="number" placeholder="High" value={form.entryHigh} onChange={set('entryHigh')} step="0.05" />
              <input type="number" placeholder="Preferred" value={form.entryPreferred} onChange={set('entryPreferred')} step="0.05" />
            </div>
          </div>
        )}

        {/* Targets */}
        <div style={{ background: '#f0fdf4', padding: '8px', borderRadius: '4px' }}>
          <label style={{ ...labelStyle, color: '#16a34a' }}>Targets (Price + Qty)</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <span style={levelLabel}>T1</span>
              <input type="number" placeholder="Price" value={form.t1Price} onChange={set('t1Price')} step="0.05" />
              <input type="number" placeholder="Qty" value={form.t1Qty} onChange={set('t1Qty')} min="0" style={{ width: '70px' }} />
            </div>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <span style={levelLabel}>T2</span>
              <input type="number" placeholder="Price" value={form.t2Price} onChange={set('t2Price')} step="0.05" />
              <input type="number" placeholder="Qty" value={form.t2Qty} onChange={set('t2Qty')} min="0" style={{ width: '70px' }} />
            </div>
            <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
              <span style={levelLabel}>T3</span>
              <input type="number" placeholder="Price" value={form.t3Price} onChange={set('t3Price')} step="0.05" />
              <input type="number" placeholder="Qty" value={form.t3Qty} onChange={set('t3Qty')} min="0" style={{ width: '70px' }} />
            </div>
          </div>
        </div>

        {/* Stop Loss Mode Toggle */}
        <div style={{ background: '#fef2f2', padding: '8px', borderRadius: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <label style={{ ...labelStyle, color: '#dc2626', margin: 0 }}>Stop Loss</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                onClick={() => setForm({ ...form, slMode: 'FIXED' })}
                style={{
                  padding: '2px 8px', fontSize: '11px',
                  background: form.slMode === 'FIXED' ? '#dc2626' : '#fff',
                  color: form.slMode === 'FIXED' ? '#fff' : '#6b7280',
                  border: '1px solid #d1d5db',
                }}
              >
                Fixed
              </button>
              <button
                type="button"
                onClick={() => setForm({ ...form, slMode: 'TRAILING' })}
                style={{
                  padding: '2px 8px', fontSize: '11px',
                  background: form.slMode === 'TRAILING' ? '#dc2626' : '#fff',
                  color: form.slMode === 'TRAILING' ? '#fff' : '#6b7280',
                  border: '1px solid #d1d5db',
                }}
              >
                Trailing
              </button>
            </div>
          </div>

          {form.slMode === 'FIXED' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span style={levelLabel}>SL1</span>
                <input type="number" placeholder="Price" value={form.sl1Price} onChange={set('sl1Price')} step="0.05" />
                <input type="number" placeholder="Qty" value={form.sl1Qty} onChange={set('sl1Qty')} min="0" style={{ width: '70px' }} />
              </div>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span style={levelLabel}>SL2</span>
                <input type="number" placeholder="Price" value={form.sl2Price} onChange={set('sl2Price')} step="0.05" />
                <input type="number" placeholder="Qty" value={form.sl2Qty} onChange={set('sl2Qty')} min="0" style={{ width: '70px' }} />
              </div>
              <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                <span style={levelLabel}>SL3</span>
                <input type="number" placeholder="Price" value={form.sl3Price} onChange={set('sl3Price')} step="0.05" />
                <input type="number" placeholder="Qty" value={form.sl3Qty} onChange={set('sl3Qty')} min="0" style={{ width: '70px' }} />
              </div>
            </div>
          ) : (
            <div>
              <input
                type="number"
                placeholder="Trailing SL Points (e.g. 30)"
                value={form.trailingSLPoints}
                onChange={set('trailingSLPoints')}
                step="0.5"
                min="0.5"
              />
              {ltp && form.trailingSLPoints && (
                <div style={{ marginTop: '4px', fontSize: '11px', color: '#6b7280' }}>
                  Initial SL at: {formatNumber(ltp - parseFloat(form.trailingSLPoints))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Estimated Cost */}
        {ltp && form.quantity && (
          <div style={{ fontSize: '12px', color: '#6b7280', textAlign: 'right' }}>
            Est. Cost: {formatINR(ltp * parseInt(form.quantity || 0))}
          </div>
        )}

        {/* Error */}
        {error && <div style={{ color: '#dc2626', fontSize: '12px' }}>{error}</div>}

        {/* Submit */}
        <button
          type="submit"
          className={form.side === 'BUY' ? 'buy-btn' : 'sell-btn'}
          disabled={submitting || !form.symbol}
          style={{ padding: '10px', fontSize: '14px', fontWeight: 700 }}
        >
          {submitting
            ? 'Placing...'
            : form.orderType === 'GTT'
            ? `Place GTT ${form.side}`
            : `${form.side} at Market`
          }
        </button>
      </form>
    </div>
  )
}

const labelStyle = {
  display: 'block',
  fontSize: '11px',
  fontWeight: 600,
  color: '#6b7280',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: '4px',
}

const levelLabel = {
  fontSize: '11px',
  fontWeight: 700,
  width: '28px',
  flexShrink: 0,
  color: '#374151',
}
