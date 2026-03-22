import { Button } from '@nextui-org/button';
import { IconArrowRight } from '@/public/svgs';

export default function EnterButton() {
  return (
    <Button isIconOnly className="bg-transparent">
      <IconArrowRight />
    </Button>
  );
}
