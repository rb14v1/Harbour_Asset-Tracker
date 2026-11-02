import { apiClient } from "./client";
import type { AssetAssignment, Paginated } from "../types";

export interface AssignmentFilters {
  asset?: number;
  employee?: number;
  open?: boolean;
}

export function listAssignments(filters: AssignmentFilters = {}) {
  return apiClient.get<Paginated<AssetAssignment>>("/assignments/", {
    params: { page_size: 100, ...filters },
  });
}

export function returnAssignment(id: number, returnedDate?: string) {
  return apiClient.post<AssetAssignment>(`/assignments/${id}/return/`, {
    returned_date: returnedDate,
  });
}
