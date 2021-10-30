import { ControlBarNav, Button } from './style';

interface ControlBarProps {
  title: string;
  forwardFunc: () => void;
  backFunc: () => void;
  disableForward: boolean;
  disableBack: boolean;
}

export const ControlBar = (props: ControlBarProps) => {
  const { title, forwardFunc, disableForward, backFunc, disableBack } = props;
  return (
    <ControlBarNav>

        <Button onClick={backFunc} disabled={disableBack}>
          Previous
        </Button>
        <h2>{ title }</h2>
        <Button onClick={forwardFunc}  disabled={disableForward}>
          Next
        </Button>

    </ControlBarNav>
  )
}