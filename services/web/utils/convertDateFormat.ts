export default function convertDateFormat(dateStr: string) {
  // 날짜 문자열을 Date 객체로 변환
  const dateObj = new Date(dateStr);

  // 월과 일, 요일 가져오기
  const month = dateObj.getMonth() + 1; // 월은 0부터 시작하므로 1을 더해줌
  const day = dateObj.getDate();
  const options = { weekday: 'long' } as const; // 요일 형식 설정
  const dayOfWeek = dateObj.toLocaleDateString('ko-KR', options).charAt(0); // 한국어 요일

  // 형식에 맞춰 문자열 반환
  return [month, day, dayOfWeek];
}
