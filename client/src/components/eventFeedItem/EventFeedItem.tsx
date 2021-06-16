import { client } from '../../index';
import { SummaryBox } from './style';
import { GET_SUMMARIES_BY_GUID, GetSummariesByGUIDResult, GetSummariesByGUIDVars } from '../../graphql/queries';


interface EventFeedItemProps {
  guid: string;
}

export const EventFeedItem = ({ guid }: EventFeedItemProps) => {
  const result = client.readQuery({
    query: GET_SUMMARIES_BY_GUID,
    variables: {
      summary_guids: [guid]
    }
  })
  console.log(result)
  return (
    <SummaryBox>
      {guid}
    </SummaryBox>
  )
}