/* eslint-disable react-hooks/rules-of-hooks */

'use client';

import { useRouter } from 'next/navigation';
import { deleteCookie, getCookie } from 'cookies-next';
import { ACCESS_TOKEN } from '@/constants';
import axios, { AxiosError } from 'axios';
// eslint-disable-next-line import/no-extraneous-dependencies
import _ from 'lodash';

export const handleSuccessReissueToken = (error: AxiosError) => {
  const { response } = error;
  const router = useRouter();

  const newConfig = _.cloneDeep(response!.config);
  const accessToken = getCookie(ACCESS_TOKEN)!;
  newConfig.headers.Authorization = `Bearer ${accessToken}`;

  return axios(newConfig).then(() => router.refresh());
};

export const handleFailReissueToken = () => {
  deleteCookie(ACCESS_TOKEN);
  const router = useRouter();
  router.push('/login');
};
