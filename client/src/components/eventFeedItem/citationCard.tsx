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
  
  return (
    <CitationContainer>
      <CitationText>Author: Diana C. Rodriguez</CitationText>
      <CitationText>Publisher: History Atlas Press</CitationText>
      <CitationText>Citation: Praesent elementum facilisis leo vel fringilla. Amet luctus venenatis lectus magna fringilla urna porttitor. At ultrices mi tempus imperdiet nulla malesuada pellentesque. Facilisi morbi tempus iaculis urna id volutpat lacus laoreet non. Nunc lobortis mattis aliquam faucibus purus. Dolor sed viverra ipsum nunc aliquet. Morbi enim nunc faucibus a pellentesque sit amet porttitor eget. Ornare suspendisse sed nisi lacus. Posuere lorem ipsum dolor sit. Quis commodo odio aenean sed adipiscing. Fringilla est ullamcorper eget nulla facilisi etiam dignissim diam. Sed nisi lacus sed viverra tellus in hac habitasse.
    </CitationText>
    </CitationContainer>
  )  
}