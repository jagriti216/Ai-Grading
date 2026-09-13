import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { KeyRound, RefreshCw, AlertCircle, ShieldCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../api';
import { useAuth } from '../hooks/useAuth';

export default function ChangePassword() {
  const { user, updateAuth } = useAuth();
  const navigate = useNavigate();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const forced = user?.must_change_password;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      return setError('New password must be at least 8 characters');
    }
    if (newPassword !== confirmPassword) {
      return setError('New password and confirmation do not match');
    }
    if (newPassword === oldPassword) {
      return setError('New password must be different from your current password');
    }

    setLoading(true);
    try {
      await api.changePassword(oldPassword, newPassword);
      updateAuth({ must_change_password: false });
      toast.success('Password updated successfully');
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors';
  const labelClass =
    'absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600';

  return (
    <div className="min-h-[70vh] flex items-center justify-center py-12">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-600 text-white shadow-card mb-2">
            <KeyRound className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 font-display">
            {forced ? 'Set a New Password' : 'Change Password'}
          </h1>
          <p className="text-sm text-slate-500 max-w-sm mx-auto">
            {forced
              ? "You're signed in with a temporary password. You must set your own password before continuing."
              : 'Update the password for your account.'}
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-card space-y-6"
        >
          {error && (
            <div className="flex items-center space-x-2 bg-rose-50 border border-rose-100 text-rose-700 text-xs font-semibold px-4 py-3 rounded-xl">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="relative">
            <input
              type="password"
              id="oldPassword"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              className={inputClass}
              placeholder=" "
              autoComplete="current-password"
              required
            />
            <label htmlFor="oldPassword" className={labelClass}>
              {forced ? 'Temporary Password' : 'Current Password'}
            </label>
          </div>

          <div className="relative">
            <input
              type="password"
              id="newPassword"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClass}
              placeholder=" "
              autoComplete="new-password"
              required
            />
            <label htmlFor="newPassword" className={labelClass}>New Password (min. 8 characters)</label>
          </div>

          <div className="relative">
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
              placeholder=" "
              autoComplete="new-password"
              required
            />
            <label htmlFor="confirmPassword" className={labelClass}>Confirm New Password</label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl text-sm font-bold shadow-card hover:shadow-card-hover transition-all active:scale-[1.01] disabled:opacity-50 disabled:pointer-events-none min-h-[46px]"
          >
            {loading ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <ShieldCheck className="h-4 w-4" />
            )}
            <span>{loading ? 'Updating...' : 'Update Password'}</span>
          </button>
        </form>
      </motion.div>
    </div>
  );
}
