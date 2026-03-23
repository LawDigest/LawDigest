import axios, {
  type AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
  Method,
  AxiosRequestConfig,
} from 'axios';
import { getCookie } from 'cookies-next';
import { ACCESS_TOKEN, HTTP_METHODS } from '@/constants';
import { BaseResponse } from '@/types';
import qs from 'qs';
import { handleSuccessReissueToken, handleFailReissueToken } from '../auth';

const serverApiBaseUrl = process.env.NEXT_PUBLIC_URL ?? 'https://api.lawdigest.net/';

const axiosInstance: AxiosInstance = axios.create({
  baseURL: typeof window === 'undefined' ? `${serverApiBaseUrl}v1` : '/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

axios.defaults.paramsSerializer = (params) => {
  return qs.stringify(params);
};

axiosInstance.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const accessToken = getCookie(ACCESS_TOKEN)!;

    if (!accessToken) {
      return config;
    }
    // eslint-disable-next-line
    config.headers.Authorization = `Bearer ${accessToken}`;
    return config;
  },
  (error: AxiosError) => {
    Promise.reject(error);
  },
);

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      return axiosInstance
        .post('/auth/reissue/token')
        .then(() => {
          return handleSuccessReissueToken(error);
        })
        .catch(() => {
          return handleFailReissueToken();
        });
    }

    return Promise.reject(error);
  },
);

const createApiMethod =
  (instance: AxiosInstance, method: Method) =>
    <T>(config: AxiosRequestConfig): Promise<BaseResponse<T>> =>
      instance({ ...config, method });

const http = {
  get: createApiMethod(axiosInstance, HTTP_METHODS.get),
  post: createApiMethod(axiosInstance, HTTP_METHODS.post),
  patch: createApiMethod(axiosInstance, HTTP_METHODS.patch),
  put: createApiMethod(axiosInstance, HTTP_METHODS.put),
  delete: createApiMethod(axiosInstance, HTTP_METHODS.delete),
};

export default http;
