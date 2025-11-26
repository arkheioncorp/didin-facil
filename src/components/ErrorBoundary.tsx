import { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen w-full flex-col items-center justify-center bg-background p-4 text-foreground">
          <h1 className="mb-4 text-4xl font-bold text-destructive">Oops!</h1>
          <p className="mb-4 text-xl">Something went wrong.</p>
          <div className="mb-6 max-w-md overflow-auto rounded bg-muted p-4 text-sm text-muted-foreground">
            {this.state.error?.message}
          </div>
          <button
            className="rounded bg-primary px-4 py-2 font-bold text-primary-foreground hover:bg-primary/90"
            onClick={() => window.location.reload()}
          >
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
