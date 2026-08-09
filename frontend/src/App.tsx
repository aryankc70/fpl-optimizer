import { useEffect, useState } from 'react';
import { api } from './api/client';
import type { PlayerPrediction } from './types/api';

function App() {
  const [predictions, setPredictions] = useState<PlayerPrediction[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPredictions(1)
      .then(setPredictions)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen p-8" style={{ fontFamily: 'var(--font-display)' }}>
      <h1 className="text-white text-2xl mb-4">API Connection Test</h1>
      {error && <p className="text-red-500">Error: {error}</p>}
      <p className="text-white/70">Loaded {predictions.length} predictions</p>
      {predictions[0] && (
        <p className="text-white/50 text-sm mt-2">
          Top prediction: {predictions[0].web_name} — {predictions[0].predicted_points.toFixed(2)} pts
        </p>
      )}
    </div>
  );
}

export default App;