import React, { useState } from 'react';

const BodyMap = ({ gender, onGenderChange, points, onPointsChange }) => {
  const [side, setSide] = useState('front'); // 'front' or 'back'
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const handleBodyClick = (e, viewSide) => {
    // Prevent default behavior
    e.preventDefault();
    e.stopPropagation();
    
    const container = e.currentTarget;
    const rect = container.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    console.log('Body clicked:', { x, y, side: viewSide });

    const newPoint = {
      id: Date.now() + Math.random(), // Ensure unique ID
      x: x.toFixed(2),
      y: y.toFixed(2),
      side: viewSide,
      timestamp: new Date().toISOString(),
    };

    const updatedPoints = [...points, newPoint];
    console.log('New points:', updatedPoints);
    onPointsChange(updatedPoints);
  };

  const removePoint = (pointId) => {
    onPointsChange(points.filter((p) => p.id !== pointId));
  };

  const getPointsForSide = (viewSide) => {
    return points.filter(p => p.side === viewSide);
  };

  // Individual image URLs for each body type and side
  const bodyImages = {
    male: {
      front: 'https://customer-assets.emergentagent.com/job_pozdrav-kako-si/artifacts/8sxf3yck_muskarac%20prednja%20strana.png',
      back: 'https://customer-assets.emergentagent.com/job_pozdrav-kako-si/artifacts/ft1hsvql_muskarac%20zadnja%20strana.png'
    },
    female: {
      front: 'https://customer-assets.emergentagent.com/job_pozdrav-kako-si/artifacts/0nihksi1_zensko%20prednja%20strana.png',
      back: 'https://customer-assets.emergentagent.com/job_pozdrav-kako-si/artifacts/k1muysu4_zensko%20zadnja%20strana.png'
    }
  };

  const BodyView = ({ viewSide }) => {
    const sidePoints = getPointsForSide(viewSide);
    const imageUrl = gender ? bodyImages[gender][viewSide] : null;
    
    if (!imageUrl) return null;
    
    return (
      <div className="relative" style={{ width: '100%', maxWidth: '350px', margin: '0 auto' }}>
        <div 
          className="relative cursor-crosshair border-2 border-indigo-400 rounded-lg overflow-hidden bg-white shadow-lg hover:border-indigo-600 transition-colors"
          onClick={(e) => handleBodyClick(e, viewSide)}
          data-testid={`body-map-${viewSide}`}
          style={{ 
            aspectRatio: '1/2',
            minHeight: '500px',
            userSelect: 'none'
          }}
          title="Kliknite na telo da dodate tačku"
        >
          <img 
            src={imageUrl}
            alt={`Body ${viewSide}`}
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              pointerEvents: 'none',
            }}
            draggable={false}
          />
          
          {/* Overlay for points */}
          <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
            {sidePoints.map((point) => (
              <div
                key={point.id}
                style={{
                  position: 'absolute',
                  left: `${point.x}%`,
                  top: `${point.y}%`,
                  transform: 'translate(-50%, -50%)',
                  cursor: 'pointer',
                  zIndex: 10,
                }}
                onMouseEnter={() => setHoveredPoint(point.id)}
                onMouseLeave={() => setHoveredPoint(null)}
                onClick={(e) => {
                  e.stopPropagation();
                  removePoint(point.id);
                }}
              >
                <div
                  style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    backgroundColor: '#ef4444',
                    border: '3px solid #991b1b',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.4)',
                  }}
                />
                {hoveredPoint === point.id && (
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      marginBottom: '8px',
                      padding: '6px 10px',
                      backgroundColor: '#991b1b',
                      color: 'white',
                      fontSize: '11px',
                      borderRadius: '4px',
                      whiteSpace: 'nowrap',
                      fontWeight: 'bold',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    }}
                  >
                    Klik za brisanje
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <p className="text-sm text-center text-gray-700 mt-3 font-semibold">
          {viewSide === 'front' ? 'Prednja strana' : 'Zadnja strana'}
        </p>
      </div>
    );
  };

  const frontPoints = getPointsForSide('front');
  const backPoints = getPointsForSide('back');
  const totalPoints = points.length;

  return (
    <div className="space-y-4" data-testid="body-map-component">
      {/* Gender Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Izaberite pol klijenta:
        </label>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => onGenderChange('male')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              gender === 'male'
                ? 'bg-blue-600 text-white shadow-lg scale-105'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            data-testid="gender-male-btn"
          >
            Muški
          </button>
          <button
            type="button"
            onClick={() => onGenderChange('female')}
            className={`px-6 py-3 rounded-lg font-medium transition-all ${
              gender === 'female'
                ? 'bg-pink-600 text-white shadow-lg scale-105'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            data-testid="gender-female-btn"
          >
            Ženski
          </button>
        </div>
      </div>

      {/* Body Map */}
      {gender && (
        <div>
          <div className="flex justify-between items-center mb-3">
            <label className="block text-sm font-medium text-gray-700">
              Kliknite na telo da označite mesta za masažu:
            </label>
            {totalPoints > 0 && (
              <button
                type="button"
                onClick={() => onPointsChange([])}
                className="text-sm text-red-600 hover:text-red-800 font-semibold"
                data-testid="clear-points-btn"
              >
                Obriši sve tačke ({totalPoints})
              </button>
            )}
          </div>

          {/* Side Toggle Buttons */}
          <div className="flex gap-3 mb-6 justify-center">
            <button
              type="button"
              onClick={() => setSide('front')}
              className={`px-8 py-3 rounded-lg font-semibold transition-all ${
                side === 'front'
                  ? 'bg-indigo-600 text-white shadow-lg scale-105'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              data-testid="front-side-btn"
            >
              Prednja strana {frontPoints.length > 0 && `(${frontPoints.length})`}
            </button>
            <button
              type="button"
              onClick={() => setSide('back')}
              className={`px-8 py-3 rounded-lg font-semibold transition-all ${
                side === 'back'
                  ? 'bg-indigo-600 text-white shadow-lg scale-105'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              data-testid="back-side-btn"
            >
              Zadnja strana {backPoints.length > 0 && `(${backPoints.length})`}
            </button>
          </div>
          
          {/* Body View */}
          <BodyView viewSide={side} />
          
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800 text-center">
              💡 <strong>Uputstvo:</strong> Kliknite na telo za dodavanje crvene tačke • Kliknite na tačku za brisanje
            </p>
          </div>
          
          {totalPoints > 0 && (
            <div className="mt-4 text-center bg-green-50 p-3 rounded-lg border border-green-200">
              <p className="text-sm text-green-800 font-semibold">
                ✓ <strong>Ukupno označenih tačaka:</strong> {totalPoints}
                {frontPoints.length > 0 && ` (Prednja: ${frontPoints.length})`}
                {backPoints.length > 0 && ` (Zadnja: ${backPoints.length})`}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BodyMap;
