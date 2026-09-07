import { useEffect, useState } from 'react';
import { fetchPairs } from '../api/pipeline';

export default function PipelineConfig({ config, onChange, disabled }) {
  const [pairs, setPairs] = useState([]);
  const [pairsError, setPairsError] = useState(null);

  useEffect(() => {
    fetchPairs()
      .then((data) => {
        const available = (data.pairs || []).filter((p) => p.tiles_available !== false);
        setPairs(available);
        if (available.length && !config.pair_id) {
          onChange({ ...config, pair_id: available[0].pair_id });
        }
      })
      .catch(() => setPairsError('Backend offline'));
  }, []);

  const set = (key, val) => onChange({ ...config, [key]: val });

  const selectedPair = pairs.find((p) => p.pair_id === config.pair_id);

  return (
    <div className="pipeline-config">
      <div className="config-group config-group-wide">
        <label>Image Pair</label>
        <select value={config.pair_id} onChange={(e) => set('pair_id', e.target.value)} disabled={disabled}>
          {pairs.length > 0 ? (
            pairs.map((p) => (
              <option key={p.pair_id} value={p.pair_id}>
                {p.pair_id} — {p.region || 'Unknown Region'}
              </option>
            ))
          ) : (
            <option value={config.pair_id}>{config.pair_id}{pairsError ? ` (${pairsError})` : ''}</option>
          )}
        </select>
      </div>

      {selectedPair && (
        <div className="pair-info">
          {isSameSensor(selectedPair) ? (
            <>
              <span className="pair-type-badge same-sensor">OHRC-OHRC</span>
              <span title="Source product">SRC: {truncateId(selectedPair.ohrc_product_id)}</span>
              {selectedPair.ohrc_product_id !== selectedPair.tmc2_product_id && (
                <span title="Reference product">REF: {truncateId(selectedPair.tmc2_product_id)}</span>
              )}
              <span>GSD: {selectedPair.ohrc_resolution_m} m/px (1:1)</span>
            </>
          ) : (
            <>
              <span title="OHRC product">OHRC: {truncateId(selectedPair.ohrc_product_id)}</span>
              <span title="TMC-2 product">TMC-2: {truncateId(selectedPair.tmc2_product_id)}</span>
              {selectedPair.ohrc_resolution_m && (
                <span>GSD: {selectedPair.ohrc_resolution_m} / {selectedPair.tmc2_resolution_m} m/px</span>
              )}
            </>
          )}
        </div>
      )}

      <div className="config-separator" />

      <div className="config-group">
        <label>Model</label>
        <select value={config.model} onChange={(e) => set('model', e.target.value)} disabled={disabled}>
          <option value="affine">Affine</option>
          <option value="homography">Homography</option>
        </select>
      </div>
      <div className="config-group">
        <label>RANSAC Thr.</label>
        <input type="number" value={config.ransac_threshold}
          onChange={(e) => set('ransac_threshold', parseFloat(e.target.value))}
          min="0.5" max="10" step="0.5" disabled={disabled} />
      </div>
      <div className="config-group">
        <label>Min Conf.</label>
        <input type="number" value={config.min_confidence}
          onChange={(e) => set('min_confidence', parseFloat(e.target.value))}
          min="0" max="1" step="0.05" disabled={disabled} />
      </div>
      <div className="config-group">
        <label>Device</label>
        <select value={config.device} onChange={(e) => set('device', e.target.value)} disabled={disabled}>
          <option value="cuda">CUDA</option>
          <option value="cpu">CPU</option>
          <option value="auto">Auto</option>
        </select>
      </div>
      <div className="config-group">
        <label>Max Size</label>
        <input type="number" value={config.max_size}
          onChange={(e) => set('max_size', parseInt(e.target.value))}
          min="128" max="1024" step="64" disabled={disabled} />
      </div>
      <div className="config-group">
        <label>Source Side</label>
        <input type="number" value={config.source_side}
          onChange={(e) => set('source_side', parseInt(e.target.value))}
          min="1024" max="12000" step="512" disabled={disabled} />
      </div>
    </div>
  );
}

function isSameSensor(pair) {
  if (!pair) return false;
  const ratio = parseFloat(pair.resolution_ratio);
  return ratio > 0 && ratio <= 1.5;
}

function truncateId(id) {
  if (!id || id.length <= 20) return id;
  return id.slice(0, 12) + '...' + id.slice(-8);
}
