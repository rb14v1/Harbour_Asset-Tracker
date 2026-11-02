import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createAsset, getAsset, updateAsset, type AssetInput } from "../../api/assets";
import { extractErrorMessage } from "../../api/client";
import type { AssetCategory } from "../../types";

const CATEGORIES: AssetCategory[] = ["laptop", "monitor", "phone", "peripheral", "other"];

const emptyForm: AssetInput = {
  asset_tag: "",
  name: "",
  category: "laptop",
  serial_number: "",
  purchase_date: null,
  is_retired: false,
};

export function AssetFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState<AssetInput>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isEdit && id) {
      getAsset(Number(id)).then((res) => {
        const { asset_tag, name, category, serial_number, purchase_date, is_retired } = res.data;
        setForm({ asset_tag, name, category, serial_number, purchase_date, is_retired });
      });
    }
  }, [id, isEdit]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (isEdit && id) {
        await updateAsset(Number(id), form);
      } else {
        await createAsset(form);
      }
      navigate("/assets");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>{isEdit ? "Edit asset" : "Add asset"}</h1>
      <form className="record-form" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}
        <label>
          Asset tag
          <input value={form.asset_tag} onChange={(e) => setForm({ ...form, asset_tag: e.target.value })} required />
        </label>
        <label>
          Name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </label>
        <label>
          Category
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value as AssetCategory })}
          >
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </label>
        <label>
          Serial number
          <input
            value={form.serial_number}
            onChange={(e) => setForm({ ...form, serial_number: e.target.value })}
          />
        </label>
        <label>
          Purchase date
          <input
            type="date"
            value={form.purchase_date ?? ""}
            onChange={(e) => setForm({ ...form, purchase_date: e.target.value || null })}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.is_retired}
            onChange={(e) => setForm({ ...form, is_retired: e.target.checked })}
          />
          Retired
        </label>
        <div className="form-actions">
          <button type="submit" disabled={submitting}>{submitting ? "Saving..." : "Save"}</button>
          <button type="button" onClick={() => navigate("/assets")}>Cancel</button>
        </div>
      </form>
    </div>
  );
}
