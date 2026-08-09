import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { Lineup } from '../types/api';
import { PlayerCard } from './PlayerCard';

const POSITION_ORDER = ['GKP', 'DEF', 'MID', 'FWD'] as const;

export function LineupView() {
  const [lineup, setLineup] = useState<Lineup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getOptimalLineup()
      .then(setLineup)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">Starting XI</h2>
      <p className="text-white/40 mb-8">Formation, captaincy, and bench — optimized separately from squad selection</p>

      {loading && <p className="text-white/50">Solving...</p>}
      {error && <p className="text-red-400">Error: {error}</p>}

      {lineup && (
        <>
          <div className="glass-panel glow-red rounded-2xl p-6 mb-8 flex gap-8">
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">Formation</span>
              <span className="text-white text-2xl font-black">{lineup.formation}</span>
            </div>
            <div>
              <span className="text-white/40 text-xs uppercase tracking-widest block">With Captain</span>
              <span className="text-[var(--color-mu-red)] text-2xl font-black">{lineup.points_with_captain.toFixed(1)}</span>
            </div>
          </div>

          {POSITION_ORDER.map((pos) => {
            const players = lineup.starting_xi.filter((p) => p.position === pos);
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
                        badge={
                          p.player_id === lineup.captain.player_id ? 'C'
                          : p.player_id === lineup.vice_captain.player_id ? 'VC'
                          : undefined
                        }
                      />
                    ))}
                </div>
              </div>
            );
          })}

          <h3 className="text-white/50 text-xs uppercase tracking-widest mb-3 mt-8">Bench</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {lineup.bench.map((p) => (
              <PlayerCard
                key={p.player_id}
                webName={p.web_name}
                position={p.position}
                cost={p.cost}
                predictedPoints={p.predicted_points}
                dimmed
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}