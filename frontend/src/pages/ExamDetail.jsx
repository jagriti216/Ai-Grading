import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import BackLink from '../components/ui/BackLink';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import { motion } from 'framer-motion';
import { Calendar, PlusCircle, ChevronRight, BookOpen, User, BarChart2 } from 'lucide-react';

export default function ExamDetail() {
  const { examId } = useParams();

  const { data: exam, isLoading } = useQuery({
    queryKey: ['exam', examId],
    queryFn: () => api.getExam(examId),
  });

  if (isLoading) return <LoadingSpinner message="Loading exam details..." />;

  const subjects = exam?.subjects || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="py-8 space-y-8"
    >
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <BackLink to="/exams" label="Back to Exams" />
        <Link
          to={`/exam/${examId}/subjects/new`}
          className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.02] min-h-[44px]"
        >
          <PlusCircle className="h-4 w-4" />
          <span>Add Subject Paper</span>
        </Link>
      </div>

      {exam && (
        <div className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 rounded-2xl p-6 sm:p-8 text-white shadow-card space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            {exam.term && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                {exam.term}
              </span>
            )}
            <span className="text-xs text-indigo-200/70 font-semibold flex items-center">
              <Calendar className="h-3.5 w-3.5 mr-1" />
              {exam.created_at ? new Date(exam.created_at).toLocaleDateString() : 'N/A'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight leading-tight font-display">{exam.title}</h1>
          <p className="text-[10px] text-indigo-300/60 font-mono select-all">ID: {exam.exam_id}</p>
        </div>
      )}

      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4 font-display">Subject Papers</h2>

        {subjects.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No subject papers yet"
            description="Add a subject (question paper + answer key) to start collecting and grading submissions."
            action={
              <Link
                to={`/exam/${examId}/subjects/new`}
                className="inline-flex items-center space-x-2 bg-indigo-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-card hover:bg-indigo-700 transition-all"
              >
                <PlusCircle className="h-4 w-4" />
                <span>Add Subject Paper</span>
              </Link>
            }
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {subjects.map((subject) => (
              <Link
                key={subject.subject_paper_id}
                to={`/subject/${subject.subject_paper_id}`}
                className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-card hover:shadow-card-hover hover:border-indigo-200 transition-all group"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-bold text-slate-800 truncate">{subject.subject_name}</div>
                    <span className="inline-flex mt-1.5 items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 text-indigo-700">
                      {subject.subject_code}
                    </span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-0.5 transition-all shrink-0 mt-1" />
                </div>
                <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
                  <span className="flex items-center gap-1.5 text-xs text-slate-500">
                    <User className="h-3.5 w-3.5" />
                    {subject.teacher_name}
                  </span>
                  <Link
                    to={`/analytics?exam_id=${examId}&subject_code=${subject.subject_code}`}
                    onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700 hover:underline"
                  >
                    <BarChart2 className="h-3.5 w-3.5" />
                    Analytics
                  </Link>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
