# ⚡ BRZI VODIČ - Websajt Integracija

## 🎯 ŠTA TREBA DA URADIŠ (Websajt Agent)

Povezi websajt `https://price-consistency.preview.emergentagent.com/` sa booking sistemom.

---

## KORAK 1: Preuzmi Slike za Popuste

```bash
cd /public  # u websajt projektu

curl -o discount-5.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/c07iqk55_-5%25.png"
curl -o discount-10.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/c7s0zotj_-10%25.png"
curl -o discount-15.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/e2nucl6a_-15%25.png"
```

---

## KORAK 2: Kreiraj API Helper Funkcije

Napravi novi fajl `/src/services/bookingApi.js`:

```javascript
const BOOKING_API = 'https://price-consistency.preview.emergentagent.com/api';

// Preuzmi sve usluge
export async function fetchServices() {
  const response = await fetch(`${BOOKING_API}/services`);
  return response.json();
}

// Filtriraj po kategoriji
export function filterByCategory(services, category) {
  return services.filter(s => s.category === category);
}

// Izračunaj cenu sa popustom
export function calculatePrice(service) {
  const originalPrice = service.price;
  const discount = service.discount_percentage || 0;
  const discountedPrice = originalPrice * (1 - discount / 100);
  
  return {
    original: originalPrice,
    discounted: discountedPrice,
    discount: discount,
    hasDiscount: discount > 0,
    savings: originalPrice - discountedPrice
  };
}

// Dobij URL slike za popust
export function getDiscountBadgeUrl(discount) {
  if (discount === 5) return '/discount-5.png';
  if (discount === 10) return '/discount-10.png';
  if (discount === 15) return '/discount-15.png';
  return null;
}
```

---

## KORAK 3: Ažuriraj Komponentu za Prikaz Usluga

U fajlu gde prikazuješ masaže (npr. `MasazePage.jsx`):

```jsx
import React, { useState, useEffect } from 'react';
import { fetchServices, filterByCategory, calculatePrice, getDiscountBadgeUrl } from '../services/bookingApi';

function MasazePage() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServices()
      .then(data => {
        const obicneMasaze = filterByCategory(data, "Obicne masaze");
        setServices(obicneMasaze);
        setLoading(false);
      })
      .catch(error => {
        console.error('Greška:', error);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Učitavanje...</div>;

  return (
    <div className="masaze-section">
      {services.map(service => {
        const priceInfo = calculatePrice(service);
        const badgeUrl = getDiscountBadgeUrl(priceInfo.discount);

        return (
          <div key={service.id} className="service-card">
            {/* Značka Popusta */}
            {badgeUrl && (
              <img 
                src={badgeUrl}
                alt={`${priceInfo.discount}% popust`}
                className="discount-badge"
              />
            )}

            <h3>{service.name}</h3>
            
            {/* Prikaz Cene */}
            {priceInfo.hasDiscount ? (
              <>
                <p className="old-price">{priceInfo.original.toLocaleString()} RSD</p>
                <p className="new-price">{priceInfo.discounted.toLocaleString()} RSD</p>
                <span className="savings">Ušteda: {priceInfo.savings.toLocaleString()} RSD</span>
              </>
            ) : (
              <p className="price">{priceInfo.original.toLocaleString()} RSD</p>
            )}
            
            <button>Zakažite</button>
          </div>
        );
      })}
    </div>
  );
}
```

---

## KORAK 4: Dodaj CSS za Popuste

U tvoj CSS fajl dodaj:

```css
.service-card {
  position: relative;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.discount-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 50px;
  height: 50px;
  z-index: 10;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.old-price {
  text-decoration: line-through;
  color: #999;
  font-size: 0.9em;
}

.new-price {
  color: #e63946;
  font-weight: bold;
  font-size: 1.5em;
}

.savings {
  background: #10b981;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
}
```

---

## KORAK 5: Implementiraj "Masaža za Parove"

U fajl za couple booking komponentu:

```jsx
import React, { useState, useEffect } from 'react';
import { fetchServices, filterByCategory, calculatePrice, getDiscountBadgeUrl } from '../services/bookingApi';

function CoupleBooking() {
  const [services, setServices] = useState([]);
  const [person1, setPerson1] = useState('');
  const [person2, setPerson2] = useState('');

  useEffect(() => {
    fetchServices()
      .then(data => {
        const coupleServices = filterByCategory(data, "Kartica Masaza za parove");
        setServices(coupleServices);
      });
  }, []);

  const getTotalPrice = () => {
    if (!person1 || !person2) return null;
    
    const s1 = services.find(s => s.id === person1);
    const s2 = services.find(s => s.id === person2);
    
    const p1 = calculatePrice(s1);
    const p2 = calculatePrice(s2);
    
    return {
      total: p1.discounted + p2.discounted,
      originalTotal: p1.original + p2.original,
      totalSavings: p1.savings + p2.savings
    };
  };

  const total = getTotalPrice();

  return (
    <div>
      <h2>Masaža za Parove</h2>
      
      {/* Osoba 1 */}
      <div>
        <label>Osoba 1:</label>
        <select value={person1} onChange={e => setPerson1(e.target.value)}>
          <option value="">Izaberite...</option>
          {services.map(s => {
            const p = calculatePrice(s);
            return (
              <option key={s.id} value={s.id}>
                {s.name} - {p.discounted.toLocaleString()} RSD
                {p.hasDiscount && ` (-${p.discount}%)`}
              </option>
            );
          })}
        </select>
        {person1 && (() => {
          const selected = services.find(s => s.id === person1);
          const badge = getDiscountBadgeUrl(selected?.discount_percentage);
          return badge && <img src={badge} alt="popust" style={{width: '40px'}} />;
        })()}
      </div>

      {/* Osoba 2 */}
      <div>
        <label>Osoba 2:</label>
        <select value={person2} onChange={e => setPerson2(e.target.value)}>
          <option value="">Izaberite...</option>
          {services.map(s => {
            const p = calculatePrice(s);
            return (
              <option key={s.id} value={s.id}>
                {s.name} - {p.discounted.toLocaleString()} RSD
                {p.hasDiscount && ` (-${p.discount}%)`}
              </option>
            );
          })}
        </select>
        {person2 && (() => {
          const selected = services.find(s => s.id === person2);
          const badge = getDiscountBadgeUrl(selected?.discount_percentage);
          return badge && <img src={badge} alt="popust" style={{width: '40px'}} />;
        })()}
      </div>

      {/* Ukupna Cena */}
      {total && (
        <div className="total-section">
          {total.totalSavings > 0 && (
            <p className="old-price">{total.originalTotal.toLocaleString()} RSD</p>
          )}
          <p className="total-price">{total.total.toLocaleString()} RSD</p>
          {total.totalSavings > 0 && (
            <p className="savings">🎉 Ušteda: {total.totalSavings.toLocaleString()} RSD!</p>
          )}
        </div>
      )}

      <button disabled={!person1 || !person2}>
        Zakažite Termin za Dvoje
      </button>
    </div>
  );
}
```

---

## ✅ GOTOVO!

Sada websajt:
- ✅ Automatski učitava cene iz booking sistema
- ✅ Prikazuje popuste sa značkama
- ✅ Prikazuje stare i nove cene
- ✅ Radi za "Obične masaže", "SPA", i "Masaža za parove"

**Testiranje:**
1. Idi u booking sistem na `https://price-consistency.preview.emergentagent.com/services`
2. Klikni na "Kartica Masaza za parove"
3. Postavi 15% popust
4. Refresh websajt - trebao bi da vidiš popuste!

---

## 📄 DETALJNIJA DOKUMENTACIJA

Za više detalja i primere, vidi: `/app/INSTRUKCIJE_ZA_WEBSAJT_INTEGRACIJA.md`
