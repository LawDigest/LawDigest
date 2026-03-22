import http from '@/api';
import { TimelineResponse, TimelineBillState } from '@/types';

export const getTimelineFeed = (page: number) =>
  http.get<TimelineResponse>({
    url: `/time-line/feed/paging`,
    params: { page, size: 3 },
  });

export const getTimelineBillState = () =>
  http.get<TimelineBillState>({
    url: `/time-line/bill-state`,
  });
