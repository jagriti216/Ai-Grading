import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { motion } from 'framer-motion';
import {
  FileText,
  Users,
  Award,
  ArrowRight,
  Plus,
  UploadCloud,
  RefreshCw,
  TrendingUp,
  Clock,
} from 'lucide-react';
import toast from 'react-hot-toast';
import PageHeader from '../components/ui/PageHeader';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { useAuth } from '../hooks/useAuth';

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, role } = useAuth();
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: api.getDashboardStats,
    onError: (err) => {
      toast.error('Failed to load dashboard: ' + (err.response?.data?.detail || err.message));
    },
  });

  const getGreeting = () => {
    const hr = new Date().getHours();
    const timeOfDay = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening';
    const roleLabel = role === 'admin' ? 'Admin' : 'Teacher';
    return `${timeOfDay}, ${user?.name || roleLabel}`;
  };

  if (isLoading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-100 rounded-2xl p-8 text-center max-w-xl mx-auto my-12 shadow-card animate-fadeIn">
        <h3 className="text-lg font-bold text-rose-800 mb-2">Error Loading Dashboard</h3>
        <p className="text-sm text-rose-600 mb-6">{error.response?.data?.detail || error.message}</p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center space-x-2 bg-rose-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-rose-700 transition-colors"
        >
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  const {
    total_exams = 0,
    total_graded_submissions = 0,
    average_percentage = 0,
    recent_activity = [],
  } = data || {};

  const getPassRate = () => {
    if (!recent_activity || recent_activity.length === 0) return 0;
    const passes = recent_activity.filter((r) => r.percentage >= 40).length;
    return Math.round((passes / recent_activity.length) * 100);
  };
  const passRate = getPassRate();

  const statCards = [
    {
      label: 'Exams Created',
      value: total_exams,
      link: { to: '/exams', text: 'View exams', color: 'text-primary-600 hover:text-primary-700' },
      icon: FileText,
      gradient: 'from-indigo-500 to-primary-600',
      shadow: 'shadow-indigo-200/50',
    },
    {
      label: 'Students Graded',
      value: total_graded_submissions,
      link: { to: '/exams', text: 'View list', color: 'text-emerald-600 hover:text-emerald-700' },
      icon: Users,
      gradient: 'from-emerald-400 to-emerald-600',
      shadow: 'shadow-emerald-200/50',
    },
    {
      label: 'Average Accuracy',
      value: `${average_percentage}%`,
      sub: 'Across all test sheets',
      icon: Award,
      gradient: 'from-amber-400 to-amber-600',
      shadow: 'shadow-amber-200/50',
    },
    {
      label: 'Pass Rate',
      value: `${passRate || 100}%`,
      sub: 'Score ≥ 40%',
      icon: TrendingUp,
      gradient: 'from-violet-400 to-violet-600',
      shadow: 'shadow-violet-200/50',
    },
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className="py-8 space-y-8"
    >
      <motion.div variants={itemVariants}>
        <PageHeader
          title={`${getGreeting()} 👋`}
          subtitle="Here is what's happening with your exams and student submissions today."
          action={
            <button
              onClick={() => {
                refetch();
                toast.success('Dashboard metrics updated');
              }}
              disabled={isFetching}
              className="flex items-center space-x-2 border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 text-slate-600 px-4 py-2.5 rounded-xl text-sm font-semibold shadow-card transition-all active:scale-95 disabled:opacity-50 min-h-[44px]"
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
              <span>Sync Dashboard</span>
            </button>
          }
        />
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card) => (
          <motion.div
            key={card.label}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-card hover:shadow-card-hover transition-shadow flex items-start justify-between"
          >
            <div className="space-y-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block">{card.label}</span>
              <span className="text-4xl font-extrabold text-slate-900 block font-display">{card.value}</span>
              {card.link ? (
                <Link to={card.link.to} className={`inline-flex items-center text-xs font-bold ${card.link.color} transition-colors`}>
                  <span>{card.link.text}</span>
                  <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Link>
              ) : (
                <span className="text-[10px] text-slate-400 font-semibold block">{card.sub}</span>
              )}
            </div>
            <div className={`p-3 bg-gradient-to-br ${card.gradient} rounded-2xl text-white shadow-md ${card.shadow}`}>
              <card.icon className="h-5 w-5" />
            </div>
          </motion.div>
        ))}
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          whileHover={{ scale: 1.01, y: -2 }}
          onClick={() => navigate('/exam/new')}
          className="bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-950 rounded-2xl p-6 text-white shadow-card hover:shadow-card-hover transition-all cursor-pointer flex items-center justify-between group min-h-[120px]"
        >
          <div className="space-y-2">
            <h3 className="text-lg font-bold flex items-center space-x-2 font-display">
              <Plus className="h-5 w-5 text-indigo-400 bg-indigo-950/60 rounded-full p-0.5 border border-indigo-800" />
              <span>Create Exam Rubric</span>
            </h3>
            <p className="text-indigo-200/80 text-xs max-w-sm">
              Register metadata and upload question papers with answer keys to configure an AI grading layout.
            </p>
          </div>
          <ArrowRight className="h-6 w-6 text-indigo-400 group-hover:translate-x-1.5 transition-transform duration-300 mr-2 shrink-0" />
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.01, y: -2 }}
          onClick={() => navigate('/exams')}
          className="bg-gradient-to-br from-slate-900 via-slate-950 to-indigo-950 rounded-2xl p-6 text-white shadow-card hover:shadow-card-hover transition-all cursor-pointer flex items-center justify-between group min-h-[120px]"
        >
          <div className="space-y-2">
            <h3 className="text-lg font-bold flex items-center space-x-2 font-display">
              <UploadCloud className="h-5 w-5 text-emerald-400 bg-slate-900/60 rounded-full p-0.5" />
              <span>Upload Student Sheet</span>
            </h3>
            <p className="text-indigo-200/80 text-xs max-w-sm">
              Evaluate scanning/handwriting sheets by selecting an exam from your rubric lists.
            </p>
          </div>
          <ArrowRight className="h-6 w-6 text-indigo-400 group-hover:translate-x-1.5 transition-transform duration-300 mr-2 shrink-0" />
        </motion.div>
      </motion.div>

      <motion.div variants={itemVariants} className="bg-white border border-slate-200/80 rounded-2xl shadow-card p-6 sm:p-8 space-y-6">
        <div>
          <h3 className="text-lg font-bold text-slate-950 font-display">Evaluation Timeline Activity</h3>
          <p className="text-xs text-slate-500 mt-1">Real-time evaluations completed by GradeAI models.</p>
        </div>

        {recent_activity.length === 0 ? (
          <div className="py-12 text-center text-slate-400 space-y-3">
            <Clock className="h-10 w-10 mx-auto text-slate-300" />
            <div>
              <p className="text-sm font-semibold text-slate-600">No graded activities recorded.</p>
              <p className="text-xs text-slate-400 max-w-xs mx-auto mt-0.5">
                Evaluations will display here once sheets are uploaded.
              </p>
            </div>
          </div>
        ) : (
          <div className="relative pl-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-100 space-y-6">
            {recent_activity.map((activity, index) => {
              const pct = activity.percentage || 0;
              let dotColor = 'bg-rose-500 ring-rose-100';
              let textBg = 'bg-rose-50 text-rose-700 border-rose-100';
              if (pct >= 70) {
                dotColor = 'bg-emerald-500 ring-emerald-100';
                textBg = 'bg-emerald-50 text-emerald-700 border-emerald-100';
              } else if (pct >= 40) {
                dotColor = 'bg-amber-500 ring-amber-100';
                textBg = 'bg-amber-50 text-amber-700 border-amber-100';
              }

              return (
                <motion.div
                  key={activity.submission_id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.3 }}
                  className="relative group"
                >
                  <span className={`absolute -left-[30px] top-1.5 w-4 h-4 rounded-full ring-4 ${dotColor}`} />
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 bg-slate-50/30 group-hover:bg-slate-50 hover:border-slate-300 transition-all duration-200">
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex items-center flex-wrap gap-2">
                        <span className="text-sm font-bold text-slate-900">{activity.student_name}</span>
                        <span className="text-[11px] font-semibold text-slate-500">submitted sheet for</span>
                        <span className="text-xs font-bold text-slate-800">{activity.exam_title}</span>
                      </div>
                      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-xs text-slate-500 font-medium">
                        <span className="flex items-center">
                          <Clock className="h-3.5 w-3.5 text-slate-400 mr-1" />
                          {new Date(activity.graded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <span className="hidden sm:inline">•</span>
                        <span>{new Date(activity.graded_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${textBg} tracking-wide`}>
                        {activity.total_scored} / {activity.total_marks} ({Math.round(pct)}%)
                      </span>
                      <Link
                        to={`/results/${activity.submission_id}`}
                        className="text-xs font-bold text-primary-600 hover:text-primary-700 flex items-center space-x-1 hover:underline"
                      >
                        <span>View Results</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
