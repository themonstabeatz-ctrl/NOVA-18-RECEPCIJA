# 🌐 INTEGRACIJA WEBSAJTA SA BOOKING SISTEMOM

## 📋 CILJ

Povezati websajt `https://spa-integration.preview.emergentagent.com/` sa booking sistemom `https://spa-integration.preview.emergentagent.com/` da:

1. **Automatski prikazuje cene** iz booking sistema
2. **Prikazuje popuste** sa značkama (-5%, -10%, -15%)
3. **Omogućava online rezervaciju** koja se šalje u booking sistem

---

## 🔌 API ENDPOINTI - Booking Sistem

### Base URL
```
https://spa-integration.preview.emergentagent.com/api
```

### 1. Preuzmi Sve Usluge
```javascript
GET /api/services

// Primer poziva:
const response = await fetch('https://spa-integration.preview.emergentagent.com/api/services');
const services = await response.json();
```

**Odgovor:**
```json
[
  {
    "id": "uuid-ovde",
    "name": "Tradicionalna tajlandska masaža - 60 min",
    "duration": 60,
    "price": 4400.0,
    "discount_percentage": 10.0,
    "category": "Obicne masaze",
    "description": "Opis masaže..."
  },
  {
    "id": "uuid-ovde-2",
    "name": "Tradicionalna tajlandska masaža - 60 min",
    "duration": 60,
    "price": 4400.0,
    "discount_percentage": 15.0,
    "category": "Kartica Masaza za parove",
    "description": "Opis masaže..."
  }
]
```

### 2. Filtriranje Po Kategorijama

**Obične Masaže:**
```javascript
const obicneMasaze = services.filter(s => s.category === "Obicne masaze");
```

**Masaže za Parove:**
```javascript
const paroveMasaze = services.filter(s => s.category === "Kartica Masaza za parove");
```

**SPA Tretmani:**
```javascript
const spaTretmani = services.filter(s => s.category === "SPA");
```

---

## 🖼️ SLIKE ZA POPUSTE

**Slike su već uploadovane na:**

1. **-5% popust:**  
   `https://customer-assets.emergentagent.com/job_spabooking/artifacts/c07iqk55_-5%25.png`

2. **-10% popust:**  
   `https://customer-assets.emergentagent.com/job_spabooking/artifacts/c7s0zotj_-10%25.png`

3. **-15% popust:**  
   `https://customer-assets.emergentagent.com/job_spabooking/artifacts/e2nucl6a_-15%25.png`

**Kopiraj ove slike u `/public` folder websajta:**
```bash
cd /public   # u websajt projektu

curl -o discount-5.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/c07iqk55_-5%25.png"
curl -o discount-10.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/c7s0zotj_-10%25.png"
curl -o discount-15.png "https://customer-assets.emergentagent.com/job_spabooking/artifacts/e2nucl6a_-15%25.png"
```

---

## 💻 IMPLEMENTACIJA - PRIKAZ CENA SA POPUSTIMA

### Funkcija za Kalkulaciju Cene sa Popustom

```javascript
function calculatePrice(service) {
  const originalPrice = service.price;
  const discount = service.discount_percentage || 0;
  const discountedPrice = originalPrice * (1 - discount / 100);
  
  return {
    original: originalPrice,
    discounted: discountedPrice,
    discount: discount,
    hasDiscount: discount > 0
  };
}

// Primer upotrebe:
const service = { name: "Masaža 60 min", price: 4400, discount_percentage: 10 };
const priceInfo = calculatePrice(service);
console.log(priceInfo);
// Output: { original: 4400, discounted: 3960, discount: 10, hasDiscount: true }
```

### Funkcija za Dobijanje Slike Popusta

```javascript
function getDiscountBadgeUrl(discount) {
  if (discount === 5) return '/discount-5.png';
  if (discount === 10) return '/discount-10.png';
  if (discount === 15) return '/discount-15.png';
  return null; // Nema popusta
}
```

---

## 🎨 PRIMER KOMPONENTE - Prikaz Usluge sa Popustom

```jsx
import React, { useState, useEffect } from 'react';

function ServiceCard({ service }) {
  const priceInfo = calculatePrice(service);
  const badgeUrl = getDiscountBadgeUrl(priceInfo.discount);

  return (
    <div className="service-card" style={{ position: 'relative', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
      
      {/* Značka Popusta */}
      {badgeUrl && (
        <img 
          src={badgeUrl}
          alt={`${priceInfo.discount}% popust`}
          style={{
            position: 'absolute',
            top: '-10px',
            right: '-10px',
            width: '50px',
            height: '50px',
            zIndex: 10
          }}
        />
      )}

      {/* Naziv Usluge */}
      <h3>{service.name}</h3>
      <p>{service.description}</p>
      <p>Trajanje: {service.duration} minuta</p>

      {/* Prikaz Cene */}
      <div style={{ marginTop: '10px' }}>
        {priceInfo.hasDiscount ? (
          <>
            {/* Stara Cena - Prekrižena */}
            <p style={{ 
              textDecoration: 'line-through', 
              color: '#999', 
              fontSize: '0.9em' 
            }}>
              {priceInfo.original.toLocaleString()} RSD
            </p>
            
            {/* Nova Cena - Sa Popustom */}
            <p style={{ 
              color: '#e63946', 
              fontWeight: 'bold', 
              fontSize: '1.5em' 
            }}>
              {priceInfo.discounted.toLocaleString()} RSD
            </p>
            
            {/* Label Uštede */}
            <span style={{
              background: '#10b981',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '0.8em',
              fontWeight: 'bold'
            }}>
              Ušteda: {(priceInfo.original - priceInfo.discounted).toLocaleString()} RSD
            </span>
          </>
        ) : (
          /* Normalna Cena */
          <p style={{ fontSize: '1.5em', fontWeight: 'bold' }}>
            {priceInfo.original.toLocaleString()} RSD
          </p>
        )}
      </div>

      {/* Dugme za Rezervaciju */}
      <button style={{
        marginTop: '15px',
        padding: '10px 20px',
        background: '#C8A165',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer'
      }}>
        Zakažite
      </button>
    </div>
  );
}
```

---

## 📱 IMPLEMENTACIJA - Sekcija MASAŽE

```jsx
import React, { useState, useEffect } from 'react';

function MasazePage() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Učitaj sve usluge
    fetch('https://spa-integration.preview.emergentagent.com/api/services')
      .then(res => res.json())
      .then(data => {
        // Filtriraj samo obične masaže
        const obicneMasaze = data.filter(s => s.category === "Obicne masaze");
        setServices(obicneMasaze);
        setLoading(false);
      })
      .catch(error => {
        console.error('Greška pri učitavanju usluga:', error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Učitavanje...</div>;
  }

  return (
    <div className="masaze-section">
      <h1>Masaže sa Bua Luang</h1>
      
      <div className="services-grid" style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px' 
      }}>
        {services.map(service => (
          <ServiceCard key={service.id} service={service} />
        ))}
      </div>
    </div>
  );
}
```

---

## 🎯 IMPLEMENTACIJA - MASAŽA ZA PAROVE (Dropdowni)

```jsx
import React, { useState, useEffect } from 'react';

function CoupleBookingForm() {
  const [services, setServices] = useState([]);
  const [person1Service, setPerson1Service] = useState('');
  const [person2Service, setPerson2Service] = useState('');

  useEffect(() => {
    fetch('https://spa-integration.preview.emergentagent.com/api/services')
      .then(res => res.json())
      .then(data => {
        // Filtriraj samo "Kartica Masaza za parove"
        const coupleServices = data.filter(s => s.category === "Kartica Masaza za parove");
        setServices(coupleServices);
      });
  }, []);

  const calculateTotalPrice = () => {
    if (!person1Service || !person2Service) return null;
    
    const service1 = services.find(s => s.id === person1Service);
    const service2 = services.find(s => s.id === person2Service);
    
    const price1 = calculatePrice(service1);
    const price2 = calculatePrice(service2);
    
    return {
      total: price1.discounted + price2.discounted,
      originalTotal: price1.original + price2.original,
      savings: (price1.original + price2.original) - (price1.discounted + price2.discounted)
    };
  };

  const totalPrice = calculateTotalPrice();

  return (
    <div className="couple-booking-form" style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      <h2>Masaža za Parove</h2>

      {/* Dropdown za Osobu 1 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Izaberite masažu za Osobu 1:
        </label>
        <select 
          value={person1Service} 
          onChange={(e) => setPerson1Service(e.target.value)}
          style={{ width: '100%', padding: '10px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ddd' }}
        >
          <option value="">-- Izaberite masažu --</option>
          {services.map(service => {
            const priceInfo = calculatePrice(service);
            return (
              <option key={service.id} value={service.id}>
                {service.name} - {priceInfo.discounted.toLocaleString()} RSD
                {priceInfo.hasDiscount && ` (-${priceInfo.discount}% popust!)`}
              </option>
            );
          })}
        </select>
        
        {/* Prikaži značku popusta ako je izabrana masaža sa popustom */}
        {person1Service && (() => {
          const selectedService = services.find(s => s.id === person1Service);
          const badgeUrl = getDiscountBadgeUrl(selectedService?.discount_percentage || 0);
          return badgeUrl && (
            <img 
              src={badgeUrl}
              alt="popust"
              style={{ width: '40px', height: '40px', marginTop: '10px' }}
            />
          );
        })()}
      </div>

      {/* Dropdown za Osobu 2 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          Izaberite masažu za Osobu 2:
        </label>
        <select 
          value={person2Service} 
          onChange={(e) => setPerson2Service(e.target.value)}
          style={{ width: '100%', padding: '10px', fontSize: '16px', borderRadius: '4px', border: '1px solid #ddd' }}
        >
          <option value="">-- Izaberite masažu --</option>
          {services.map(service => {
            const priceInfo = calculatePrice(service);
            return (
              <option key={service.id} value={service.id}>
                {service.name} - {priceInfo.discounted.toLocaleString()} RSD
                {priceInfo.hasDiscount && ` (-${priceInfo.discount}% popust!)`}
              </option>
            );
          })}
        </select>

        {person2Service && (() => {
          const selectedService = services.find(s => s.id === person2Service);
          const badgeUrl = getDiscountBadgeUrl(selectedService?.discount_percentage || 0);
          return badgeUrl && (
            <img 
              src={badgeUrl}
              alt="popust"
              style={{ width: '40px', height: '40px', marginTop: '10px' }}
            />
          );
        })()}
      </div>

      {/* Ukupna Cena */}
      {totalPrice && (
        <div style={{ 
          marginTop: '30px', 
          padding: '20px', 
          background: '#f9f9f9', 
          borderRadius: '8px',
          border: '2px solid #C8A165'
        }}>
          <h3>Ukupna Cena:</h3>
          
          {totalPrice.savings > 0 && (
            <p style={{ 
              textDecoration: 'line-through', 
              color: '#999', 
              fontSize: '1em' 
            }}>
              Stara cena: {totalPrice.originalTotal.toLocaleString()} RSD
            </p>
          )}
          
          <p style={{ 
            fontSize: '2em', 
            fontWeight: 'bold', 
            color: totalPrice.savings > 0 ? '#e63946' : '#000',
            margin: '10px 0'
          }}>
            {totalPrice.total.toLocaleString()} RSD
          </p>
          
          {totalPrice.savings > 0 && (
            <p style={{ 
              color: '#10b981', 
              fontWeight: 'bold',
              fontSize: '1.2em'
            }}>
              🎉 Ušteda: {totalPrice.savings.toLocaleString()} RSD!
            </p>
          )}
        </div>
      )}

      {/* Dugme za Rezervaciju */}
      <button 
        disabled={!person1Service || !person2Service}
        style={{
          width: '100%',
          padding: '15px',
          marginTop: '20px',
          background: (person1Service && person2Service) ? '#C8A165' : '#ccc',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          fontSize: '1.2em',
          fontWeight: 'bold',
          cursor: (person1Service && person2Service) ? 'pointer' : 'not-allowed'
        }}
        onClick={() => {
          // TODO: Implementirati rezervaciju
          alert('Rezervacija za parove - implementacija sledi!');
        }}
      >
        Zakažite Termin za Dvoje
      </button>
    </div>
  );
}
```

---

## ✅ CHECKLIST ZA WEBSAJT AGENTA

- [ ] **Preuzmi slike za popuste** i stavi ih u `/public` folder
- [ ] **Kreiraj funkcije** `calculatePrice()` i `getDiscountBadgeUrl()`
- [ ] **Ažuriraj sekciju "MASAŽE"** da dinamički učitava iz API-ja
- [ ] **Ažuriraj sekciju "SPA"** da dinamički učitava iz API-ja
- [ ] **Implementiraj "Masaža za parove"** sa dva dropdowna
- [ ] **Prikaži značke popusta** kada `discount_percentage > 0`
- [ ] **Prikaži prekriženu staru cenu** i novu cenu sa popustom
- [ ] **Testiraj** da se popusti ažuriraju kada admin promeni u booking sistemu

---

## 🎉 OČEKIVANI REZULTAT

Kada admin u booking sistemu postavi 15% popust na "Tradicionalna tajlandska masaža":

**Websajt automatski prikazuje:**
- ✅ Značku sa slikom "-15%"
- ✅ Staru cenu prekriženu: ~~4,400 RSD~~
- ✅ Novu cenu: **3,740 RSD**
- ✅ Ušteda: **660 RSD**

---

## 📞 PODRŠKA

Ako websajt agent ima problema, kontaktiraj booking sistem agenta za pomoć!
