import { motion } from 'framer-motion';

export default function ScoreBar({ score, maxMarks, showText = true }) {
  const scoreVal = parseFloat(score) || 0;
  const maxVal = parseFloat(maxMarks) || 100;
  const percentage = maxVal > 0 ? (scoreVal / maxVal) * 100 : 0;
  const roundedPercentage = Math.round(percentage * 10) / 10;

  const color = percentage >= 70 ? 'from-emerald-400 to-emerald-600'
              : percentage >= 40 ? 'from-amber-400 to-amber-500'
              : 'from-red-400 to-red-500';

  const textBg = percentage >= 70 ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
               : percentage >= 40 ? 'bg-amber-50 text-amber-700 border border-amber-200'
               : 'bg-rose-50 text-rose-700 border border-rose-200';

  return (
    <div className="w-full flex items-center space-x-3">
      <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percentage, 100)}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      {showText && (
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${textBg} min-w-[70px] text-center shrink-0`}>
          {scoreVal} / {maxVal} ({roundedPercentage}%)
        </span>
      )}
    </div>
  );
}
