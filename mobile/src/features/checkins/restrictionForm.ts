import type { AthletePlanChoice, CheckInRestriction, Discipline, InjuryRestriction, RestrictionStatus } from '../../api/types';

export type RestrictionChoice = 'none' | 'low' | 'blocked' | 'professional' | 'retain';
export type RestrictionForm = {
  choice: RestrictionChoice | null;
  advice: string;
  adviceAt: string | null | undefined;
  original: CheckInRestriction | null;
  previous: InjuryRestriction | null;
  reviewed: boolean;
};

export const restrictionLabels: Record<RestrictionStatus, string> = {
  none: 'Vrij',
  self_reported_limited: 'Alleen rustig',
  self_reported_blocked: 'Geblokkeerd',
  professional_restricted: 'Professioneel advies',
  clearance_required: 'Vrijgave vereist',
  expired: 'Herbeoordeling vereist; beperking blijft actief',
};

const choices: Record<RestrictionStatus, RestrictionChoice> = {
  none: 'none', self_reported_limited: 'low', self_reported_blocked: 'blocked',
  professional_restricted: 'professional', clearance_required: 'retain', expired: 'retain',
};
const sources = ['athlete', 'physician', 'physiotherapist', 'other_professional'] as const;
const disciplines: Discipline[] = ['swim', 'bike', 'run'];

export function sameRestriction(left: CheckInRestriction, right: InjuryRestriction): boolean {
  return left.status === right.status && left.source === right.source &&
    left.athlete_plan_choice === right.athlete_plan_choice &&
    (left.professional_advice ?? null) === (right.professional_advice ?? null) &&
    (left.professional_advice_at ? Date.parse(left.professional_advice_at) : null) ===
      (right.professional_advice_at ? Date.parse(right.professional_advice_at) : null);
}

export function restoreRestrictions(
  saved: readonly CheckInRestriction[],
  active: readonly InjuryRestriction[],
): Record<Discipline, RestrictionForm> {
  if ([...saved, ...active].some(item => !disciplines.includes(item.discipline) ||
      !Object.prototype.hasOwnProperty.call(choices, item.status) || !['keep_blocked', 'train_low_only', 'resume_unrestricted'].includes(item.athlete_plan_choice)) ||
      active.some(item => item.cleared_at === undefined)) {
    throw new Error('De opgeslagen beperkingen zijn onvolledig. Heropen de check-in.');
  }
  const current = active.filter(item => item.cleared_at === null && item.status !== 'none');
  if ([...saved, ...current].some(item => !sources.includes(item.source as CheckInRestriction['source']))) {
    throw new Error('De bron van een bestaande beperking moet worden gecontroleerd.');
  }
  if (new Set(saved.map(item => item.discipline)).size !== saved.length ||
      new Set(current.map(item => item.discipline)).size !== current.length) {
    throw new Error('De beperkingen konden niet eenduidig worden geladen. Heropen de check-in.');
  }
  // Keep the saved sequence as well as the decision values on an unchanged save.
  const order = [...new Set([...saved.map(item => item.discipline), ...disciplines])];
  return Object.fromEntries(order.map(discipline => {
    const previous = current.find(item => item.discipline === discipline) ?? null;
    const existing = saved.find(item => item.discipline === discipline);
    let original: CheckInRestriction | null = existing ? { ...existing } : null;
    if (!original && previous) {
      original = {
        discipline, status: previous.status, source: previous.source as CheckInRestriction['source'],
        athlete_plan_choice: previous.athlete_plan_choice,
        professional_advice: previous.professional_advice,
        professional_advice_at: previous.professional_advice_at,
      };
    }
    return [discipline, {
      choice: original ? choices[original.status] : null,
      advice: original?.professional_advice ?? '',
      adviceAt: original?.professional_advice_at,
      original, previous, reviewed: previous === null,
    }];
  })) as Record<Discipline, RestrictionForm>;
}

export function restrictionPayload(discipline: Discipline, form: RestrictionForm): CheckInRestriction {
  if (form.choice === null || (form.previous && !form.reviewed)) {
    throw new Error('Beoordeel elke discipline en elke bestaande beperking expliciet.');
  }
  if (form.original && form.choice === choices[form.original.status] &&
      form.advice === (form.original.professional_advice ?? '')) {
    return { ...form.original };
  }
  if (form.choice === 'retain') {
    if (!form.original) throw new Error('De bestaande beperking ontbreekt.');
    return { ...form.original };
  }
  if (form.choice === 'professional') {
    if (!form.advice.trim() || !form.adviceAt) {
      throw new Error('Vul het professionele advies en de herleidbare bron in.');
    }
    return {
      discipline, status: 'professional_restricted',
      source: form.original?.status === 'professional_restricted' ? form.original.source : 'physiotherapist',
      athlete_plan_choice: 'keep_blocked', professional_advice: form.advice.trim(),
      professional_advice_at: form.adviceAt,
    };
  }
  const values: Record<'none' | 'low' | 'blocked', [RestrictionStatus, AthletePlanChoice]> = {
    none: ['none', 'resume_unrestricted'], low: ['self_reported_limited', 'train_low_only'],
    blocked: ['self_reported_blocked', 'keep_blocked'],
  };
  const [status, athlete_plan_choice] = values[form.choice];
  // A new athlete choice does not erase the advice that was shown alongside it.
  return { ...form.original, discipline, status, source: 'athlete', athlete_plan_choice };
}
