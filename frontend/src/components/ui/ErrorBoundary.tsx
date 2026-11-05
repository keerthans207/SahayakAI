import React from "react";
import { AlertTriangle } from "lucide-react";

interface Props { children: React.ReactNode; fallback?: React.ReactNode; }
interface State { hasError: boolean; error?: Error; }

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex flex-col items-center gap-3 p-8 text-center"
             role="alert">
          <AlertTriangle className="h-10 w-10 text-amber-500" aria-hidden />
          <p className="font-semibold text-base" style={{ color: "hsl(var(--color-text))" }}>
            Something went wrong
          </p>
          <p className="text-sm" style={{ color: "hsl(var(--color-text-muted))" }}>
            {this.state.error?.message ?? "An unexpected error occurred."}
          </p>
          <button
            className="btn-primary text-sm"
            onClick={() => this.setState({ hasError: false })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
