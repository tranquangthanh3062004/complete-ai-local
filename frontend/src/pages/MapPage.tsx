import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MapPin, Navigation, Clock, CreditCard, Loader2 } from 'lucide-react';
import { api } from '@/services/api';

import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

function MapFlyTo({ routeData }: { routeData: any }) {
  const map = useMap();
  useEffect(() => {
    if (routeData && routeData.steps && routeData.steps.length > 0) {
      const bounds = L.latLngBounds([]);
      bounds.extend([routeData.origin_lat, routeData.origin_lng]);
      bounds.extend([routeData.dest_lat, routeData.dest_lng]);
      routeData.steps.forEach((step: any) => {
        bounds.extend([step.from_lat, step.from_lng]);
        bounds.extend([step.to_lat, step.to_lng]);
      });
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [routeData, map]);
  return null;
}

export default function MapPage() {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [routeData, setRouteData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRouteSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!origin || !destination) return;
    
    setIsLoading(true);
    setError('');
    setRouteData(null);
    try {
      const res = await api.get(`/maps/route?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`);
      setRouteData(res.data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Lỗi tìm đường. Vui lòng thử lại.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderRouteDetails = () => {
    if (!routeData) return null;

    return (
      <div className="mt-4 flex flex-col gap-3 overflow-y-auto pr-2 custom-scrollbar">
        <div className="flex flex-col gap-1 p-3 bg-primary/10 rounded-lg">
          <div className="font-medium text-primary">Tóm tắt lộ trình</div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
            <Clock size={14} /> {routeData.total_time} phút
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <CreditCard size={14} /> {routeData.total_cost.toLocaleString('vi-VN')} VNĐ
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Navigation size={14} /> {routeData.transfers} lần chuyển chuyến
          </div>
        </div>

        <div className="flex flex-col gap-2 mt-2 relative">
          <div className="absolute top-2 bottom-2 left-[15px] w-0.5 bg-border z-0"></div>
          {routeData.steps.map((step: any, i: number) => (
            <div key={i} className="flex gap-4 relative z-10 items-start">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border-2 border-background ${step.type === 'metro' ? 'bg-blue-500' : step.type === 'brt' ? 'bg-orange-500' : 'bg-green-500'} text-white`}>
                <span className="text-xs font-bold">{step.line.replace('Metro ', 'M').replace('BRT ', 'B')}</span>
              </div>
              <div className="flex-1 pb-4">
                <div className="font-medium text-sm">{step.from}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Đến {step.to} ({step.duration} phút)
                </div>
              </div>
            </div>
          ))}
          <div className="flex gap-4 relative z-10 items-start">
            <div className="w-8 h-8 rounded-full bg-destructive flex items-center justify-center shrink-0 border-2 border-background text-white">
              <MapPin size={16} />
            </div>
            <div className="flex-1">
              <div className="font-medium text-sm">{routeData.destination}</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMapElements = () => {
    if (!routeData || !routeData.steps) return null;

    return (
      <>
        {routeData.steps.map((step: any, i: number) => {
            const color = step.type === 'metro' ? '#3b82f6' : step.type === 'brt' ? '#f97316' : '#22c55e';
            return (
              <Polyline 
                key={i}
                positions={[
                  [step.from_lat, step.from_lng], 
                  [step.to_lat, step.to_lng]
                ]} 
                color={color} 
                weight={5} 
                opacity={0.8} 
              />
            );
        })}
        
        {/* Origin Marker */}
        <Marker position={[routeData.origin_lat, routeData.origin_lng]}>
          <Popup><strong>Điểm đi:</strong> {routeData.origin}</Popup>
        </Marker>

        {/* Destination Marker */}
        <Marker position={[routeData.dest_lat, routeData.dest_lng]}>
          <Popup><strong>Điểm đến:</strong> {routeData.destination}</Popup>
        </Marker>
      </>
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 max-w-[1600px] mx-auto w-full">
      <h1 className="text-2xl font-bold mb-4 px-2">Bản đồ Giao thông Thông minh</h1>
      <Card className="flex-1 overflow-hidden relative shadow-sm border-border">
        <div className="absolute top-4 left-4 z-[400] w-80 bg-background/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-border flex flex-col max-h-[90%]">
          <form onSubmit={handleRouteSearch} className="flex flex-col gap-3 shrink-0">
            <Input 
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="Điểm đi (VD: Bến Thành, Sân bay)..."
            />
            <Input 
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Điểm đến (VD: Suối Tiên, Yên Nghĩa)..."
            />
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Navigation className="w-4 h-4 mr-2" />}
              Tìm lộ trình
            </Button>
          </form>

          {error && <div className="mt-3 text-sm text-destructive font-medium shrink-0">{error}</div>}
          
          {renderRouteDetails()}
        </div>
        
        <MapContainer 
          center={[10.7769, 106.7009]} 
          zoom={13} 
          style={{ height: '100%', width: '100%', zIndex: 0 }}
        >
          {/* CartoDB Voyager for a beautiful map */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          />
          {renderMapElements()}
          {routeData && <MapFlyTo routeData={routeData} />}
        </MapContainer>
      </Card>
    </div>
  );
}
