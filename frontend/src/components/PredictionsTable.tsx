import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { PlayerPrediction } from '../types/api';
import { PositionBadge } from './PositionBadge';

const FILTERS = ['ALL', 'GKP', 'DEF', 'MID', 'FWD'] as const;

export function PredictionsTable() {
  const [predictions, setPredictions] = useState<PlayerPrediction[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPredictions(1)
      .then(setPredictions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === 'ALL' ? predictions : predictions.filter((p) => p.position === filter);

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">Predicted Points</h2>
      <p className="text-white/40 mb-8">Every player, ranked by model prediction for the upcoming gameweek</p>

      <div className="flex gap-2 mb-6">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full text-xs font-bold border transition-colors ${
              filter === f
                ? 'bg-[var(--color-mu-red)] text-white border-[var(--color-mu-red)]'
                : 'text-white/50 border-white/10 hover:border-white/30'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {loading && <p className="text-white/50">Loading...</p>}
      {error && <p className="text-red-400">Error: {error}</p>}

      <div className="glass-panel rounded-2xl overflow-hidden">
        {filtered.slice(0, 30).map((p, i) => (
          <div
            key={p.player_id}
            className={`flex items-center justify-between px-5 py-3 ${i !== 0 ? 'border-t border-white/5' : ''}`}
          >
            <div className="flex items-center gap-3">
              <span className="text-white/30 text-sm w-5 text-right">{i + 1}</span>
              <PositionBadge position={p.position} />
              <div>
                <span className="text-white font-medium block">{p.web_name}</span>
                <span className="text-white/40 text-xs">{p.team_name} · £{p.now_cost.toFixed(1)}m</span>
              </div>
            </div>
            <span className="text-[var(--color-mu-red)] font-black">{p.predicted_points.toFixed(1)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}