import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Squad } from '../types/api';
import { PlayerCard } from './PlayerCard';

const POSITION_ORDER = ['GKP', 'DEF', 'MID', 'FWD'] as const;

export function SquadView() {
  const [squad, setSquad] = useState<Squad | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOptimalSquad()
      .then(setSquad)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">Optimal Squad</h2>
      <p className="text-white/40 mb-8">15-man squad, selected via integer linear programming</p>

      {loading && <p className="text-white/50">Solving...</p>}
      {error && <p className="text-red-400">Error: {error}</p>}

      {squad && (
        <>
          <div className="glass-panel glow-red rounded-2xl p-6 mb-8 flex gap-8">
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Budget Used</span>
              <span className="text-white text-2xl font-black">£{squad.total_cost.toFixed(1)}m</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Predicted Points</span>
              <span className="text-[var(--color-mu-red)] text-2xl font-black">{squad.total_predicted_points.toFixed(1)}</span>
            </div>
          </div>

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