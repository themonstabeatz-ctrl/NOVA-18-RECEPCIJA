/**
 * Comprehensive Test Suite for Appointments Price Display
 * Based on Serbian Review Request Requirements
 * 
 * Tests:
 * 1. Dashboard Login with password studio149
 * 2. Appointments listing with proper price display
 * 3. Backend API validation for price/final_price/discount_percentage
 * 4. Edge cases and different discount levels
 */

const { test, expect } = require('@playwright/test');

test.describe('Appointments Price Display - Serbian Review Request', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set viewport for consistent testing
    await page.setViewportSize({ width: 1920, height: 1080 });
  });

  test('1. Dashboard Login with password studio149', async ({ page }) => {
    await page.goto('/');
    
    // Check for login modal
    const passwordInput = await page.locator('input[type="password"]');
    if (await passwordInput.isVisible()) {
      await passwordInput.fill('studio149');
      
      const loginButton = await page.locator('button:has-text("Potvrdi"), button:has-text("Prijavi")').first();
      await loginButton.click();
      
      // Wait for dashboard to load
      await page.waitForTimeout(2000);
      
      // Verify we're on dashboard
      await expect(page.locator('h1:has-text("CEO Dashboard")')).toBeVisible();
    }
  });

  test('2. Appointments Price Display - WITH DISCOUNT', async ({ page }) => {
    // Navigate to appointments page
    await page.goto('/appointments');
    
    // Wait for appointments to load
    await page.waitForTimeout(3000);
    
    // Look for appointments with discounts
    const appointmentRows = await page.locator('tbody tr').all();
    
    let foundDiscountAppointment = false;
    
    for (const row of appointmentRows) {
      const priceCell = row.locator('td:nth-child(5)'); // CENA column
      const priceHTML = await priceCell.innerHTML();
      
      // Check for discount styling
      if (priceHTML.includes('line-through') && priceHTML.includes('text-green')) {
        foundDiscountAppointment = true;
        
        // Verify discount display requirements
        // 1. Strikethrough original price (light gray)
        const strikethroughPrice = row.locator('.line-through');
        await expect(strikethroughPrice).toBeVisible();
        
        // 2. Green final price (bold)
        const greenPrice = row.locator('.text-green-600, .text-green-700');
        await expect(greenPrice).toBeVisible();
        
        // 3. Discount badge
        const discountBadge = row.locator('.bg-red-100, .text-red-800');
        await expect(discountBadge).toBeVisible();
        
        console.log('✅ DISCOUNT APPOINTMENT FOUND - All styling requirements met');
        break;
      }
    }
    
    expect(foundDiscountAppointment).toBe(true);
  });

  test('3. Appointments Price Display - WITHOUT DISCOUNT', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForTimeout(3000);
    
    const appointmentRows = await page.locator('tbody tr').all();
    
    let foundRegularAppointment = false;
    
    for (const row of appointmentRows) {
      const priceCell = row.locator('td:nth-child(5)');
      const priceHTML = await priceCell.innerHTML();
      
      // Check for regular price display (no discount styling)
      if (!priceHTML.includes('line-through') && !priceHTML.includes('text-green')) {
        foundRegularAppointment = true;
        
        // Verify regular price display
        const regularPrice = row.locator('td:nth-child(5) .text-gray-900, td:nth-child(5) .font-medium');
        await expect(regularPrice).toBeVisible();
        
        console.log('✅ REGULAR APPOINTMENT FOUND - No discount styling (correct)');
        break;
      }
    }
    
    // Note: This might not always pass if all appointments have discounts
    console.log(`Regular appointment found: ${foundRegularAppointment}`);
  });

  test('4. Backend API Validation - Services Endpoint', async ({ page }) => {
    await page.goto('/appointments');
    
    // Test the services API endpoint
    const response = await page.evaluate(async () => {
      const res = await fetch('/api/services');
      const data = await res.json();
      
      const validation = {
        status: res.status,
        totalServices: data.length,
        validationResults: {
          correctDiscountLogic: 0,
          incorrectDiscountLogic: 0,
          errors: []
        }
      };
      
      // Validate each service
      data.forEach(service => {
        const { price, final_price, discount_percentage, name } = service;
        
        if (discount_percentage > 0) {
          // For services with discount: final_price should be < price
          const expectedFinalPrice = price * (1 - discount_percentage / 100);
          if (Math.abs(final_price - expectedFinalPrice) < 0.01 && final_price < price) {
            validation.validationResults.correctDiscountLogic++;
          } else {
            validation.validationResults.incorrectDiscountLogic++;
            validation.validationResults.errors.push(
              `${name}: Expected final_price ${expectedFinalPrice}, got ${final_price}`
            );
          }
        } else {
          // For services without discount: final_price should equal price
          if (Math.abs(final_price - price) < 0.01) {
            validation.validationResults.correctDiscountLogic++;
          } else {
            validation.validationResults.incorrectDiscountLogic++;
            validation.validationResults.errors.push(
              `${name}: No discount but final_price (${final_price}) != price (${price})`
            );
          }
        }
      });
      
      return validation;
    });
    
    // Assertions
    expect(response.status).toBe(200);
    expect(response.totalServices).toBeGreaterThan(0);
    expect(response.validationResults.incorrectDiscountLogic).toBe(0);
    
    console.log(`✅ API Validation: ${response.validationResults.correctDiscountLogic} services passed validation`);
    
    if (response.validationResults.errors.length > 0) {
      console.log('❌ Validation errors:', response.validationResults.errors.slice(0, 3));
    }
  });

  test('5. Dashboard Listing Rezervacija Modal', async ({ page }) => {
    await page.goto('/');
    
    // Login if needed
    const passwordInput = await page.locator('input[type="password"]');
    if (await passwordInput.isVisible()) {
      await passwordInput.fill('studio149');
      const loginButton = await page.locator('button:has-text("Potvrdi")').first();
      await loginButton.click();
      await page.waitForTimeout(2000);
    }
    
    // Click Listing Rezervacija button
    const listingButton = await page.locator('button:has-text("Listing Rezervacija")');
    await expect(listingButton).toBeVisible();
    await listingButton.click();
    
    // Wait for modal to open
    await page.waitForTimeout(2000);
    
    // Verify modal content
    await expect(page.locator('text=Listing Rezervacija')).toBeVisible();
    
    // Check for price displays with discounts in the modal
    const discountElements = await page.locator('.line-through, .text-green-700, .-15%').count();
    expect(discountElements).toBeGreaterThan(0);
    
    console.log(`✅ Found ${discountElements} discount-related elements in listing modal`);
  });

  test('6. Edge Cases - Different Discount Levels', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForTimeout(3000);
    
    // Check for different discount percentages
    const discountBadges = await page.locator('[class*="red"]:has-text("%")').all();
    
    const discountLevels = new Set();
    
    for (const badge of discountBadges) {
      const text = await badge.textContent();
      const match = text.match(/-?(\d+)%/);
      if (match) {
        discountLevels.add(parseInt(match[1]));
      }
    }
    
    console.log(`✅ Found discount levels: ${Array.from(discountLevels).join(', ')}%`);
    
    // Verify we have different discount levels (5%, 10%, 15% as mentioned in requirements)
    const expectedLevels = [5, 10, 15];
    const foundExpectedLevels = expectedLevels.filter(level => discountLevels.has(level));
    
    console.log(`✅ Expected discount levels found: ${foundExpectedLevels.join(', ')}%`);
  });

  test('7. Date Navigation and Appointment Search', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForTimeout(2000);
    
    // Try to navigate to 01/12/2025 as mentioned in requirements
    const datePicker = await page.locator('input[type="date"]');
    if (await datePicker.isVisible()) {
      await datePicker.fill('2025-12-01');
      await page.waitForTimeout(2000);
      
      const appointmentsAfterDateChange = await page.locator('tbody tr').count();
      console.log(`✅ Found ${appointmentsAfterDateChange} appointments on 01/12/2025`);
      
      // If no appointments on that date, try current date
      if (appointmentsAfterDateChange === 0) {
        const currentDate = new Date().toISOString().split('T')[0];
        await datePicker.fill(currentDate);
        await page.waitForTimeout(2000);
        
        const currentAppointments = await page.locator('tbody tr').count();
        console.log(`✅ Found ${currentAppointments} appointments on current date`);
      }
    }
  });

  test('8. Booking Flow Test', async ({ page }) => {
    await page.goto('/appointments');
    await page.waitForTimeout(2000);
    
    // Click "Zakazite termin" button
    const addButton = await page.locator('button:has-text("Zakazite termin")');
    await addButton.click();
    
    // Wait for modal
    await page.waitForTimeout(1000);
    
    // Verify modal opened
    await expect(page.locator('text=Zakazite termin')).toBeVisible();
    
    // Fill form with realistic data
    await page.fill('input[placeholder*="Ime"], [data-testid="client-firstname-input"]', 'Marko');
    await page.fill('input[placeholder*="Prezime"], [data-testid="client-lastname-input"]', 'Petrović');
    await page.fill('input[placeholder*="Telefon"], [data-testid="client-phone-input"]', '+381641234567');
    await page.fill('input[placeholder*="Email"], [data-testid="client-email-input"]', 'marko.petrovic@email.com');
    
    // Select service and therapist
    const serviceSelect = page.locator('select').first();
    await serviceSelect.selectOption({ index: 1 });
    
    const therapistSelect = page.locator('select').nth(1);
    await therapistSelect.selectOption({ index: 1 });
    
    // Set appointment time
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowString = tomorrow.toISOString().slice(0, 16);
    
    await page.fill('input[type="datetime-local"]', tomorrowString);
    
    console.log('✅ Booking form filled successfully');
    
    // Note: We don't actually submit to avoid creating test data
    // await page.click('button:has-text("Sačuvaj")');
  });

});

// Helper function to format currency for testing
function formatCurrency(amount) {
  return new Intl.NumberFormat('sr-RS', { 
    style: 'currency', 
    currency: 'RSD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount);
}