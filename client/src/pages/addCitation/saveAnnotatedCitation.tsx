import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { PUBLISH_NEW_CITATION, PublishNewCitationResult, PublishNewCitationVars } from '../../graphql/publishNewCitation';
import { useMutation } from '@apollo/client'
import { isParameter } from 'typescript';

interface SaveSummaryProps {
  annotation: PublishNewCitationVars["Annotation"]
}

export const SaveSummary = (props: SaveSummaryProps) => {
  const {annotation: Annotation} = props;
  const { summary, meta, summaryTags, citation } = Annotation
  // remove temporary IDs 
  const updatedTags = summaryTags.map(tag => tag.id?.startsWith("new") ? {...tag, id: undefined} : tag)
  const updatedAnnotation = {
    summary: summary,
    meta: meta,
    citation: citation,
    summaryTags: updatedTags,
    citationId: Annotation.citationId,
    summaryId: Annotation.summaryId,
    token: Annotation.token
  }
  console.log("about to publish new citation -----")
  console.log({updatedAnnotation})
  console.log({updatedTags})
  const [
    uploadSummary,
    { data, loading, error }
   ] = useMutation<PublishNewCitationResult, PublishNewCitationVars>(PUBLISH_NEW_CITATION)
  console.log({error})
  if (loading) {
      return <Typography variant="h2">Loading</Typography>
  } else if (error) {
      return <Typography variant="h2">there was an error</Typography>
  } else if (data) {
    return <Typography variant="h2">Thanks for contributing to the History Atlas!</Typography>
  } else {
    return (
      <Paper>
        <Typography variant="h2" align='center' sx={{alignItems: 'center'}}>Confirm and Upload Citation</Typography>
        <Typography variant="h3" sx={{marginTop: 20}}>Source</Typography>
        <Typography variant="body1">Author: {meta.author}</Typography>
        <Typography variant="body1">Title: {meta.title}</Typography>
        <Typography variant="body1">Publisher: {meta.publisher}</Typography>
        <Typography variant="h3" sx={{marginTop: 20}}>Citation Text</Typography>
        <Typography variant="body1">{citation}</Typography>
        <Typography variant="h3" sx={{marginTop: 20}}>Summary Text</Typography>
        <Typography variant="body1">{summary}</Typography>
        <Typography variant="h3" sx={{marginTop: 20}}>Entity Tags</Typography>
        {
          summaryTags.map(tag => 
          <Chip label={tag.name}/>
          )
        }
        <br />
        <Button 
          onClick={() => uploadSummary({ variables: { Annotation: updatedAnnotation } })}
          variant="contained"
          sx={{marginTop: 20}}
          color='secondary'
        >Upload</Button>
      </Paper>
    )
  }
}
