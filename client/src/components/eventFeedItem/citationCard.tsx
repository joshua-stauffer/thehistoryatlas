import { useQuery } from "@apollo/client";
import { CitationContainer, CitationText } from "./style";
import { GET_CITATION_BY_GUID, GetCitationByGUIDResult, GetCitationByGUIDVars } from '../../graphql/queries';

interface CitationCardProps {
  citationGUID: string;
}


export const CitationCard = ({ citationGUID }: CitationCardProps) => {
  const {
    loading, 
    error, 
    data 
  } = useQuery<GetCitationByGUIDResult, GetCitationByGUIDVars>(
    GET_CITATION_BY_GUID,
    { variables: { citationGUID: citationGUID } }
  )
  const metaData = data ? data.GetCitationByGUID.meta : null;
  const authorText = metaData ? metaData.author : '';
  const publisherText = metaData ? metaData.publisher : '';
  const titleText = metaData ? metaData.title : '';
  const text = data ? data.GetCitationByGUID.text : '';
  return (
    <CitationContainer>
      <CitationText>Author: {authorText}</CitationText>
      <CitationText>Publisher: {publisherText}</CitationText>
      <CitationText>Title: {titleText}</CitationText>
      <CitationText>Text: {text}</CitationText>
    </CitationContainer>
  )  
}