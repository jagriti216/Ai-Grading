import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import BackLink from '../components/ui/BackLink';
import PageHeader from '../components/ui/PageHeader';
import { motion } from 'framer-motion';
import { PlusCircle, RefreshCw, Lightbulb } from 'lucide-react';
import toast from 'react-hot-toast';

export default function CreateExam() {
  const [title, setTitle] = useState('');
  const [term, setTerm] = useState('');

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: api.createExam,
    onSuccess: (data) => {
      toast.success('Exam created — now add subject papers under it.');
      queryClient.invalidateQueries(['exams']);
      queryClient.invalidateQueries(['dashboardStats']);
      navigate(`/exam/${data.exam_id}`);
    },
    onError: (err) => {
      toast.error('Failed to create exam: ' + (err.response?.data?.detail || err.message));
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!title.trim()) return toast.error('Exam title is required');
    mutation.mutate({ title: title.trim(), term: term.trim() });
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors';
  const labelClass =
    'absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600';

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="py-8 space-y-6 max-w-2xl mx-auto"
    >
      <BackLink label="Back" />

      <PageHeader
        title="Create an Exam"
        subtitle="An exam is a container — e.g. 'Mid-Term 2026'. Add subject papers (Physics, Chemistry, ...) under it next."
      />

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-card space-y-6">
        <div className="relative">
          <input type="text" id="title" value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} placeholder=" " required />
          <label htmlFor="title" className={labelClass}>Exam Title (e.g. "Mid-Term 2026")</label>
        </div>
        <div className="relative">
          <input type="text" id="term" value={term} onChange={(e) => setTerm(e.target.value)} className={inputClass} placeholder=" " />
          <label htmlFor="term" className={labelClass}>Term / Batch (optional)</label>
        </div>

        <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 flex items-start space-x-2.5">
          <Lightbulb className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
          <p className="text-xs text-indigo-700 leading-relaxed">
            After creating the exam, you'll add one or more subject papers to it — each with its own question paper, answer key, subject name, and subject code. Multiple teachers can each own different subjects under the same exam.
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
                <span>Creating...</span>
              </>
            ) : (
              <>
                <PlusCircle className="h-4 w-4" />
                <span>Create Exam</span>
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
