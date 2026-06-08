import { Route, Routes } from "react-router-dom";

/**
 * Minimal scaffold placeholder — proves the dev server boots, providers are
 * wired (QueryClient + Router), and Tailwind v4 + shadcn theming applies.
 * Real routes (/login, /signup, /forgot-password, /reset-password, /) land
 * in Plan 03 per 01-SKELETON.md.
 */
function ScaffoldHome() {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background">
      <p className="text-display text-foreground">Library — scaffold OK</p>
    </main>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<ScaffoldHome />} />
    </Routes>
  );
}

export default App;
