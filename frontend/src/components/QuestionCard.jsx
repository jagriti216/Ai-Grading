import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, ChevronUp, Sparkles, CheckCircle, XCircle, Lightbulb } from 'lucide-react';
import ScoreBar from './ScoreBar';

export default function QuestionCard({ question, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const {
    q_number,
    question_text,
    student_answer,
    expected_answer,
    score,
    max_marks,
    feedback = {},
    breakdown = {},
  } = question;

  const percentage = max_marks > 0 ? (score / max_marks) * 100 : 0;

  let accentBorder;
  let badgeColor;

  if (percentage >= 70) {
    accentBorder = 'hover:border-emerald-300';
    badgeColor = 'bg-emerald-50/50 text-emerald-700 border-emerald-200';
  } else if (percentage >= 40) {
    accentBorder = 'hover:border-amber-300';
    badgeColor = 'bg-amber-50/50 text-amber-700 border-amber-200';
  } else {
    accentBorder = 'hover:border-rose-300';
    badgeColor = 'bg-rose-50/50 text-rose-700 border-rose-200';
  }

  const toggle = () => setIsOpen(!isOpen);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggle();
    }
  };

  return (
    <div className={`border border-slate-200 rounded-2xl bg-white shadow-card transition-all duration-300 overflow-hidden print-card ${accentBorder}`}>
      <div
        role="button"
        tabIndex={0}
        aria-expanded={isOpen}
        onClick={toggle}
        onKeyDown={handleKeyDown}
        className="p-4 sm:p-5 flex items-center justify-between cursor-pointer hover:bg-slate-50/40 select-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500"
      >
        <div className="flex-1 min-w-0 pr-4 flex items-center space-x-3">
          <span className={`px-2.5 py-0.5 rounded-lg text-xs font-bold border shrink-0 ${badgeColor}`}>
            Q{q_number}
          </span>
          <h4 className="text-sm font-semibold text-slate-800 truncate">
            {question_text || `Question Prompt ${q_number}`}
          </h4>
        </div>

        <div className="flex items-center space-x-4 shrink-0">
          <div className="w-28 sm:w-40 hidden sm:block">
            <ScoreBar score={score} maxMarks={max_marks} showText={false} />
          </div>
          <span className="text-xs font-bold text-slate-600 bg-slate-100/70 border border-slate-200 px-2 py-0.5 rounded-md">
            {score} / {max_marks}
          </span>
          <div className="text-slate-400 no-print">
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
          >
            <div className="px-5 pb-6 border-t border-slate-100 bg-slate-50/20 space-y-6">
              {question_text && (
                <div className="pt-4">
                  <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1.5">Question Prompt</h5>
                  <p className="text-sm text-slate-700 font-medium bg-white p-3.5 rounded-xl border border-slate-100 leading-relaxed">
                    {question_text}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="space-y-1.5">
                  <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Student's Answer</h5>
                  <div className="text-sm text-slate-800 bg-white p-4 rounded-xl border border-slate-200/80 min-h-[90px] whitespace-pre-wrap leading-relaxed shadow-sm">
                    {student_answer || <span className="text-slate-400 italic font-medium">No answer detected.</span>}
                  </div>
                </div>
                <div className="space-y-1.5">
                  <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Expected Answer</h5>
                  <div className="text-sm text-slate-800 bg-white p-4 rounded-xl border border-slate-200/80 min-h-[90px] whitespace-pre-wrap leading-relaxed shadow-sm">
                    {expected_answer || <span className="text-slate-400 italic font-medium">No answer key provided.</span>}
                  </div>
                </div>
              </div>

              <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm space-y-4">
                <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
                  <Sparkles className="h-4 w-4 text-indigo-500" />
                  <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider">AI Scorer Match</h5>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                  {[
                    { label: 'DeBERTa Score', value: breakdown.deberta_score },
                    { label: 'SBERT Similarity', value: breakdown.sbert_score },
                    { label: 'Concept Similarity', value: breakdown.concept_score },
                  ].map((item) => (
                    <div key={item.label} className="space-y-1.5">
                      <span className="block text-[11px] font-semibold text-slate-500">{item.label}</span>
                      <ScoreBar score={((item.value || 0) * 10).toFixed(1)} maxMarks={10} showText={true} />
                    </div>
                  ))}
                </div>
                {breakdown.method && (
                  <p className="text-[10px] text-slate-500 italic pt-2 border-t border-slate-50">
                    Grading Method: <span className="font-semibold text-slate-600">{breakdown.method}</span>
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Grading Comments & Tips</h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-emerald-50/40 border border-emerald-100 rounded-2xl p-4 space-y-2">
                    <div className="flex items-center space-x-1.5 text-emerald-800">
                      <CheckCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-[11px] font-bold uppercase tracking-wider">Correct Details</span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {feedback.correct || 'Accurately answered all parts of the rubric.'}
                    </p>
                  </div>

                  <div className="bg-rose-50/40 border border-rose-100 rounded-2xl p-4 space-y-2">
                    <div className="flex items-center space-x-1.5 text-rose-800">
                      <XCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-[11px] font-bold uppercase tracking-wider">Missing Concepts</span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {feedback.missing || 'No critical concepts missing.'}
                    </p>
                  </div>

                  <div className="bg-indigo-50/40 border border-indigo-100 rounded-2xl p-4 space-y-2">
                    <div className="flex items-center space-x-1.5 text-indigo-900">
                      <Lightbulb className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-[11px] font-bold uppercase tracking-wider">Evaluation Tip</span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {feedback.tip || 'Verify syntax structure and terminology.'}
                    </p>
                  </div>
                </div>

                {feedback.summary && (
                  <div className="bg-white p-3.5 rounded-xl border border-slate-200/80 mt-2">
                    <span className="block text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1">AI Evaluator Notes</span>
                    <p className="text-xs text-slate-700 leading-relaxed">{feedback.summary}</p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
