import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function BackLink({ to, onClick, label = 'Back', className = '' }) {
  const navigate = useNavigate();
  const baseClass = `inline-flex items-center space-x-2 text-slate-500 hover:text-slate-800 text-sm font-semibold transition-colors no-print ${className}`;

  if (to) {
    return (
      <Link to={to} className={baseClass}>
        <ArrowLeft className="h-4 w-4" />
        <span>{label}</span>
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick || (() => navigate(-1))}
      className={baseClass}
    >
      <ArrowLeft className="h-4 w-4" />
      <span>{label}</span>
    </button>
  );
}
