export default function getTimeRemaining(time: string) {
  const timeDiff = new Date().getTime() - new Date(time.replace('T', ' ')).getTime();
  const hours = Math.floor(timeDiff / 1000 / 60 / 60);
  // eslint-disable-next-line no-nested-ternary
  return hours > 720
    ? time.split(' ')[0]
    : // eslint-disable-next-line no-nested-ternary
      hours > 24
      ? `${Math.floor(hours / 24)}일 전`
      : hours > 0
        ? `${hours}시간 전`
        : `${Math.floor(timeDiff / 1000 / 60)}분 전`;
}
