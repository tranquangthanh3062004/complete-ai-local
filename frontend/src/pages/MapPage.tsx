import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { 
  Navigation, Clock, CreditCard, Loader2, Footprints, 
  Locate, Sparkles, ChevronDown, ChevronUp, Leaf, Bus, Train, Bike,
  Power, ShieldAlert, CheckCircle2, MessageSquare, Send, X, Bot,
  Copy, Check
} from 'lucide-react';
import { api } from '@/services/api';
import L from 'leaflet';

function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c * 10) / 10;
}

// ── Custom Leaflet Icons ──────────────────────────────────────────────────────
const userIcon = L.divIcon({
  className: 'custom-user-marker',
  html: `<div class="relative flex items-center justify-center">
          <span class="animate-ping absolute inline-flex h-6 w-6 rounded-full bg-sky-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-4 w-4 bg-sky-500 border-2 border-white shadow-md"></span>
         </div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const originIcon = L.divIcon({
  className: 'custom-origin-marker',
  html: `<div class="bg-emerald-500 text-white p-1.5 rounded-full shadow-lg border-2 border-white flex items-center justify-center">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2e1a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/><circle cx="12" cy="10" r="3"/></svg>
         </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28]
});

const destIcon = L.divIcon({
  className: 'custom-dest-marker',
  html: `<div class="bg-rose-500 text-white p-1.5 rounded-full shadow-lg border-2 border-white flex items-center justify-center">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s-8-4.5-8-11.8A8 8 0 0 1 12 2e1a8 8 0 0 1 8 8.2c0 7.3-8 11.8-8 11.8z"/><circle cx="12" cy="10" r="3"/></svg>
         </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28]
});

// ── Auto Fit Map Bounds Component ─────────────────────────────────────────────
function MapFlyTo({ activeOption, userPos }: { activeOption: any; userPos: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (activeOption && activeOption.steps && activeOption.steps.length > 0) {
      const bounds = L.latLngBounds([]);
      if (activeOption.origin_lat && activeOption.origin_lng) {
        bounds.extend([activeOption.origin_lat, activeOption.origin_lng]);
      }
      if (activeOption.dest_lat && activeOption.dest_lng) {
        bounds.extend([activeOption.dest_lat, activeOption.dest_lng]);
      }
      activeOption.steps.forEach((step: any) => {
        if (step.from_lat && step.from_lng) bounds.extend([step.from_lat, step.from_lng]);
        if (step.to_lat && step.to_lng) bounds.extend([step.to_lat, step.to_lng]);
      });
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 15 });
      }
    } else if (userPos) {
      map.flyTo(userPos, 14);
    }
  }, [activeOption, userPos, map]);
  return null;
}

export default function MapPage() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [userPos, setUserPos] = useState<[number, number] | null>(null);
  
  // Mini Chat Widget state
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'bot'; text: string }>>([
    { sender: 'bot', text: 'Xin chào! Tôi là Trợ lý AI Giao thông Hà Nội. Bạn muốn tra cứu tuyến buýt, metro hay tìm đường đi nào?' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

  // GPS state
  const [isGpsEnabled, setIsGpsEnabled] = useState(true);
  const [accuracyRadius, setAccuracyRadius] = useState(45);
  const [lastGpsUpdate, setLastGpsUpdate] = useState<string>('');
  const [gpsStatus, setGpsStatus] = useState<'active' | 'disabled' | 'denied' | 'loading'>('loading');
  const [showStraightLine, setShowStraightLine] = useState(false);

  // Enterprise features state
  const [isCopied, setIsCopied] = useState(false);

  const handleCopyRoute = () => {
    if (!activeOption) return;
    let text = `🗺️ LỘ TRÌNH GIAO THÔNG: ${activeOption.origin} ➔ ${activeOption.destination}\n⏱️ Thời gian: ~${activeOption.total_time} phút | 💵 Chi phí: ${activeOption.total_cost ? activeOption.total_cost.toLocaleString() + 'đ' : 'Miễn phí'}\n\n`;
    if (activeOption.steps) {
      activeOption.steps.forEach((s: any, idx: number) => {
        text += `Chặng ${idx + 1}: ${s.line} (${s.from} ➔ ${s.to}) - ~${s.duration} phút\n`;
      });
    }
    navigator.clipboard.writeText(text);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2500);
  };

  const handleSendChatMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userText = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { sender: 'user', text: userText }]);
    setIsChatLoading(true);

    // ── 2-Way Sync: Chatbot -> Map Controller ────────────────────────────────
    const lower = userText.toLowerCase();
    let detectedDest = '';
    if (lower.includes('bách khoa')) detectedDest = 'Đại học Bách Khoa Hà Nội';
    else if (lower.includes('mỹ đình')) detectedDest = 'Bến xe Mỹ Đình';
    else if (lower.includes('giáp bát')) detectedDest = 'Bến xe Giáp Bát';
    else if (lower.includes('nội bài')) detectedDest = 'Sân bay Nội Bài';
    else if (lower.includes('cát linh')) detectedDest = 'Ga Cát Linh';

    if (detectedDest) {
      setDestination(detectedDest);
      executeSearchWithParams(origin || 'Vị trí của tôi', detectedDest);
    }

    try {
      const res = await api.post('/chat', { message: userText });
      let reply = res.data.reply || res.data.response || 'Đã nhận yêu cầu của bạn.';
      if (detectedDest) {
        reply = `🤖 Tôi đã tự động tìm kiếm lộ trình và đánh dấu điểm đến "${detectedDest}" trên bản đồ cho bạn!\n\n${reply}`;
      }
      setChatMessages((prev) => [...prev, { sender: 'bot', text: reply }]);
    } catch {
      setChatMessages((prev) => [...prev, { sender: 'bot', text: 'Xin lỗi, không thể kết nối với chatbot lúc me. Vui lòng thử lại sau.' }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Multi-option state
  const [routeOptions, setRouteOptions] = useState<any[]>([]);
  const [activeOptIdx, setActiveOptIdx] = useState(0);
  
  // Autocomplete state
  const [origSuggestions, setOrigSuggestions] = useState<any[]>([]);
  const [destSuggestions, setDestSuggestions] = useState<any[]>([]);
  const [showOrigSuggest, setShowOrigSuggest] = useState(false);
  const [showDestSuggest, setShowDestSuggest] = useState(false);
  
  const [isLoading, setIsLoading] = useState(false);
  const [isGpsLoading, setIsGpsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPanelExpanded, setIsPanelExpanded] = useState(true);

  // ── 1. Request GPS Geolocation ─────────────────────────────────────────────
  const requestLocation = () => {
    if (!navigator.geolocation) {
      setError('Trình duyệt của bạn không hỗ trợ định vị GPS.');
      setGpsStatus('disabled');
      return;
    }
    setIsGpsLoading(true);
    setGpsStatus('loading');
    
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude, accuracy } = pos.coords;
        setUserPos([latitude, longitude]);
        setAccuracyRadius(Math.round(accuracy) || 40);
        setLastGpsUpdate(new Date().toLocaleTimeString('vi-VN'));
        setGpsStatus('active');
        setIsGpsEnabled(true);
        setOrigin('Vị trí của tôi');
        setIsGpsLoading(false);
      },
      (err) => {
        console.warn('GPS Error:', err);
        setGpsStatus('denied');
        setIsGpsLoading(false);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const toggleGps = () => {
    if (isGpsEnabled) {
      setIsGpsEnabled(false);
      setGpsStatus('disabled');
    } else {
      requestLocation();
    }
  };

  useEffect(() => {
    requestLocation();
  }, []);

  // ── 2. Autocomplete Suggestions ────────────────────────────────────────────
  const fetchAutocomplete = async (text: string, setFn: (data: any[]) => void) => {
    if (text.length < 2 || text === 'Vị trí của tôi') {
      setFn([]);
      return;
    }
    try {
      const res = await api.get(`/maps/autocomplete?q=${encodeURIComponent(text)}`);
      setFn(res.data || []);
    } catch {
      setFn([]);
    }
  };

  const handleOrigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setOrigin(val);
    setShowOrigSuggest(true);
    fetchAutocomplete(val, setOrigSuggestions);
  };

  const handleDestChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setDestination(val);
    setShowDestSuggest(true);
    fetchAutocomplete(val, setDestSuggestions);
  };

  // ── 3. Route Search Helper ──────────────────────────────────────────────────
  const executeSearchWithParams = async (origVal: string, destVal: string) => {
    if (!origVal || !destVal) return;
    setIsLoading(true);
    setError('');
    setRouteOptions([]);
    setActiveOptIdx(0);
    setShowOrigSuggest(false);
    setShowDestSuggest(false);

    try {
      const queryOrig = origVal === 'Vị trí của tôi' && userPos ? `${userPos[0]},${userPos[1]}` : origVal;
      const res = await api.get(`/maps/route?origin=${encodeURIComponent(queryOrig)}&destination=${encodeURIComponent(destVal)}`);
      
      const opts = res.data.options && res.data.options.length > 0 
        ? res.data.options 
        : (res.data.primary ? [res.data.primary] : []);

      if (opts.length === 0) {
        setError('Không tìm thấy kết quả phù hợp cho tuyến đường này.');
      } else {
        setRouteOptions(opts);
        // Map -> Chatbot 2-Way Notification
        const firstOpt = opts[0];
        setChatMessages((prev) => [
          ...prev, 
          { sender: 'bot', text: `📍 **Tự động đồng bộ từ Bản đồ:**\nĐã tải ${opts.length} phương án lộ trình từ "${origVal}" đến "${destVal}". Đang chọn phương án: ${firstOpt.option_name || 'Tối ưu nhất'} (~${firstOpt.total_time} phút).` }
        ]);
      }
    } catch (err: any) {
      console.error(err);
      if (err.response?.status === 404) {
        setError(err.response?.data?.detail || 'Không tìm thấy điểm khởi hành hoặc điểm đến trong hệ thống dữ liệu.');
      } else {
        setError('Không thể tìm tuyến đường lúc này. Vui lòng thử lại.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRouteSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!origin || !destination) return;

    if (origin === 'Vị trí của tôi' && !userPos) {
      setError('Hệ thống chưa lấy được vị trí GPS. Vui lòng bấm "Bật định vị" hoặc nhập địa điểm xuất phát cụ thể.');
      requestLocation();
      return;
    }

    executeSearchWithParams(origin, destination);
  };

  const activeOption = routeOptions[activeOptIdx] || null;

  // ── 4. Render Step Icon & Badge ────────────────────────────────────────────
  const getStepBadge = (type: string, line: string) => {
    switch (type?.toLowerCase()) {
      case 'metro':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blue-500 text-white"><Train className="w-3 h-3 mr-1" /> {line || 'Metro'}</span>;
      case 'brt':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-orange-500 text-white"><Bus className="w-3 h-3 mr-1" /> {line || 'BRT'}</span>;
      case 'bike':
      case 'xe_dap':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-500 text-white"><Bike className="w-3 h-3 mr-1" /> TNGO</span>;
      case 'walk':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-gray-500 text-white"><Footprints className="w-3 h-3 mr-1" /> Đi bộ</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-green-600 text-white"><Bus className="w-3 h-3 mr-1" /> {line || 'Bus'}</span>;
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-3 md:p-4 max-w-[1600px] mx-auto w-full">
      <div className="flex items-center justify-between mb-3 px-1 flex-wrap gap-2">
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2 text-foreground">
          <Navigation className="w-6 h-6 text-primary" /> Bản đồ & Định tuyến Thông minh
        </h1>
        
        {/* GPS Control Status Bar */}
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${
            gpsStatus === 'active' 
              ? 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:text-emerald-400'
              : gpsStatus === 'loading'
              ? 'bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400'
              : 'bg-rose-500/10 text-rose-600 border-rose-500/30 dark:text-rose-400'
          }`}>
            {gpsStatus === 'active' && <CheckCircle2 className="w-3.5 h-3.5" />}
            {gpsStatus === 'loading' && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {gpsStatus === 'denied' && <ShieldAlert className="w-3.5 h-3.5" />}
            {gpsStatus === 'disabled' && <Power className="w-3.5 h-3.5" />}
            GPS: {gpsStatus === 'active' ? `Bật (${lastGpsUpdate})` : gpsStatus === 'loading' ? 'Đang tìm...' : 'Đã tắt / Từ chối'}
          </span>

          <Button variant={isGpsEnabled ? "default" : "outline"} size="sm" onClick={toggleGps} disabled={isGpsLoading} className="shadow-sm">
            {isGpsLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1.5" /> : <Locate className="w-4 h-4 mr-1.5" />}
            {isGpsEnabled ? 'Bật định vị' : 'Tắt định vị'}
          </Button>

          <Button 
            variant={showStraightLine ? "secondary" : "outline"} 
            size="sm" 
            onClick={() => setShowStraightLine(!showStraightLine)} 
            className="shadow-sm text-xs"
          >
            {showStraightLine ? 'Ẩn đường chim bay' : 'Hiện đường chim bay'}
          </Button>
        </div>
      </div>

      <Card className="flex-1 overflow-hidden relative shadow-md border-border rounded-xl">
        {/* Floating Search & Transit Info Panel */}
        <div className="absolute top-4 left-4 z-[400] w-80 md:w-96 bg-background/95 backdrop-blur-md rounded-xl shadow-xl p-4 border border-border flex flex-col max-h-[88%] transition-all duration-200">
          
          <form onSubmit={handleRouteSearch} className="flex flex-col gap-2.5 shrink-0 relative">
            {/* Origin Input */}
            <div className="relative">
              <Input 
                value={origin}
                onChange={handleOrigChange}
                placeholder="Điểm xuất phát (VD: Mỹ Đình, Triều Khúc)..."
                className="pr-8 text-sm"
              />
              {origin && (
                <button type="button" onClick={() => setOrigin('')} className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground text-xs font-bold">✕</button>
              )}
              {/* Origin Autocomplete Dropdown */}
              {showOrigSuggest && origSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-background border border-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {origSuggestions.map((item, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => { setOrigin(item.name); setShowOrigSuggest(false); }}
                      className="p-2 text-xs hover:bg-accent cursor-pointer border-b border-border/50 last:border-0 truncate"
                    >
                      📍 {item.name}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Destination Input */}
            <div className="relative">
              <Input 
                value={destination}
                onChange={handleDestChange}
                placeholder="Điểm đến (VD: Hồ Gươm, Bến xe Giáp Bát)..."
                className="pr-8 text-sm"
              />
              {destination && (
                <button type="button" onClick={() => setDestination('')} className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground text-xs font-bold">✕</button>
              )}
              {/* Destination Autocomplete Dropdown */}
              {showDestSuggest && destSuggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-background border border-border rounded-lg shadow-lg max-h-48 overflow-y-auto">
                  {destSuggestions.map((item, idx) => (
                    <div 
                      key={idx} 
                      onClick={() => { setDestination(item.name); setShowDestSuggest(false); }}
                      className="p-2 text-xs hover:bg-accent cursor-pointer border-b border-border/50 last:border-0 truncate"
                    >
                      🏁 {item.name}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <Button type="submit" disabled={isLoading} className="w-full font-medium shadow-sm">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Navigation className="w-4 h-4 mr-2" />}
              Tìm lộ trình đa phương thức
            </Button>
          </form>

          {error && <div className="mt-3 p-2.5 bg-destructive/10 text-destructive rounded-lg text-xs font-medium shrink-0">{error}</div>}

          {/* Multi-Option Tabs & Timeline Info */}
          {routeOptions.length > 0 && (
            <div className="mt-3 flex flex-col flex-1 overflow-hidden">
              
              {/* Tabs */}
              <div className="flex gap-1.5 overflow-x-auto pb-2 shrink-0 custom-scrollbar">
                {routeOptions.map((opt, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveOptIdx(idx)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors border ${
                      activeOptIdx === idx 
                        ? 'bg-primary text-primary-foreground border-primary shadow-sm' 
                        : 'bg-muted/50 text-muted-foreground border-border hover:bg-muted'
                    }`}
                  >
                    {opt.option_name || `Phương án ${idx + 1}`}
                  </button>
                ))}
              </div>

              {/* Active Option Details */}
              {activeOption && (
                <div className="flex-1 overflow-y-auto pr-1 mt-1 custom-scrollbar">
                  
                  {/* Quick Place Shortcuts */}
                  <div className="flex gap-1 overflow-x-auto pb-1 custom-scrollbar">
                    <button type="button" onClick={() => { setDestination('Đại học Bách Khoa Hà Nội'); executeSearchWithParams(origin || 'Vị trí của tôi', 'Đại học Bách Khoa Hà Nội'); }} className="px-2 py-1 rounded bg-muted/60 hover:bg-muted text-[11px] font-medium whitespace-nowrap">
                      🎓 Bách Khoa
                    </button>
                    <button type="button" onClick={() => { setDestination('Bến xe Mỹ Đình'); executeSearchWithParams(origin || 'Vị trí của tôi', 'Bến xe Mỹ Đình'); }} className="px-2 py-1 rounded bg-muted/60 hover:bg-muted text-[11px] font-medium whitespace-nowrap">
                      🚌 Mỹ Đình
                    </button>
                    <button type="button" onClick={() => { setDestination('Bến xe Giáp Bát'); executeSearchWithParams(origin || 'Vị trí của tôi', 'Bến xe Giáp Bát'); }} className="px-2 py-1 rounded bg-muted/60 hover:bg-muted text-[11px] font-medium whitespace-nowrap">
                      🚌 Giáp Bát
                    </button>
                    <button type="button" onClick={() => { setDestination('Ga Cát Linh'); executeSearchWithParams(origin || 'Vị trí của tôi', 'Ga Cát Linh'); }} className="px-2 py-1 rounded bg-muted/60 hover:bg-muted text-[11px] font-medium whitespace-nowrap">
                      🚇 Cát Linh
                    </button>
                  </div>

                  {/* Summary Bar */}
                  <div className="p-3 bg-card border border-border rounded-xl shadow-xs mb-3 space-y-2">
                    <div className="flex items-center justify-between text-xs font-bold text-foreground">
                      <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-primary" /> ~{activeOption.total_time} phút</span>
                      <span className="flex items-center gap-1"><CreditCard className="w-3.5 h-3.5 text-emerald-500" /> {activeOption.total_cost ? `${activeOption.total_cost.toLocaleString()}đ` : 'Miễn phí'}</span>
                      <span className="flex items-center gap-1"><Leaf className="w-3.5 h-3.5 text-green-500" /> {activeOption.co2_kg || 0.2}kg CO₂</span>
                    </div>

                    <div className="pt-2 border-t border-border/50 flex justify-end">
                      <Button variant="outline" size="sm" onClick={handleCopyRoute} className="h-7 text-xs shadow-2xs gap-1.5">
                        {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                        {isCopied ? 'Đã sao chép!' : 'Sao chép lộ trình'}
                      </Button>
                    </div>
                  </div>

                  {/* AI Recommendation Box */}
                  <div className="p-2.5 bg-sky-500/10 border border-sky-500/20 rounded-lg text-xs text-sky-700 dark:text-sky-300 mb-3 flex items-start gap-2">
                    <Sparkles className="w-4 h-4 shrink-0 text-sky-500 mt-0.5" />
                    <div>
                      <strong>AI Đề xuất:</strong> Lộ trình {activeOption.option_name?.toLowerCase()} tối ưu nhất về thời gian và giảm thiểu chuyển tuyến.
                    </div>
                  </div>

                  {/* Expand/Collapse Toggle Header */}
                  <div 
                    onClick={() => setIsPanelExpanded(!isPanelExpanded)} 
                    className="flex items-center justify-between text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 cursor-pointer hover:text-foreground"
                  >
                    <span>Chi tiết các chặng di chuyển</span>
                    {isPanelExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>

                  {/* Steps Timeline (Moovit & Citymapper Style) */}
                  {isPanelExpanded && activeOption.steps && (
                    <div className="space-y-3 relative pl-2">
                      <div className="absolute top-3 bottom-3 left-4 w-0.5 bg-border z-0"></div>
                      
                      {activeOption.steps.map((step: any, idx: number) => (
                        <div key={idx} className="flex gap-3 relative z-10 items-start text-xs">
                          <div className="w-7 h-7 rounded-full bg-background border-2 border-primary flex items-center justify-center shrink-0 shadow-sm font-bold text-primary">
                            {idx + 1}
                          </div>
                          <div className="flex-1 bg-card p-3 rounded-xl border border-border shadow-xs space-y-1.5">
                            <div className="flex items-center justify-between">
                              {getStepBadge(step.type, step.line)}
                              <span className="text-muted-foreground font-medium">⏱️ ~{step.duration || 5} phút</span>
                            </div>
                            
                            <div className="font-bold text-foreground">
                              <span className="text-emerald-600 dark:text-emerald-400">📍 Đón:</span> {step.from}
                            </div>
                            <div className="font-bold text-foreground">
                              <span className="text-rose-600 dark:text-rose-400">🏁 Xuống:</span> {step.to}
                            </div>
                            
                            <div className="text-muted-foreground text-[11px] pt-1 border-t border-border/50 flex items-center justify-between">
                              <span>Vé: {step.cost ? `${step.cost.toLocaleString()}đ` : 'Miễn phí'}</span>
                              <span>Độ dài: ~{haversineDistance(step.from_lat, step.from_lng, step.to_lat, step.to_lng)} km</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              )}

            </div>
          )}

        </div>

        {/* Leaflet Interactive Map */}
        <MapContainer 
          center={userPos || [21.0285, 105.8542]} 
          zoom={13} 
          style={{ height: '100%', width: '100%', zIndex: 0 }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />

          {/* User Location GPS Marker & Accuracy Circle */}
          {isGpsEnabled && userPos && (
            <>
              <Circle 
                center={userPos} 
                radius={accuracyRadius} 
                pathOptions={{ color: '#0284c7', fillColor: '#0284c7', fillOpacity: 0.15, weight: 1.5 }} 
              />
              <Marker position={userPos} icon={userIcon}>
                <Popup>
                  <div className="text-xs">
                    <strong>📍 Vị trí GPS của bạn</strong><br/>
                    Độ chính xác: ~{accuracyRadius}m<br/>
                    Cập nhật: {lastGpsUpdate}
                  </div>
                </Popup>
              </Marker>
            </>
          )}

          {/* Straight-line distance Polyline (Optional dashed gray) */}
          {showStraightLine && activeOption && activeOption.origin_lat && activeOption.origin_lng && activeOption.dest_lat && activeOption.dest_lng && (
            <Polyline
              positions={[
                [activeOption.origin_lat, activeOption.origin_lng],
                [activeOption.dest_lat, activeOption.dest_lng]
              ]}
              pathOptions={{ color: '#9ca3af', weight: 2, dashArray: '5, 8', opacity: 0.6 }}
            >
              <Popup>
                <div className="text-xs">
                  <strong>📏 Đường chim bay (Tham khảo):</strong><br/>
                  ~{haversineDistance(activeOption.origin_lat, activeOption.origin_lng, activeOption.dest_lat, activeOption.dest_lng)} km
                </div>
              </Popup>
            </Polyline>
          )}

          {/* Active Option Real-World Road Polylines & Markers */}
          {activeOption && activeOption.steps && (
            <>
              {activeOption.steps.map((step: any, idx: number) => {
                if (!step.from_lat || !step.from_lng || !step.to_lat || !step.to_lng) return null;
                const color = step.type === 'metro' ? '#3b82f6' : step.type === 'brt' ? '#f97316' : step.type === 'walk' ? '#6b7280' : '#22c55e';
                const poly = (step.polyline_coords && step.polyline_coords.length > 0)
                  ? step.polyline_coords
                  : [[step.from_lat, step.from_lng], [step.to_lat, step.to_lng]];
                  
                return (
                  <Polyline 
                    key={idx}
                    positions={poly}
                    pathOptions={{ color: color, weight: 6, opacity: 0.9, dashArray: step.type === 'walk' ? '6, 10' : undefined }}
                  />
                );
              })}

              {activeOption.origin_lat && activeOption.origin_lng && (
                <Marker position={[activeOption.origin_lat, activeOption.origin_lng]} icon={originIcon}>
                  <Popup><strong>Điểm xuất phát:</strong> {activeOption.origin}</Popup>
                </Marker>
              )}

              {activeOption.dest_lat && activeOption.dest_lng && (
                <Marker position={[activeOption.dest_lat, activeOption.dest_lng]} icon={destIcon}>
                  <Popup><strong>Điểm đến:</strong> {activeOption.destination}</Popup>
                </Marker>
              )}
            </>
          )}

          <MapFlyTo activeOption={activeOption} userPos={userPos} />
        </MapContainer>
      </Card>

      {/* Floating Bottom-Right Mini Chatbot Widget */}
      <div className="fixed bottom-6 right-6 z-[999] flex flex-col items-end pointer-events-auto">
        {isChatOpen && (
          <div className="w-80 md:w-96 h-[440px] bg-background/95 backdrop-blur-md rounded-2xl shadow-2xl border border-border mb-3 flex flex-col overflow-hidden transition-all duration-200 animate-in fade-in slide-in-from-bottom-5">
            {/* Header */}
            <div className="p-3.5 bg-primary text-primary-foreground flex items-center justify-between shadow-xs">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center font-bold">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-xs">Trợ lý AI Giao thông</div>
                  <div className="text-[10px] text-primary-foreground/80 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Trực tuyến
                  </div>
                </div>
              </div>
              <button 
                onClick={() => setIsChatOpen(false)}
                className="p-1 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Chat History */}
            <div className="flex-1 p-3 overflow-y-auto space-y-2.5 text-xs custom-scrollbar bg-muted/20">
              {chatMessages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] p-2.5 rounded-2xl shadow-2xs whitespace-pre-wrap ${
                    msg.sender === 'user' 
                      ? 'bg-primary text-primary-foreground rounded-br-none' 
                      : 'bg-card text-foreground border border-border/60 rounded-bl-none'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex justify-start">
                  <div className="bg-card p-2.5 rounded-2xl border border-border/60 text-muted-foreground flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" /> AI đang suy nghĩ...
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleSendChatMessage} className="p-2.5 bg-background border-t border-border flex items-center gap-2">
              <Input 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Hỏi AI bất kỳ câu hỏi nào..."
                className="text-xs h-9"
              />
              <Button type="submit" size="icon" disabled={isChatLoading || !chatInput.trim()} className="h-9 w-9 shrink-0 shadow-xs">
                <Send className="w-3.5 h-3.5" />
              </Button>
            </form>
          </div>
        )}

        {/* Floating Bubble Button */}
        <Button 
          onClick={() => setIsChatOpen(!isChatOpen)}
          className="h-13 w-13 rounded-full shadow-2xl bg-primary hover:bg-primary/90 text-primary-foreground flex items-center justify-center transition-transform hover:scale-105 active:scale-95"
        >
          {isChatOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
        </Button>
      </div>
    </div>
  );
}
