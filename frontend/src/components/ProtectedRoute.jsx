import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * Gates a route behind authentication and (optionally) a role allowlist.
 * Also enforces the forced password-change flow: a user who logged in
 * with a temporary password is redirected to /change-password no
 * matter what route they try to hit, until they set their own password.
 */
export default function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, user, role } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (user?.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />;
  }

  if (roles && !roles.includes(role)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
