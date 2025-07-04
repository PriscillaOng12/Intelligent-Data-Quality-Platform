import React, { useEffect, useState } from 'react';
import {
  Incident,
  fetchIncidents,
  acknowledgeIncident,
} from '../lib/api';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selected, setSelected] = useState<Incident | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function load() {
    const data = await fetchIncidents();
    setIncidents(data);
  }

  useEffect(() => {
    load().catch((err) => console.error(err));
  }, []);

  async function handleAcknowledge() {
    if (!selected) return;
    setLoading(true);
    try {
      const updated = await acknowledgeIncident(selected.id);
      setIncidents((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      setSelected(updated);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Incidents</h2>
      <div style={{ display: 'flex' }}>
        <table style={{ borderCollapse: 'collapse', width: '60%' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Dataset</th>
              <th>Rule</th>
              <th>Severity</th>
              <th>Acknowledged</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((inc) => (
              <tr
                key={inc.id}
                onClick={() => setSelected(inc)}
                style={{ cursor: 'pointer', background: selected?.id === inc.id ? '#eef' : undefined }}
              >
                <td>{inc.id}</td>
                <td>{inc.dataset_id}</td>
                <td>{inc.rule_id}</td>
                <td>{inc.severity}</td>
                <td>{inc.acknowledged ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ flex: 1, paddingLeft: '1rem' }}>
          {selected ? (
            <div>
              <h3>Incident #{selected.id}</h3>
              <p><strong>Severity:</strong> {selected.severity}</p>
              <p><strong>Metric value:</strong> {selected.metric_value}</p>
              <p><strong>Description:</strong> {selected.description}</p>
              <p><strong>Created at:</strong> {new Date(selected.created_at).toLocaleString()}</p>
              <p><strong>Acknowledged:</strong> {selected.acknowledged ? 'Yes' : 'No'}</p>
              {!selected.acknowledged && (
                <button onClick={handleAcknowledge} disabled={loading}>
                  {loading ? 'Acknowledging...' : 'Acknowledge'}
                </button>
              )}
            </div>
          ) : (
            <p>Select an incident to see details.</p>
          )}
        </div>
      </div>
    </div>
  );
}