import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { fetchIncidents, fetchDatasets, fetchRules, Incident, Dataset, Rule } from '../lib/api';

interface SeverityCount {
  severity: string;
  count: number;
}

export default function OverviewPage() {
  const [severityData, setSeverityData] = useState<SeverityCount[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);

  useEffect(() => {
    async function load() {
      const incidents: Incident[] = await fetchIncidents();
      const counts: Record<string, number> = {};
      incidents.forEach((i) => {
        counts[i.severity] = (counts[i.severity] || 0) + 1;
      });
      setSeverityData(Object.keys(counts).map((severity) => ({ severity, count: counts[severity] })));
      setDatasets(await fetchDatasets());
      setRules(await fetchRules());
    }
    load().catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h2>Overview</h2>
      <p>Datasets: {datasets.length}</p>
      <p>Rules: {rules.length}</p>
      <h3>Incidents by Severity</h3>
      <div style={{ width: '100%', height: 300 }}>
        <ResponsiveContainer>
          <BarChart data={severityData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <XAxis dataKey="severity" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#8884d8" name="Incidents" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}