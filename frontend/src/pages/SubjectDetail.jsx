import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import StatusBadge from '../components/StatusBadge';
import ScoreBar from '../components/ScoreBar';
import BackLink from '../components/ui/BackLink';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import { motion } from 'framer-motion';
import { UploadCloud, ChevronRight, BookOpen, BarChart2, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SubjectDetail() {
  const { subjectPaperId } = useParams();

  const { data: subject, isLoading: loadingSubject } = useQuery({
    queryKey: ['subjectPaper', subjectPaperId],
    queryFn: () => api.getSubjectPaper(subjectPaperId),
  });

  const { data: subs = [], isLoading: loadingSubs, refetch } = useQuery({
    queryKey: ['submissions', subjectPaperId],
    queryFn: () => api.listSubmissions(subjectPaperId),
  });

  if (loadingSubject || loadingSubs) return <LoadingSpinner message="Loading subject roster..." />;

  const getInitials = (name) => {
    if (!name) return 'S';
    return name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();
  };

  const sorted = [...subs].sort((a, b) => (a.roll_no || '').localeCompare(b.roll_no || '', undefined, { numeric: true }));

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="py-8 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <BackLink to={subject ? `/exam/${subject.exam_id}` : '/exams'} label="Back to Exam" />
        <div className="flex items-center gap-3">
          <button
            onClick={() => { refetch(); toast.success('Roster synced'); }}
            className="flex items-center space-x-2 border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 px-4 py-2.5 rounded-xl text-sm font-semibold shadow-card transition-all active:scale-95 min-h-[44px]"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Sync</span>
          </button>
          {subject && (
            <Link
              to={`/analytics?exam_id=${subject.exam_id}&subject_code=${subject.subject_code}`}
              className="flex items-center space-x-2 border border-indigo-200 text-indigo-700 bg-indigo-50/50 hover:bg-indigo-50 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all min-h-[44px]"
            >
              <BarChart2 className="h-4 w-4" />
              <span>Analytics</span>
            </Link>
          )}
          <Link
            to={`/subject/${subjectPaperId}/upload`}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.02] min-h-[44px]"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Upload Sheet</span>
          </Link>
        </div>
      </div>

      {subject && (
        <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 rounded-2xl p-6 sm:p-8 text-white shadow-card space-y-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
            {subject.subject_code}
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight leading-tight font-display">{subject.subject_name}</h1>
          <p className="text-xs text-indigo-200/70">Graded by {subject.teacher_name} &middot; {subs.length} submission(s)</p>
        </div>
      )}

      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-card overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900 font-display">Student Roster</h3>
          <p className="text-xs text-slate-500 mt-0.5">Submissions for this subject, keyed by roll number.</p>
        </div>

        {sorted.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No submissions uploaded yet"
            description="Upload a student's answer sheet to trigger grading."
            action={
              <Link to={`/subject/${subjectPaperId}/upload`} className="inline-flex items-center space-x-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-card hover:bg-indigo-700 transition-all">
                <UploadCloud className="h-4 w-4" />
                <span>Upload First Sheet</span>
              </Link>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50/80">
                <tr>
                  {['Roll No', 'Student', 'Score', 'Status', 'Uploaded', ''].map((col, i) => (
                    <th key={col || 'actions'} className={`px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider ${i === 5 ? 'sr-only' : ''}`}>
                      {col || 'Actions'}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {sorted.map((sub) => (
                  <tr key={sub.submission_id} className="hover:bg-indigo-50/20 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-bold text-slate-700">{sub.roll_no}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-100 font-bold text-indigo-700 text-xs flex items-center justify-center uppercase shrink-0">
                          {getInitials(sub.student_name)}
                        </div>
                        <div className="text-sm font-bold text-slate-800">{sub.student_name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap min-w-[160px]">
                      {sub.status === 'graded' && sub.score != null ? (
                        <ScoreBar score={sub.score} maxMarks={sub.total_marks} showText={true} />
                      ) : (
                        <span className="text-xs text-slate-400 italic">Pending</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap"><StatusBadge status={sub.status} /></td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      {sub.created_at ? new Date(sub.created_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-semibold">
                      {sub.status === 'graded' ? (
                        <Link to={`/results/${sub.submission_id}`} className="text-indigo-600 hover:text-indigo-700 flex items-center justify-end space-x-1 hover:underline min-h-[44px]">
                          <span>Results</span>
                          <ChevronRight className="h-4 w-4" />
                        </Link>
                      ) : sub.status === 'failed' ? (
                        <span className="text-rose-500 text-xs font-semibold">Failed</span>
                      ) : (
                        <Link to={`/subject/${subjectPaperId}/upload?resume=${sub.submission_id}`} className="text-amber-600 hover:text-amber-700 text-xs font-semibold flex items-center justify-end space-x-1 hover:underline">
                          <span>Track</span>
                        </Link>
                      )}
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
