import {Paper, Chip} from '@mui/material'
import { Person, Place, LockClockRounded } from '@mui/icons-material'

import { addToHistoryProps } from '../../hooks/history';
import { EntityType } from '../../types'

interface Tag {
  tag_type: EntityType;
  tag_guid: string;
  start_char: number;
  stop_char: number;
  names?: string[] | undefined;
  name?: string | undefined;
}

interface TagBoxProps {
  tags: Tag[]
  setCurrentEntity: (props: addToHistoryProps) => void
}

export const TagBox = (props: TagBoxProps) => {
  const { tags, setCurrentEntity } = props;
  return (
      <>
      {tags.map(tag => 
        <Chip 
          variant={"filled"}
          onClick={() => setCurrentEntity({ 
            entity: { 
              name: tag.name ?? 'NO NAME',
              guid: tag.tag_guid, 
              type: tag.tag_type 
            } })}
          icon={ tag.tag_type === 'PERSON'
            ? <Person />
            : tag.tag_type === 'PLACE'
            ? <Place />
            : <LockClockRounded />
          }
          title={tag.names?.join(' ') ?? tag.name ?? ''}
          label={tag.names?.join(' ') ?? tag.name ?? ''}
        />
      )
    }
    </>
  )
}
