import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import LoginPage from "./pages/LoginPage";
import WorkspacePage from "./pages/WorkspacePage";
import AdminUsersPage from "./pages/AdminUsersPage";
import SettingsPage from "./pages/SettingsPage";
import AdminFeedbackPage from "./pages/AdminFeedbackPage";
import { useAuth } from "./store/auth";

function RequireAuth({ children }: { children: ReactNode }) {
  const token = useAuth((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireAdmin({ children }: { children: ReactNode }) {
  const user = useAuth((s) => s.user);
  if (user?.role !== "admin") return <Navigate to="/workspace" replace />;
  return <>{children}</>;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/workspace" element={<RequireAuth><WorkspacePage /></RequireAuth>} />
      <Route path="/admin/users" element={
        <RequireAuth><RequireAdmin><AdminUsersPage /></RequireAdmin></RequireAuth>
      } />
      <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
      <Route path="/admin/feedback" element={
        <RequireAuth><RequireAdmin><AdminFeedbackPage /></RequireAdmin></RequireAuth>
      } />
      <Route path="*" element={<Navigate to="/workspace" replace />} />
    </Routes>
  );
}
