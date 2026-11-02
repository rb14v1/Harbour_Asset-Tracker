import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchDashboard } from "../../api/dashboard";
import { extractErrorMessage } from "../../api/client";
import type { DashboardSummary } from "../../types";

export function Dashboard() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboard()
      .then((res) => setData(res.data))
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  if (error) return <div className="page"><div className="form-error">{error}</div></div>;
  if (!data) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <section>
        <h2>Assets by status</h2>
        <div className="stat-row">
          {Object.entries(data.counts_by_status).map(([status, count]) => (
            <div key={status} className={`stat-card stat-${status}`}>
              <span className="stat-value">{count}</span>
              <span className="stat-label">{status}</span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Assets by category</h2>
        <div className="stat-row">
          {Object.entries(data.counts_by_category).map(([category, count]) => (
            <div key={category} className="stat-card">
              <span className="stat-value">{count}</span>
              <span className="stat-label">{category}</span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Employees with currently-assigned assets</h2>
        <table className="data-table">
          <thead>
            <tr><th>Employee</th><th>Assets in custody</th></tr>
          </thead>
          <tbody>
            {data.employees_with_assets.map((row) => (
              <tr key={row.employee_id}>
                <td>{row.name}</td>
                <td>{row.asset_count}</td>
              </tr>
            ))}
            {data.employees_with_assets.length === 0 && (
              <tr><td colSpan={2}>No assets currently assigned.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      <section>
        <h2>Never-assigned assets (underutilized stock)</h2>
        <table className="data-table">
          <thead>
            <tr><th>Tag</th><th>Name</th><th>Category</th></tr>
          </thead>
          <tbody>
            {data.never_assigned_assets.map((row) => (
              <tr key={row.id}>
                <td><Link to={`/assets/${row.id}`}>{row.asset_tag}</Link></td>
                <td>{row.name}</td>
                <td>{row.category}</td>
              </tr>
            ))}
            {data.never_assigned_assets.length === 0 && (
              <tr><td colSpan={3}>Every asset has been assigned at least once.</td></tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
