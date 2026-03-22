import { atom } from 'recoil';

interface SearchModalStateProps {
  show: boolean;
}

const searchModalState = atom<SearchModalStateProps>({
  key: 'searchModalState',
  default: {
    show: false,
  },
});

export default searchModalState;
