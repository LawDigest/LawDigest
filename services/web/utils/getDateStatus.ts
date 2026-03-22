export default function getDateStatus(date: string) {
  /**
   * 기준일: 오늘(00:00:00)
   * - 지난 한 주: 오늘을 포함해 과거 6일 전까지 (총 7일)
   * - 지난 한 달: 오늘을 포함해 과거 29일 전까지 (총 30일)
   * 그 외: 지난 알림
   */

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const inputDate = new Date(date);
  inputDate.setHours(0, 0, 0, 0);

  // 지난 한 주(최근 7일) 계산
  const startOfLast7Days = new Date(today);
  startOfLast7Days.setDate(today.getDate() - 6);

  // 지난 한 달(최근 30일) 계산
  const startOfLast30Days = new Date(today);
  startOfLast30Days.setDate(today.getDate() - 29);

  if (inputDate >= startOfLast7Days && inputDate <= today) {
    return '지난 한 주';
  }

  if (inputDate >= startOfLast30Days && inputDate < startOfLast7Days) {
    return '지난 한 달';
  }

  return '지난 알림';
}
