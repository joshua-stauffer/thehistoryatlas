import { PUBLISH_NEW_CITATION, PublishNewCitationResult, PublishNewCitationVars } from '../../graphql/publishNewCitation';
import { useQuery } from '@apollo/client'


export const SaveSummary = (annotation: PublishNewCitationVars) => {
    const {
      data, loading, error
    } = useQuery<PublishNewCitationResult, PublishNewCitationVars>(PUBLISH_NEW_CITATION,
      { variables: {...annotation} }
    )
    if (loading) {
        return <h1>Loading</h1>
    } else if (error) {
        return <h1>{error}</h1>
    }
  }