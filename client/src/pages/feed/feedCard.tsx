import { useRef } from 'react';
import { Card, CardContent } from '@mui/material'

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

  return (
    <Card ref={ref} variant={"outlined"}>
      <CardContent>{text}</CardContent>
    </Card>
  )
}
