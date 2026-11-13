import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { ApiRequestError, getFrequencyPreferences, saveFrequencyPreferences } from '../../api/client';
import type { Discipline, FrequencyPreferences } from '../../api/types';
import { newIdempotencyKey } from '../activities/activityCreateInput';
import { Button } from '../../ui-v2/primitives/Button';
import { Card } from '../../ui-v2/primitives/Card';
import { Input } from '../../ui-v2/primitives/Input';
import { Notice } from '../../ui-v2/primitives/Notice';
import { Text } from '../../ui-v2/primitives/Text';
import { space } from '../../ui-v2/tokens';

const labels: Record<Discipline, string> = { run: 'Hardlopen', bike: 'Fietsen', swim: 'Zwemmen' };
type Inputs = Record<Discipline, string>;
const empty: Inputs = { run: '', bike: '', swim: '' };

export function FrequencyPreferenceCard({ accessToken, sports }: { accessToken: string; sports: Discipline[] }) {
  const token = useRef(accessToken); token.current = accessToken;
  const alive = useRef(true);
  const lock = useRef(false);
  const attempt = useRef<Parameters<typeof saveFrequencyPreferences>[1] | null>(null);
  const [saved, setSaved] = useState<FrequencyPreferences | null>(null);
  const [inputs, setInputs] = useState<Inputs>(empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [uncertain, setUncertain] = useState(false);
  const hydrate = (value: FrequencyPreferences) => {
    setSaved(value);
    setInputs({ run: value.preferences.run?.toString() ?? '', bike: value.preferences.bike?.toString() ?? '', swim: value.preferences.swim?.toString() ?? '' });
  };
  const load = async () => {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError(null);
    try {
      const value = await getFrequencyPreferences(token.current);
      if (!alive.current) return;
      hydrate(value); attempt.current = null; setUncertain(false);
    } catch {
      if (alive.current) setError('Je voorkeur kon niet worden opgehaald. Probeer opnieuw.');
    } finally { lock.current = false; if (alive.current) setBusy(false); }
  };
  useEffect(() => {
    alive.current = true; void load();
    return () => { alive.current = false; };
    // The containing authenticated screen is keyed by account. Token rotation
    // uses token.current and preserves the unsaved preference.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const save = async () => {
    if (!saved || lock.current) return;
    const preferences = { ...saved.preferences };
    for (const sport of sports) {
      const raw = inputs[sport].trim();
      if (raw && (!/^(0|[1-9][0-9]*)$/.test(raw) || Number(raw) > 24)) {
        setError('Vul een geheel aantal van 0 tot en met 24 in, of laat leeg voor geen voorkeur.'); return;
      }
      preferences[sport] = raw === '' ? null : Number(raw);
    }
    if (Object.values(preferences).reduce<number>((total, value) => total + (value ?? 0), 0) > 24) {
      setError('Je kunt technisch maximaal 24 sessies samen aanvragen.'); return;
    }
    attempt.current ??= { expected_revision: saved.revision, operation_id: newIdempotencyKey(), preferences };
    lock.current = true; setBusy(true); setError(null); setMessage(null);
    try {
      const value = await saveFrequencyPreferences(token.current, attempt.current);
      if (!alive.current) return;
      hydrate(value); attempt.current = null; setUncertain(false);
      setMessage('Voorkeur opgeslagen. Deze geldt voor volgende nieuwe voorstellen. Elk weekplan bevestig je apart.');
    } catch (caught) {
      if (!alive.current) return;
      const unknown = !(caught instanceof ApiRequestError) || caught.outcome === 'unknown';
      setUncertain(unknown);
      if (!unknown) attempt.current = null;
      setError(caught instanceof ApiRequestError && caught.status === 409
        ? 'Je voorkeur is intussen gewijzigd. Haal de opgeslagen voorkeur op en beoordeel je wijziging opnieuw.'
        : 'Opslaan kon niet worden bevestigd. Haal de opgeslagen voorkeur op of probeer dezelfde opslag opnieuw.');
    } finally { lock.current = false; if (alive.current) setBusy(false); }
  };
  return <Card elevated style={{ gap: space[16] }}>
    <Text variant="cardTitle" accessibilityRole="header">Gewenste sessies per week (optioneel)</Text>
    <Text tone="textMuted">Dit is je voorkeur. Je weekvoorstel kan minder sessies bevatten door je herstel, geschiktheid en beschikbare dagen. Je beoordeelt en bevestigt elk weekplan apart.</Text>
    <Text tone="textMuted">Leeg betekent geen voorkeur. Nul vraagt geen nieuwe sessies voor die sport.</Text>
    {saved?.reconfirmation_required.length ? <Notice tone="warning">Controleer je voorkeur na je onderbreking en sla deze opnieuw op. Extra sessies vragen een nieuwe beoordeling.</Notice> : null}
    {error ? <Notice tone="error">{error}</Notice> : null}
    {message ? <Notice>{message}</Notice> : null}
    {saved ? <>
      <Text>Opgeslagen voorkeur (revisie {saved.revision}): {sports.map(s => `${labels[s]} ${saved.preferences[s] ?? 'geen voorkeur'}`).join(' · ')}</Text>
      {sports.map(sport => <View key={sport}>
        <Input label={`${labels[sport]}: gewenste sessies`} value={inputs[sport]} placeholder="Geen voorkeur" keyboardType="number-pad"
          disabled={busy || uncertain} onChangeText={value => { setInputs(current => ({ ...current, [sport]: value })); setMessage(null); }} />
      </View>)}
      <Button label={uncertain ? 'Dezelfde voorkeur opnieuw opslaan' : 'Voorkeur opslaan'} busy={busy} disabled={!sports.length} onPress={() => { void save(); }} />
    </> : null}
    {error || !saved ? <Button label="Opgeslagen voorkeur ophalen" variant="secondary" busy={busy} onPress={() => { void load(); }} /> : null}
  </Card>;
}
