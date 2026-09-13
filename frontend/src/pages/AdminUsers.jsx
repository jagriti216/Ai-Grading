import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  UserPlus, RefreshCw, Trash2, Copy, Check, ShieldAlert, Users as UsersIcon, GraduationCap,
} from 'lucide-react';
import { api } from '../api';
import PageHeader from '../components/ui/PageHeader';
import EmptyState from '../components/ui/EmptyState';
import { TableSkeleton } from '../components/ui/Skeleton';

function CopyableCredential({ label, value }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
      <div>
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">{label}</div>
        <div className="text-sm font-mono font-bold text-slate-800 select-all">{value}</div>
      </div>
      <button
        type="button"
        onClick={handleCopy}
        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
        aria-label={`Copy ${label}`}
      >
        {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
      </button>
    </div>
  );
}

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const [role, setRole] = useState('student');
  const [username, setUsername] = useState('');
  const [name, setName] = useState('');
  const [rollNo, setRollNo] = useState('');
  const [className, setClassName] = useState('');
  const [subjectCodes, setSubjectCodes] = useState('');
  const [createdCredential, setCreatedCredential] = useState(null);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => api.listUsers(),
  });

  const createMutation = useMutation({
    mutationFn: api.createUser,
    onSuccess: (data) => {
      toast.success(`${data.role === 'student' ? 'Student' : 'Teacher'} account created`);
      setCreatedCredential(data);
      queryClient.invalidateQueries(['adminUsers']);
      setUsername('');
      setName('');
      setRollNo('');
      setClassName('');
      setSubjectCodes('');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to create account'),
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteUser,
    onSuccess: () => {
      toast.success('Account deleted');
      queryClient.invalidateQueries(['adminUsers']);
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to delete account'),
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!username.trim() || !name.trim()) return toast.error('Username and name are required');
    if (role === 'student' && !rollNo.trim()) return toast.error('Roll number is required for students');

    createMutation.mutate({
      username: username.trim(),
      name: name.trim(),
      role,
      roll_no: role === 'student' ? rollNo.trim() : undefined,
      class_name: className.trim() || undefined,
      subject_codes: role === 'teacher' && subjectCodes.trim()
        ? subjectCodes.split(',').map((s) => s.trim()).filter(Boolean)
        : undefined,
    });
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors';
  const labelClass =
    'absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600';

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="py-8 space-y-8">
      <PageHeader title="User Management" subtitle="Create and manage teacher and student accounts." />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <div className="lg:col-span-1 space-y-6">
          <form onSubmit={handleSubmit} className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-card space-y-5">
            <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <UserPlus className="h-4 w-4 text-indigo-600" />
              <span>Create Account</span>
            </h3>

            <div className="flex bg-slate-100 rounded-xl p-1">
              {['student', 'teacher'].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRole(r)}
                  className={`flex-1 py-2 rounded-lg text-xs font-bold capitalize transition-all ${
                    role === r ? 'bg-white shadow-sm text-indigo-700' : 'text-slate-500'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>

            <div className="relative">
              <input type="text" id="username" value={username} onChange={(e) => setUsername(e.target.value)} className={inputClass} placeholder=" " required />
              <label htmlFor="username" className={labelClass}>Username</label>
            </div>
            <div className="relative">
              <input type="text" id="name" value={name} onChange={(e) => setName(e.target.value)} className={inputClass} placeholder=" " required />
              <label htmlFor="name" className={labelClass}>Full Name</label>
            </div>

            {role === 'student' ? (
              <>
                <div className="relative">
                  <input type="text" id="rollNo" value={rollNo} onChange={(e) => setRollNo(e.target.value)} className={inputClass} placeholder=" " required />
                  <label htmlFor="rollNo" className={labelClass}>Roll Number</label>
                </div>
                <div className="relative">
                  <input type="text" id="className" value={className} onChange={(e) => setClassName(e.target.value)} className={inputClass} placeholder=" " />
                  <label htmlFor="className" className={labelClass}>Class (optional)</label>
                </div>
              </>
            ) : (
              <div className="relative">
                <input type="text" id="subjectCodes" value={subjectCodes} onChange={(e) => setSubjectCodes(e.target.value)} className={inputClass} placeholder=" " />
                <label htmlFor="subjectCodes" className={labelClass}>Subject Codes (comma-separated, optional)</label>
              </div>
            )}

            <div className="bg-amber-50/60 border border-amber-100 rounded-xl p-3 flex items-start space-x-2">
              <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
              <p className="text-[11px] text-amber-800 leading-relaxed">
                A random temporary password will be generated. It is shown once after creation — the account holder must change it on first login.
              </p>
            </div>

            <button
              type="submit"
              disabled={createMutation.isLoading}
              className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.01] disabled:opacity-50 min-h-[44px]"
            >
              {createMutation.isLoading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />}
              <span>Create {role === 'student' ? 'Student' : 'Teacher'} Account</span>
            </button>
          </form>

          {createdCredential && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-emerald-50 border border-emerald-100 rounded-2xl p-5 space-y-3"
            >
              <h4 className="text-xs font-bold text-emerald-800">Account Created — Share These Credentials</h4>
              <CopyableCredential label="Username" value={createdCredential.username} />
              <CopyableCredential label="Temporary Password" value={createdCredential.temporary_password} />
              <p className="text-[10px] text-emerald-700">This password will not be shown again after you leave this page.</p>
            </motion.div>
          )}
        </div>

        <div className="lg:col-span-2 bg-white border border-slate-200/80 rounded-2xl shadow-card overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 font-display">All Accounts</h3>
            <p className="text-xs text-slate-500 mt-0.5">{users.length} teacher/student account(s)</p>
          </div>

          {isLoading ? (
            <TableSkeleton rows={5} />
          ) : users.length === 0 ? (
            <EmptyState icon={UsersIcon} title="No accounts yet" description="Create your first teacher or student account using the form." />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100">
                <thead className="bg-slate-50/80">
                  <tr>
                    {['Name', 'Username', 'Role', 'Roll No / Subjects', ''].map((col) => (
                      <th key={col} className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {users.map((u) => (
                    <tr key={u.user_id} className="hover:bg-indigo-50/20 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800">{u.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 font-mono">{u.username}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          u.role === 'teacher' ? 'bg-indigo-50 text-indigo-700' : 'bg-emerald-50 text-emerald-700'
                        }`}>
                          {u.role === 'teacher' ? <GraduationCap className="h-3 w-3" /> : <UsersIcon className="h-3 w-3" />}
                          {u.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                        {u.role === 'student' ? (u.roll_no || '—') : (u.subject_codes?.join(', ') || '—')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete account "${u.name}"?`)) deleteMutation.mutate(u.user_id);
                          }}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all min-h-[36px] min-w-[36px] inline-flex items-center justify-center"
                          aria-label={`Delete ${u.name}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
