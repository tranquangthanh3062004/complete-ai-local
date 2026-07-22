import { Navigation, Train, Bus, MapPin, FileText, Star } from 'lucide-react';
import { motion } from 'framer-motion';

export const HANOI_SUGGESTIONS = [
  { label: "Từ Mỹ Đình lên Hồ Gươm", icon: <Bus size={13}/> },
  { label: "Giá vé Metro Cát Linh - Hà Đông", icon: <Train size={13}/> },
  { label: "Xe buýt đi sân bay Nội Bài", icon: <MapPin size={13}/> },
  { label: "Mức phạt vượt đèn đỏ 2024", icon: <FileText size={13}/> },
  { label: "Vé tháng sinh viên giá bao nhiêu?", icon: <Star size={13}/> },
];

export function WelcomeScreen({ onSuggestionClick }: { onSuggestionClick: (label: string) => void }) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center h-full min-h-[380px] text-center space-y-6"
    >
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-primary/20 blur-2xl scale-125" />
        <div className="relative w-24 h-24 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-xl border-4 border-background/50">
          <Navigation size={42} className="text-white fill-white/20" />
        </div>
      </div>

      <div className="space-y-1.5">
        <h1 className="text-2xl font-bold tracking-tight">HNTransit AI</h1>
        <p className="text-muted-foreground text-sm max-w-xs">
          Trợ lý thông minh về giao thông công cộng Hà Nội —<br />
          xe buýt, metro, lộ trình, luật giao thông
        </p>
      </div>

      <div className="flex flex-wrap gap-2 justify-center max-w-sm">
        {HANOI_SUGGESTIONS.map(({ label, icon }) => (
          <button
            key={label}
            className="chip flex items-center gap-1.5"
            onClick={() => onSuggestionClick(label)}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      <div className="flex gap-3 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">🚌 120+ tuyến buýt</span>
        <span className="text-border">·</span>
        <span className="flex items-center gap-1">🚇 Metro Hà Nội</span>
        <span className="text-border">·</span>
        <span className="flex items-center gap-1">⚖️ Luật giao thông</span>
      </div>
    </motion.div>
  );
}
