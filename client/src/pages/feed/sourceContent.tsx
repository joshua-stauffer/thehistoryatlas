import { useQuery } from "@apollo/client";
import { CardContent, Typography, Skeleton } from "@mui/material";
import {
  GET_CITATION_BY_GUID,
  GetCitationByGUIDResult,
  GetCitationByGUIDVars,
} from "../../graphql/getCitationByGUID";

interface SourceContentProps {
  citationGUIDs: string[];
  isOpen: boolean;
}

export const SourceContent = (props: SourceContentProps) => {
  const { citationGUIDs, isOpen } = props;
  const guid = isOpen && citationGUIDs.length ? citationGUIDs[0] : "";
  const { data, loading, error } = useQuery<
    GetCitationByGUIDResult,
    GetCitationByGUIDVars
  >(GET_CITATION_BY_GUID, { variables: { citationGUID: guid } });
  console.log({ data, loading, error });
  if (error)
    return (
      <CardContent>
        <Typography variant="h4">Oops!</Typography>
        <Typography variant="body2">
          There was an error loading this citation. Please try again later
        </Typography>
      </CardContent>
    );
  if (loading || !data?.GetCitationByGUID.meta)
    return (
      <Skeleton
        sx={{
          height: 100,
        }}
      />
    );
  return (
    <CardContent>
      <Typography variant="h4">Source</Typography>
      <Typography variant="body2">{data.GetCitationByGUID.meta}</Typography>
    </CardContent>
  );
};
