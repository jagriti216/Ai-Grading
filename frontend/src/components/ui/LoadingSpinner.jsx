import { RefreshCw } from 'lucide-react';

export default function LoadingSpinner({ message = 'Loading...', size = 'md' }) {
  const iconSize = size === 'lg' ? 'h-10 w-10' : 'h-8 w-8';

  return (
    <div className="flex flex-col items-center justify-center min-h-[450px] space-y-4 animate-fadeIn">
      <RefreshCw className={`${iconSize} text-primary-500 animate-spin`} />
      <p className="text-sm font-medium text-slate-500">{message}</p>
    </div>
  );
}
