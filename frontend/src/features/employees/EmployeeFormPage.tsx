import { useEffect, useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createEmployee, getEmployee, updateEmployee, type EmployeeInput } from "../../api/employees";
import { extractErrorMessage } from "../../api/client";

const emptyForm: EmployeeInput = {
  name: "",
  email: "",
  department: "",
  job_title: "",
  hire_date: null,
  is_active: true,
};

export function EmployeeFormPage() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState<EmployeeInput>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isEdit && id) {
      getEmployee(Number(id)).then((res) => {
        const { name, email, department, job_title, hire_date, is_active } = res.data;
        setForm({ name, email, department, job_title, hire_date, is_active });
      });
    }
  }, [id, isEdit]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (isEdit && id) {
        await updateEmployee(Number(id), form);
      } else {
        await createEmployee(form);
      }
      navigate("/employees");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>{isEdit ? "Edit employee" : "Add employee"}</h1>
      <form className="record-form" onSubmit={handleSubmit}>
        {error && <div className="form-error">{error}</div>}
        <label>
          Name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </label>
        <label>
          Email
          <input
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            required
          />
        </label>
        <label>
          Department
          <input value={form.department} onChange={(e) => setForm({ ...form, department: e.target.value })} />
        </label>
        <label>
          Job title
          <input value={form.job_title} onChange={(e) => setForm({ ...form, job_title: e.target.value })} />
        </label>
        <label>
          Hire date
          <input
            type="date"
            value={form.hire_date ?? ""}
            onChange={(e) => setForm({ ...form, hire_date: e.target.value || null })}
          />
        </label>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          Active
        </label>
        <div className="form-actions">
          <button type="submit" disabled={submitting}>{submitting ? "Saving..." : "Save"}</button>
          <button type="button" onClick={() => navigate("/employees")}>Cancel</button>
        </div>
      </form>
    </div>
  );
}
