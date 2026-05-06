import { TimelineBoard, ListContainer } from './components';

export const dynamic = 'force-dynamic';

export default function Timeline() {
  return (
    <section>
      <TimelineBoard />
      <ListContainer />
    </section>
  );
}
