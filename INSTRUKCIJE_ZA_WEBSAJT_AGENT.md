# 🎯 INSTRUKCIJE ZA INTEGRACIJU POPUSTA SA BOOKING SISTEMOM

## 📋 PREGLED
Booking sistem (`spa-booking-system-2`) već podržava popuste za usluge i vraća ih preko API-ja.
Web sajt (`thaimassage-web`) treba da učita ove popuste i prikaže odgovarajuće slike.

---

## ✅ ŠTA JE SPREMNO (Booking Sistem)

### API Endpoint
```
GET https://price-analyzer-8.preview.emergentagent.com/api/services
```

### Odgovor API-ja (Primer)
```json
[
  {
    "id": "98249336-b9d9-4685-b70c-81971d3cf216",
    "name": "Tradicionalna tajlandska masaža - 60 min",
    "duration": 60,
    "price": 4400.0,
    "description": "Tradicionalna tajlandska masaža tretman u trajanju od 60 minuta",
    "discount_percentage": 5.0,
    "category": "regular",
    "created_at": "2025-11-06T00:04:00.244853"
  },
  {
    "id": "106f23bf-771b-4049-bb09-413910bbc3b9",
    "name": "Aroma terapija - 60 min",
    "duration": 60,
    "price": 4400.0,
    "description": "Aroma terapija tretman u trajanju od 60 minuta",
    "discount_percentage": 0.0,
    "category": "regular",
    "created_at": "2025-11-06T00:04:00.397442"
  }
]
```

### Ključna Polja
- `discount_percentage`: 0, 5, 10, ili 15 (procenat popusta)
- `price`: Osnovna cena u RSD
- `name`: Naziv usluge

---

## 🎨 ŠTA TREBA URADITI NA WEB SAJTU

### 1. Učitavanje Usluga sa Popustima
```javascript
// Fetch services from booking system API
const response = await fetch('https://price-analyzer-8.preview.emergentagent.com/api/services');
const services = await response.json();

// Process each service
services.forEach(service => {
  const discount = service.discount_percentage || 0;
  const originalPrice = service.price;
  const discountedPrice = originalPrice * (1 - discount / 100);
  
  console.log(`${service.name}:`);
  console.log(`  Popust: ${discount}%`);
  console.log(`  Cena: ${originalPrice} RSD`);
  if (discount > 0) {
    console.log(`  Akcijska cena: ${discountedPrice} RSD`);
  }
});
```

### 2. Prikazivanje Slika sa Popustima

**Uslovi za prikaz:**
- Ako `discount_percentage === 5` → Prikaži sliku "5% popust"
- Ako `discount_percentage === 10` → Prikaži sliku "10% popust"
- Ako `discount_percentage === 15` → Prikaži sliku "15% popust"
- Ako `discount_percentage === 0` → Bez slike popusta

**Primer HTML strukture:**
```html
<div class="service-card">
  <img src="service-image.jpg" alt="Service">
  
  <!-- Prikaži badge sa popustom ako postoji -->
  {discount > 0 && (
    <div class="discount-badge">
      <img src={`/images/discounts/${discount}-percent.png`} alt={`${discount}% popust`} />
    </div>
  )}
  
  <h3>Tradicionalna tajlandska masaža - 60 min</h3>
  
  <!-- Prikaži cenu -->
  {discount > 0 ? (
    <div>
      <span class="original-price" style="text-decoration: line-through;">
        {price} RSD
      </span>
      <span class="discounted-price" style="color: red; font-weight: bold;">
        {price * (1 - discount/100)} RSD
      </span>
      <span class="discount-label">(-{discount}%)</span>
    </div>
  ) : (
    <span class="price">{price} RSD</span>
  )}
</div>
```

### 3. CSS Stilovi za Popuste
```css
.service-card {
  position: relative;
}

.discount-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

.discount-badge img {
  width: 80px;
  height: 80px;
  animation: pulse 2s infinite;
}

.original-price {
  text-decoration: line-through;
  color: #999;
  margin-right: 10px;
}

.discounted-price {
  color: #e63946;
  font-weight: bold;
  font-size: 1.2em;
}

.discount-label {
  color: #e63946;
  font-weight: bold;
  margin-left: 5px;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

---

## 🖼️ ORGANIZACIJA SLIKA POPUSTA

Slike sa popustima treba da budu organizovane na sledeći način:

```
/public/images/discounts/
  ├── 5-percent.png    (Slika za 5% popust)
  ├── 10-percent.png   (Slika za 10% popust)
  └── 15-percent.png   (Slika za 15% popust)
```

**Ili** ako slike već postoje na web sajtu, identifikuj njihove putanje i koristi ih.

---

## 📝 KOMANDA ZA AGENTA WEB SAJTA

Kopiraj i pošalji sledeću poruku agenta za **thaimassage-web** projekat:

---

**POČETAK PORUKE ZA AGENTA:**

```
Treba da integriš prikaz popusta iz booking sistema na web sajtu.

ZADATAK:
1. Učitaj usluge iz booking sistema API-ja:
   GET https://price-analyzer-8.preview.emergentagent.com/api/services

2. Za svaku uslugu proveri "discount_percentage" polje (može biti 0, 5, 10 ili 15)

3. Ako je discount_percentage > 0:
   - Prikaži odgovarajuću sliku popusta (5%, 10%, ili 15%)
   - Prikaži precrtanu originalnu cenu
   - Prikaži akcijsku cenu u crvenoj boji: cena * (1 - discount_percentage/100)
   - Dodaj badge ili oznaku "-X% popust"

4. Ako je discount_percentage === 0:
   - Prikaži normalnu cenu bez popusta

5. Slike sa popustima koje treba koristiti:
   - Proveri da li već postoje slike za 5%, 10%, 15% popust na web sajtu
   - Ako postoje, koristi njihove putanje
   - Ako ne postoje, reci mi da ti dam linkove za slike

TEHNIČKI DETALJI:
- API vraća JSON niz objekata sa poljima: id, name, price, discount_percentage, duration
- discount_percentage je broj između 0 i 15
- Akcijska cena = price * (1 - discount_percentage / 100)

PRIMER:
- Ako je price = 4400 RSD i discount_percentage = 5:
  - Prikaži: ~~4400 RSD~~ 4180 RSD (Ušteda: 220 RSD)
  - Prikaži sliku "5% popust"

Implementiraj ovo na stranici sa masažama/uslugama gde korisnici mogu da vide cene i zakazuju termine.
```

**KRAJ PORUKE ZA AGENTA**

---

## ✅ PROVERA DA LI JE USPEŠNO IMPLEMENTIRANO

Nakon implementacije, web sajt treba da:

1. **Učita usluge** iz booking sistema API-ja
2. **Prikaže slike popusta** (5%, 10%, 15%) na uslugama koje imaju popust
3. **Prikaže precrtanu cenu** i akcijsku cenu
4. **Automatski se ažurira** kada promeniš popust u booking sistemu

### Test Scenario:
1. Idi u booking sistem → Usluge → Promeni popust za "Tradicionalna tajlandska masaža" na 10%
2. Refreshuj web sajt
3. Trebalo bi da vidiš sliku "10% popust" na toj usluzi
4. Trebalo bi da vidiš precrtanu staru cenu i novu akcijsku cenu

---

## 🆘 AKO NEŠTO NE RADI

### Problem: API ne vraća podatke
**Rešenje:** Proveri da li booking sistem radi:
```bash
curl https://price-analyzer-8.preview.emergentagent.com/api/services
```

### Problem: Slike popusta se ne prikazuju
**Rešenje:** Proveri putanje do slika i da li slike postoje na serveru

### Problem: Cene se ne računaju pravilno
**Rešenje:** Formula za akcijsku cenu: `price * (1 - discount_percentage / 100)`

---

## 📊 TRENUTNO STANJE POPUSTA U BAZI

Trenutno postoje sledeće usluge sa popustima:

- **Tradicionalna tajlandska masaža (60/90/120 min)**: 5% popust
- **Ostale usluge**: Bez popusta (0%)

Popusti se mogu menjati u booking sistemu u sekciji **Usluge → AKCIJE (POPUST)** dropdown.

---

**NAPOMENA:** Ova integracija omogućava da se popusti ažuriraju u realnom vremenu. 
Kada admin promeni popust u booking sistemu, web sajt će automatski prikazati nove cene.
