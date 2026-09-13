
export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-12 text-center space-y-4 shadow-card animate-fadeIn">
      {Icon && <Icon className="h-12 w-12 text-slate-300 mx-auto" />}
      <div className="space-y-1">
        <h3 className="text-base font-bold text-slate-800">{title}</h3>
        {description && (
          <p className="text-sm text-slate-500 max-w-sm mx-auto">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
