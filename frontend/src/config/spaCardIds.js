/**
 * SPA Card IDs Configuration
 * Maps frontend package codes to backend card_ids
 */

export const SPA_CARD_IDS = {
  SILKY_BODY_RITUAL: "silky_body_ritual",
  GENTLE_TOUCH_RITUAL: "gentle_touch_ritual",
  DEEP_RENEWAL_RITUAL: "deep_renewal_ritual",
  SILKY_HERBAL_COMPRESS_RITUAL: "silky_herbal_compress_ritual",
  THAI_HERBAL_COMPRESS_RITUAL: "thai_herbal_compress_ritual",
  AROMA_STONE_HARMONY_RITUAL: "aroma_stone_harmony_ritual",
  SPA_ZONE: "spa_zone",
  ROMANTIC_COUPLE_PACKAGE: "romantic_couple_package",
  ROMANTIC_PEELING_COUPLE_PACKAGE: "romantic_peeling_couple_package",
};

// Map frontend package codes to backend card_ids
export const PACKAGE_TO_CARD_MAP = {
  // Classic Rituals
  "SPA1": SPA_CARD_IDS.SILKY_BODY_RITUAL,
  "SILKY_BODY": SPA_CARD_IDS.SILKY_BODY_RITUAL,
  "silky_body_ritual": SPA_CARD_IDS.SILKY_BODY_RITUAL,
  
  "SPA2": SPA_CARD_IDS.GENTLE_TOUCH_RITUAL,
  "GENTLE_TOUCH": SPA_CARD_IDS.GENTLE_TOUCH_RITUAL,
  "gentle_touch_ritual": SPA_CARD_IDS.GENTLE_TOUCH_RITUAL,
  
  "SPA3": SPA_CARD_IDS.DEEP_RENEWAL_RITUAL,
  "DEEP_RENEWAL": SPA_CARD_IDS.DEEP_RENEWAL_RITUAL,
  "deep_renewal_ritual": SPA_CARD_IDS.DEEP_RENEWAL_RITUAL,

  // Herbal Rituals
  "SPA4": SPA_CARD_IDS.SILKY_HERBAL_COMPRESS_RITUAL,
  "SILKY_HERBAL": SPA_CARD_IDS.SILKY_HERBAL_COMPRESS_RITUAL,
  "silky_herbal_compress_ritual": SPA_CARD_IDS.SILKY_HERBAL_COMPRESS_RITUAL,
  
  "SPA5": SPA_CARD_IDS.THAI_HERBAL_COMPRESS_RITUAL,
  "THAI_HERBAL": SPA_CARD_IDS.THAI_HERBAL_COMPRESS_RITUAL,
  "thai_herbal_compress_ritual": SPA_CARD_IDS.THAI_HERBAL_COMPRESS_RITUAL,
  
  "SPA6": SPA_CARD_IDS.AROMA_STONE_HARMONY_RITUAL,
  "AROMA_STONE": SPA_CARD_IDS.AROMA_STONE_HARMONY_RITUAL,
  "aroma_stone_harmony_ritual": SPA_CARD_IDS.AROMA_STONE_HARMONY_RITUAL,

  // SPA Zone
  "SPA_ZONE": SPA_CARD_IDS.SPA_ZONE,
  "spa_zone": SPA_CARD_IDS.SPA_ZONE,

  // Couple Packages
  "SPA7": SPA_CARD_IDS.ROMANTIC_COUPLE_PACKAGE,
  "ROMANTIC_COUPLE": SPA_CARD_IDS.ROMANTIC_COUPLE_PACKAGE,
  "romantic_couple_package": SPA_CARD_IDS.ROMANTIC_COUPLE_PACKAGE,
  
  "SPA8": SPA_CARD_IDS.ROMANTIC_PEELING_COUPLE_PACKAGE,
  "ROMANTIC_PEELING": SPA_CARD_IDS.ROMANTIC_PEELING_COUPLE_PACKAGE,
  "romantic_peeling_couple_package": SPA_CARD_IDS.ROMANTIC_PEELING_COUPLE_PACKAGE,
};

/**
 * Get card_id from package code
 */
export function getCardId(packageCode) {
  if (!packageCode) return null;
  return PACKAGE_TO_CARD_MAP[packageCode] || PACKAGE_TO_CARD_MAP[packageCode.toLowerCase()] || null;
}

/**
 * Format price in RSD
 */
export function formatRSD(amount) {
  if (amount == null || isNaN(amount)) return "0 RSD";
  return `${Number(amount).toLocaleString('sr-RS')} RSD`;
}
