import React, { useState } from 'react';
import { X } from 'lucide-react';

const BodyMap = ({ gender, onGenderChange, points, onPointsChange }) => {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const handleBodyClick = (e) => {
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    const newPoint = {
      id: Date.now(),
      x: x.toFixed(2),
      y: y.toFixed(2),
      timestamp: new Date().toISOString(),
    };

    onPointsChange([...points, newPoint]);
  };

  const removePoint = (pointId) => {
    onPointsChange(points.filter((p) => p.id !== pointId));
  };

  // Jednostavna kontura muškog tela
  const MaleBodySVG = () => (
    <svg
      viewBox="0 0 200 400"
      className="w-full h-full cursor-crosshair"
      onClick={handleBodyClick}
      data-testid="body-map-svg"
    >
      {/* Pozadina */}
      <rect width="200" height="400" fill="#f3f4f6" />
      
      {/* Glava */}
      <ellipse cx="100" cy="40" rx="25" ry="30" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Vrat */}
      <rect x="90" y="65" width="20" height="15" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Trup */}
      <ellipse cx="100" cy="140" rx="45" ry="65" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Ramena */}
      <line x1="55" y1="90" x2="145" y2="90" stroke="#6b7280" strokeWidth="2" />
      
      {/* Leva ruka */}
      <line x1="55" y1="90" x2="30" y2="150" stroke="#6b7280" strokeWidth="3" />
      <line x1="30" y1="150" x2="25" y2="210" stroke="#6b7280" strokeWidth="3" />
      <circle cx="25" cy="210" r="6" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Desna ruka */}
      <line x1="145" y1="90" x2="170" y2="150" stroke="#6b7280" strokeWidth="3" />
      <line x1="170" y1="150" x2="175" y2="210" stroke="#6b7280" strokeWidth="3" />
      <circle cx="175" cy="210" r="6" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Kukovi */}
      <rect x="70" y="200" width="60" height="30" rx="5" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Leva noga */}
      <line x1="80" y1="230" x2="75" y2="330" stroke="#6b7280" strokeWidth="3" />
      <line x1="75" y1="330" x2="70" y2="380" stroke="#6b7280" strokeWidth="3" />
      <ellipse cx="70" cy="385" rx="8" ry="5" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Desna noga */}
      <line x1="120" y1="230" x2="125" y2="330" stroke="#6b7280" strokeWidth="3" />
      <line x1="125" y1="330" x2="130" y2="380" stroke="#6b7280" strokeWidth="3" />
      <ellipse cx="130" cy="385" rx="8" ry="5" fill="#e5e7eb" stroke="#6b7280" strokeWidth="2" />
      
      {/* Označene tačke */}
      {points.map((point) => (
        <g key={point.id}>
          <circle
            cx={(point.x / 100) * 200}
            cy={(point.y / 100) * 400}
            r="6"
            fill="#ef4444"
            stroke="#991b1b"
            strokeWidth="2"
            onMouseEnter={() => setHoveredPoint(point.id)}
            onMouseLeave={() => setHoveredPoint(null)}
            onClick={(e) => {
              e.stopPropagation();
              removePoint(point.id);
            }}
            style={{ cursor: 'pointer' }}
          />
          {hoveredPoint === point.id && (
            <text
              x={(point.x / 100) * 200}
              y={(point.y / 100) * 400 - 10}
              textAnchor="middle"
              fill="#991b1b"
              fontSize="10"
              fontWeight="bold"
            >
              Klik za brisanje
            </text>
          )}
        </g>
      ))}
    </svg>
  );

  // Jednostavna kontura ženskog tela
  const FemaleBodySVG = () => (
    <svg
      viewBox="0 0 200 400"
      className="w-full h-full cursor-crosshair"
      onClick={handleBodyClick}
      data-testid="body-map-svg"
    >
      {/* Pozadina */}
      <rect width="200" height="400" fill="#fef3c7" />
      
      {/* Glava */}
      <ellipse cx="100" cy="40" rx="23" ry="28" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Kosa */}
      <path d="M 77 25 Q 77 15, 100 15 Q 123 15, 123 25" fill="#92400e" />
      
      {/* Vrat */}
      <rect x="92" y="65" width="16" height="12" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Trup - ženska silueta */}
      <ellipse cx="100" cy="110" rx="35" ry="30" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      <path d="M 65 140 Q 75 165, 100 170 Q 125 165, 135 140" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Ramena */}
      <line x1="65" y1="85" x2="135" y2="85" stroke="#d97706" strokeWidth="2" />
      
      {/* Leva ruka */}
      <line x1="65" y1="85" x2="40" y2="145" stroke="#d97706" strokeWidth="3" />
      <line x1="40" y1="145" x2="35" y2="205" stroke="#d97706" strokeWidth="3" />
      <circle cx="35" cy="205" r="5" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Desna ruka */}
      <line x1="135" y1="85" x2="160" y2="145" stroke="#d97706" strokeWidth="3" />
      <line x1="160" y1="145" x2="165" y2="205" stroke="#d97706" strokeWidth="3" />
      <circle cx="165" cy="205" r="5" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Kukovi */}
      <ellipse cx="100" cy="200" rx="38" ry="28" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Leva noga */}
      <line x1="80" y1="225" x2="75" y2="325" stroke="#d97706" strokeWidth="3" />
      <line x1="75" y1="325" x2="70" y2="380" stroke="#d97706" strokeWidth="3" />
      <ellipse cx="70" cy="385" rx="7" ry="5" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Desna noga */}
      <line x1="120" y1="225" x2="125" y2="325" stroke="#d97706" strokeWidth="3" />
      <line x1="125" y1="325" x2="130" y2="380" stroke="#d97706" strokeWidth="3" />
      <ellipse cx="130" cy="385" rx="7" ry="5" fill="#fde68a" stroke="#d97706" strokeWidth="2" />
      
      {/* Označene tačke */}
      {points.map((point) => (
        <g key={point.id}>
          <circle
            cx={(point.x / 100) * 200}
            cy={(point.y / 100) * 400}
            r="6"
            fill="#dc2626"
            stroke="#991b1b"
            strokeWidth="2"
            onMouseEnter={() => setHoveredPoint(point.id)}
            onMouseLeave={() => setHoveredPoint(null)}
            onClick={(e) => {
              e.stopPropagation();
              removePoint(point.id);
            }}
            style={{ cursor: 'pointer' }}
          />
          {hoveredPoint === point.id && (
            <text
              x={(point.x / 100) * 200}
              y={(point.y / 100) * 400 - 10}
              textAnchor="middle"
              fill="#991b1b"
              fontSize="10"
              fontWeight="bold"
            >
              Klik za brisanje
            </text>
          )}
        </g>
      ))}
    </svg>
  );

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
            {points.length > 0 && (
              <button
                type="button"
                onClick={() => onPointsChange([])}
                className="text-sm text-red-600 hover:text-red-800"
                data-testid="clear-points-btn"
              >
                Obriši sve tačke ({points.length})
              </button>
            )}
          </div>
          
          <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-white" style={{ maxWidth: '400px', margin: '0 auto' }}>
            {gender === 'male' ? <MaleBodySVG /> : <FemaleBodySVG />}
          </div>
          
          <p className="text-xs text-gray-500 mt-2 text-center">
            💡 Kliknite na telo za dodavanje tačke • Kliknite na tačku za brisanje
          </p>
        </div>
      )}
    </div>
  );
};

export default BodyMap;
