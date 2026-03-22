/**
 * 알림
 */
export interface Notification {
  title: string;
  notification_id: number;
  content: string;
  target: string;
  type: string;
  extra: string;
  created_date: string;
  notification_image_url_list: string[];
  read: boolean;
}
