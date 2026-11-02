export type AssetCategory = "laptop" | "monitor" | "phone" | "peripheral" | "other";
export type AssetStatus = "available" | "assigned" | "retired";

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface Employee {
  id: number;
  name: string;
  email: string;
  department: string;
  job_title: string;
  hire_date: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Asset {
  id: number;
  asset_tag: string;
  name: string;
  category: AssetCategory;
  serial_number: string;
  purchase_date: string | null;
  is_retired: boolean;
  status: AssetStatus;
  created_at: string;
}

export interface AssetAssignment {
  id: number;
  asset: number;
  asset_tag: string;
  asset_name: string;
  employee: number;
  employee_name: string;
  assigned_date: string;
  returned_date: string | null;
  notes: string;
  is_open: boolean;
  created_at: string;
}

export interface DashboardEmployeeRow {
  employee_id: number;
  name: string;
  asset_count: number;
}

export interface DashboardNeverAssignedRow {
  id: number;
  asset_tag: string;
  name: string;
  category: AssetCategory;
}

export interface DashboardSummary {
  counts_by_status: Record<AssetStatus, number>;
  counts_by_category: Record<AssetCategory, number>;
  employees_with_assets: DashboardEmployeeRow[];
  never_assigned_assets: DashboardNeverAssignedRow[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
