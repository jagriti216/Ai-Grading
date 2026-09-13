
export default function StatusBadge({ status }) {
  const normalized = status?.toLowerCase() || 'unknown';

  const styles = {
    graded:   'bg-emerald-50 text-emerald-700 border-emerald-200',
    grading:  'bg-blue-50 text-blue-700 border-blue-200',
    uploaded: 'bg-slate-50 text-slate-600 border-slate-200',
    failed:   'bg-rose-50 text-rose-700 border-rose-200',
    unknown:  'bg-slate-50 text-slate-600 border-slate-200',
  };

  const displayLabels = {
    graded:   'Graded',
    grading:  'Grading',
    uploaded: 'Uploaded',
    failed:   'Failed',
  };

  const label = displayLabels[normalized] || status;
  const currentStyle = styles[normalized] || styles.unknown;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${currentStyle}`}>
      {normalized === 'grading' && (
        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse motion-reduce:animate-none" aria-hidden="true" />
      )}
      <span>{label}</span>
    </span>
  );
}
