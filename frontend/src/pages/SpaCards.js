import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CreditCard, Percent, Save, RefreshCw } from 'lucide-react';
import { spaService } from '../services/api';
import { formatRSD } from '../config/spaCardIds';

export default function SpaCards() {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [error, setError] = useState(null);

  // Fetch all SPA cards
  const fetchCards = async () => {
    try {
      setLoading(true);
      const res = await spaService.getCards();
      setCards(res.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching cards:', err);
      setError('Greška pri učitavanju kartica');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
  }, []);

  // Update card discount
  const updateDiscount = async (cardId, discount) => {
    try {
      setSaving(prev => ({ ...prev, [cardId]: true }));
      
      await spaService.updateCardDiscount(cardId, discount);
      
      // Update local state
      setCards(prev => prev.map(card => 
        card.card_id === cardId 
          ? { ...card, discount_percent: discount, has_discount: discount > 0 }
          : card
      ));
      
    } catch (err) {
      console.error('Error updating discount:', err);
      alert(`Greška: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSaving(prev => ({ ...prev, [cardId]: false }));
    }
  };

  // Group cards by category
  const classicRituals = cards.filter(c => 
    ['silky_body_ritual', 'gentle_touch_ritual', 'deep_renewal_ritual'].includes(c.card_id)
  );
  const herbalRituals = cards.filter(c => 
    ['silky_herbal_compress_ritual', 'thai_herbal_compress_ritual', 'aroma_stone_harmony_ritual'].includes(c.card_id)
  );
  const otherCards = cards.filter(c => 
    ['spa_zone', 'romantic_couple_package', 'romantic_peeling_couple_package'].includes(c.card_id)
  );

  const CardRow = ({ card }) => (
    <div className="flex items-center justify-between p-4 border-b last:border-b-0 hover:bg-gray-50">
      <div className="flex items-center gap-3">
        <CreditCard className="w-5 h-5 text-amber-600" />
        <span className="font-medium">{card.title_sr || card.name}</span>
      </div>
      
      <div className="flex items-center gap-3">
        <Select
          value={String(card.discount_percent)}
          onValueChange={(value) => updateDiscount(card.card_id, parseInt(value))}
          disabled={saving[card.card_id]}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Popust" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="0">Bez popusta</SelectItem>
            <SelectItem value="5">5% popust</SelectItem>
            <SelectItem value="10">10% popust</SelectItem>
            <SelectItem value="15">15% popust</SelectItem>
          </SelectContent>
        </Select>
        
        {card.discount_percent > 0 && (
          <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">
            -{card.discount_percent}%
          </span>
        )}
        
        {saving[card.card_id] && (
          <RefreshCw className="w-4 h-4 animate-spin text-gray-400" />
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-amber-600" />
            SPA Kartice - Popusti
          </h1>
          <p className="text-gray-500 mt-1">
            Podesite popust za svaku SPA karticu. Popust se primenjuje na celu cenu kartice.
          </p>
        </div>
        
        <Button variant="outline" onClick={fetchCards} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Osveži
        </Button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Classic Rituals */}
      <Card className="mb-6">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Percent className="w-5 h-5 text-amber-600" />
            Klasični Rituali
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {classicRituals.map(card => (
            <CardRow key={card.card_id} card={card} />
          ))}
        </CardContent>
      </Card>

      {/* Herbal Rituals */}
      <Card className="mb-6">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Percent className="w-5 h-5 text-green-600" />
            Biljni Rituali
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {herbalRituals.map(card => (
            <CardRow key={card.card_id} card={card} />
          ))}
        </CardContent>
      </Card>

      {/* Other Cards */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Percent className="w-5 h-5 text-purple-600" />
            Ostale Kartice
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {otherCards.map(card => (
            <CardRow key={card.card_id} card={card} />
          ))}
        </CardContent>
      </Card>

      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>Napomena:</strong> Popust na karticu se primenjuje na <strong>celu cenu</strong> uključujući:
        </p>
        <ul className="text-sm text-amber-700 mt-2 ml-4 list-disc">
          <li>Osnovnu cenu rituala</li>
          <li>Varijante (npr. "Sa masažom lica +3.000 RSD")</li>
          <li>SPA Zone dodatke (Sauna, Parno kupatilo, Jacuzzi)</li>
        </ul>
      </div>
    </div>
  );
}
