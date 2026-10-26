import { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import AppLayout from "./layouts/AppLayout";
import { Loading } from "./components/ui";
import Landing from "./pages/Landing";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import Assignments from "./pages/Assignments";
import AssignmentDetail from "./pages/AssignmentDetail";
import Submissions from "./pages/Submissions";
import SubmissionDetail from "./pages/SubmissionDetail";
import Workspace from "./pages/Workspace";
import ReviewQueue from "./pages/ReviewQueue";
import Compare from "./pages/Compare";
import PublicAnalyzer from "./pages/PublicAnalyzer";

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8"><Loading /></div>;
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<PublicAnalyzer />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route element={<Protected><AppLayout /></Protected>}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/assignments" element={<Assignments />} />
          <Route path="/assignments/:id" element={<AssignmentDetail />} />
          <Route path="/submissions" element={<Submissions />} />
          <Route path="/submissions/:id" element={<SubmissionDetail />} />
          <Route path="/reviews" element={<ReviewQueue />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/workspace" element={<Workspace />} />
        </Route>
        <Route path="*" element={<div className="p-10">Page not found.</div>} />
      </Routes>
    </AuthProvider>
  );
}
