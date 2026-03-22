'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
  type UseMutationOptions,
} from '@tanstack/react-query';
import { Notification } from '@/types';
import {
  getNotification,
  getNotificationCount,
  getNotificationTopThree,
  putNotificationRead,
  putNotificationReadAll,
  deleteNotification,
  deleteNotificationAll,
} from './apis';

/**
 * 알림 목록을 조회합니다.
 * @param options
 */
export const useGetNotification = <TData = Notification[], TError = unknown>(
  options?: Omit<UseQueryOptions<Notification[], TError, TData, ['notifications']>, 'queryKey' | 'queryFn'>,
) =>
  useQuery({
    queryKey: ['notifications'],
    queryFn: () => getNotification(),
    ...options,
  });

/**
 * 읽지 않은 알림 개수를 조회합니다.
 * @param options
 */
export const useGetNotificationCount = <TData = { user_id: number; notification_count: number }, TError = unknown>(
  options?: Omit<
    UseQueryOptions<{ user_id: number; notification_count: number }, TError, TData, ['notifications', 'count']>,
    'queryKey' | 'queryFn'
  >,
) =>
  useQuery({
    queryKey: ['notifications', 'count'],
    queryFn: () => getNotificationCount(),
    ...options,
  });

/**
 * 읽지 않은 알림 Top3를 조회합니다.
 * @param options
 */
export const useGetNotificationTopThree = <TData = Notification[], TError = unknown>(
  options?: Omit<UseQueryOptions<Notification[], TError, TData, ['notifications', 'top3']>, 'queryKey' | 'queryFn'>,
) =>
  useQuery({
    queryKey: ['notifications', 'top3'],
    queryFn: () => getNotificationTopThree(),
    ...options,
  });

/**
 * 알림을 읽습니다.
 * @param options
 * @returns
 */
export const usePutNotificationRead = <TError = unknown, TVariables extends number = number, TContext = unknown>(
  options?: Omit<UseMutationOptions<Notification[], TError, TVariables, TContext>, 'mutationFn'>,
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: number) => putNotificationRead(notificationId),
    ...options,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'top3'] });

      options?.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      options?.onError?.(error, variables, context);
    },
  });
};

/**
 * 모든 알림을 읽음 처리합니다.
 * @param options
 */
export const usePutNotificationReadAll = <TError = unknown, TContext = unknown>(
  options?: Omit<UseMutationOptions<Notification[], TError, void, TContext>, 'mutationFn'>,
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => putNotificationReadAll(),
    ...options,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'top3'] });

      options?.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      options?.onError?.(error, variables, context);
    },
  });
};

/**
 * 개별 알림을 삭제합니다.
 * @param options
 */
export const useDeleteNotification = <TError = unknown, TVariables extends number = number, TContext = unknown>(
  options?: Omit<UseMutationOptions<Notification[], TError, TVariables, TContext>, 'mutationFn'>,
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: number) => deleteNotification(notificationId),
    ...options,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'top3'] });

      options?.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      options?.onError?.(error, variables, context);
    },
  });
};

/**
 * 모든 알림을 삭제합니다.
 * @param options
 */
export const useDeleteNotificationAll = <TError = unknown, TContext = unknown>(
  options?: Omit<UseMutationOptions<Notification[], TError, void, TContext>, 'mutationFn'>,
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => deleteNotificationAll(),
    ...options,
    onSuccess: (data, variables, context) => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'count'] });
      queryClient.invalidateQueries({ queryKey: ['notifications', 'top3'] });

      options?.onSuccess?.(data, variables, context);
    },
    onError: (error, variables, context) => {
      options?.onError?.(error, variables, context);
    },
  });
};
