import { Paper, Button, Typography } from '@material-ui/core'

import { PUBLISH_NEW_CITATION, PublishNewCitationResult, PublishNewCitationVars } from '../../graphql/publishNewCitation';
import { useMutation } from '@apollo/client'

interface SaveSummaryProps {
  annotation: PublishNewCitationVars["Annotation"]
}

export const SaveSummary = (props: SaveSummaryProps) => {
  const {annotation: Annotation} = props;
  const [
    uploadSummary,
    { data, loading, error }
   ] = useMutation<PublishNewCitationResult, PublishNewCitationVars>(PUBLISH_NEW_CITATION)
  console.log({data})
  console.log({loading})
  console.log({error})
  if (loading) {
      return <Typography variant="h2">Loading</Typography>
  } else if (error) {
      return <Typography variant="h2">there was an error</Typography>
  } else if (data) {
    return <Typography variant="h2">Success!</Typography>
  } else {
    return <Paper><Button onClick={() => uploadSummary({ variables: { Annotation } })}>Upload</Button></Paper>
  }
}
