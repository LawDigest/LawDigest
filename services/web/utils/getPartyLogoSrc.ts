const LOCAL_PARTY_LOGO_IDS = new Set(['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']);
const LOCAL_DARK_PARTY_LOGO_IDS = new Set(['1', '2', '6', '7', '9', '10']);

export default function getPartyLogoSrc(partyImageUrl: string | null | undefined, isDark: boolean) {
  if (!partyImageUrl) return null;

  const match = partyImageUrl.match(/\/party\/(?:wide|dark)\/(\d+)\.png$/);
  if (!match) {
    return `${process.env.NEXT_PUBLIC_IMAGE_URL ?? ''}${partyImageUrl}`;
  }

  const [, partyId] = match;
  if (!LOCAL_PARTY_LOGO_IDS.has(partyId)) {
    return `${process.env.NEXT_PUBLIC_IMAGE_URL ?? ''}${partyImageUrl}`;
  }

  const variant = isDark && LOCAL_DARK_PARTY_LOGO_IDS.has(partyId) ? 'dark' : 'wide';
  return `/images/parties/${variant}/${partyId}.png`;
}
