import type { ChipGuidance, HitEvaluation, Lineup, MySquad, PlayerPrediction, Squad, TransferSuggestion } from '../types/api';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  getPredictions: (gameweek: number) =>
    fetchJSON<PlayerPrediction[]>(`/predictions/${gameweek}`),

  getPlayer: (playerId: number, gameweek = 1) =>
    fetchJSON<PlayerPrediction>(`/players/${playerId}?gameweek=${gameweek}`),

  getOptimalSquad: () =>
    fetchJSON<Squad>('/squad/optimal'),

  getOptimalLineup: () =>
    fetchJSON<Lineup>('/lineup/optimal'),

  evaluateHit: (outgoingId: number, incomingId: number, numHits = 1) =>
    fetchJSON<HitEvaluation>('/hit-advisor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        outgoing_player_id: outgoingId,
        incoming_player_id: incomingId,
        num_hits: numHits,
      }),
    }),

  getChipCalendar: (gameweek: number) =>
    fetchJSON<ChipGuidance>(`/chip-calendar/${gameweek}`),

  getMySquad: () =>
    fetchJSON<MySquad>('/my-squad'),

  getSuggestedTransfers: (maxTransfers?: number) =>
    fetchJSON<TransferSuggestion>(`/my-squad/suggest-transfers${maxTransfers ? `?max_transfers=${maxTransfers}` : ''}`),
};