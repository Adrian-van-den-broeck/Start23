import { useState } from 'react';
import { ScrollView, StyleSheet, useWindowDimensions, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Divider } from '../primitives/Divider';
import { IconTile } from '../primitives/IconTile';
import { Input } from '../primitives/Input';
import { Notice } from '../primitives/Notice';
import { SegmentedControl } from '../primitives/SegmentedControl';
import { Skeleton } from '../primitives/Skeleton';
import { Text } from '../primitives/Text';
import { colors, layout, radius, space } from '../tokens';
import { sourceWorkout } from '../utils/workout.test-fixtures';

const copy = {
  en: { form: 'Form fields', workout: 'Workout card', states: 'Control states', notices: 'Notices',
    name: 'First name', optional: '(optional)', birth: 'Birth date', heart: 'Resting heart rate',
    helper: 'Enter your measured value. The unit remains part of the label.',
    error: 'Check the entered date before continuing.', disabled: 'Unavailable in this fixture.',
    readOnly: 'Read-only value', continue: 'Continue', skip: 'Skip this workout', undo: 'Undo',
    busy: 'Saving changes', select: 'Choose this workout', duration: 'Duration', effort: 'Effort',
    low: 'Low intensity', choices: 'Availability', selected: 'Monday', unselected: 'Tuesday',
    long: 'An extended option label that must remain fully readable', week: 'Week', month: 'Month',
    info: 'Information', warning: 'Review required', failure: 'Error', success: 'Saved',
    infoBody: 'This is a public review fixture. No athlete data is read or changed.',
    warningBody: 'Read this explanation before deciding how to continue.',
    errorBody: 'The entered value needs attention. Your input remains available.',
    successBody: 'The example result has an explicit label and icon.', icons: 'Icon circles',
  },
  nl: { form: 'Formuliervelden', workout: 'Trainingskaart', states: 'Bedieningsstatussen', notices: 'Meldingen',
    name: 'Voornaam', optional: '(optioneel)', birth: 'Geboortedatum', heart: 'Rusthartslag',
    helper: 'Vul je gemeten waarde in. De eenheid blijft onderdeel van het label.',
    error: 'Controleer de ingevulde datum voordat je verdergaat.', disabled: 'Niet beschikbaar in dit voorbeeld.',
    readOnly: 'Alleen-lezen waarde', continue: 'Verder', skip: 'Deze training overslaan', undo: 'Ongedaan maken',
    busy: 'Wijzigingen opslaan', select: 'Deze training kiezen', duration: 'Duur', effort: 'Inspanning',
    low: 'Lage intensiteit', choices: 'Beschikbaarheid', selected: 'Maandag', unselected: 'Dinsdag',
    long: 'Een uitgebreide optie die altijd volledig leesbaar moet blijven', week: 'Week', month: 'Maand',
    info: 'Informatie', warning: 'Controle nodig', failure: 'Fout', success: 'Opgeslagen',
    infoBody: 'Dit is een openbaar voorbeeld. Sportergegevens worden niet gelezen of gewijzigd.',
    warningBody: 'Lees deze toelichting voordat je beslist hoe je verdergaat.',
    errorBody: 'De ingevulde waarde vraagt aandacht. Je invoer blijft beschikbaar.',
    successBody: 'Het voorbeeldresultaat heeft een expliciet label en pictogram.', icons: 'Pictogramcirkels',
  },
};
export type ReviewSection = 'form' | 'workout' | 'states' | 'notices';
const noop = () => {};

// Same guarded, unlinked dev-route policy as the accepted asset gallery.
// Only local display/field state and public DTO fixtures; no clients or owners.
export function PrimitiveGallery({ language = 'en', section = 'form' }: {
  language?: keyof typeof copy; section?: ReviewSection;
}) {
  const c = copy[language];
  const { width, fontScale } = useWindowDimensions();
  const [name, setName] = useState('Alex');
  const [day, setDay] = useState('monday');
  const [mode, setMode] = useState('week');
  if (!__DEV__) return null;
  return <SafeAreaView style={styles.screen}>
    <ScrollView key={`${section}-${language}`} keyboardShouldPersistTaps="handled" contentContainerStyle={styles.content}>
      <Text variant="sectionTitle" accessibilityRole="header">{c[section]}</Text>
      <Text variant="supporting" tone="textMuted">DEV / {language.toUpperCase()} / {Math.round(width)} dp / {fontScale.toFixed(2)}</Text>
      {section === 'form' ? <Card padding="form" elevated style={styles.fields}>
        <Input label={c.name} optionalLabel={c.optional} icon="profile" value={name} onChangeText={setName} />
        <Input label={c.birth} icon="calendar" value="08-10-1990" error={c.error} />
        <Input label={c.heart} icon="heartRate" value="58" unit="bpm" hint={c.helper} inputMode="numeric" />
        <Input label={c.readOnly} value="Alex" readOnly />
        <Input label={c.birth} value="08-10-1990" disabled disabledReason={c.disabled} />
        <Button label={c.continue} trailingIcon="forward" onPress={noop} />
      </Card> : null}
      {section === 'workout' ? <Card padding="focus" elevated style={{ gap: space[16] }}>
        <View style={[styles.facts, (width < 360 || fontScale >= 1.5) && styles.stack]}>
          <IconTile name={sourceWorkout.discipline} size="focus" />
          <View style={{ flex: 1, gap: space[4] }}><View style={{ alignSelf: 'flex-start', backgroundColor: colors.primarySoft, borderRadius: radius.pill, paddingHorizontal: space[12], paddingVertical: space[4] }}><Text variant="supporting" tone="primary">{sourceWorkout.discipline}</Text></View>
            <Text variant="cardTitle" accessibilityRole="header">{sourceWorkout.name}</Text></View>
        </View>
        <View style={[styles.facts, (width < 393 || fontScale >= 1.5) && styles.stack]}>
          <View style={styles.fact}><IconTile name="clock" size="field" /><View style={{ flex: 1 }}><Text variant="label">{c.duration}</Text><Text>{sourceWorkout.duration_minutes} min</Text></View></View>
          <View style={styles.fact}><IconTile name="intensity" size="field" /><View style={{ flex: 1 }}><Text variant="label">{c.effort}</Text><Text>{c.low}</Text></View></View>
        </View>
        <Divider /><Text>{sourceWorkout.description}</Text>
        <View style={{ gap: space[12], marginTop: space[8] }}><Button label={c.select} onPress={noop} />
          <Button label={c.skip} variant="secondary" onPress={noop} />
          <Button label={c.undo} variant="outline" onPress={noop} /></View>
      </Card> : null}
      {section === 'notices' ? <>
        <Notice title={c.info}>{c.infoBody}</Notice>
        <Notice tone="warning" title={c.warning} action={{ label: c.continue, onPress: noop }}>{c.warningBody}</Notice>
        <Notice tone="error" title={c.failure}>{c.errorBody}</Notice>
        <Notice tone="success" title={c.success}>{c.successBody}</Notice>
      </> : null}
      {section === 'states' ? <>
        <Button label={c.continue} onPress={noop} />
        <Button label={c.skip} variant="secondary" onPress={noop} />
        <Button label={c.undo} variant="outline" onPress={noop} />
        <Button label={c.continue} disabled disabledReason={c.disabled} onPress={noop} />
        <Button label={c.busy} busy onPress={noop} />
        <ChoiceRow label={c.selected} selected={day === 'monday'} onPress={() => setDay('monday')} />
        <ChoiceRow label={c.unselected} selected={day === 'tuesday'} onPress={() => setDay('tuesday')} />
        <ChoiceRow label={c.long} selected disabled disabledReason={c.disabled} onPress={noop} mode="checkbox" />
        <SegmentedControl accessibilityLabel={c.choices} options={[{ value: 'week', label: c.week }, { value: 'month', label: c.month }]}
          value={mode} onChange={setMode} />
        <Text variant="label">{c.icons}</Text>
        <View style={[styles.facts, { flexWrap: 'wrap' }]}><IconTile name="profile" size="field" /><IconTile name="calendar" />
          <IconTile name="run" size="focus" /><IconTile name="run" tone="run" /><IconTile name="bike" tone="bike" /><IconTile name="swim" tone="swim" /></View>
        <Skeleton />
      </> : null}
    </ScrollView>
  </SafeAreaView>;
}
const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  content: { padding: layout.phoneGutter, paddingBottom: space[32], gap: space[16],
    width: '100%', maxWidth: layout.readingWidth, alignSelf: 'center' },
  fields: { gap: layout.fieldGroupGap },
  facts: { flexDirection: 'row', alignItems: 'center', gap: space[16] },
  stack: { flexDirection: 'column', alignItems: 'stretch' },
  fact: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: space[12] },
});
