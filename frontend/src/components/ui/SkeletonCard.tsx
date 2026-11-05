export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card animate-pulse">
      <div className="mb-3 h-4 w-3/4 rounded"
           style={{ backgroundColor: "hsl(var(--color-surface-2))" }} />
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="mt-2 h-3 rounded"
             style={{
               backgroundColor: "hsl(var(--color-surface-2))",
               width: i === lines - 1 ? "55%" : "100%",
             }} />
      ))}
    </div>
  );
}
