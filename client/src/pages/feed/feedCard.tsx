import { useRef } from 'react';
import { Card, CardContent, Typography } from '@mui/material'

import { CurrentFocus } from '../../types';


interface FeedCardProps {
  currentFocus: CurrentFocus
  summary: {
    guid: string;
    text: string;
    tags: {
      tag_type: string;
      tag_guid: string;
      start_char: number;
      stop_char: number;
      names?: string[] | undefined;
      name?: string | undefined;
    }[]
    citation_guids: string[];
  }
}

export const FeedCard = (props: FeedCardProps) => {
  const { 
    summary: { guid, text }, 
    currentFocus: { focusedGUID, scrollIntoView } 
  } = props;

  const ref = useRef<HTMLDivElement>(null)
  if (ref.current && guid === focusedGUID) {
    if (scrollIntoView) ref.current.scrollIntoView()
  }
  // console.log({props})

  return (
    <Card 
      ref={ref} 
      variant={"outlined"}
      sx={{
        height: 150
      }}
    >
      <CardContent><Typography variant="h6">{text}</Typography></CardContent>
    </Card>
  )
}
