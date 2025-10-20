import React, { useState, useEffect } from 'react';
import { ZoomIn, X } from 'lucide-react';

const MobileHint = () => {
  const [showHint, setShowHint] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Check if hint was previously dismissed
    const isDismissed = localStorage.getItem('mobileHintDismissed');
    if (!isDismissed && window.innerWidth < 768) {
      // Show hint after 2 seconds on mobile
      const timer = setTimeout(() => {
        setShowHint(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, []);

  const handleDismiss = () => {
    setShowHint(false);
    setDismissed(true);
    localStorage.setItem('mobileHintDismissed', 'true');
  };

  if (!showHint || dismissed) return null;

  return (
    <div 
      className="fixed bottom-4 left-4 right-4 bg-amber-700 text-white p-4 rounded-lg shadow-lg z-50 animate-bounce"
      style={{ maxWidth: '400px', margin: '0 auto' }}
    >
      <div className="flex items-start gap-3">
        <ZoomIn className="w-6 h-6 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <p className="font-semibold text-sm mb-1">Koristite zoom na telefonu</p>
          <p className="text-xs opacity-90">
            Možete koristiti pinch-to-zoom (štipanje prstima) da uvećate ili umanjite prikaz. Scroll radi na svim stranama.
          </p>
        </div>
        <button 
          onClick={handleDismiss}
          className="flex-shrink-0 text-white hover:text-amber-100"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default MobileHint;
