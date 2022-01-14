import { Typography } from '@material-ui/core';
import { Tag } from './tagEntities';

interface ViewEntityProps {
  tag: Tag
}

export const ViewEntity = (props: ViewEntityProps) => {
  const { tag } = props;
  return (
    <>
    <Typography variant="h3">{tag.name}</Typography>
    <Typography variant="body1">{tag.type}</Typography>
    </>
  )
}