import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { deleteEmployee, listEmployees } from "../../api/employees";
import { extractErrorMessage } from "../../api/client";
import type { Employee } from "../../types";

export function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    listEmployees()
      .then((res) => setEmployees(res.data.results))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleDelete(id: number) {
    if (!window.confirm("Delete this employee?")) return;
    try {
      await deleteEmployee(id);
      load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Employees</h1>
        <Link className="btn btn-primary" to="/employees/new">Add employee</Link>
      </div>
      {error && <div className="form-error">{error}</div>}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Department</th>
              <th>Job title</th>
              <th>Hire date</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {employees.map((employee) => (
              <tr key={employee.id}>
                <td>{employee.name}</td>
                <td>{employee.email}</td>
                <td>{employee.department}</td>
                <td>{employee.job_title}</td>
                <td>{employee.hire_date ?? "-"}</td>
                <td>
                  <span className={`badge ${employee.is_active ? "badge-available" : "badge-retired"}`}>
                    {employee.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="row-actions">
                  <Link to={`/employees/${employee.id}/edit`}>Edit</Link>
                  <button className="btn-link" onClick={() => handleDelete(employee.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {employees.length === 0 && (
              <tr>
                <td colSpan={7}>No employees yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
