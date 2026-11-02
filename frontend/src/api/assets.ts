import { apiClient } from "./client";
import type { Asset, AssetAssignment, Paginated } from "../types";

export type AssetInput = Omit<Asset, "id" | "created_at" | "status">;

export function listAssets() {
  return apiClient.get<Paginated<Asset>>("/assets/", { params: { page_size: 100 } });
}

export function getAsset(id: number) {
  return apiClient.get<Asset>(`/assets/${id}/`);
}

export function createAsset(data: AssetInput) {
  return apiClient.post<Asset>("/assets/", data);
}

export function updateAsset(id: number, data: AssetInput) {
  return apiClient.put<Asset>(`/assets/${id}/`, data);
}

export function deleteAsset(id: number) {
  return apiClient.delete(`/assets/${id}/`);
}

export function assignAsset(id: number, employeeId: number, assignedDate?: string, notes?: string) {
  return apiClient.post<AssetAssignment>(`/assets/${id}/assign/`, {
    employee_id: employeeId,
    assigned_date: assignedDate,
    notes,
  });
}

export function retireAsset(id: number) {
  return apiClient.post<Asset>(`/assets/${id}/retire/`);
}

export function unretireAsset(id: number) {
  return apiClient.post<Asset>(`/assets/${id}/unretire/`);
}
