import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Wallet, 
  ArrowUpRight, 
  ArrowDownLeft, 
  History, 
  Send, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  RefreshCw,
  User,
  ShieldCheck,
  Zap,
  ChevronRight,
  TrendingUp,
  Banknote
} from 'lucide-react';
import { format } from 'date-fns';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  const [merchants, setMerchants] = useState([]);
  const [selectedMerchant, setSelectedMerchant] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [payoutAmount, setPayoutAmount] = useState('');
  const [bankId, setBankId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  useEffect(() => {
    fetchMerchants();
  }, []);

  useEffect(() => {
    if (selectedMerchant) {
      fetchDashboard();
      const interval = setInterval(fetchDashboard, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedMerchant]);

  const fetchMerchants = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/merchants`);
      setMerchants(res.data);
      if (res.data.length > 0) setSelectedMerchant(res.data[0]);
    } catch (err) {
      setError("System Offline: Failed to synchronize merchants.");
    }
  };

  const fetchDashboard = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/dashboard`, {
        params: { merchant_id: selectedMerchant.id }
      });
      setData(res.data);
      setLoading(false);
    } catch (err) {
      // setError("Connection error. Retrying...");
    }
  };

  const handlePayout = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    
    const idempotencyKey = crypto.randomUUID();
    
    try {
      await axios.post(`${API_BASE_URL}/payouts`, {
        amount_paise: parseInt(payoutAmount),
        bank_account_id: bankId
      }, {
        headers: {
          'X-Merchant-Id': selectedMerchant.id,
          'Idempotency-Key': idempotencyKey
        }
      });
      
      setPayoutAmount('');
      setBankId('');
      setSuccessMsg("Payout request initiated successfully.");
      fetchDashboard();
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err) {
      setError(err.response?.data?.error || "Payout processing failed. Check balance and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!selectedMerchant) return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <RefreshCw className="w-10 h-10 text-indigo-600 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#FDFDFE] text-slate-900 font-['Inter'] selection:bg-indigo-100 selection:text-indigo-700">
      {/* Top Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
              <Zap className="w-6 h-6 text-white fill-white" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-slate-900">PLAYTO<span className="text-indigo-600">PAY</span></span>
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-emerald-600 uppercase tracking-widest">
                <ShieldCheck className="w-3 h-3" />
                <span>Enterprise Engine</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-full border border-slate-200">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-xs font-semibold text-slate-600 uppercase tracking-tight">System Live</span>
            </div>
            <div className="flex items-center gap-3 pl-4 border-l border-slate-100">
              <div className="text-right hidden sm:block">
                <p className="text-xs font-medium text-slate-400">Current Session</p>
                <p className="text-sm font-bold text-slate-700">{selectedMerchant.name}</p>
              </div>
              <select 
                className="bg-slate-100 border-none rounded-full px-3 py-2 text-sm font-bold text-slate-600 focus:ring-2 focus:ring-indigo-500 cursor-pointer hover:bg-slate-200 transition-all"
                value={selectedMerchant.id}
                onChange={(e) => {
                  const m = merchants.find(m => m.id == e.target.value);
                  setSelectedMerchant(m);
                  setLoading(true);
                }}
              >
                {merchants.map(m => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-10">
        {loading && !data ? (
          <div className="flex items-center justify-center h-96">
            <RefreshCw className="w-12 h-12 text-indigo-500 animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
            {/* Left Column: Stats & Form */}
            <div className="lg:col-span-8 space-y-10">
              
              {/* Balances Section */}
              <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="group bg-gradient-to-br from-indigo-600 to-indigo-700 p-8 rounded-[2rem] shadow-2xl shadow-indigo-200 relative overflow-hidden transition-transform hover:scale-[1.02]">
                  <div className="absolute top-0 right-0 -mt-8 -mr-8 w-40 h-40 bg-white/10 rounded-full blur-3xl"></div>
                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-8">
                      <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
                        <Wallet className="w-6 h-6 text-white" />
                      </div>
                      <span className="text-xs font-bold text-indigo-100 uppercase tracking-widest bg-white/10 px-3 py-1 rounded-full">Available</span>
                    </div>
                    <p className="text-indigo-100/80 font-medium mb-1">Withdrawable Balance</p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-4xl font-black text-white">₹{(data.balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="mt-8 pt-6 border-t border-white/10 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-white/70 text-sm font-medium">
                        <TrendingUp className="w-4 h-4" />
                        <span>Live Ledger sync active</span>
                      </div>
                      <button className="text-xs font-bold text-white bg-white/20 px-4 py-2 rounded-xl hover:bg-white/30 transition-all">Audit</button>
                    </div>
                  </div>
                </div>

                <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-100 relative overflow-hidden group">
                  <div className="flex items-center justify-between mb-8">
                    <div className="p-3 bg-amber-50 rounded-2xl">
                      <Clock className="w-6 h-6 text-amber-600" />
                    </div>
                    <span className="text-xs font-bold text-amber-600 uppercase tracking-widest bg-amber-50 px-3 py-1 rounded-full">Locked</span>
                  </div>
                  <p className="text-slate-400 font-medium mb-1">Held in Settlement</p>
                  <h2 className="text-4xl font-black text-slate-800 tracking-tight">
                    ₹{(data.held_balance_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </h2>
                  <div className="mt-8 flex items-center gap-3">
                    <div className="flex -space-x-2">
                      {[1,2,3].map(i => <div key={i} className="w-6 h-6 rounded-full border-2 border-white bg-slate-100"></div>)}
                    </div>
                    <span className="text-xs font-bold text-slate-400">3 Payouts in transit</span>
                  </div>
                </div>
              </section>

              {/* Payout Table Section */}
              <section className="bg-white rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-100 overflow-hidden">
                <div className="p-8 border-b border-slate-50 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-50 rounded-xl">
                      <History className="w-5 h-5 text-slate-400" />
                    </div>
                    <h3 className="text-lg font-black text-slate-800 tracking-tight">Payout History</h3>
                  </div>
                  <button 
                    onClick={() => window.open(`${API_BASE_URL}/export?merchant_id=${selectedMerchant.id}`, '_blank')}
                    className="text-sm font-bold text-indigo-600 hover:text-indigo-700 transition-colors"
                  >
                    Export to Excel
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50/50 text-slate-400 text-[10px] uppercase font-black tracking-[0.1em]">
                      <tr>
                        <th className="px-8 py-5">Initiated At</th>
                        <th className="px-8 py-5">Amount</th>
                        <th className="px-8 py-5">Destination</th>
                        <th className="px-8 py-5">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {data.recent_payouts.map(p => (
                        <tr key={p.id} className="group hover:bg-slate-50/50 transition-all cursor-default">
                          <td className="px-8 py-6">
                            <p className="text-sm font-bold text-slate-700">{format(new Date(p.created_at), 'MMM dd')}</p>
                            <p className="text-[10px] text-slate-400 font-bold uppercase">{format(new Date(p.created_at), 'HH:mm a')}</p>
                          </td>
                          <td className="px-8 py-6">
                            <p className="text-base font-black text-slate-900 leading-none">₹{(p.amount_paise / 100).toLocaleString()}</p>
                            <p className="text-[10px] text-slate-400 font-bold uppercase mt-1">INR</p>
                          </td>
                          <td className="px-8 py-6">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center">
                                <Banknote className="w-4 h-4 text-slate-400" />
                              </div>
                              <p className="text-sm font-bold text-slate-600 font-mono">{p.bank_account_id}</p>
                            </div>
                          </td>
                          <td className="px-8 py-6">
                            <StatusBadge status={p.status} />
                          </td>
                        </tr>
                      ))}
                      {data.recent_payouts.length === 0 && (
                        <tr>
                          <td colSpan="4" className="px-8 py-20 text-center">
                            <div className="max-w-xs mx-auto">
                              <div className="w-16 h-16 bg-slate-50 rounded-3xl flex items-center justify-center mx-auto mb-4">
                                <History className="w-8 h-8 text-slate-200" />
                              </div>
                              <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">No payout activity found</p>
                            </div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            {/* Right Column: Sidebar */}
            <div className="lg:col-span-4 space-y-8">
              
              {/* Form Card */}
              <section className="bg-[#111827] p-8 rounded-[2rem] shadow-2xl shadow-indigo-100 relative overflow-hidden">
                <div className="absolute bottom-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <div className="relative z-10">
                  <div className="flex items-center gap-3 mb-8">
                    <div className="p-2.5 bg-indigo-500/20 rounded-xl">
                      <Send className="w-5 h-5 text-indigo-400" />
                    </div>
                    <h3 className="text-lg font-black text-white tracking-tight">Withdraw Funds</h3>
                  </div>
                  
                  <form onSubmit={handlePayout} className="space-y-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Transfer Amount (Paise)</label>
                      <div className="relative group">
                        <input 
                          type="number"
                          required
                          placeholder="00"
                          className="w-full bg-slate-900 border-2 border-slate-800 rounded-2xl px-5 py-4 focus:ring-0 focus:border-indigo-500 transition-all text-white font-black text-xl placeholder:text-slate-700 outline-none"
                          value={payoutAmount}
                          onChange={(e) => setPayoutAmount(e.target.value)}
                        />
                        <div className="absolute right-5 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500 bg-slate-800 px-2 py-1 rounded-md">PAISE</div>
                      </div>
                      <div className="flex items-center justify-between px-1">
                        <p className="text-xs font-bold text-indigo-400">≈ ₹{(payoutAmount / 100).toLocaleString()}</p>
                        <p className="text-[10px] font-bold text-slate-600">Min: ₹10.00</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Destination Account ID</label>
                      <input 
                        type="text"
                        required
                        placeholder="ACC_XXXXXXX"
                        className="w-full bg-slate-900 border-2 border-slate-800 rounded-2xl px-5 py-4 focus:ring-0 focus:border-indigo-500 transition-all text-white font-bold text-sm placeholder:text-slate-700 outline-none"
                        value={bankId}
                        onChange={(e) => setBankId(e.target.value)}
                      />
                    </div>

                    {error && (
                      <div className="bg-red-500/10 border border-red-500/20 p-4 rounded-2xl flex items-start gap-3 text-red-400">
                        <XCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                        <span className="text-xs font-bold leading-tight">{error}</span>
                      </div>
                    )}

                    {successMsg && (
                      <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl flex items-start gap-3 text-emerald-400">
                        <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0" />
                        <span className="text-xs font-bold leading-tight">{successMsg}</span>
                      </div>
                    )}

                    <button 
                      disabled={submitting || !payoutAmount || !bankId}
                      className="group relative w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:grayscale transition-all text-white font-black py-5 rounded-[1.5rem] flex items-center justify-center gap-3 mt-4 shadow-xl shadow-indigo-500/20 overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                      {submitting ? (
                        <RefreshCw className="w-5 h-5 animate-spin" />
                      ) : (
                        <>
                          <span className="tracking-tight text-base">Request Settlement</span>
                          <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </button>
                  </form>
                </div>
              </section>

              {/* Ledger Preview */}
              <section className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-xl shadow-slate-50">
                <h3 className="text-base font-black text-slate-800 tracking-tight mb-6 flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                  Real-time Ledger
                </h3>
                <div className="space-y-5">
                  {data.recent_ledger.map(l => (
                    <div key={l.id} className="flex items-center justify-between group cursor-default">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${l.amount > 0 ? 'bg-emerald-50' : 'bg-red-50'}`}>
                          {l.amount > 0 ? <ArrowDownLeft className={`w-5 h-5 ${l.amount > 0 ? 'text-emerald-600' : 'text-red-500'}`} /> : <ArrowUpRight className="w-5 h-5 text-red-500" />}
                        </div>
                        <div>
                          <p className="text-xs font-black text-slate-700 leading-none truncate max-w-[120px]">{l.description}</p>
                          <p className="text-[10px] font-bold text-slate-400 uppercase mt-1">{format(new Date(l.created_at), 'HH:mm:ss')}</p>
                        </div>
                      </div>
                      <span className={`text-sm font-black tracking-tight ${l.amount > 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                        {l.amount > 0 ? '+' : ''}{l.amount.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
                <button className="w-full mt-8 py-3 rounded-xl border-2 border-slate-50 text-xs font-black text-slate-400 hover:bg-slate-50 transition-all uppercase tracking-widest">
                  View Full Audit Log
                </button>
              </section>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function StatusBadge({ status }) {
  const styles = {
    'PENDING': 'bg-indigo-50 text-indigo-600 border-indigo-100',
    'PROCESSING': 'bg-amber-50 text-amber-600 border-amber-100',
    'COMPLETED': 'bg-emerald-50 text-emerald-600 border-emerald-100',
    'FAILED': 'bg-red-50 text-red-600 border-red-100'
  };

  const icons = {
    'PENDING': <Clock className="w-3.5 h-3.5" />,
    'PROCESSING': <RefreshCw className="w-3.5 h-3.5 animate-spin" />,
    'COMPLETED': <CheckCircle2 className="w-3.5 h-3.5" />,
    'FAILED': <XCircle className="w-3.5 h-3.5" />
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-black border uppercase tracking-wider ${styles[status]}`}>
      {icons[status]}
      {status}
    </span>
  );
}

export default App;
