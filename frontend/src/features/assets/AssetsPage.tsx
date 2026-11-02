import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { assignAsset, deleteAsset, listAssets, retireAsset, unretireAsset } from "../../api/assets";
import { extractErrorMessage } from "../../api/client";
import { listEmployees } from "../../api/employees";
import type { Asset, Employee } from "../../types";

const STATUS_LABEL: Record<Asset["status"], string> = {
  available: "Available",
  assigned: "Assigned",
  retired: "Retired",
};

export function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assigningId, setAssigningId] = useState<number | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<string>("");

  function load() {
    setLoading(true);
    Promise.all([listAssets(), listEmployees()])
      .then(([assetsRes, employeesRes]) => {
        setAssets(assetsRes.data.results);
        setEmployees(employeesRes.data.results);
      })
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleAssign(assetId: number) {
    if (!selectedEmployee) return;
    setError(null);
    try {
      await assignAsset(assetId, Number(selectedEmployee));
      setAssigningId(null);
      setSelectedEmployee("");
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleRetire(assetId: number) {
    setError(null);
    try {
      await retireAsset(assetId);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleUnretire(assetId: number) {
    setError(null);
    try {
      await unretireAsset(assetId);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleDelete(assetId: number) {
    if (!window.confirm("Delete this asset?")) return;
    setError(null);
    try {
      await deleteAsset(assetId);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Assets</h1>
        <Link className="btn btn-primary" to="/assets/new">Add asset</Link>
      </div>
      {error && <div className="form-error">{error}</div>}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Tag</th>
              <th>Name</th>
              <th>Category</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset) => (
              <tr key={asset.id}>
                <td><Link to={`/assets/${asset.id}`}>{asset.asset_tag}</Link></td>
                <td>{asset.name}</td>
                <td>{asset.category}</td>
                <td>
                  <span className={`badge badge-${asset.status}`}>{STATUS_LABEL[asset.status]}</span>
                </td>
                <td className="row-actions">
                  <Link to={`/assets/${asset.id}/edit`}>Edit</Link>
                  {asset.status === "available" && assigningId !== asset.id && (
                    <button className="btn-link" onClick={() => setAssigningId(asset.id)}>Assign</button>
                  )}
                  {assigningId === asset.id && (
                    <span className="inline-assign">
                      <select value={selectedEmployee} onChange={(e) => setSelectedEmployee(e.target.value)}>
                        <option value="">Select employee...</option>
                        {employees.map((employee) => (
                          <option key={employee.id} value={employee.id}>{employee.name}</option>
                        ))}
                      </select>
                      <button className="btn-link" onClick={() => handleAssign(asset.id)}>Confirm</button>
                      <button className="btn-link" onClick={() => setAssigningId(null)}>Cancel</button>
                    </span>
                  )}
                  {!asset.is_retired && (
                    <button className="btn-link" onClick={() => handleRetire(asset.id)}>Retire</button>
                  )}
                  {asset.is_retired && (
                    <button className="btn-link" onClick={() => handleUnretire(asset.id)}>Unretire</button>
                  )}
                  <button className="btn-link" onClick={() => handleDelete(asset.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {assets.length === 0 && (
              <tr>
                <td colSpan={5}>No assets yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
