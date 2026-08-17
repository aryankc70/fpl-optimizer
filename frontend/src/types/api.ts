export interface PlayerPrediction {
  player_id: number;
  web_name: string;
  position: 'GKP' | 'DEF' | 'MID' | 'FWD';
  team_name: string;
  now_cost: number;
  predicted_points: number;
  status: string;
  chance_of_playing: number | null;
}

export interface SquadPlayer {
  player_id: number;
  web_name: string;
  position: 'GKP' | 'DEF' | 'MID' | 'FWD';
  cost: number;
  predicted_points: number;
  status: string;
}

export interface Squad {
  total_cost: number;
  total_predicted_points: number;
  players: SquadPlayer[];
}

export interface Lineup {
  formation: string;
  starting_xi: SquadPlayer[];
  bench: SquadPlayer[];
  captain: SquadPlayer;
  vice_captain: SquadPlayer;
  base_points: number;
  points_with_captain: number;
}

export interface HitEvaluation {
  outgoing_name: string;
  incoming_name: string;
  outgoing_3gw_projection: number;
  incoming_3gw_projection: number;
  net_gain: number;
  hit_cost: number;
  recommendation: string;
  reasoning: string;
}

export interface ChipGuidance {
  gameweek: number;
  windows: { phase: string; focus: string; guidance: string }[];
}

export interface MySquad {
  players: SquadPlayer[];
  free_transfers: number;
  bank: number;
  last_updated_gameweek: number;
}

export interface TransferSuggestion {
  num_transfers: number;
  hits_taken: number;
  hit_cost: number;
  points_gained: number;
  net_points_gained: number;
  transfers_out: SquadPlayer[];
  transfers_in: SquadPlayer[];
}