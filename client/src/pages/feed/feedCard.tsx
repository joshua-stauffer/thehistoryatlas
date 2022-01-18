import { useRef, useState } from 'react';
import { Card, CardContent, CardActions, Typography, Collapse, IconButton } from '@mui/material'
import ExpandMoreIcon from '@material-ui/icons/ExpandMore'
import ShareIcon from '@material-ui/icons/Share'

import { CurrentFocus } from '../../types';
import { SourceContent } from './sourceContent';


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
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const toggleIsOpen = () => setIsOpen(current => !current)
  const { 
    summary: { guid, text, citation_guids }, 
    currentFocus: { focusedGUID, scrollIntoView },
  } = props;

  const ref = useRef<HTMLDivElement>(null)
  if (ref.current && guid === focusedGUID) {
    if (scrollIntoView) ref.current.scrollIntoView()
  }

  return (
    <Card 
      ref={ref} 
      variant={"outlined"}
      sx={{
        minHeight: 150
      }}
    >
      <CardContent><Typography variant="h6" gutterBottom textAlign="center">{text}</Typography></CardContent>
      <CardActions>
        <IconButton>
          <ShareIcon />
        </IconButton>
        <IconButton
          onClick={toggleIsOpen}
        >
          <Typography variant="button">Source</Typography>
          <ExpandMoreIcon />
        </IconButton>
      </CardActions>
      <Collapse in={isOpen} timeout="auto">
        <Typography>Hi! Citation here soon.</Typography>
      </Collapse>
    </Card>
  )
}
// <SourceContent citationGUIDs={citation_guids} isOpen={isOpen} />