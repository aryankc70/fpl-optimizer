import { useEffect, useState } from 'react';
import { api } from '../api/client';
import type { ChipGuidance } from '../types/api';

export function ChipCalendarView() {
  const [gameweek, setGameweek] = useState(1);
  const [guidance, setGuidance] = useState<ChipGuidance | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.getChipCalendar(gameweek)
      .then(setGuidance)
      .finally(() => setLoading(false));
  }, [gameweek]);

  return (
    <section className="max-w-4xl mx-auto px-6 py-16">
      <h2 className="text-3xl font-extrabold text-white mb-2">Chip Strategy Calendar</h2>
      <p className="text-white/40 mb-8">Season-phase guidance for Wildcard, Bench Boost, Free Hit, and Triple Captain timing</p>

      <div className="glass-panel rounded-2xl p-6 mb-6">
        <label className="text-white/50 text-xs uppercase tracking-widest block mb-3">
          Gameweek {gameweek}
        </label>
        <input
          type="range"
          min={1}
          max={38}
          value={gameweek}
          onChange={(e) => setGameweek(Number(e.target.value))}
          className="w-full accent-[var(--color-mu-red)]"
        />
        <div className="flex justify-between text-white/30 text-xs mt-1">
          <span>GW1</span>
          <span>GW38</span>
        </div>
      </div>

      {loading && <p className="text-white/50">Loading...</p>}

      {guidance && guidance.windows.length === 0 && (
        <div className="glass-panel rounded-2xl p-6">
          <p className="text-white/40 text-sm">No specific guidance recorded for this gameweek.</p>
        </div>
      )}

      {guidance && guidance.windows.map((w, i) => (
        <div key={i} className="glass-panel rounded-2xl p-6 mb-4">
          <div className="flex items-center gap-3 mb-3">
            <span className="bg-[var(--color-mu-red)]/20 text-red-300 border border-[var(--color-mu-red)]/30 text-xs font-bold px-3 py-1 rounded-full">
              {w.phase}
            </span>
            <span className="text-white font-semibold">{w.focus}</span>
          </div>
          <p className="text-white/60 text-sm leading-relaxed">{w.guidance}</p>
        </div>
      ))}
    </section>
  );
}