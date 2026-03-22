import { atom } from 'recoil';
import { SnackbarType } from '@/types';

interface SnackbarStateProps {
  show: boolean;
  type: SnackbarType;
  message: string;
  duration?: number;
}

const snackbarState = atom<SnackbarStateProps>({
  key: 'snackbarState',
  default: {
    show: false,
    type: 'DEFAULT',
    message: '',
    duration: 3000,
  },
});

export default snackbarState;
