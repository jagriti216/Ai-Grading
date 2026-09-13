import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AnimatePresence, motion } from 'framer-motion';

import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import LoadingSpinner from './components/ui/LoadingSpinner';

import Login from './pages/Login';

const ChangePassword = lazy(() => import('./pages/ChangePassword'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const StudentDashboard = lazy(() => import('./pages/StudentDashboard'));
const AdminUsers = lazy(() => import('./pages/AdminUsers'));
const ExamList = lazy(() => import('./pages/ExamList'));
const ExamDetail = lazy(() => import('./pages/ExamDetail'));
const CreateExam = lazy(() => import('./pages/CreateExam'));
const AddSubjectPaper = lazy(() => import('./pages/AddSubjectPaper'));
const SubjectDetail = lazy(() => import('./pages/SubjectDetail'));
const UploadSubmission = lazy(() => import('./pages/UploadSubmission'));
const ResultPage = lazy(() => import('./pages/ResultPage'));
const Analytics = lazy(() => import('./pages/Analytics'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

function HomeRoute() {
  const { role } = useAuth();
  return role === 'student' ? <StudentDashboard /> : <Dashboard />;
}

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.main
        key={location.pathname}
        initial="initial"
        animate="animate"
        exit="exit"
        variants={pageVariants}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16"
      >
        <Suspense fallback={<LoadingSpinner />}>
        <Routes location={location}>
          <Route path="/login" element={<Login />} />

          <Route path="/change-password" element={
            <ProtectedRoute><ChangePassword /></ProtectedRoute>
          } />

          <Route path="/" element={
            <ProtectedRoute><HomeRoute /></ProtectedRoute>
          } />

          <Route path="/admin/users" element={
            <ProtectedRoute roles={['admin']}><AdminUsers /></ProtectedRoute>
          } />

          <Route path="/exams" element={
            <ProtectedRoute roles={['admin', 'teacher']}><ExamList /></ProtectedRoute>
          } />
          <Route path="/exam/new" element={
            <ProtectedRoute roles={['admin', 'teacher']}><CreateExam /></ProtectedRoute>
          } />
          <Route path="/exam/:examId" element={
            <ProtectedRoute roles={['admin', 'teacher']}><ExamDetail /></ProtectedRoute>
          } />
          <Route path="/exam/:examId/subjects/new" element={
            <ProtectedRoute roles={['admin', 'teacher']}><AddSubjectPaper /></ProtectedRoute>
          } />

          <Route path="/subject/:subjectPaperId" element={
            <ProtectedRoute roles={['admin', 'teacher']}><SubjectDetail /></ProtectedRoute>
          } />
          <Route path="/subject/:subjectPaperId/upload" element={
            <ProtectedRoute roles={['admin', 'teacher']}><UploadSubmission /></ProtectedRoute>
          } />

          <Route path="/analytics" element={
            <ProtectedRoute roles={['admin', 'teacher']}><Analytics /></ProtectedRoute>
          } />

          <Route path="/results/:submissionId" element={
            <ProtectedRoute><ResultPage /></ProtectedRoute>
          } />
        </Routes>
        </Suspense>
      </motion.main>
    </AnimatePresence>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="flex flex-col min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50/40">
            <Navbar />
            <AnimatedRoutes />
          </div>
        </Router>
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'text-sm font-semibold rounded-xl text-slate-800 bg-white border border-slate-200 shadow-card',
            success: {
              duration: 4000,
              iconTheme: { primary: '#4f46e5', secondary: '#fff' },
            },
            error: { duration: 5000 },
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
