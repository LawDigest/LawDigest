/**
 * 오브젝트 스토리지에 저장된 상대 경로 이미지 URL에 오리진(NEXT_PUBLIC_IMAGE_URL) 접두어를 붙인다.
 * 경로가 비어 있으면 undefined를 반환하여 <Avatar> 등의 폴백이 동작하도록 한다.
 */
export default function getImageSrc(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  return `${process.env.NEXT_PUBLIC_IMAGE_URL ?? ''}${path}`;
}
