import { useState, useEffect } from 'react';

import { processQueue } from '../services/syncQueue';

export function useNetworkStatus() {
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      processQueue(); // Sync data up to cloud when back online
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Optional: Periodic ping to verify real internet connection (in case connected to router without internet)
    const pingInterval = setInterval(async () => {
      if (navigator.onLine) {
        try {
          // Send a lightweight HEAD request to check real connectivity
          const res = await fetch(window.location.origin, { method: 'HEAD', cache: 'no-store' });
          if (res.ok && !isOnline) setIsOnline(true);
        } catch (error) {
          if (isOnline) setIsOnline(false);
        }
      }
    }, 15000); // Check every 15 seconds

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(pingInterval);
    };
  }, []);

  return isOnline;
}
