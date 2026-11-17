import { useState, type ReactNode } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, View } from 'react-native';
import type { Discipline } from '../../api/types';
import { useLanguage } from '../../i18n/LanguageProvider';
import { Button } from '../primitives/Button';
import { Card } from '../primitives/Card';
import { ChoiceRow } from '../primitives/ChoiceRow';
import { Divider } from '../primitives/Divider';
import { Input } from '../primitives/Input';
import { Screen } from '../primitives/Screen';
import { Text } from '../primitives/Text';
import { space } from '../tokens';
import { ActivityStatus } from './ActivitiesScreen';

export type ActivityChoice = Readonly<{ id: string; kind: 'workout' | 'external'; name: string; date: string; discipline: Discipline }>;
export function ActivityEntryScreen(props: {
  discipline: Discipline; duration: string; distance: string; startedAt: string; timezone: string;
  choices: readonly ActivityChoice[]; selectedId: string | null; selectedName: string | null;
  busy: boolean; error: string | null; blocked: boolean; controls: ReactNode;
  onDiscipline: (value: Discipline) => void; onDuration: (value: string) => void;
  onDistance: (value: string) => void; onStartedAt: (value: string) => void;
  onChoose: (choice: ActivityChoice | null) => void; onSave: () => Promise<void>; onBack: () => void;
}) {
  const { t } = useLanguage();
  const [choosing, setChoosing] = useState(false);
  return <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
    <Screen title={t('activity.register')} landscape="ridges" titleVariant="display" onBack={props.onBack} backLabel={t('activities.return')} backDisabled={props.busy}
      scrollProps={{ keyboardShouldPersistTaps: 'handled', testID: 'activity-entry-scroll' }}>
      <ActivityStatus busy={props.busy} error={props.error} />
      <Text>{t('activity.registerHint')}</Text>
      <Card elevated padding="form" style={styles.stack}>
        <Text variant="sectionTitle" accessibilityRole="header">{props.selectedName ?? t('activity.unplanned')}</Text>
        <Button label={t('activities.chooseContext')} variant="secondary" trailingIcon="chevron" disabled={props.busy}
          accessibilityState={{ expanded: choosing }} onPress={() => setChoosing(value => !value)} />
        {choosing ? <View style={styles.stack} accessibilityRole="radiogroup" accessibilityLabel={t('activities.chooseContext')}>
          <ChoiceRow label={t('activity.unplanned')} selected={props.selectedId === null}
            disabled={props.busy} onPress={() => { props.onChoose(null); setChoosing(false); }} />
          {props.choices.map(choice => <ChoiceRow key={`${choice.kind}:${choice.id}`}
            label={`${choice.name} · ${t(`common.${choice.discipline}`)} · ${choice.date}${choice.kind === 'external' ? ` · ${t('activity.external')}` : ''}`}
            selected={props.selectedId === choice.id}
            disabled={props.busy} onPress={() => { props.onChoose(choice); setChoosing(false); }} />)}
        </View> : null}
        {props.selectedId === null ? <View style={styles.stack} accessibilityRole="radiogroup" accessibilityLabel={t('activities.sport')}>
          <Text variant="label">{t('activities.sport')}</Text>
          {(['swim', 'bike', 'run'] as const).map(sport => <ChoiceRow key={sport}
            label={t(`common.${sport}`)} selected={props.discipline === sport}
            disabled={props.busy} onPress={() => props.onDiscipline(sport)} />)}
        </View> : null}
      </Card>
      <Card elevated padding="form" style={styles.fields}>
        <Input label={t('activity.startedAt')} value={props.startedAt} onChangeText={props.onStartedAt}
          icon="calendar" autoCapitalize="none" disabled={props.busy} />
        <Text variant="supporting" tone="textMuted">{`${t('activity.timezone')}: ${props.timezone || t('activities.timezoneMissing')}`}</Text>
        <Input label={props.discipline === 'swim' ? t('activities.swimDuration') : t('activity.duration')}
          icon="clock" inputMode="decimal" value={props.duration} onChangeText={props.onDuration} disabled={props.busy} />
        <Input label={t('activity.distance')} icon="location" inputMode="numeric" value={props.distance}
          onChangeText={props.onDistance} disabled={props.busy} />
        <Divider />
        <Button label={t('activity.save')} trailingIcon="forward" busy={props.busy} disabled={!props.timezone || props.blocked}
          disabledReason={props.blocked ? t('activities.blocked') : !props.timezone ? t('activities.timezoneMissing') : undefined}
          onPress={props.onSave} />
      </Card>
      {props.controls}
    </Screen>
  </KeyboardAvoidingView>;
}
const styles = StyleSheet.create({ stack: { gap: space[16] }, fields: { gap: space[24] } });
