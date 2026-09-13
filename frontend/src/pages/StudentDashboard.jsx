import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ChevronRight, Award, BookOpen, Clock } from 'lucide-react';
import { api } from '../api';
import { useAuth } from '../hooks/useAuth';
import PageHeader from '../components/ui/PageHeader';
import EmptyState from '../components/ui/EmptyState';
import ScoreBar from '../components/ScoreBar';
import { DashboardSkeleton } from '../components/ui/Skeleton';

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data: results = [], isLoading } = useQuery({
    queryKey: ['myResults'],
    queryFn: api.getMyResults,
  });

  if (isLoading) return <DashboardSkeleton />;

  const sorted = [...results].sort((a, b) => (b.graded_at || '').localeCompare(a.graded_at || ''));
  const avgPct = results.length
    ? Math.round(results.reduce((sum, r) => sum + (r.percentage || 0), 0) / results.length)
    : 0;

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="py-8 space-y-8">
      <PageHeader
        title={`Welcome, ${user?.name || 'Student'} 👋`}
        subtitle={user?.roll_no ? `Roll No. ${user.roll_no}${user.class_name ? ` · ${user.class_name}` : ''}` : 'Your graded results across every subject.'}
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {[
          { label: 'Subjects Graded', value: results.length, icon: BookOpen, gradient: 'from-indigo-500 to-primary-600' },
          { label: 'Average Score', value: `${avgPct}%`, icon: Award, gradient: 'from-amber-400 to-amber-600' },
          {
            label: 'Latest Result',
            value: sorted[0] ? `${sorted[0].percentage ?? 0}%` : '—',
            icon: Clock,
            gradient: 'from-emerald-400 to-emerald-600',
          },
        ].map((card) => (
          <div key={card.label} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-card flex items-center justify-between">
            <div className="space-y-1.5">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">{card.label}</span>
              <span className="text-3xl font-extrabold text-slate-900 block font-display">{card.value}</span>
            </div>
            <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-2xl text-white shadow-md`}>
              <card.icon className="h-5 w-5" />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900 font-display">My Results</h3>
          <p className="text-xs text-slate-500 mt-0.5">Every subject you've been graded in, most recent first.</p>
        </div>

        {sorted.length === 0 ? (
          <EmptyState icon={BookOpen} title="No results yet" description="Once your teacher grades a submission, it will appear here." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50/80">
                <tr>
                  {['Subject', 'Score', 'Remark', 'Graded At', ''].map((col, i) => (
                    <th key={col || 'actions'} className={`px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider ${i === 4 ? 'sr-only' : ''}`}>
                      {col || 'Actions'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {sorted.map((r) => (
                  <tr key={r.submission_id} className="hover:bg-indigo-50/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-bold text-slate-800">{r.subject_name}</div>
                      <div className="text-[11px] text-slate-400">{r.subject_code}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap min-w-[160px]">
                      <ScoreBar score={r.total_scored} maxMarks={r.total_marks} showText />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">{r.overall_remark || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {r.graded_at ? new Date(r.graded_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold">
                      <Link to={`/results/${r.submission_id}`} className="text-indigo-600 hover:text-indigo-700 flex items-center justify-end space-x-1 hover:underline min-h-[44px]">
                        <span>Details</span>
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </motion.div>
  );
}
