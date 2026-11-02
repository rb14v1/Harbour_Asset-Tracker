import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { listAssignments, returnAssignment } from "../../api/assignments";
import { getAsset } from "../../api/assets";
import { extractErrorMessage } from "../../api/client";
import type { Asset, AssetAssignment } from "../../types";

export function AssetDetailPage() {
  const { id } = useParams();
  const assetId = Number(id);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [history, setHistory] = useState<AssetAssignment[]>([]);
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([getAsset(assetId), listAssignments({ asset: assetId })])
      .then(([assetRes, historyRes]) => {
        setAsset(assetRes.data);
        setHistory(historyRes.data.results);
      })
      .catch((err) => setError(extractErrorMessage(err)));
  }

  useEffect(load, [assetId]);

  async function handleReturn(assignmentId: number) {
    setError(null);
    try {
      await returnAssignment(assignmentId);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (!asset) {
    return <div className="page">{error ? <div className="form-error">{error}</div> : "Loading..."}</div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>{asset.asset_tag} - {asset.name}</h1>
        <Link to="/assets">Back to assets</Link>
      </div>
      {error && <div className="form-error">{error}</div>}
      <dl className="detail-grid">
        <dt>Category</dt><dd>{asset.category}</dd>
        <dt>Status</dt><dd><span className={`badge badge-${asset.status}`}>{asset.status}</span></dd>
        <dt>Serial number</dt><dd>{asset.serial_number || "-"}</dd>
        <dt>Purchase date</dt><dd>{asset.purchase_date ?? "-"}</dd>
      </dl>

      <h2>Assignment history</h2>
      <table className="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Assigned</th>
            <th>Returned</th>
            <th>Notes</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {history.map((assignment) => (
            <tr key={assignment.id}>
              <td>{assignment.employee_name}</td>
              <td>{assignment.assigned_date}</td>
              <td>{assignment.returned_date ?? "-"}</td>
              <td>{assignment.notes || "-"}</td>
              <td>
                {assignment.is_open && (
                  <button className="btn-link" onClick={() => handleReturn(assignment.id)}>Return</button>
                )}
              </td>
            </tr>
          ))}
          {history.length === 0 && (
            <tr>
              <td colSpan={5}>This asset has never been assigned.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
