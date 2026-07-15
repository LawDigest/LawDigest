import { Button } from '@heroui/button';
import { IconArrowRight } from '@/public/svgs';

export default function EnterButton() {
  return (
    <Button isIconOnly className="bg-transparent">
      <IconArrowRight />
    </Button>
  );
}
