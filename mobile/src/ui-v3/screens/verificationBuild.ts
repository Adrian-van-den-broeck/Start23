// Staging candidates only: the three checks the sign-in screen uses before it
// prints its build line. Internal provenance stays out of production builds.
const verificationHost = 'r6-api-r6-staging.up.railway.app';

export function isVerificationBuild(): boolean {
  return process.env.EXPO_PUBLIC_VERIFICATION_BUILD === '1' &&
    process.env.EXPO_PUBLIC_API_BASE_URL === `https://${verificationHost}` &&
    process.env.EXPO_PUBLIC_SUPABASE_URL === 'https://isfumhgqphieoayqahjv.supabase.co';
}
