# 🔧 HITNA ISPRAVKA - Popusti samo za "Masaža za parove"

## ❌ TRENUTNI PROBLEM

Websajt prikazuje popuste (-10%) na **SVIM** masažama:
- Tradicionalna tajlandska masaža ❌ (ne treba popust ovde)
- Aroma terapija ❌ (ne treba popust ovde)
- Masaža toplim uljem ❌ (ne treba popust ovde)
- Masaža za parove ❌ (treba popust, ali ne prikazuje se)

## ✅ ŠTA TREBA DA BUDE

Popusti treba da se prikazuju **SAMO** u kartici "Masaža za parove" (Osoba 1 i Osoba 2 dropdowni).

Sve ostale kartice ("Tradicionalna tajlandska masaža", "Aroma terapija", itd.) **NE treba da prikazuju popuste**.

---

## 🎯 REŠENJE

### Problem 1: Websajt poziva POGREŠAN API URL

**Trenutno websajt poziva:**
```
https://spabooking.emergent.host/api/services  ❌ (produkcija)
```

**Treba da poziva:**
```
https://price-analyzer-8.preview.emergentagent.com/api/services  ✅ (preview)
```

**Ili bolje - nek se može preklopiti između preview i produkcije kroz env varijablu.**

---

### Problem 2: Prikazivanje Popusta na Svim Karticama

**KLJUČNO PRAVILO:**

Popusti se prikazuju **SAMO** ako:
1. Usluga ima `discount_percentage > 0`
2. **I** usluga pripada kategoriji `"Kartica Masaza za parove"`

---

## 💻 KOD KOJI TREBA PROMENITI (Websajt Agent)

### 1. Ažuriraj API URL

U fajlu `/src/services/bookingApi.js`:

```javascript
// STARO (POGREŠNO):
const BOOKING_API = 'https://spabooking.emergent.host/api';  ❌

// NOVO (TAČNO):
const BOOKING_API = 'https://price-analyzer-8.preview.emergentagent.com/api';  ✅

// ILI BOLJE - koristi environment varijablu:
const BOOKING_API = process.env.REACT_APP_BOOKING_API || 'https://price-analyzer-8.preview.emergentagent.com/api';
```

---

### 2. Funkcija za Proveru da li Prikazati Popust

Dodaj novu funkciju u `/src/services/bookingApi.js`:

```javascript
// NOVA FUNKCIJA - Proveri da li treba prikazati popust
export function shouldShowDiscount(service) {
  // Popust se prikazuje SAMO za "Kartica Masaza za parove" kategoriju
  const hasDiscount = (service.discount_percentage || 0) > 0;
  const isCoupleCategory = service.category === "Kartica Masaza za parove";
  
  return hasDiscount && isCoupleCategory;
}
```

---

### 3. Ažuriraj Prikaz Usluga - NE prikazuj popuste na običnim masažama

**U SVIM KARTICAMA za "Obične masaže" (Tradicionalna, Aroma, Masaža toplim uljem, itd.):**

```jsx
import { shouldShowDiscount } from '../services/bookingApi';

// Primer u komponenti za prikaz usluge:
function ServiceCard({ service }) {
  const priceInfo = calculatePrice(service);
  const showDiscount = shouldShowDiscount(service);  // ← DODAJ OVO
  const badgeUrl = showDiscount ? getDiscountBadgeUrl(priceInfo.discount) : null;  // ← IZMENI

  return (
    <div className="service-card">
      {/* Značka Popusta - SAMO ako je shouldShowDiscount = true */}
      {badgeUrl && (
        <img src={badgeUrl} alt={`${priceInfo.discount}% popust`} className="discount-badge" />
      )}

      <h3>{service.name}</h3>
      
      {/* UVEK prikazuj NORMALNU cenu za obične masaže */}
      <p className="price">{priceInfo.original.toLocaleString()} RSD</p>
      
      {/* NE prikazuj staru/novu cenu ovde! */}
      
      <button>Zakažite</button>
    </div>
  );
}
```

**KLJUČNO:** Za kartice "Tradicionalna tajlandska masaža", "Aroma terapija", "Masaža toplim uljem" - **uvek prikazuj normalnu cenu, nikada popuste!**

---

### 4. Prikaži Popuste SAMO u "Masaža za parove" dropdownu

**U komponenti za "Masaža za parove" (CoupleBooking):**

```jsx
import { fetchServices, filterByCategory, calculatePrice, getDiscountBadgeUrl, shouldShowDiscount } from '../services/bookingApi';

function CoupleBooking() {
  const [services, setServices] = useState([]);
  const [person1, setPerson1] = useState('');
  const [person2, setPerson2] = useState('');

  useEffect(() => {
    fetchServices()
      .then(data => {
        // FILRIRAJ SAMO "Kartica Masaza za parove"
        const coupleServices = filterByCategory(data, "Kartica Masaza za parove");
        setServices(coupleServices);
      });
  }, []);

  return (
    <div>
      <h2>Masaža za Parove</h2>
      
      {/* Dropdown za Osobu 1 */}
      <div>
        <label>Osoba 1 - Izaberite masažu:</label>
        <select value={person1} onChange={e => setPerson1(e.target.value)}>
          <option value="">Izaberite...</option>
          {services.map(service => {
            const priceInfo = calculatePrice(service);
            const showDiscount = shouldShowDiscount(service);  // ← PROVERI
            
            return (
              <option key={service.id} value={service.id}>
                {service.name} - 
                {showDiscount ? (
                  // Prikaži cenu sa popustom
                  `${priceInfo.discounted.toLocaleString()} RSD (-${priceInfo.discount}%)`
                ) : (
                  // Prikaži normalnu cenu
                  `${priceInfo.original.toLocaleString()} RSD`
                )}
              </option>
            );
          })}
        </select>
        
        {/* Značka Popusta - SAMO ako je shouldShowDiscount = true */}
        {person1 && (() => {
          const selected = services.find(s => s.id === person1);
          const showDiscount = shouldShowDiscount(selected);
          const badgeUrl = showDiscount ? getDiscountBadgeUrl(selected.discount_percentage) : null;
          
          return badgeUrl && (
            <img src={badgeUrl} alt="popust" style={{ width: '50px', height: '50px', marginLeft: '10px' }} />
          );
        })()}
      </div>

      {/* Isti kod i za Osobu 2 */}
      <div>
        <label>Osoba 2 - Izaberite masažu:</label>
        <select value={person2} onChange={e => setPerson2(e.target.value)}>
          <option value="">Izaberite...</option>
          {services.map(service => {
            const priceInfo = calculatePrice(service);
            const showDiscount = shouldShowDiscount(service);
            
            return (
              <option key={service.id} value={service.id}>
                {service.name} - 
                {showDiscount ? (
                  `${priceInfo.discounted.toLocaleString()} RSD (-${priceInfo.discount}%)`
                ) : (
                  `${priceInfo.original.toLocaleString()} RSD`
                )}
              </option>
            );
          })}
        </select>
        
        {person2 && (() => {
          const selected = services.find(s => s.id === person2);
          const showDiscount = shouldShowDiscount(selected);
          const badgeUrl = showDiscount ? getDiscountBadgeUrl(selected.discount_percentage) : null;
          
          return badgeUrl && (
            <img src={badgeUrl} alt="popust" style={{ width: '50px', height: '50px', marginLeft: '10px' }} />
          );
        })()}
      </div>

      {/* Ukupna cena sa popustom */}
      {/* ... (ostatak koda) ... */}
    </div>
  );
}
```

---

## 📝 SAŽETAK PROMENA

1. ✅ Promeni API URL u `/src/services/bookingApi.js` na preview URL
2. ✅ Dodaj funkciju `shouldShowDiscount()` koja vraća `true` SAMO za "Kartica Masaza za parove"
3. ✅ U karticama za obične masaže - UVEK prikazuj normalnu cenu, nikad popuste
4. ✅ U "Masaža za parove" dropdownu - prikaži popuste SAMO za masaže iz te kategorije koje imaju discount_percentage > 0

---

## ✅ OČEKIVANI REZULTAT

**POSLE ISPRAVKE:**

### Obične Masaže (Tradicionalna, Aroma, itd.):
```
Tradicionalna tajlandska masaža - 60 min
4,400 RSD  ← BEZ popusta, BEZ značke
[Zakažite]
```

### Masaža za Parove (dropdown):
```
Osoba 1: [Dropdown]
  - Tradicionalna 60 min - 3,740 RSD (-15%) [🏷️ -15%]
  - Aroma 90 min - 4,760 RSD (-15%) [🏷️ -15%]
  
Osoba 2: [Dropdown]
  - Tradicionalna 60 min - 3,740 RSD (-15%) [🏷️ -15%]
  
Ukupno: 7,480 RSD  
Stara cena: 8,800 RSD (prekriženo)
Ušteda: 1,320 RSD! 🎉
```

---

## 🧪 KAKO TESTIRATI

1. **Postavi popust u booking sistemu:**
   - Idi na: https://price-analyzer-8.preview.emergentagent.com/services
   - Klikni na "Kartica Masaza za parove"
   - Postavi -15% popust
   - Potvrdi

2. **Proveri websajt:**
   - Idi na websajt
   - Refresh
   - **Obične masaže NE treba da prikazuju popuste**
   - **Samo "Masaža za parove" dropdown treba da prikazuje popuste i značke**

---

## 📞 PODRŠKA

Ako websajt agent ima problema, pošalji mu ovaj fajl!
