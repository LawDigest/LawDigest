export default function getDDay(targetDate: string) {
  const now = new Date();
  const target = new Date(targetDate);
  const differenceInTime = target.getTime() - now.getTime();
  const differenceInDays = Math.ceil(differenceInTime / (1000 * 3600 * 24));

  return differenceInDays;
}
