
import { useQuery } from '@apollo/client';
import { GET_TEXT_ANALYSIS } from './graphql/queries';
import { TextVisualizer } from './components/textVisualizer';

interface ReviewCitationProps {
  text: string;
}


export const ReviewCitationPage = ({ text }: ReviewCitationProps) => {
  const { loading, error, data } = useQuery(GET_TEXT_ANALYSIS,
      {variables: { text: text }}
    )

  if (loading) return <p>loading..</p>
  if (error) return <p>error!</p>
  console.log(data)
  const chunkedText = [{text: 'On', entityType: ''}]
  return <TextVisualizer chunkedText={chunkedText}/>
}