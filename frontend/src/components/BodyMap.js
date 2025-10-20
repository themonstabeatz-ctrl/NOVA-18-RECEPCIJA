import React, { useState } from 'react';

const BodyMap = ({ gender, onGenderChange, points, onPointsChange }) => {
  const [side, setSide] = useState('front'); // 'front' or 'back'
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const handleBodyClick = (e, viewSide) => {
    const container = e.currentTarget;
    const rect = container.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    const newPoint = {
      id: Date.now(),
      x: x.toFixed(2),
      y: y.toFixed(2),
      side: viewSide,
      timestamp: new Date().toISOString(),
    };

    onPointsChange([...points, newPoint]);
  };

  const removePoint = (pointId) => {
    onPointsChange(points.filter((p) => p.id !== pointId));
  };

  const getPointsForSide = (viewSide) => {
    return points.filter(p => p.side === viewSide);
  };

  // Image URLs from uploaded file - 4 body contours
  const bodyImageUrl = 'https://customer-assets.emergentagent.com/job_pozdrav-kako-si/artifacts/npczje4d_konture%20tela.jpg';

  const BodyView = ({ viewSide, imageStyle }) => {
    const sidePoints = getPointsForSide(viewSide);
    
    return (
      <div className="relative" style={{ width: '100%', maxWidth: '300px', margin: '0 auto' }}>
        <div 
          className="relative cursor-crosshair border-2 border-gray-300 rounded-lg overflow-hidden bg-white"
          onClick={(e) => handleBodyClick(e, viewSide)}
          data-testid={`body-map-${viewSide}`}
          style={{ aspectRatio: '1/2' }}
        >
          <img 
            src={bodyImageUrl}
            alt={`Body ${viewSide}`}
            style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              ...imageStyle
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
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: '#ef4444',
                    border: '2px solid #991b1b',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
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
                      padding: '4px 8px',
                      backgroundColor: '#991b1b',
                      color: 'white',
                      fontSize: '10px',
                      borderRadius: '4px',
                      whiteSpace: 'nowrap',
                      fontWeight: 'bold',
                    }}
                  >
                    Klik za brisanje
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <p className="text-xs text-center text-gray-600 mt-2 font-medium">
          {viewSide === 'front' ? 'Prednja strana' : 'Zadnja strana'}
        </p>
      </div>
    );
  };

  // Calculate image crop positions for 4 body types
  const getImageStyle = () => {
    if (gender === 'male') {
      if (side === 'front') {
        // Top-left quadrant (male front)
        return {
          objectPosition: '0% 0%',
          transform: 'scale(2)',
          transformOrigin: 'top left'
        };
      } else {
        // Top-right quadrant (male back)
        return {
          objectPosition: '100% 0%',
          transform: 'scale(2)',
          transformOrigin: 'top right'
        };
      }
    } else {
      if (side === 'front') {
        // Bottom-left quadrant (female front)
        return {
          objectPosition: '0% 100%',
          transform: 'scale(2)',
          transformOrigin: 'bottom left'
        };
      } else {
        // Bottom-right quadrant (female back)
        return {
          objectPosition: '100% 100%',
          transform: 'scale(2)',
          transformOrigin: 'bottom right'
        };
      }
    }
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
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              gender === 'male'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            data-testid="gender-male-btn"
          >
            Muški
          </button>
          <button
            type="button"
            onClick={() => onGenderChange('female')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              gender === 'female'
                ? 'bg-pink-600 text-white'
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
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Kliknite na telo da označite mesta za masažu:
            </label>
            {totalPoints > 0 && (
              <button
                type="button"
                onClick={() => onPointsChange([])}
                className="text-sm text-red-600 hover:text-red-800"
                data-testid="clear-points-btn"
              >
                Obriši sve tačke ({totalPoints})
              </button>
            )}
          </div>

          {/* Side Toggle Buttons */}
          <div className="flex gap-2 mb-4 justify-center">
            <button
              type="button"
              onClick={() => setSide('front')}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                side === 'front'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              data-testid="front-side-btn"
            >
              Prednja strana {frontPoints.length > 0 && `(${frontPoints.length})`}
            </button>
            <button
              type="button"
              onClick={() => setSide('back')}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                side === 'back'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              data-testid="back-side-btn"
            >
              Zadnja strana {backPoints.length > 0 && `(${backPoints.length})`}
            </button>
          </div>
          
          {/* Body View */}
          <BodyView viewSide={side} imageStyle={getImageStyle()} />
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            💡 Kliknite na telo za dodavanje tačke • Kliknite na tačku za brisanje
          </p>
          
          {totalPoints > 0 && (
            <div className="mt-3 text-center">
              <p className="text-sm text-gray-600">
                <strong>Ukupno označenih tačaka:</strong> {totalPoints}
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
