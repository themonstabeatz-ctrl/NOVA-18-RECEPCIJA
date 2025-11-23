# 🎯 WEBSAJT - Integracija Booking Funkcionalnosti

## ❌ TRENUTNI PROBLEM

Korisnik pokušava da zakаže termin sa websajta ali dobija grešku:
**"Greška! Molimo pokušajte ponovo."**

## ✅ REŠENJE

Websajt treba da pošalje podatke na **pravi API endpoint** sa **tačnim formatom podataka**.

---

## 📡 API ENDPOINT ZA ZAKAZIVANJE

### URL:
```
POST https://spabooking.emergent.host/api/book-couple-appointment
```

**ILI (za preview):**
```
POST https://backend-pricing.preview.emergentagent.com/api/book-couple-appointment
```

---

## 📦 FORMAT PODATAKA (Request Body)

```json
{
  "client_first_name": "Milos",
  "client_last_name": "Stanić",
  "client_phone": "9843768",
  "client_email": "themonstabenzq@gmail.com",
  "start_time": "2025-11-09T14:00:00",
  "duration_type": 120,
  "person1_services": ["service-id-1"],
  "person2_services": ["service-id-2"],
  "discount_couples_massage": 15.0
}
```

### OBJAŠNJENJE POLJA:

| Polje | Tip | Obavezno | Opis |
|-------|-----|----------|------|
| `client_first_name` | string | ✅ DA | Ime klijenta |
| `client_last_name` | string | ✅ DA | Prezime klijenta |
| `client_phone` | string | ✅ DA | Telefon klijenta |
| `client_email` | string | ❌ NE | Email klijenta (opciono) |
| `start_time` | string (ISO) | ✅ DA | Datum i vreme u formatu: "2025-11-09T14:00:00" |
| `duration_type` | integer | ✅ DA | Trajanje po osobi: 60, 90, ili 120 minuta |
| `person1_services` | array | ✅ DA | Lista ID-jeva usluga za Osobu 1 |
| `person2_services` | array | ✅ DA | Lista ID-jeva usluga za Osobu 2 |
| `discount_couples_massage` | float | ❌ NE | Popust za parove (default: 15.0%) |

---

## 💻 KOD ZA WEBSAJT

### 1. Funkcija za Slanje Booking Zahteva

```javascript
async function bookCoupleAppointment(formData) {
  // Format podataka prema API specifikaciji
  const bookingData = {
    client_first_name: formData.firstName,
    client_last_name: formData.lastName,
    client_phone: formData.phone,
    client_email: formData.email,
    start_time: formatToISO(formData.date, formData.time), // "2025-11-09T14:00:00"
    duration_type: getDurationType(formData.selectedService), // 60, 90, ili 120
    person1_services: [formData.person1ServiceId],
    person2_services: [formData.person2ServiceId],
    discount_couples_massage: 15.0 // default popust
  };
  
  try {
    const response = await fetch('https://spabooking.emergent.host/api/book-couple-appointment', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bookingData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      console.error('Booking failed:', errorData);
      throw new Error('Booking failed');
    }
    
    const appointment = await response.json();
    console.log('✅ Booking successful:', appointment);
    
    return appointment;
  } catch (error) {
    console.error('❌ Error booking appointment:', error);
    throw error;
  }
}
```

---

### 2. Helper Funkcija - Format Datuma u ISO

```javascript
function formatToISO(date, time) {
  // Očekuje: date = "09/11/2025" (DD/MM/YYYY)
  //          time = "14:00"
  
  const [day, month, year] = date.split('/');
  const [hours, minutes] = time.split(':');
  
  // Kreiraj ISO format: "2025-11-09T14:00:00"
  return `${year}-${month}-${day}T${hours}:${minutes}:00`;
}
```

---

### 3. Helper Funkcija - Dobij Duration Type

```javascript
function getDurationType(serviceText) {
  // Iz teksta "Masaža za parove - 240 min" izvuci trajanje
  if (serviceText.includes('240 min')) return 120; // 120 x 2 = 240
  if (serviceText.includes('180 min')) return 90;  // 90 x 2 = 180
  if (serviceText.includes('120 min')) return 60;  // 60 x 2 = 120
  
  // Default
  return 60;
}
```

---

### 4. Dobij Service ID-jeve

**VAŽNO:** Trebaš da znaš **ID-jeve usluga** koje korisnik bira!

Kada korisnik bira masažu, čuvaš ID-jeve sa API-ja:

```javascript
// Kada učitavaš usluge iz API-ja:
const services = await fetch('https://spabooking.emergent.host/api/services').then(r => r.json());

// Filtriraj "Kartica Masaza za parove"
const coupleServices = services.filter(s => s.category === "Kartica Masaza za parove");

// Prikaži u dropdown-u i čuvaj ID
coupleServices.forEach(service => {
  console.log(`Service: ${service.name}, ID: ${service.id}`);
});
```

Kada korisnik izabere masažu, čuvaš `service.id` za `person1_services` i `person2_services`.

---

## 🔄 KOMPLETAN PRIMER - Integracija u Formu

```javascript
// Stanje forme
const [formData, setFormData] = useState({
  firstName: '',
  lastName: '',
  phone: '',
  email: '',
  date: '',
  time: '',
  person1ServiceId: '',
  person2ServiceId: '',
  selectedService: '' // tekst za prikaz
});

// Handle Submit
const handleSubmit = async (e) => {
  e.preventDefault();
  
  try {
    // Prikaži loading
    setLoading(true);
    setError(null);
    
    // Pošalji booking
    const appointment = await bookCoupleAppointment(formData);
    
    // Uspešno!
    alert(`✅ Termin uspešno zakazan! ID: ${appointment.id}`);
    
    // OPCIONO: Prikaži korisniku njegovu rezervaciju
    showAppointmentConfirmation(appointment);
    
    // Reset forma
    setFormData({...});
    
  } catch (error) {
    // Greška
    setError('Došlo je do greške. Molimo pokušajte ponovo ili nas kontaktirajte.');
  } finally {
    setLoading(false);
  }
};
```

---

## 📧 PRIKAŽI KORISNIKU REZERVACIJU

Nakon uspešnog bookinga, možeš prikazati potvrdu:

```javascript
function showAppointmentConfirmation(appointment) {
  // Kreiraj modal ili sekciju sa podacima:
  const message = `
    ✅ Vaš termin je uspešno zakazan!
    
    📅 Datum: ${formatDate(appointment.start_time)}
    ⏰ Vreme: ${formatTime(appointment.start_time)}
    💆 Usluga: ${appointment.service_name}
    💰 Cena: ${appointment.price} RSD
    
    Očekujemo Vas!
    Za pitanja pozovite: +381 XX XXX XXXX
  `;
  
  // Prikaži u modalu ili na ekranu
  alert(message); // ili koristi modal komponentu
}
```

---

## 🧪 TESTIRANJE

### 1. Test sa Postman ili cURL

```bash
curl -X POST https://spabooking.emergent.host/api/book-couple-appointment \
  -H "Content-Type: application/json" \
  -d '{
    "client_first_name": "Milos",
    "client_last_name": "Stanić",
    "client_phone": "9843768",
    "client_email": "themonstabenzq@gmail.com",
    "start_time": "2025-11-09T14:00:00",
    "duration_type": 120,
    "person1_services": ["service-id-1"],
    "person2_services": ["service-id-2"],
    "discount_couples_massage": 15.0
  }'
```

**Odgovor (Uspešno):**
```json
{
  "id": "appointment-uuid",
  "client_first_name": "Milos",
  "client_last_name": "Stanić",
  "start_time": "2025-11-09T14:00:00",
  "end_time": "2025-11-09T18:00:00",
  "service_name": "Masaža za parove - 240 min (2x120 min) - 15% popust",
  "price": 8500.0,
  "status": "scheduled"
}
```

---

## ✅ CHECKLIST

- [ ] Implementiraj `bookCoupleAppointment()` funkciju
- [ ] Implementiraj `formatToISO()` helper
- [ ] Implementiraj `getDurationType()` helper
- [ ] Čuvaj `service.id` kada korisnik bira masaže
- [ ] Integriši u booking formu
- [ ] Testiraj sa stvarnim podacima
- [ ] Prikaži potvrdu korisniku nakon uspešnog bookinga
- [ ] Dodaj error handling za neuspešne bookinge

---

## 🎉 REZULTAT

Nakon implementacije:
- ✅ Korisnik može da zakаže termin sa websajta
- ✅ Booking sistem automatski kreira rezervaciju
- ✅ Korisnik dobija potvrdu o rezervaciji
- ✅ Admin vidi rezervaciju u booking sistemu na https://spabooking.emergent.host/appointments

---

## 📞 DODATNO - Provera Rezervacije

Ako želiš da korisnik može da vidi svoju rezervaciju kasnije, možeš dodati endpoint:

```javascript
// GET rezervacija po email-u
async function getMyAppointments(email) {
  const response = await fetch(`https://spabooking.emergent.host/api/appointments?client_email=${email}`);
  const appointments = await response.json();
  return appointments;
}
```

**NAPOMENA:** Trenutno booking sistem API ne podržava filtriranje po email-u direktno. Ovo bi trebalo dodati ako želiš tu funkcionalnost.

---

## 🚨 VAŽNE NAPOMENE

1. **Service ID-jevi:** Moraš imati tačne ID-jeve usluga. Dobij ih preko `/api/services` endpointa.
2. **Datum Format:** Mora biti ISO format: `"2025-11-09T14:00:00"` (YYYY-MM-DDTHH:mm:ss)
3. **Duration Type:** Mora biti 60, 90, ili 120 (ne 120, 180, 240!)
4. **person1_services i person2_services:** Mora biti **array** (lista), čak i ako ima samo jedan element!

---

Ako websajt agent ima problema, javi se!
