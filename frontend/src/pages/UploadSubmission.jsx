import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api';
import FileUpload from '../components/FileUpload';
import StatusBadge from '../components/StatusBadge';
import BackLink from '../components/ui/BackLink';
import PageHeader from '../components/ui/PageHeader';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, UploadCloud, AlertCircle, CheckCircle, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';

const STEPS = ['Upload', 'Processing', 'Results'];

const CYCLING_MESSAGES = [
  'Extracting text from PDF...',
  'Parsing question structure...',
  'Running AI grading model...',
  'Generating feedback...',
  'Saving results...',
];

function StepIndicator({ currentStep }) {
  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-card flex items-center justify-between max-w-lg mx-auto select-none no-print">
      {STEPS.map((label, index) => {
        const stepNum = index + 1;
        const isComplete = currentStep > stepNum;
        const isActive = currentStep >= stepNum;
        return (
          <div key={label} className="contents">
            <div className="flex items-center space-x-2">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  isActive ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isComplete ? '✓' : stepNum}
              </div>
              <span className={`text-xs font-bold hidden xs:inline ${isActive ? 'text-indigo-600' : 'text-slate-400'}`}>
                {label}
              </span>
            </div>
            {index < STEPS.length - 1 && (
              <div className="flex-1 mx-2 h-0.5 rounded-full bg-slate-100 overflow-hidden min-w-[24px]">
                <div
                  className="h-full bg-indigo-500 transition-all duration-500 ease-out"
                  style={{ width: currentStep > stepNum ? '100%' : currentStep === stepNum ? '50%' : '0%' }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function UploadSubmission() {
  const { subjectPaperId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const resumeSubmissionId = searchParams.get('resume');

  const [rollNo, setRollNo] = useState('');
  const [studentName, setStudentName] = useState('');
  const [studentAnswer, setStudentAnswer] = useState(null);
  const [activeSubmissionId, setActiveSubmissionId] = useState(resumeSubmissionId || null);
  const [cycledMessageIndex, setCycledMessageIndex] = useState(0);

  // Poll the grading status via React Query instead of a hand-rolled
  // setInterval — refetchInterval stops itself once status is a terminal
  // state (graded/failed), same behavior as before but without manually
  // managing the interval/cleanup lifecycle.
  const { data: statusData, error: statusError } = useQuery({
    queryKey: ['submissionStatus', activeSubmissionId],
    queryFn: () => api.getGradingStatus(activeSubmissionId),
    enabled: !!activeSubmissionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'graded' || status === 'failed' ? false : 3000;
    },
  });

  const gradingStatus = activeSubmissionId ? statusData?.status ?? 'grading' : null;
  const currentStep = !activeSubmissionId ? 1 : gradingStatus === 'graded' ? 3 : 2;

  useEffect(() => {
    let msgInterval;
    if (currentStep === 2) {
      msgInterval = setInterval(() => {
        setCycledMessageIndex((prev) => (prev + 1) % CYCLING_MESSAGES.length);
      }, 3000);
    }
    return () => clearInterval(msgInterval);
  }, [currentStep]);

  useEffect(() => {
    if (statusError) console.error('Error polling status:', statusError);
  }, [statusError]);

  useEffect(() => {
    if (statusData?.status === 'failed') {
      toast.error('AI grading pipeline failed. Please try again.');
    }
  }, [statusData]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!rollNo.trim()) return toast.error('Roll Number is required');
    if (!studentName.trim()) return toast.error('Student Name is required');
    if (!studentAnswer) return toast.error('Student Answer PDF sheet is required');

    setCycledMessageIndex(0);

    try {
      const uploadRes = await api.uploadSubmission(subjectPaperId, {
        roll_no: rollNo,
        student_name: studentName,
        student_answer: studentAnswer,
      });
      const subId = uploadRes.submission_id;

      await api.triggerGrading(subId);
      setActiveSubmissionId(subId);
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message;
      toast.error('Upload / grading trigger failed: ' + errMsg);
    }
  };

  const inputClass =
    'block px-3.5 pb-2.5 pt-4 w-full text-sm text-slate-900 bg-slate-50/50 rounded-xl border border-slate-200 appearance-none focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 peer transition-colors';

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="max-w-3xl mx-auto py-8 space-y-8"
    >
      <BackLink to={`/subject/${subjectPaperId}`} label="Back to Subject" />

      <PageHeader
        title="Evaluate Student Answer Sheet"
        subtitle="Upload a scanned PDF containing a student's handwriting to grade it."
      />

      <StepIndicator currentStep={currentStep} />

      <AnimatePresence mode="wait">
        {currentStep === 1 && (
          <motion.form
            key="step1-form"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            onSubmit={handleSubmit}
            className="bg-white border border-slate-200/80 rounded-2xl p-6 sm:p-8 shadow-card space-y-6"
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="relative">
                  <input
                    type="text"
                    id="rollNo"
                    value={rollNo}
                    onChange={(e) => setRollNo(e.target.value)}
                    className={inputClass}
                    placeholder=" "
                    required
                  />
                  <label
                    htmlFor="rollNo"
                    className="absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600"
                  >
                    Class Roll Number
                  </label>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    id="studentName"
                    value={studentName}
                    onChange={(e) => setStudentName(e.target.value)}
                    className={inputClass}
                    placeholder=" "
                    required
                  />
                  <label
                    htmlFor="studentName"
                    className="absolute text-xs font-bold text-slate-400 duration-200 transform -translate-y-3.5 scale-90 top-3.5 z-10 origin-[0] bg-white px-1.5 left-3 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-placeholder-shown:text-slate-500 peer-placeholder-shown:top-3.5 peer-focus:top-3.5 peer-focus:-translate-y-3.5 peer-focus:scale-90 peer-focus:text-indigo-600"
                  >
                    Student Full Name
                  </label>
                </div>
              </div>

              <FileUpload
                label="Student Answer Sheet PDF"
                file={studentAnswer}
                setFile={setStudentAnswer}
                acceptDescription="Upload the student's handwritten answer script in PDF"
              />
            </div>

            <div className="flex justify-end pt-4 border-t border-slate-100">
              <button
                type="submit"
                className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-card hover:shadow-card-hover transition-all active:scale-[1.01] min-h-[44px]"
              >
                <UploadCloud className="h-4 w-4" />
                <span>Submit for AI Grading</span>
              </button>
            </div>
          </motion.form>
        )}

        {currentStep === 2 && (
          <motion.div
            key="step2-loading"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            className="bg-white border border-slate-200 rounded-2xl p-8 sm:p-12 text-center shadow-card space-y-6"
          >
            <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
              <div className="absolute inset-0 rounded-full bg-indigo-50 border border-indigo-100 animate-ping opacity-75 motion-reduce:animate-none" />
              <div className="w-16 h-16 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 relative">
                <RefreshCw className="h-8 w-8 animate-spin" />
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-800 font-display">Processing Grading Models</h3>
              <p className="text-sm text-slate-500 font-semibold max-w-sm mx-auto h-5">
                {CYCLING_MESSAGES[cycledMessageIndex]}
              </p>
            </div>

            <div className="flex justify-center pt-2">
              <StatusBadge status={gradingStatus || 'grading'} />
            </div>

            {gradingStatus === 'failed' && (
              <div className="pt-4 border-t border-slate-100 max-w-md mx-auto space-y-3">
                <div className="flex items-center space-x-2 text-rose-600 text-xs font-semibold justify-center">
                  <AlertCircle className="h-4 w-4" />
                  <span>Evaluation failed. Please verify PDF layout.</span>
                </div>
                <button
                  type="button"
                  onClick={() => setActiveSubmissionId(null)}
                  className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-4 py-2.5 rounded-xl transition-all min-h-[44px]"
                >
                  Reset and Upload Again
                </button>
              </div>
            )}
          </motion.div>
        )}

        {currentStep === 3 && (
          <motion.div
            key="step3-success"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white border border-slate-200 rounded-2xl p-8 sm:p-12 text-center shadow-card space-y-6 max-w-xl mx-auto"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto ring-8 ring-emerald-100/50"
            >
              <CheckCircle className="h-8 w-8" />
            </motion.div>

            <div className="space-y-1.5">
              <h3 className="text-xl font-bold text-slate-900 font-display">Grading Complete!</h3>
              <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">
                The GradeAI models have finished indexing OCR transcriptions and scoring answers.
              </p>
            </div>

            <button
              onClick={() => navigate(`/results/${activeSubmissionId}`)}
              className="w-full max-w-xs inline-flex items-center justify-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-xl text-sm font-bold shadow-card transition-all active:scale-[1.01] min-h-[44px]"
            >
              <span>View Evaluation Results</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
