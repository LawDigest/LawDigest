import { atomWithReset } from 'jotai/utils';
import { SnackbarType } from '@/types';

interface SnackbarStateProps {
  show: boolean;
  type: SnackbarType;
  message: string;
  duration?: number;
}

const snackbarState = atomWithReset<SnackbarStateProps>({
  show: false,
  type: 'DEFAULT',
  message: '',
  duration: 3000,
});

export default snackbarState;
