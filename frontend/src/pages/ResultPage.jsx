import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import QuestionCard from '../components/QuestionCard';
import BackLink from '../components/ui/BackLink';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import { motion } from 'framer-motion';
import {
  Printer,
  Clock,
  GraduationCap,
  Award,
  CheckCircle,
  FileCheck,
} from 'lucide-react';
import toast from 'react-hot-toast';

const getPerformanceLabel = (pct) => {
  if (pct >= 70) return { label: 'Excellent', color: 'text-emerald-600' };
  if (pct >= 40) return { label: 'Pass', color: 'text-amber-600' };
  return { label: 'Needs Improvement', color: 'text-rose-600' };
};

const ScoreGauge = ({ percentage }) => {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color = percentage >= 70 ? '#10B981' : percentage >= 40 ? '#F59E0B' : '#EF4444';
  const perf = getPerformanceLabel(percentage);

  return (
    <div className="flex flex-col items-center space-y-1">
      <svg width="130" height="130" viewBox="0 0 140 140" className="shrink-0 drop-shadow-sm select-none">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#F3F4F6" strokeWidth="12" />
        <motion.circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
        />
        <text x="70" y="65" textAnchor="middle" fontSize="22" fontWeight="800" fill={color}>
          {Math.round(percentage)}%
        </text>
        <text x="70" y="85" textAnchor="middle" fontSize="9" fontWeight="600" fill="#64748b">
          {perf.label}
        </text>
      </svg>
    </div>
  );
};

export default function ResultPage() {
  const { submissionId } = useParams();

  const { data: result, isLoading, error, refetch } = useQuery({
    queryKey: ['result', submissionId],
    queryFn: () => api.getResult(submissionId),
    onError: (err) => {
      toast.error('Failed to load result: ' + (err.response?.data?.detail || err.message));
    },
  });

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading evaluation breakdown..." />;
  }

  if (error || !result || result.status === 'failed') {
    return (
      <div className="max-w-xl mx-auto my-12 text-center animate-fadeIn">
        <div className="bg-rose-50 border border-rose-100 rounded-2xl p-8 space-y-4 shadow-card">
          <Award className="h-12 w-12 text-rose-500 mx-auto" />
          <h3 className="text-lg font-bold text-rose-800 font-display">Result Loading Failed</h3>
          <p className="text-sm text-rose-600">
            {error?.response?.data?.detail || result?.error || 'The grading results could not be recovered.'}
          </p>
          <div className="flex justify-center space-x-3 pt-2">
            <button
              onClick={() => refetch()}
              className="bg-rose-600 text-white font-bold text-xs px-4 py-2.5 rounded-xl hover:bg-rose-700 transition-colors min-h-[44px]"
            >
              Retry
            </button>
            <Link
              to="/exams"
              className="bg-slate-900 text-white font-bold text-xs px-4 py-2.5 rounded-xl hover:bg-slate-800 transition-colors min-h-[44px] inline-flex items-center"
            >
              Rubrics Directory
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const {
    student_name = 'Student',
    roll_number = '',
    total_scored = 0,
    total_marks = 100,
    percentage = 0,
    overall_remark = '',
    questions = [],
    graded_at = '',
    exam_id = '',
  } = result;

  let performanceColor = 'bg-rose-50/50 text-rose-700 border-rose-100';

  if (percentage >= 70) {
    performanceColor = 'bg-emerald-50/50 text-emerald-700 border-emerald-100';
  } else if (percentage >= 40) {
    performanceColor = 'bg-amber-50/50 text-amber-700 border-amber-100';
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="max-w-5xl mx-auto py-8 space-y-8"
    >
      <div className="flex justify-between items-center no-print">
        <BackLink to={`/exam/${exam_id}`} label="Back to Exam Detail" />
        <button
          onClick={handlePrint}
          className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.02] min-h-[44px]"
        >
          <Printer className="h-4 w-4" />
          <span className="hidden sm:inline">Download PDF Report</span>
          <span className="sm:hidden">Print</span>
        </button>
      </div>

      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-card flex flex-col sm:flex-row items-center justify-between gap-8 print-card">
        <div className="space-y-4 text-center sm:text-left">
          <div className="flex items-center space-x-3 justify-center sm:justify-start">
            <div className="p-3 bg-indigo-50 rounded-2xl text-indigo-600 shrink-0">
              <GraduationCap className="h-7 w-7" />
            </div>
            <div className="text-left">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Student Report Card</span>
              <h1 className="text-2xl font-black text-slate-900 leading-tight font-display">{student_name}</h1>
              {roll_number && <p className="text-xs text-slate-500 font-semibold mt-0.5">Roll Number: {roll_number}</p>}
            </div>
          </div>

          <div className="flex flex-wrap justify-center sm:justify-start gap-y-2 gap-x-6 text-xs text-slate-500 font-semibold">
            <span className="flex items-center">
              <Clock className="h-4 w-4 text-slate-400 mr-1.5" />
              Graded: {graded_at ? new Date(graded_at).toLocaleString() : 'N/A'}
            </span>
            <span className="flex items-center">
              <FileCheck className="h-4 w-4 text-slate-400 mr-1.5" />
              Report ID: <span className="font-mono select-all ml-1 text-slate-600">{submissionId.slice(0, 8)}</span>
            </span>
          </div>
        </div>

        <div className="flex flex-col items-center space-y-2 sm:pr-4">
          <ScoreGauge percentage={percentage} />
          <span className="text-xs font-bold text-slate-500 text-center">
            {total_scored} / {total_marks} marks
          </span>
        </div>
      </div>

      {overall_remark && (
        <div className={`border rounded-2xl p-5 shadow-card space-y-2.5 print-card ${performanceColor}`}>
          <h3 className="text-xs font-bold uppercase tracking-wider flex items-center">
            <CheckCircle className="h-4 w-4 mr-1.5 shrink-0" />
            <span>AI Feedback Summary</span>
          </h3>
          <p className="text-sm leading-relaxed font-semibold">{overall_remark}</p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-950 font-display">Question Wise Evaluation</h2>
          <p className="text-slate-500 text-xs mt-1">Expand a question to inspect semantic score breakdowns and AI keyword checks.</p>
        </div>

        {questions.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 text-sm shadow-card">
            No question evaluations loaded.
          </div>
        ) : (
          <div className="space-y-4 print-expand-all">
            {questions.map((q, index) => (
              <QuestionCard key={q.q_number} question={q} defaultOpen={index === 0} />
            ))}
          </div>
        )}
      </div>

      <div className="text-center text-slate-400 text-[10px] font-semibold pt-8 border-t border-slate-100 no-print">
        AI Evaluation Engine © {new Date().getFullYear()} — GradeAI Evaluation Suite
      </div>
    </motion.div>
  );
}
