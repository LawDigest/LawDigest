'use client';

import { useRouter } from 'next/navigation';
import { useCallback } from 'react';
import { Button, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter } from '@nextui-org/react';
import { ACCESS_TOKEN } from '@/constants';
import { deleteCookie } from 'cookies-next';
import { postWithdraw } from './apis';

export default function WithdrawModal({ isOpen, onOpenChange }: { isOpen: boolean; onOpenChange: () => void }) {
  const router = useRouter();
  const onClickWithdraw = useCallback(() => {
    postWithdraw().then((res) => {
      if (Number(res.code) === 200) {
        deleteCookie(ACCESS_TOKEN);
        router.push('/login');
      }
    });
  }, []);

  return (
    <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="xs" placement="center">
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader className="flex flex-col gap-1">주의</ModalHeader>
            <ModalBody>
              <p>회원탈퇴를 진행하시겠습니까 ?</p>
            </ModalBody>
            <ModalFooter>
              <Button color="primary" variant="light" onPress={onClose}>
                취소
              </Button>
              <Button color="danger" variant="light" onPress={onClickWithdraw}>
                확인
              </Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
