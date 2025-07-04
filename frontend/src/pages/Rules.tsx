import React, { useEffect, useState } from 'react';
import { Dataset, Rule, fetchDatasets, fetchRules, createRule } from '../lib/api';

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [form, setForm] = useState({
    dataset_id: 0,
    rule_type: 'completeness',
    column: '',
    threshold: 0.1,
    severity: 'warning',
    enabled: true,
  });

  useEffect(() => {
    async function load() {
      setDatasets(await fetchDatasets());
      setRules(await fetchRules());
    }
    load().catch((err) => console.error(err));
  }, []);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Build params object
    const params: Record<string, unknown> = {};
    if (form.rule_type === 'completeness' || form.rule_type === 'freshness' || form.rule_type === 'uniqueness' || form.rule_type === 'outlier_rate' || form.rule_type === 'distribution_drift') {
      params[form.rule_type === 'uniqueness' ? 'primary_key' : 'column'] = form.column;
      if (form.rule_type === 'freshness') {
        params['timestamp_column'] = form.column;
      }
    }
    await createRule({
      dataset_id: Number(form.dataset_id),
      rule_type: form.rule_type,
      params,
      threshold: Number(form.threshold),
      severity: form.severity,
      enabled: form.enabled,
    });
    setRules(await fetchRules());
  }

  return (
    <div>
      <h2>Rules</h2>
      <table style={{ borderCollapse: 'collapse', width: '100%' }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Dataset</th>
            <th>Type</th>
            <th>Threshold</th>
            <th>Enabled</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {rules.map((rule) => (
            <tr key={rule.id}>
              <td>{rule.id}</td>
              <td>{rule.dataset_id}</td>
              <td>{rule.rule_type}</td>
              <td>{rule.threshold}</td>
              <td>{rule.enabled ? 'Yes' : 'No'}</td>
              <td>{new Date(rule.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Create Rule</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', maxWidth: '400px' }}>
        <label>
          Dataset:
          <select name="dataset_id" value={form.dataset_id} onChange={handleChange} required>
            <option value="">Select dataset</option>
            {datasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Rule Type:
          <select name="rule_type" value={form.rule_type} onChange={handleChange} required>
            <option value="completeness">Completeness</option>
            <option value="freshness">Freshness</option>
            <option value="uniqueness">Uniqueness</option>
            <option value="outlier_rate">Outlier Rate</option>
            <option value="distribution_drift">Distribution Drift</option>
          </select>
        </label>
        <label>
          Column/Primary Key:
          <input name="column" value={form.column} onChange={handleChange} placeholder="column name" required />
        </label>
        <label>
          Threshold:
          <input name="threshold" type="number" step="0.01" value={form.threshold} onChange={handleChange} required />
        </label>
        <label>
          Severity:
          <select name="severity" value={form.severity} onChange={handleChange} required>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </label>
        <label>
          Enabled:
          <input name="enabled" type="checkbox" checked={form.enabled} onChange={handleChange} />
        </label>
        <button type="submit" style={{ marginTop: '1rem' }}>Save</button>
      </form>
    </div>
  );
}