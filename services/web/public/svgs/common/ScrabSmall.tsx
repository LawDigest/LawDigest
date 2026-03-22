export default function IconScrabSmall({ isActive }: { isActive: boolean }) {
  return isActive ? (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4.65 20.9483V2.65H19.35V20.9483L12.2907 17.4186L12 17.2733L11.7093 17.4186L4.65 20.9483Z"
        fill="#E63946"
      />
    </svg>
  ) : (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M4.65 20.9483V2.65H19.35V20.9483L12.2907 17.4186L12 17.2733L11.7093 17.4186L4.65 20.9483Z"
        stroke="#555555"
        strokeWidth="1.3"
      />
    </svg>
  );
}
