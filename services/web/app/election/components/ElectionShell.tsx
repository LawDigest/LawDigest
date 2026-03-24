'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Card, CardBody, Spinner, Button } from '@nextui-org/react';
import { Layout } from '@/components';
import {
  ElectionId,
  ElectionRegionCode,
  ElectionRegionResolveRequest,
  ElectionRegionResolveResponse,
  ElectionRegionType,
} from '@/types';
import { useGetElectionSelector, usePostElectionRegionConfirm, usePostElectionRegionResolve } from '../apis/queries';
import { compareElectionSelectorItems, getDefaultElectionId } from '../utils/compareRules';
import {
  inferElectionFamilyFromId,
  getElectionFamilyLabel,
  getElectionHeadline,
  getResolveStateMessage,
} from '../utils/electionLabels';
import ElectionModeTabs from './ElectionModeTabs';
import ElectionSelector from './ElectionSelector';
import EmptyRegionState from './EmptyRegionState';
import ManualRegionPicker, { ManualRegionFormValue } from './ManualRegionPicker';
import PresidentialElectionView from './PresidentialElectionView';
import RegionConfirmCard from './RegionConfirmCard';
import RegionalElectionView from './RegionalElectionView';

type ConfirmedRegion = {
  regionCode: ElectionRegionCode;
  regionType: ElectionRegionType;
  regionName: string;
};

type PendingRequestGuard = {
  electionId: ElectionId;
  requestId: number;
};

const buildConfirmedRegion = (
  response: ElectionRegionResolveResponse | undefined,
  fallback?: Partial<ConfirmedRegion>,
): ConfirmedRegion | null => {
  const regionCode = response?.suggested_region_code ?? fallback?.regionCode ?? null;
  const regionType = response?.suggested_region_type ?? fallback?.regionType ?? null;
  const regionName = response?.suggested_region_name ?? fallback?.regionName ?? null;

  if (!regionCode || !regionType || !regionName) {
    return null;
  }

  return {
    regionCode,
    regionType,
    regionName,
  };
};

const createResolveState = (
  electionId: ElectionId,
  state: ElectionRegionResolveResponse['state'],
  manualCorrectionAvailable: boolean,
): ElectionRegionResolveResponse => ({
  election_id: electionId,
  state,
  confirmation_required: false,
  suggested_region_type: null,
  suggested_region_code: null,
  suggested_region_name: null,
  manual_correction_available: manualCorrectionAvailable,
  deny_available: false,
});

export default function ElectionShell() {
  const selectorQuery = useGetElectionSelector();
  const resolveRegion = usePostElectionRegionResolve();
  const confirmRegion = usePostElectionRegionConfirm();

  const selectorData = selectorQuery.data?.data;
  const sortedElections = useMemo(
    () => [...(selectorData?.elections ?? [])].sort(compareElectionSelectorItems),
    [selectorData?.elections],
  );

  const [selectedElectionId, setSelectedElectionId] = useState<ElectionId>('local-2026');
  const [resolution, setResolution] = useState<ElectionRegionResolveResponse | null>(null);
  const [confirmedRegion, setConfirmedRegion] = useState<ConfirmedRegion | null>(null);
  const [showManualPicker, setShowManualPicker] = useState(false);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [activePendingRequest, setActivePendingRequest] = useState<PendingRequestGuard | null>(null);
  const selectedElectionIdRef = useRef(selectedElectionId);
  const latestRequestIdRef = useRef(0);

  useEffect(() => {
    if (!selectorData) {
      return;
    }

    setSelectedElectionId((current) => {
      if (selectorData.elections.some(({ election_id }) => election_id === current)) {
        return current;
      }

      return getDefaultElectionId(selectorData);
    });
  }, [selectorData]);

  useEffect(() => {
    selectedElectionIdRef.current = selectedElectionId;
  }, [selectedElectionId]);

  useEffect(() => {
    latestRequestIdRef.current += 1;
    setResolution(null);
    setConfirmedRegion(null);
    setShowManualPicker(false);
    setFlowError(null);
    setActivePendingRequest(null);
  }, [selectedElectionId]);

  const selectedElection = useMemo(
    () => sortedElections.find(({ election_id }) => election_id === selectedElectionId) ?? null,
    [selectedElectionId, sortedElections],
  );

  const electionFamily = inferElectionFamilyFromId(selectedElectionId);
  const isRegionalElection = electionFamily !== 'president';
  let selectionDescription = '선거를 선택하면 지역 기반 결과 셸을 확인할 수 있습니다.';

  if (selectedElection) {
    selectionDescription =
      electionFamily === 'president'
        ? '대통령 선거는 후보자 중심 전용 템플릿으로 보여줍니다.'
        : `${getElectionFamilyLabel(electionFamily)} 기준으로 지역별 결과 템플릿을 준비했습니다.`;
  }

  const createRequestGuard = (): PendingRequestGuard => {
    const requestId = latestRequestIdRef.current + 1;
    latestRequestIdRef.current = requestId;

    return {
      electionId: selectedElectionIdRef.current,
      requestId,
    };
  };

  const isGuardCurrent = ({ electionId, requestId }: PendingRequestGuard) =>
    selectedElectionIdRef.current === electionId && latestRequestIdRef.current === requestId;

  const mutationPending =
    !!activePendingRequest &&
    activePendingRequest.electionId === selectedElectionId &&
    isGuardCurrent(activePendingRequest);

  const beginPendingRequest = (guard: PendingRequestGuard) => {
    setActivePendingRequest(guard);
  };

  const finishPendingRequest = (guard: PendingRequestGuard) => {
    setActivePendingRequest((current) => {
      if (!current) {
        return current;
      }

      if (current.electionId !== guard.electionId || current.requestId !== guard.requestId) {
        return current;
      }

      return null;
    });
  };

  const applyResolvedRegion = (
    response: ElectionRegionResolveResponse | undefined,
    fallback?: Partial<ConfirmedRegion>,
    guard?: PendingRequestGuard,
  ) => {
    if (!response || (guard && !isGuardCurrent(guard))) {
      return;
    }

    setFlowError(null);
    setResolution(response);

    const nextRegion = buildConfirmedRegion(response, fallback);
    if (response.state === 'confirmed' && nextRegion) {
      setConfirmedRegion(nextRegion);
      setShowManualPicker(false);
      return;
    }

    setConfirmedRegion(null);
    setShowManualPicker(response.state === 'manual-required');
  };

  const handleResolveSuccess = (
    response: ElectionRegionResolveResponse | undefined,
    fallback?: Partial<ConfirmedRegion>,
    guard?: PendingRequestGuard,
  ) => {
    applyResolvedRegion(response, fallback, guard);
  };

  const recoverFromMutationError = (guard: PendingRequestGuard, message: string) => {
    if (!isGuardCurrent(guard)) {
      return;
    }

    setConfirmedRegion(null);
    setResolution((current) => ({
      ...(current ?? createResolveState(guard.electionId, 'manual-required', true)),
      election_id: guard.electionId,
      state: 'manual-required',
      confirmation_required: false,
      manual_correction_available: true,
      deny_available: false,
    }));
    setShowManualPicker(true);
    setFlowError(message);
  };

  const handleResolveRegion = () => {
    setFlowError(null);

    if (typeof window === 'undefined' || !navigator.geolocation) {
      setResolution(createResolveState(selectedElectionIdRef.current, 'manual-required', true));
      setShowManualPicker(true);
      return;
    }

    const guard = createRequestGuard();
    beginPendingRequest(guard);
    setResolution(createResolveState(guard.electionId, 'requesting-permission', false));

    navigator.geolocation.getCurrentPosition(
      async ({ coords }) => {
        try {
          const response = await resolveRegion.mutateAsync({
            election_id: guard.electionId,
            latitude: coords.latitude,
            longitude: coords.longitude,
            permission_status: 'granted',
          });

          handleResolveSuccess(response.data, undefined, guard);
        } catch {
          recoverFromMutationError(guard, '지역 확인 요청에 실패했습니다. 직접 지역을 선택하거나 다시 시도해 주세요.');
        } finally {
          finishPendingRequest(guard);
        }
      },
      async () => {
        try {
          const response = await resolveRegion.mutateAsync({
            election_id: guard.electionId,
            permission_status: 'denied',
          });

          handleResolveSuccess(response.data, undefined, guard);
          if (isGuardCurrent(guard) && response.data.state !== 'gps-suggested') {
            setShowManualPicker(true);
          }
        } catch {
          recoverFromMutationError(guard, '위치 권한 없이 지역을 찾지 못했습니다. 직접 지역을 선택해 주세요.');
        } finally {
          finishPendingRequest(guard);
        }
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 },
    );
  };

  const handleConfirmSuggestedRegion = async () => {
    if (!resolution?.suggested_region_code || !resolution.suggested_region_type || !resolution.suggested_region_name) {
      return;
    }

    const guard = createRequestGuard();
    const requestBody: ElectionRegionResolveRequest = {
      election_id: guard.electionId,
      region_code: resolution.suggested_region_code,
      region_type: resolution.suggested_region_type,
      region_name: resolution.suggested_region_name,
      permission_status: 'granted',
    };

    setFlowError(null);
    beginPendingRequest(guard);

    try {
      const response = await confirmRegion.mutateAsync(requestBody);
      handleResolveSuccess(
        response.data,
        {
          regionCode: resolution.suggested_region_code,
          regionType: resolution.suggested_region_type,
          regionName: resolution.suggested_region_name,
        },
        guard,
      );
    } catch {
      recoverFromMutationError(guard, '추천 지역 확정에 실패했습니다. 직접 지역을 선택하거나 다시 시도해 주세요.');
    } finally {
      finishPendingRequest(guard);
    }
  };

  const handleManualSubmit = async ({ regionCode, regionName, regionType }: ManualRegionFormValue) => {
    const guard = createRequestGuard();
    setFlowError(null);
    beginPendingRequest(guard);

    try {
      const response = await confirmRegion.mutateAsync({
        election_id: guard.electionId,
        region_code: regionCode,
        region_name: regionName,
        region_type: regionType,
        permission_status: 'idle',
      });

      handleResolveSuccess(response.data, { regionCode, regionName, regionType }, guard);
    } catch {
      recoverFromMutationError(guard, '수동 지역 확정에 실패했습니다. 입력값을 확인한 뒤 다시 시도해 주세요.');
    } finally {
      finishPendingRequest(guard);
    }
  };

  return (
    <Layout nav logo>
      <section className="flex flex-col gap-6 px-5 py-6 md:px-8 md:py-8">
        <header className="flex flex-col gap-3">
          <div className="space-y-1">
            <p className="text-sm font-medium text-gray-500">선거</p>
            <h1 className="text-3xl font-bold tracking-tight">{getElectionHeadline(selectedElection)}</h1>
          </div>
          <p className="text-sm leading-6 text-gray-500">{selectionDescription}</p>
        </header>

        {selectorQuery.isLoading ? (
          <Card className="border border-default-200 bg-transparent">
            <CardBody className="flex min-h-[160px] items-center justify-center">
              <Spinner color="default" label="선거 목록을 불러오는 중입니다." />
            </CardBody>
          </Card>
        ) : null}

        {!selectorQuery.isLoading && selectorQuery.isError ? (
          <Card className="border border-danger-200 bg-danger-50/40">
            <CardBody className="flex flex-col gap-4 p-6">
              <div className="space-y-1">
                <h2 className="text-xl font-semibold">선거 목록을 불러오지 못했습니다.</h2>
                <p className="text-sm leading-6 text-gray-500">
                  네트워크 상태를 확인한 뒤 다시 시도해 주세요. 복구되면 선거를 선택하고 바로 지도를 볼 수 있습니다.
                </p>
              </div>
              <div>
                <Button
                  color="default"
                  className="font-medium"
                  onClick={() => {
                    selectorQuery.refetch();
                  }}>
                  다시 시도
                </Button>
              </div>
            </CardBody>
          </Card>
        ) : null}

        {!selectorQuery.isLoading && !selectorQuery.isError && selectorData ? (
          <>
            <ElectionSelector
              elections={sortedElections}
              selectedElectionId={selectedElectionId}
              onChange={setSelectedElectionId}
            />

            {isRegionalElection ? (
              <>
                <ElectionModeTabs selectedKey="REGIONAL" />

                {flowError ? (
                  <div
                    role="alert"
                    className="rounded-2xl border border-danger-200 bg-danger-50/40 px-4 py-3 text-sm leading-6 text-danger-700">
                    {flowError}
                  </div>
                ) : null}

                {confirmedRegion ? (
                  <RegionalElectionView
                    electionId={selectedElectionId}
                    regionCode={confirmedRegion.regionCode}
                    regionType={confirmedRegion.regionType}
                    regionName={confirmedRegion.regionName}
                  />
                ) : null}

                {!confirmedRegion && resolution?.state === 'gps-suggested' && !showManualPicker ? (
                  <RegionConfirmCard
                    isPending={mutationPending}
                    regionName={resolution.suggested_region_name}
                    regionCode={resolution.suggested_region_code}
                    regionType={resolution.suggested_region_type}
                    onConfirm={handleConfirmSuggestedRegion}
                    onManualSelect={() => setShowManualPicker(true)}
                  />
                ) : null}

                {!confirmedRegion && showManualPicker ? (
                  <ManualRegionPicker
                    isPending={mutationPending}
                    initialValue={{
                      regionCode: resolution?.suggested_region_code ?? '',
                      regionName: resolution?.suggested_region_name ?? '',
                      regionType: resolution?.suggested_region_type ?? 'PROVINCE',
                    }}
                    onSubmit={handleManualSubmit}
                    onCancel={() => setShowManualPicker(false)}
                  />
                ) : null}

                {!confirmedRegion &&
                !showManualPicker &&
                resolution?.state !== 'gps-suggested' &&
                resolution?.state !== 'requesting-permission' ? (
                  <EmptyRegionState
                    isPending={mutationPending}
                    title="지역을 확인하면 지역별 선거 결과 셸이 열립니다."
                    description={getResolveStateMessage(resolution?.state)}
                    onResolve={handleResolveRegion}
                    onManualSelect={() => setShowManualPicker(true)}
                  />
                ) : null}

                {resolution?.state === 'requesting-permission' ? (
                  <div className="flex items-center gap-3 rounded-2xl border border-dashed border-default-300 px-4 py-3 text-sm text-gray-500">
                    <Spinner size="sm" color="default" />
                    <span>현재 위치 권한을 확인하고 있습니다.</span>
                  </div>
                ) : null}

                {confirmedRegion ? (
                  <div className="flex items-center justify-between rounded-2xl border border-default-200 bg-default-50 px-4 py-3">
                    <div>
                      <p className="text-xs font-medium uppercase tracking-[0.16em] text-gray-500">선택된 지역</p>
                      <p className="mt-1 text-sm font-semibold">{confirmedRegion.regionName}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="light"
                      onClick={() => {
                        setConfirmedRegion(null);
                        setShowManualPicker(true);
                      }}>
                      지역 변경
                    </Button>
                  </div>
                ) : null}
              </>
            ) : (
              <PresidentialElectionView electionId={selectedElectionId} />
            )}
          </>
        ) : null}
      </section>
    </Layout>
  );
}
