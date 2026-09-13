import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { GraduationCap, Menu, X, Plus, LogOut, KeyRound } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isAuthenticated, user, role, logout } = useAuth();

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const navItemsByRole = {
    admin: [{ path: '/', label: 'Dashboard' }, { path: '/exams', label: 'Exams' }, { path: '/admin/users', label: 'Users' }],
    teacher: [{ path: '/', label: 'Dashboard' }, { path: '/exams', label: 'Exams' }, { path: '/analytics', label: 'Analytics' }],
    student: [{ path: '/', label: 'My Results' }],
  };
  const navItems = isAuthenticated ? (navItemsByRole[role] || []) : [];

  const closeMobile = () => setMobileOpen(false);

  const handleLogout = () => {
    logout();
    closeMobile();
    navigate('/login');
  };

  const roleBadge = { admin: 'Admin', teacher: 'Teacher', student: 'Student' }[role] || '';

  return (
    <motion.nav
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="bg-white/80 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-50 no-print"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link
            to="/"
            onClick={closeMobile}
            className="flex items-center space-x-2 text-indigo-600 font-extrabold text-xl tracking-tight shrink-0 hover:scale-[1.02] active:scale-95 transition-transform"
          >
            <GraduationCap className="h-7 w-7 text-indigo-600" />
            <span className="bg-gradient-to-r from-indigo-600 to-indigo-500 bg-clip-text text-transparent font-display">
              GradeAI
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex space-x-1 relative h-full items-center justify-center">
            {navItems.map((item) => {
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative flex items-center px-4 py-2 text-sm font-semibold transition-colors duration-150 h-full ${
                    active ? 'text-indigo-600 font-bold' : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  <span className="relative z-10">{item.label}</span>
                  {active && (
                    <motion.div
                      layoutId="nav-underline"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 rounded-full"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            {isAuthenticated && (role === 'admin' || role === 'teacher') && (
              <Link
                to="/exam/new"
                className="hidden sm:inline-flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-2 rounded-xl text-xs font-bold shadow-sm transition-all active:scale-95"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Create Exam</span>
              </Link>
            )}

            {isAuthenticated ? (
              <div className="hidden lg:flex items-center space-x-3">
                <div className="text-right leading-tight">
                  <div className="text-xs font-bold text-slate-700">{user?.name}</div>
                  <div className="text-[10px] font-semibold text-slate-400">{roleBadge}</div>
                </div>
                <div
                  className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-sm select-none"
                  aria-hidden="true"
                >
                  {user?.name?.[0]?.toUpperCase() || '?'}
                </div>
                <Link to="/change-password" className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors" aria-label="Change password">
                  <KeyRound className="h-4 w-4" />
                </Link>
                <button onClick={handleLogout} className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors" aria-label="Log out">
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            ) : (
              <Link to="/login" className="hidden lg:inline-flex bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-all">
                Sign In
              </Link>
            )}

            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden border-t border-slate-100 bg-white/95 backdrop-blur-md"
          >
            <div className="px-4 py-4 space-y-1">
              {isAuthenticated && (
                <div className="flex items-center space-x-3 px-4 py-3 mb-2 bg-slate-50 rounded-xl">
                  <div className="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shrink-0">
                    {user?.name?.[0]?.toUpperCase() || '?'}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-slate-800">{user?.name}</div>
                    <div className="text-[10px] font-semibold text-slate-400">{roleBadge}</div>
                  </div>
                </div>
              )}

              {navItems.map((item) => {
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={closeMobile}
                    className={`block px-4 py-3 rounded-xl text-sm font-semibold transition-colors ${
                      active ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}

              {isAuthenticated && (role === 'admin' || role === 'teacher') && (
                <Link
                  to="/exam/new"
                  onClick={closeMobile}
                  className="flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-bold bg-indigo-600 text-white mt-2"
                >
                  <Plus className="h-4 w-4" />
                  <span>Create Exam</span>
                </Link>
              )}

              {isAuthenticated ? (
                <>
                  <Link to="/change-password" onClick={closeMobile} className="flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-50">
                    <KeyRound className="h-4 w-4" />
                    <span>Change Password</span>
                  </Link>
                  <button onClick={handleLogout} className="w-full flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-semibold text-rose-600 hover:bg-rose-50">
                    <LogOut className="h-4 w-4" />
                    <span>Log Out</span>
                  </button>
                </>
              ) : (
                <Link to="/login" onClick={closeMobile} className="flex items-center space-x-2 px-4 py-3 rounded-xl text-sm font-bold bg-indigo-600 text-white">
                  <span>Sign In</span>
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
