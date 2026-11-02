import { apiClient } from "./client";
import type { Employee, Paginated } from "../types";

export type EmployeeInput = Omit<Employee, "id" | "created_at">;

export function listEmployees() {
  return apiClient.get<Paginated<Employee>>("/employees/", { params: { page_size: 100 } });
}

export function getEmployee(id: number) {
  return apiClient.get<Employee>(`/employees/${id}/`);
}

export function createEmployee(data: EmployeeInput) {
  return apiClient.post<Employee>("/employees/", data);
}

export function updateEmployee(id: number, data: EmployeeInput) {
  return apiClient.put<Employee>(`/employees/${id}/`, data);
}

export function deleteEmployee(id: number) {
  return apiClient.delete(`/employees/${id}/`);
}
