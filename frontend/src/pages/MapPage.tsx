import { useState } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search } from 'lucide-react';
import { api } from '@/services/api';

export default function MapPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);

  const handleSearch = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query) return;
    try {
      const res = await api.get(`/maps/autocomplete?q=${encodeURIComponent(query)}`);
      setResults(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] p-4 max-w-[1600px] mx-auto w-full">
      <h1 className="text-2xl font-bold mb-4 px-2">Bản đồ Giao thông Thông minh</h1>
      <Card className="flex-1 overflow-hidden relative shadow-sm border-border">
        <div className="absolute top-4 left-4 z-[400] w-80 bg-background/95 backdrop-blur-sm rounded-lg shadow-lg p-4 border border-border">
          <form onSubmit={handleSearch} className="flex gap-2">
            <Input 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Tìm kiếm địa điểm..."
            />
            <Button size="icon" type="submit"><Search size={18} /></Button>
          </form>
          {results.length > 0 && (
            <div className="mt-2 flex flex-col gap-1 max-h-[60vh] overflow-y-auto">
              {results.map((r, i) => (
                <div key={i} className="text-sm p-3 hover:bg-muted cursor-pointer rounded-md transition-colors border-b last:border-0 border-border/50">
                  {r.name}
                </div>
              ))}
            </div>
          )}
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
        </MapContainer>
      </Card>
    </div>
  );
}
