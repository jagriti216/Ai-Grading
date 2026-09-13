import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { Search, TrendingUp, CheckCircle, XCircle, Users, RefreshCw, AlertCircle, BarChart2 } from 'lucide-react';
import { api } from '../api';
import PageHeader from '../components/ui/PageHeader';
import ScoreBar from '../components/ScoreBar';

const DIST_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#10b981'];

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl px-3 py-2 shadow-card text-xs">
      <p className="font-bold text-slate-800 mb-1">{label}</p>
      <p className="text-indigo-600 font-semibold">{payload[0].value} student(s)</p>
    </div>
  );
};

export default function Analytics() {
  const [searchParams, setSearchParams] = useSearchParams();
  // The URL is the source of truth for which subject is being analyzed
  // (so a shared/bookmarked link works); local state below only backs
  // the two form inputs the user types into before submitting.
  const urlExamId = searchParams.get('exam_id') || '';
  const urlSubjectCode = searchParams.get('subject_code') || '';

  const [examId, setExamId] = useState(urlExamId);
  const [subjectCode, setSubjectCode] = useState(urlSubjectCode);

  const { data, isLoading, error } = useQuery({
    queryKey: ['subjectAnalytics', urlExamId, urlSubjectCode],
    queryFn: () => api.getSubjectAnalytics(urlExamId, urlSubjectCode),
    enabled: !!urlExamId && !!urlSubjectCode,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!examId.trim() || !subjectCode.trim()) return;
    setSearchParams({ exam_id: examId.trim(), subject_code: subjectCode.trim() });
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors font-mono';
  const labelClass =
    'absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600';

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="py-8 space-y-8">
      <PageHeader
        title="Subject Performance Analytics"
        subtitle="Enter an exam ID and subject code to see a full performance breakdown for that subject."
      />

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-card flex flex-col sm:flex-row gap-4 items-end">
        <div className="relative flex-1 w-full">
          <input type="text" id="examId" value={examId} onChange={(e) => setExamId(e.target.value)} className={inputClass} placeholder=" " required />
          <label htmlFor="examId" className={labelClass}>Exam ID</label>
        </div>
        <div className="relative flex-1 w-full">
          <input type="text" id="subjectCode" value={subjectCode} onChange={(e) => setSubjectCode(e.target.value)} className={inputClass} placeholder=" " required />
          <label htmlFor="subjectCode" className={labelClass}>Subject Code</label>
        </div>
        <button
          type="submit"
          className="flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.02] min-h-[46px] w-full sm:w-auto shrink-0"
        >
          <Search className="h-4 w-4" />
          <span>Analyze</span>
        </button>
      </form>

      {isLoading && (
        <div className="flex items-center justify-center py-16 text-slate-400">
          <RefreshCw className="h-6 w-6 animate-spin mr-2" />
          <span className="text-sm font-semibold">Crunching numbers...</span>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 border border-rose-100 rounded-2xl p-6 flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-rose-800">Couldn't load analytics</h3>
            <p className="text-xs text-rose-600 mt-1">{error.response?.data?.detail || error.message}</p>
          </div>
        </div>
      )}

      {data && data.total_students === 0 && (
        <div className="bg-amber-50/60 border border-amber-100 rounded-2xl p-6 text-center space-y-1">
          <BarChart2 className="h-8 w-8 text-amber-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-amber-800">{data.subject_name} ({data.subject_code})</h3>
          <p className="text-xs text-amber-700">{data.message || 'No graded submissions yet for this subject.'}</p>
        </div>
      )}

      {data && data.total_students > 0 && (
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 rounded-2xl p-6 text-white shadow-card">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
              {data.subject_code}
            </span>
            <h2 className="text-xl font-extrabold mt-2 font-display">{data.subject_name}</h2>
            <p className="text-xs text-indigo-200/70 mt-1">Graded by {data.teacher_name} &middot; Exam {data.exam_id}</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { label: 'Students', value: data.total_students, icon: Users },
              { label: 'Average', value: `${data.average_percent}%`, sub: `${data.average_score}/${data.total_marks}` },
              { label: 'Highest', value: data.highest_score, sub: `/${data.total_marks}`, color: 'text-emerald-600', icon: TrendingUp },
              { label: 'Lowest', value: data.lowest_score, sub: `/${data.total_marks}`, color: 'text-rose-600' },
              { label: 'Passed', value: data.pass_count, sub: `${data.pass_rate}%`, color: 'text-emerald-600', icon: CheckCircle },
              { label: 'Failed', value: data.fail_count, color: 'text-rose-600', icon: XCircle },
            ].map((m) => (
              <div key={m.label} className="bg-white border border-slate-200/80 p-4 rounded-xl shadow-card text-center">
                <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-center gap-1">
                  {m.icon && <m.icon className="h-3.5 w-3.5 shrink-0" />}
                  {m.label}
                </span>
                <span className={`text-2xl font-black my-1 block ${m.color || 'text-slate-900'}`}>{m.value}</span>
                {m.sub && <span className="block text-[9px] text-slate-400 font-bold">{m.sub}</span>}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-card space-y-4">
              <h4 className="text-sm font-bold text-slate-800">Score Distribution</h4>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.score_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: '#f8fafc' }} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {data.score_distribution.map((_, i) => (
                        <Cell key={i} fill={DIST_COLORS[i % DIST_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {data.per_question_averages?.length > 0 && (
              <div className="bg-white border border-slate-200/80 p-5 rounded-2xl shadow-card space-y-4">
                <h4 className="text-sm font-bold text-slate-800">Average Score Per Question</h4>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart layout="vertical" data={data.per_question_averages} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                      <XAxis type="number" stroke="#94a3b8" fontSize={11} tickLine={false} />
                      <YAxis dataKey="q_number" type="category" stroke="#94a3b8" fontSize={11} tickLine={false} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: '#f8fafc' }} />
                      <Bar dataKey="average_score" fill="#6366f1" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>

          <div className="bg-white border border-slate-200/80 rounded-2xl shadow-card overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 font-display">Roll-No Wise Results</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-100">
                <thead className="bg-slate-50/80">
                  <tr>
                    {['Roll No', 'Student', 'Score'].map((col) => (
                      <th key={col} className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-100">
                  {data.roster.map((r) => (
                    <tr key={r.submission_id} className="hover:bg-indigo-50/20 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-bold text-slate-700">{r.roll_no}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-800">{r.student_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap min-w-[160px]">
                        <ScoreBar score={r.total_scored} maxMarks={r.total_marks} showText />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
