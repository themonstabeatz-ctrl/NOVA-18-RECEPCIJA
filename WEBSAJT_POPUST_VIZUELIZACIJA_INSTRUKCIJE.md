# Instrukcije za Websajt: Vizuelni Prikaz Popusta

## Cilj
Websajt mora da prikazuje popuste jasno i vizuelno - precrtanu originalnu cenu i finalnu sniženu cenu.

## 1. Backend API Endpointi (Već Implementirani)

Backend već vraća sve potrebne podatke:

### `/api/services` (ili `/api/services/single/list` i `/api/services/couples/list`)

Vraća usluge sa sledećim poljima:
```json
{
  "id": "...",
  "name": "Masaža stopala - 60 min",
  "duration": 60,
  "price": 3150,                    // Ovo je ORIGINALNA cena
  "discount_percentage": 10,         // Aktivan popust (0 ako nema popusta)
  "final_price": 2835,              // FINALNA cena nakon popusta
  "service_code": "MASAZA_STOPALA_60",
  "is_couple": false,
  "category": "regular"
}
```

**Primer bez popusta:**
```json
{
  "id": "...",
  "name": "Tradicionalna tajlandska masaža - 60 min",
  "duration": 60,
  "price": 4400,
  "discount_percentage": 0,          // Nema popusta
  "final_price": 4400,              // Ista kao price
  "service_code": "TRADICIONALNA_60",
  "is_couple": false,
  "category": "regular"
}
```

**VAŽNO**: 
- `price` = originalna cena
- `final_price` = cena nakon popusta
- `discount_percentage` = procenat popusta (0-100)

## 2. Vizuelni Dizajn za Booking Formu

### Trenutno stanje:
```
Dropdown prikazuje: "Masaža stopala - 60 min - 3,000 RSD"
```

### Novo stanje (SA POPUSTOM):
```
Dropdown prikazuje: "Masaža stopala - 60 min - ~~3,000 RSD~~ 2,550 RSD (-15%)"
```

### Novo stanje (BEZ POPUSTA):
```
Dropdown prikazuje: "Masaža stopala - 60 min - 3,000 RSD"
```

## 3. Implementacija

### Pseudokod za dropdown opcije:

```javascript
services.forEach(service => {
  let displayText = `${service.name} - ${service.duration} min`;
  
  if (service.discount_percentage > 0) {
    // Ako ima popust, prikaži precrtanu originalnu i sniženu cenu
    displayText += ` - ${service.price} RSD ${service.final_price} RSD (-${service.discount_percentage}%)`;
  } else {
    // Ako nema popusta, prikaži samo regularnu cenu
    displayText += ` - ${service.price} RSD`;
  }
  
  // Dodaj u dropdown
  dropdown.addOption(displayText, service.id);
});
```

### HTML/CSS za vizuelni prikaz:

```html
<!-- Primer dropdown opcije sa popustom -->
<option value="service-id">
  Masaža stopala - 60 min - 
  <span style="text-decoration: line-through; color: #999;">3,000 RSD</span>
  <span style="color: #16a34a; font-weight: bold;">2,550 RSD</span>
  <span style="color: #dc2626;">(-15%)</span>
</option>
```

**NAPOMENA**: Ako HTML stilovi ne funkcionišu u `<option>` tagovima (neki browseri ih ne podržavaju), alternativa je da koristite obične tekstualne oznake:

```html
<option value="service-id">
  Masaža stopala - 60 min - 3,000 RSD → 2,550 RSD (-15%)
</option>
```

## 4. Snapshot Sistem (KRITIČNO)

Kada korisnik pošalje rezervaciju, **OBAVEZNO** uključite sledeća tri polja u API payload:

```javascript
const bookingPayload = {
  client_first_name: "...",
  client_last_name: "...",
  // ... ostala polja ...
  service_id: selectedService.id,
  
  // SNAPSHOT CENA (OBAVEZNO):
  snapshot_original_price: selectedService.price,        // Originalna cena
  snapshot_price: selectedService.final_price,           // Finalna cena nakon popusta
  snapshot_discount_percentage: selectedService.discount_percentage  // Procenat popusta
};
```

**ZAŠTO JE OVO VAŽNO?**
- Backend čuva tačnu cenu koju je korisnik video u trenutku rezervacije
- Sprečava retroaktivne promene cena
- Omogućava ispravne izveštaje

## 5. API Endpointi za Booking

### Za obične masaže:
```
POST /api/appointments
```

### Za masaže za parove:
```
POST /api/book-couple-appointment
```

Oba endpointa prihvataju `snapshot_*` polja.

## 6. Testiranje

1. Dodajte popust na neku uslugu preko admin panela
2. Otvorite websajt i proverite da li se popust prikazuje u dropdown-u
3. Rezervišite tu uslugu
4. Otvorite admin panel (Dashboard) i proverite da li se u "Listing Rezervacija" prikazuje:
   - Precrtana originalna cena
   - Zelena finalna cena
   - Badge sa popustom

## 7. Dodatne Preporuke

- Koristite **zelenu boju** za sniženu cenu (#16a34a ili text-green-600)
- Koristite **crvenu boju** za badge popusta (#dc2626 ili text-red-600)
- Precrtana cena treba da bude svetlo sive boje (#999 ili text-gray-400)

---

**Kontakt**: Ako imate pitanja ili probleme, kontaktirajte backend tim.
