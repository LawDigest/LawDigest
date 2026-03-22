export interface BaseResponse<T> {
  code: string;
  data: T;
  message: string;
}
