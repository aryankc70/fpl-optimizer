import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { MySquad, TransferSuggestion } from '../types/api';
import { PlayerCard } from './PlayerCard';

const POSITION_ORDER = ['GKP', 'DEF', 'MID', 'FWD'] as const;

export function MySquadView() {
  const [squad, setSquad] = useState<MySquad | null>(null);
  const [suggestion, setSuggestion] = useState<TransferSuggestion | null>(null);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmMsg, setConfirmMsg] = useState<string | null>(null);

  const refreshSquad = () => {
    setLoading(true);
    return api.getMySquad()
      .then(setSquad)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshSquad();
  }, []);

  const checkTransfers = () => {
    setChecking(true);
    setSuggestion(null);
    setConfirmMsg(null);
    api.getSuggestedTransfers()
      .then(setSuggestion)
      .catch((e) => setError(e.message))
      .finally(() => setChecking(false));
  };

  const applyTransfers = () => {
    setApplying(true);
    api.applyTransfers()
      .then((result) => {
        setSuggestion(null);
        setConfirmMsg(
          result.num_transfers > 0
            ? `Applied ${result.num_transfers} transfer(s).`
            : 'No changes were needed.'
        );
        return refreshSquad();
      })
      .catch((e) => setError(e.message))
      .finally(() => setApplying(false));
  };

  const skipWeek = () => {
    setApplying(true);
    api.advanceGameweek()
      .then((newSquad) => {
        setSuggestion(null);
        setSquad(newSquad);
        setConfirmMsg('Advanced to next gameweek — free transfer rolled over.');
      })
      .catch((e) => setError(e.message))
      .finally(() => setApplying(false));
  };

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">My Squad</h2>
      <p className="text-white/40 mb-8">Your actual season squad, tracked week to week — not a fresh re-optimization</p>

      {loading && <p className="text-white/50">Loading...</p>}
      {error && <p className="text-red-400">Error: {error}</p>}

      {squad && (
        <>
          <div className="glass-panel glow-red rounded-2xl p-6 mb-8 flex flex-wrap gap-8 items-center">
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Gameweek</span>
              <span className="text-white text-2xl font-black">{squad.last_updated_gameweek}</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Free Transfers</span>
              <span className="text-white text-2xl font-black">{squad.free_transfers}</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Bank</span>
              <span className="text-white text-2xl font-black">£{squad.bank.toFixed(1)}m</span>
            </div>
            <div className="ml-auto flex gap-3">
              <button
                onClick={skipWeek}
                disabled={applying || checking}
                className="border border-white/20 disabled:opacity-30 text-white font-bold text-sm px-5 py-2.5 rounded-xl hover:border-white/40 transition"
              >
                Skip Week
              </button>
              <button
                onClick={checkTransfers}
                disabled={checking || applying}
                className="bg-[var(--color-mu-red)] disabled:opacity-30 text-white font-bold text-sm px-6 py-2.5 rounded-xl hover:brightness-110 transition"
              >
                {checking ? 'Checking...' : 'Check for Transfers'}
              </button>
            </div>
          </div>

          {confirmMsg && (
            <div className="glass-panel rounded-2xl p-4 mb-6">
              <p className="text-emerald-300 text-sm font-semibold">{confirmMsg}</p>
            </div>
          )}

          {suggestion && (
            <div className="glass-panel rounded-2xl p-6 mb-8">
              {suggestion.num_transfers === 0 ? (
                <p className="text-emerald-300 text-sm font-semibold">No changes recommended — your squad is already optimal within your transfer budget.</p>
              ) : (
                <>
                  <p className="text-white font-semibold mb-4">
                    {suggestion.num_transfers} transfer{suggestion.num_transfers > 1 ? 's' : ''} suggested
                    {suggestion.hits_taken > 0 && ` (${suggestion.hits_taken} hit, -${suggestion.hit_cost} pts)`}
                  </p>
                  {suggestion.transfers_out.map((out, i) => (
                    <div key={out.player_id} className="flex items-center gap-3 text-sm mb-2">
                      <span className="text-red-400">{out.web_name}</span>
                      <span className="text-white/30">→</span>
                      <span className="text-emerald-400">{suggestion.transfers_in[i]?.web_name}</span>
                    </div>
                  ))}
                  <p className={`text-sm font-bold mt-3 mb-4 ${suggestion.net_points_gained >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    Net gain: {suggestion.net_points_gained >= 0 ? '+' : ''}{suggestion.net_points_gained.toFixed(1)} pts
                  </p>
                  <button
                    onClick={applyTransfers}
                    disabled={applying}
                    className="bg-emerald-600 disabled:opacity-30 text-white font-bold text-sm px-6 py-2.5 rounded-xl hover:brightness-110 transition"
                  >
                    {applying ? 'Applying...' : 'Apply These Transfers'}
                  </button>
                </>
              )}
            </div>
          )}

          {POSITION_ORDER.map((pos) => {
            const players = squad.players.filter((p) => p.position === pos);
            if (players.length === 0) return null;
            return (
              <div key={pos} className="mb-6">
                <h3 className="text-white/50 text-xs uppercase tracking-widest mb-3">{pos}</h3>
                <div className="grid gap-3 sm:grid-cols-2">
                  {players
                    .sort((a, b) => b.predicted_points - a.predicted_points)
                    .map((p) => (
                      <PlayerCard
                        key={p.player_id}
                        webName={p.web_name}
                        position={p.position}
                        cost={p.cost}
                        predictedPoints={p.predicted_points}
                      />
                    ))}
                </div>
              </div>
            );
          })}
        </>
      )}
    </section>
  );
}