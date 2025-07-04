import React, { useEffect, useState } from 'react';
import { Dataset, fetchDatasets } from '../lib/api';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    fetchDatasets().then(setDatasets).catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h2>Datasets</h2>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Description</th>
            <th>Owner</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((ds) => (
            <tr key={ds.id}>
              <td>{ds.id}</td>
              <td>{ds.name}</td>
              <td>{ds.description}</td>
              <td>{ds.owner_id}</td>
              <td>{new Date(ds.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}