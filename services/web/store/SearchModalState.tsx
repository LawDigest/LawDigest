import { atomWithReset } from 'jotai/utils';

interface SearchModalStateProps {
  show: boolean;
}

const searchModalState = atomWithReset<SearchModalStateProps>({
  show: false,
});

export default searchModalState;
