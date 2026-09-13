import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../hooks/useAuth';
import { Search, Trash2, Calendar, FileText, Layers, AlertCircle, X } from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../components/ui/PageHeader';
import EmptyState from '../components/ui/EmptyState';
import { TableSkeleton } from '../components/ui/Skeleton';

export default function ExamList() {
  const [titleFilter, setTitleFilter] = useState('');
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { role } = useAuth();

  const { data: exams = [], isLoading, error, refetch } = useQuery({
    queryKey: ['exams'],
    queryFn: api.getExams,
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteExam,
    onSuccess: (res) => {
      toast.success(res.message || 'Exam deleted successfully');
      queryClient.invalidateQueries(['exams']);
      queryClient.invalidateQueries(['dashboardStats']);
    },
    onError: (err) => {
      toast.error('Failed to delete exam: ' + (err.response?.data?.detail || err.message));
    },
  });

  const handleDelete = (e, examId, title) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete the exam "${title}"? This will delete all subjects, submissions and results under it.`)) {
      deleteMutation.mutate(examId);
    }
  };

  const filteredExams = titleFilter
    ? exams.filter((e) => e.title.toLowerCase().includes(titleFilter.toLowerCase()))
    : exams;

  if (error) {
    return (
      <div className="py-12 text-center animate-fadeIn">
        <div className="bg-rose-50 border border-rose-100 rounded-2xl p-6 inline-block max-w-xl shadow-card">
          <AlertCircle className="h-10 w-10 text-rose-600 mx-auto mb-3" />
          <h3 className="text-base font-bold text-rose-800 mb-1">Failed to Load Exams</h3>
          <p className="text-sm text-rose-600 mb-4">{error.response?.data?.detail || error.message}</p>
          <button onClick={() => refetch()} className="bg-rose-600 text-white px-4 py-2.5 rounded-xl text-sm font-semibold hover:bg-rose-700 transition-colors min-h-[44px]">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="py-8 space-y-6 animate-fadeIn">
      <PageHeader
        title="Exams"
        subtitle="Manage exam containers and their subject papers."
        action={
          <Link
            to="/exam/new"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-card hover:shadow-card-hover active:scale-95 transition-all min-h-[44px] inline-flex items-center"
          >
            Create New Exam
          </Link>
        }
      />

      <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-card flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            value={titleFilter}
            onChange={(e) => setTitleFilter(e.target.value)}
            placeholder="Search by exam title..."
            className="w-full pl-10 pr-10 py-2.5 border border-slate-200 rounded-xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all bg-slate-50/50 min-h-[44px]"
          />
          {titleFilter && (
            <button type="button" onClick={() => setTitleFilter('')} aria-label="Clear search" className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 rounded">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <div className="text-xs text-slate-500 font-semibold">
          Found {filteredExams.length} exam{filteredExams.length === 1 ? '' : 's'}
        </div>
      </div>

      {isLoading ? (
        <TableSkeleton rows={6} />
      ) : filteredExams.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No Exams Found"
          description={titleFilter ? `No exams matching "${titleFilter}" could be found.` : 'Get started by creating your first exam.'}
          action={
            !titleFilter && (
              <Link to="/exam/new" className="inline-flex items-center bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-card hover:bg-indigo-700 transition-all">
                Create New Exam
              </Link>
            )
          }
        />
      ) : (
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50/80">
                <tr>
                  {['Title', 'Term', 'Created', 'Subject Papers', 'Actions'].map((col, i) => (
                    <th key={col} scope="col" className={`px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider ${i === 4 ? 'text-right' : ''}`}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {filteredExams.map((exam) => (
                  <tr
                    key={exam.exam_id}
                    onClick={() => navigate(`/exam/${exam.exam_id}`)}
                    className="hover:bg-indigo-50/30 cursor-pointer transition-colors border-l-2 border-l-transparent hover:border-l-indigo-500"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600 shrink-0">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div>
                          <div className="text-sm font-bold text-slate-800">{exam.title}</div>
                          <div className="text-[11px] text-slate-400 font-mono select-all" onClick={(e) => e.stopPropagation()}>
                            ID: {exam.exam_id}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{exam.term || '—'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                      <div className="flex items-center space-x-1.5">
                        <Calendar className="h-3.5 w-3.5 text-slate-400" />
                        <span>{exam.created_at ? new Date(exam.created_at).toLocaleDateString() : 'N/A'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                      <div className="flex items-center space-x-1.5">
                        <Layers className="h-4 w-4 text-slate-400" />
                        <span className="font-semibold">{exam.subject_count}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {role === 'admin' && (
                        <button
                          onClick={(e) => handleDelete(e, exam.exam_id, exam.title)}
                          disabled={deleteMutation.isLoading}
                          aria-label={`Delete exam ${exam.title}`}
                          className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-all disabled:opacity-50 min-h-[44px] min-w-[44px] inline-flex items-center justify-center"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
