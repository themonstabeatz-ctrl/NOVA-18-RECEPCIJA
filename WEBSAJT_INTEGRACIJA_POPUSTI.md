# 🎯 WEBSAJT INTEGRACIJA - Popusti za "Masaža za parove"

## 📋 CILJ

Kada korisnik bira "Masaža za parove" na web sajtu, treba da vidi:
1. **Dropdown meniji** sa svim dostupnim masažama (60, 90, 120 min)
2. **Slike popusta** (-5%, -10%, -15%) pored masaža koje imaju aktivne popuste
3. **Akcijske cene** sa popustom

---

## 🔌 API ENDPOINT - Booking Sistem

### Učitaj Masaže za "Masaža za parove"

```javascript
// GET request
const response = await fetch('https://therapist-scheduler.preview.emergentagent.com/api/services');
const allServices = await response.json();

// Filtriraj samo "Kartica Masaza za parove" kategoriju
const coupleServices = allServices.filter(s => s.category === "Kartica Masaza za parove");

console.log('Masaže za couple booking:', coupleServices);
```

### Primer Odgovora:

```json
[
  {
    "id": "abc123",
    "name": "Tradicionalna tajlandska masaža - 60 min",
    "duration": 60,
    "price": 4400.0,
    "discount_percentage": 15.0,
    "category": "Kartica Masaza za parove"
  },
  {
    "id": "def456",
    "name": "Aroma terapija - 90 min",
    "duration": 90,
    "price": 5600.0,
    "discount_percentage": 0.0,
    "category": "Kartica Masaza za parove"
  }
]
```

---

## 🖼️ SLIKE POPUSTA

### Lokacije Slika:

Web sajt treba da ima iste slike kao booking sistem:

1. **-5% popust:** `/discount-5.png`
2. **-10% popust:** `/discount-10.png`
3. **-15% popust:** `/discount-15.png`

**Download linkovi za slike:**
- https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/gxxldjta_-5%25.png
- https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/7ytu8zc1_-10%25.png
- https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/z9xclo41_-15%25.png

---

## 💻 IMPLEMENTACIJA NA WEB SAJTU

### 1. Preuzmi Slike i Stavi u `/public` folder

```bash
# U web sajt projektu
cd /public
curl -o discount-5.png "https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/gxxldjta_-5%25.png"
curl -o discount-10.png "https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/7ytu8zc1_-10%25.png"
curl -o discount-15.png "https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/z9xclo41_-15%25.png"
```

### 2. Kreiraj "Masaža za parove" Formu sa Dropdown-ovima

```jsx
import React, { useState, useEffect } from 'react';

function CoupleBookingForm() {
  const [services, setServices] = useState([]);
  const [person1Service, setPerson1Service] = useState('');
  const [person2Service, setPerson2Service] = useState('');

  // Učitaj masaže za couple booking
  useEffect(() => {
    fetch('https://therapist-scheduler.preview.emergentagent.com/api/services')
      .then(res => res.json())
      .then(data => {
        // Filtriraj samo "Kartica Masaza za parove"
        const coupleServices = data.filter(s => s.category === "Kartica Masaza za parove");
        setServices(coupleServices);
      });
  }, []);

  // Funkcija za prikaz cene sa popustom
  const getDiscountedPrice = (service) => {
    const discount = service.discount_percentage || 0;
    const originalPrice = service.price;
    const discountedPrice = originalPrice * (1 - discount / 100);
    return { originalPrice, discountedPrice, discount };
  };

  // Funkcija za prikaz slike popusta
  const getDiscountImage = (discount) => {
    if (discount === 5) return '/discount-5.png';
    if (discount === 10) return '/discount-10.png';
    if (discount === 15) return '/discount-15.png';
    return null;
  };

  return (
    <div className="couple-booking-form">
      <h2>Masaža za Parove</h2>

      {/* Dropdown za Osobu 1 */}
      <div className="form-group">
        <label>Masaža za Osobu 1:</label>
        <select value={person1Service} onChange={(e) => setPerson1Service(e.target.value)}>
          <option value="">-- Izaberite masažu --</option>
          {services.map(service => {
            const { originalPrice, discountedPrice, discount } = getDiscountedPrice(service);
            const discountImage = getDiscountImage(discount);

            return (
              <option key={service.id} value={service.id}>
                {service.name} - 
                {discount > 0 ? (
                  ` ${discountedPrice.toFixed(0)} RSD (${discount}% popust)`
                ) : (
                  ` ${originalPrice} RSD`
                )}
              </option>
            );
          })}
        </select>

        {/* Prikaži sliku popusta ako je izabrana masaža sa popustom */}
        {person1Service && services.find(s => s.id === person1Service)?.discount_percentage > 0 && (
          <img 
            src={getDiscountImage(services.find(s => s.id === person1Service).discount_percentage)}
            alt={`${services.find(s => s.id === person1Service).discount_percentage}% popust`}
            style={{ width: '48px', height: '48px', marginLeft: '10px' }}
          />
        )}
      </div>

      {/* Dropdown za Osobu 2 */}
      <div className="form-group">
        <label>Masaža za Osobu 2:</label>
        <select value={person2Service} onChange={(e) => setPerson2Service(e.target.value)}>
          <option value="">-- Izaberite masažu --</option>
          {services.map(service => {
            const { originalPrice, discountedPrice, discount } = getDiscountedPrice(service);

            return (
              <option key={service.id} value={service.id}>
                {service.name} - 
                {discount > 0 ? (
                  ` ${discountedPrice.toFixed(0)} RSD (${discount}% popust)`
                ) : (
                  ` ${originalPrice} RSD`
                )}
              </option>
            );
          })}
        </select>

        {/* Prikaži sliku popusta */}
        {person2Service && services.find(s => s.id === person2Service)?.discount_percentage > 0 && (
          <img 
            src={getDiscountImage(services.find(s => s.id === person2Service).discount_percentage)}
            alt={`${services.find(s => s.id === person2Service).discount_percentage}% popust`}
            style={{ width: '48px', height: '48px', marginLeft: '10px' }}
          />
        )}
      </div>

      {/* Prikaži ukupnu cenu */}
      {person1Service && person2Service && (
        <div className="total-price">
          <h3>Ukupna Cena:</h3>
          {(() => {
            const service1 = services.find(s => s.id === person1Service);
            const service2 = services.find(s => s.id === person2Service);
            
            const price1 = getDiscountedPrice(service1);
            const price2 = getDiscountedPrice(service2);
            
            const total = price1.discountedPrice + price2.discountedPrice;
            const originalTotal = price1.originalPrice + price2.originalPrice;
            const hasSavings = total < originalTotal;

            return (
              <div>
                {hasSavings && (
                  <p style={{ textDecoration: 'line-through', color: '#999' }}>
                    {originalTotal.toFixed(0)} RSD
                  </p>
                )}
                <p style={{ fontSize: '1.5em', fontWeight: 'bold', color: hasSavings ? '#e63946' : '#000' }}>
                  {total.toFixed(0)} RSD
                </p>
                {hasSavings && (
                  <p style={{ color: '#10b981', fontWeight: 'bold' }}>
                    Ušteda: {(originalTotal - total).toFixed(0)} RSD! 🎉
                  </p>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Submit button */}
      <button onClick={handleSubmit}>Zakaži Termin</button>
    </div>
  );
}
```

---

## 🎨 CSS ZA PRIKAZ POPUSTA

```css
/* Kartica sa popustom */
.service-card-with-discount {
  position: relative;
}

.discount-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  width: 48px;
  height: 48px;
  z-index: 10;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* Akcijska cena */
.price-with-discount {
  display: flex;
  align-items: center;
  gap: 10px;
}

.original-price {
  text-decoration: line-through;
  color: #999;
  font-size: 0.9em;
}

.discounted-price {
  color: #e63946;
  font-weight: bold;
  font-size: 1.2em;
}

.discount-label {
  background: #e63946;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
}
```

---

## 📝 KOMANDA ZA WEB SAJT AGENTA

**Kopiraj i pošalji:**

```
Treba implementirati prikaz popusta za "Masaža za parove" karticu.

ZADATAK:

1. PREUZMI SLIKE POPUSTA:
   - Snimi u /public folder web sajta
   - Download linkovi:
     * https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/gxxldjta_-5%25.png → /public/discount-5.png
     * https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/7ytu8zc1_-10%25.png → /public/discount-10.png
     * https://customer-assets.emergentagent.com/job_therapist-booking-2/artifacts/z9xclo41_-15%25.png → /public/discount-15.png

2. UČITAJ MASAŽE ZA COUPLE BOOKING:
   API: GET https://therapist-scheduler.preview.emergentagent.com/api/services
   Filtriraj: services.filter(s => s.category === "Kartica Masaza za parove")

3. U "MASAŽA ZA PAROVE" FORMI:
   - Dva dropdown menija (Osoba 1, Osoba 2)
   - Svaki dropdown prikazuje masaže iz "Kartica Masaza za parove"
   - Pored svake masaže sa popustom prikaži:
     * Akcijsku cenu: price * (1 - discount_percentage/100)
     * Sliku popusta ako discount_percentage > 0

4. PRIKAZ U DROPDOWN-u:
   - Ako discount_percentage === 5 → prikaži "/discount-5.png" pored opcije
   - Ako discount_percentage === 10 → prikaži "/discount-10.png"
   - Ako discount_percentage === 15 → prikaži "/discount-15.png"
   - Ako discount_percentage === 0 → bez slike

5. UKUPNA CENA:
   - Saberi akcijske cene obe izabrane masaže
   - Prikaži uštredu ako ima popusta

Detaljnu implementaciju pogledaj u fajlu /app/WEBSAJT_INTEGRACIJA_POPUSTI.md na booking sistemu.
```

---

## ✅ TESTIRANJE

Nakon implementacije na web sajtu:

1. **Admin (vi) u booking sistemu:**
   - Idi na Usluge → "Kartica Masaza za parove"
   - Klikni na sliku popusta (npr. -15%)
   - Potvrdi → Sve masaže dobijaju 15% popust

2. **Korisnik na web sajtu:**
   - Idi na "Masaža za parove" karticu
   - Otvori dropdown meni
   - Trebao bi da vidi slike popusta (-15%) pored masaža
   - Trebao bi da vidi akcijske cene

3. **Provera:**
   - Ako admin promeni popust u booking sistemu
   - Web sajt automatski prikazuje novi popust (nakon refresh-a)

---

## 🎯 OČEKIVANI REZULTAT

**U Dropdown meniju na web sajtu:**

```
Masaža za Osobu 1:
----------------------------
Tradicionalna tajlandska masaža - 60 min - 3740 RSD [🏷️ -15%]
Tradicionalna tajlandska masaža - 90 min - 4760 RSD [🏷️ -15%]
Aroma terapija - 60 min - 4400 RSD (bez popusta)
Masaža toplim uljem - 60 min - 4600 RSD (bez popusta)
```

**Ukupna Cena:**
```
Osoba 1: Tradicionalna 60 min - 3740 RSD (-15%)
Osoba 2: Aroma 90 min - 5600 RSD (bez popusta)
----------------------------
Ukupno: 9340 RSD
Ušteda: 660 RSD! 🎉
```
