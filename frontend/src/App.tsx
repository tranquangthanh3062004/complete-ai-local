import { Routes, Route, BrowserRouter, NavLink } from 'react-router-dom';
import Home from '@/pages/Home';
import MapPage from '@/pages/MapPage';
import AdminDashboard from '@/pages/AdminDashboard';
import { Toaster } from '@/components/ui/toaster';
import { Bot, Map, LayoutDashboard, Train } from 'lucide-react';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col font-sans dark">
        {/* Background gradient blobs */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
          <div className="absolute -top-40 -left-40 w-96 h-96 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute top-1/3 -right-40 w-80 h-80 bg-purple-500/8 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-1/3 w-72 h-72 bg-blue-500/8 rounded-full blur-3xl" />
        </div>

        {/* Header */}
        <header className="sticky top-0 z-50 w-full glass border-b border-border/40">
          <div className="container flex h-14 max-w-screen-2xl items-center px-4">
            {/* Logo */}
            <a className="mr-6 flex items-center gap-2.5" href="/">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center shadow-lg">
                <Train size={16} className="text-white" />
              </div>
              <span className="font-bold text-sm tracking-tight hidden sm:block">
                HN<span className="text-primary">Transit</span> AI
              </span>
            </a>

            {/* Nav */}
            <nav className="flex items-center gap-1 text-sm">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-200 font-medium
                  ${isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`
                }
              >
                <Bot size={15} />
                <span>Chat</span>
              </NavLink>
              <NavLink
                to="/map"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-200 font-medium
                  ${isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`
                }
              >
                <Map size={15} />
                <span>Bản đồ</span>
              </NavLink>
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all duration-200 font-medium
                  ${isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'}`
                }
              >
                <LayoutDashboard size={15} />
                <span>Dashboard</span>
              </NavLink>
            </nav>

            {/* Status badge */}
            <div className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="hidden sm:block">Online</span>
            </div>
          </div>
        </header>

        <main className="flex-1 flex flex-col relative z-10">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/admin" element={<AdminDashboard />} />
          </Routes>
        </main>
      </div>
      <Toaster />
    </BrowserRouter>
  );
}

export default App;
