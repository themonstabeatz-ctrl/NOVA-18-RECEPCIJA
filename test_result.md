# Test Results - Couples Multi-Service & Discount Display Fix

## Testing Required

### Test Scenario 1: Couples 60 - 4 Services Display
- **Action**: Create couples booking with Person1: 60+60min, Person2: 60+60min (4 total services)
- **Expected**: 
  - Listing shows ALL 4 services (2 per person)
  - Notification shows ALL 4 services
  - Each service name with duration visible

### Test Scenario 2: Couples 120 - 3 Services Display  
- **Action**: Create couples booking with Person1: 120min, Person2: 60+60min (3 total services)
- **Expected**:
  - Listing shows ALL 3 services
  - Notification shows ALL 3 services

### Test Scenario 3: Discount Display
- **Action**: Create couples booking WITH 10% discount
- **Expected**:
  - Listing shows: crossed out original price + green final price + "-10%" badge
  - Notification shows same price info
  - CEO Dashboard "Ukupan Popust" shows non-zero value
  - CEO Dashboard category shows "Sa popustom: X"

### Test Scenario 4: No Therapist Required
- **Action**: Create couples booking WITHOUT therapist_id
- **Expected**:
  - Booking creates successfully (200 OK)
  - therapist_id is null in response
  - Listing shows "Unknown" in Terapeut column

## Credentials
- Dashboard password: `studio149`
- API URL: `https://massage-booking-fix.preview.emergentagent.com`

## Incorporate User Feedback
- PRIORITY: Verify that ALL services from couples snapshot are displayed, not just first one
- PRIORITY: Verify discount is shown in listings and counted in statistics
- DO NOT require therapist_id for online booking
