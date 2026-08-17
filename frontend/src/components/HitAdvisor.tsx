import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { HitEvaluation, PlayerPrediction } from '../types/api';

function recommendationStyle(rec: string) {
  if (rec.includes('TAKE THE HIT')) return 'bg-[var(--color-fpl-green)]/20 text-[var(--color-fpl-green)] border-[var(--color-fpl-green)]/30';
  if (rec.includes('DO NOT')) return 'bg-fuchsia-500/20 text-fuchsia-300 border-fuchsia-500/30';
  return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
}

export function HitAdvisor() {
  const [players, setPlayers] = useState<PlayerPrediction[]>([]);
  const [outgoingId, setOutgoingId] = useState<number | null>(null);
  const [incomingId, setIncomingId] = useState<number | null>(null);
  const [result, setResult] = useState<HitEvaluation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPredictions(1).then((data) => {
      setPlayers([...data].sort((a, b) => a.web_name.localeCompare(b.web_name)));
    });
  }, []);

  const handleEvaluate = () => {
    if (outgoingId === null || incomingId === null) return;
    setLoading(true);
    setError(null);
    setResult(null);
    api.evaluateHit(outgoingId, incomingId)
      .then(setResult)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">Hit Advisor</h2>
      <p className="text-white/40 mb-8">
        Applies the 3-week outscore rule: only take a -4 hit if the incoming player projects
        4+ points higher than the outgoing player over the next 3 gameweeks.
      </p>

      <div className="glass-panel rounded-2xl p-6 mb-6">
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-white/50 text-xs uppercase tracking-widest block mb-2">Outgoing</label>
            <select
              className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:border-[var(--color-fpl-green)]/50 outline-none"
              value={outgoingId ?? ''}
              onChange={(e) => setOutgoingId(Number(e.target.value) || null)}
            >
              <option value="">Select player...</option>
              {players.map((p) => (
                <option key={p.player_id} value={p.player_id}>{p.web_name} ({p.team_name})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-white/50 text-xs uppercase tracking-widest block mb-2">Incoming</label>
            <select
              className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:border-[var(--color-fpl-green)]/50 outline-none"
              value={incomingId ?? ''}
              onChange={(e) => setIncomingId(Number(e.target.value) || null)}
            >
              <option value="">Select player...</option>
              {players.map((p) => (
                <option key={p.player_id} value={p.player_id}>{p.web_name} ({p.team_name})</option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={handleEvaluate}
          disabled={outgoingId === null || incomingId === null || loading}
          className="bg-[var(--color-fpl-green)] disabled:opacity-30 disabled:cursor-not-allowed text-[var(--color-fpl-purple)] font-bold text-sm px-6 py-2.5 rounded-xl hover:brightness-110 transition"
        >
          {loading ? 'Evaluating...' : 'Evaluate Transfer'}
        </button>
      </div>

      {error && (
        <div className="glass-panel rounded-2xl p-6 border-fuchsia-500/30">
          <p className="text-fuchsia-400 text-sm">{error}</p>
        </div>
      )}

      {result && (
        <div className="glass-panel glow-purple rounded-2xl p-6">
          <div className={`inline-block text-xs font-bold px-3 py-1 rounded-full border mb-4 ${recommendationStyle(result.recommendation)}`}>
            {result.recommendation}
          </div>
          <div className="grid sm:grid-cols-3 gap-4 mb-4">
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">{result.outgoing_name}</span>
              <span className="text-white text-xl font-black">{result.outgoing_3gw_projection.toFixed(1)}</span>
              <span className="text-white/30 text-xs block">3-GW proj.</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">{result.incoming_name}</span>
              <span className="text-white text-xl font-black">{result.incoming_3gw_projection.toFixed(1)}</span>
              <span className="text-white/30 text-xs block">3-GW proj.</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Net (after -{result.hit_cost})</span>
              <span className={`text-xl font-black ${result.net_gain >= 0 ? 'text-[var(--color-fpl-green)]' : 'text-fuchsia-400'}`}>
                {result.net_gain >= 0 ? '+' : ''}{result.net_gain.toFixed(1)}
              </span>
            </div>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">{result.reasoning}</p>
        </div>
      )}
    </section>
  );
}