import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import FileUpload from '../components/FileUpload';
import BackLink from '../components/ui/BackLink';
import PageHeader from '../components/ui/PageHeader';
import { motion } from 'framer-motion';
import { PlusCircle, RefreshCw, ShieldAlert } from 'lucide-react';
import toast from 'react-hot-toast';

export default function AddSubjectPaper() {
  const { examId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: exam } = useQuery({ queryKey: ['exam', examId], queryFn: () => api.getExam(examId) });

  const [subjectName, setSubjectName] = useState('');
  const [subjectCode, setSubjectCode] = useState('');
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerKey, setAnswerKey] = useState(null);

  const mutation = useMutation({
    mutationFn: () => api.createSubjectPaper(examId, {
      subject_name: subjectName,
      subject_code: subjectCode,
      question_paper: questionPaper,
      answer_key: answerKey,
    }),
    onSuccess: () => {
      toast.success('Subject paper added — you can now upload student submissions for it.');
      queryClient.invalidateQueries(['exam', examId]);
      queryClient.invalidateQueries(['subjectPapers', examId]);
      navigate(`/exam/${examId}`);
    },
    onError: (err) => toast.error('Failed to add subject: ' + (err.response?.data?.detail || err.message)),
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!subjectName.trim()) return toast.error('Subject name is required');
    if (!subjectCode.trim()) return toast.error('Subject code is required');
    if (!questionPaper) return toast.error('Question Paper PDF is required');
    if (!answerKey) return toast.error('Answer Key PDF is required');
    mutation.mutate();
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors';
  const labelClass =
    'absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600';

  return (
    <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="py-8 space-y-6 max-w-2xl mx-auto">
      <BackLink to={`/exam/${examId}`} label="Back to Exam" />

      <PageHeader
        title="Add Subject Paper"
        subtitle={exam ? `Adding a subject under "${exam.title}"` : 'Add a subject with its question paper and answer key.'}
      />

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-card space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="relative">
            <input type="text" id="subjectName" value={subjectName} onChange={(e) => setSubjectName(e.target.value)} className={inputClass} placeholder=" " required />
            <label htmlFor="subjectName" className={labelClass}>Subject Name (e.g. Physics)</label>
          </div>
          <div className="relative">
            <input type="text" id="subjectCode" value={subjectCode} onChange={(e) => setSubjectCode(e.target.value)} className={inputClass} placeholder=" " required />
            <label htmlFor="subjectCode" className={labelClass}>Subject Code (e.g. PHY101)</label>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <FileUpload label="Question Paper PDF" file={questionPaper} setFile={setQuestionPaper} acceptDescription="Upload question paper PDF" />
          <FileUpload label="Answer Key PDF" file={answerKey} setFile={setAnswerKey} acceptDescription="Upload the answer key PDF" />
        </div>

        <div className="bg-amber-50/50 border border-amber-100 rounded-xl p-4 flex items-start space-x-2.5">
          <ShieldAlert className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-[11px] text-amber-800 leading-relaxed">
            You will be recorded as the grading teacher for this subject — only you (or an admin) will be able to view and grade submissions under it.
          </p>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-100">
          <button
            type="submit"
            disabled={mutation.isLoading}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-card hover:shadow-card-hover transition-all active:scale-[1.02] disabled:opacity-50 disabled:pointer-events-none min-h-[44px]"
          >
            {mutation.isLoading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Adding...</span>
              </>
            ) : (
              <>
                <PlusCircle className="h-4 w-4" />
                <span>Add Subject Paper</span>
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
