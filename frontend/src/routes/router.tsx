import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "../auth/ProtectedRoute";
import { Dashboard } from "../features/dashboard/Dashboard";
import { AssetDetailPage } from "../features/assets/AssetDetailPage";
import { AssetFormPage } from "../features/assets/AssetFormPage";
import { AssetsPage } from "../features/assets/AssetsPage";
import { EmployeeFormPage } from "../features/employees/EmployeeFormPage";
import { EmployeesPage } from "../features/employees/EmployeesPage";
import { AppLayout } from "../layouts/AppLayout";
import { LoginPage } from "../pages/LoginPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <Dashboard /> },
          { path: "/employees", element: <EmployeesPage /> },
          { path: "/employees/new", element: <EmployeeFormPage /> },
          { path: "/employees/:id/edit", element: <EmployeeFormPage /> },
          { path: "/assets", element: <AssetsPage /> },
          { path: "/assets/new", element: <AssetFormPage /> },
          { path: "/assets/:id/edit", element: <AssetFormPage /> },
          { path: "/assets/:id", element: <AssetDetailPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
