import { Routes, Route, BrowserRouter, NavLink } from 'react-router-dom';
import Home from '@/pages/Home';
import MapPage from '@/pages/MapPage';
import AdminDashboard from '@/pages/AdminDashboard';
import { Toaster } from '@/components/ui/toaster';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background text-foreground flex flex-col font-sans">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 max-w-screen-2xl items-center">
            <div className="mr-4 hidden md:flex">
              <a className="mr-6 flex items-center space-x-2" href="/">
                <span className="hidden font-bold sm:inline-block">
                  GTCC AI Bot
                </span>
              </a>
              <nav className="flex items-center space-x-6 text-sm font-medium">
                <NavLink 
                  to="/" 
                  className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}
                >
                  Chat
                </NavLink>
                <NavLink 
                  to="/map" 
                  className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}
                >
                  Bản đồ
                </NavLink>
                <NavLink 
                  to="/admin" 
                  className={({ isActive }) => `transition-colors hover:text-foreground/80 ${isActive ? 'text-foreground' : 'text-foreground/60'}`}
                >
                  Dashboard
                </NavLink>
                <a className="transition-colors hover:text-foreground/80 text-foreground/60" href="/docs">Tài liệu</a>
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/admin" element={<AdminDashboard />} />
            {/* Additional routes will be added here */}
          </Routes>
        </main>
      </div>
      <Toaster />
    </BrowserRouter>
  );
}

export default App;
