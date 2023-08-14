import { useQuery } from "@apollo/client";
import { Typography } from "@material-ui/core";
import { Tag } from "./tagEntities";
import { SingleEntityMap } from "../../components/singleEntityMap";
import {
  GET_ENTITY_SUMMARIES_BY_GUID,
  GetEntitySummariesByGUIDVars,
  GetEntitySummariesByGUIDResult,
} from "../../graphql/getEntitySummariesByGUID";

interface ViewEntityProps {
  tag: Tag;
}

export const ViewEntity = (props: ViewEntityProps) => {
  const { tag } = props;
  const { data, loading, error } = useQuery<
    GetEntitySummariesByGUIDResult,
    GetEntitySummariesByGUIDVars
  >(GET_ENTITY_SUMMARIES_BY_GUID, { variables: { guids: [tag.guid ?? ""] } });

  // the query only returns something useful if there's a guid
  if (!tag.guid || !data?.GetEntitySummariesByGUID.length)
    return (
      <>
        <Typography variant="h3">{tag.name}</Typography>
        <Typography variant="body1">
          This {tag.type.toLowerCase()} doesn't exist yet in our database.
        </Typography>
        <Typography variant="body1">
          You'll be the first to tag {tag.type === "PERSON" ? "them" : "it"}!
        </Typography>
      </>
    );

  let map;
  if (tag.type === "PLACE") {
    map = (
      <>
        <Typography variant="h3">{tag.name}</Typography>
        <SingleEntityMap
          latitude={tag.latitude ?? 0}
          longitude={tag.longitude ?? 0}
          title={tag.name ?? ""}
          mapTyle={"natGeoWorld"}
          size={"SM"}
          zoom={6}
        />
      </>
    );
  } else {
    map = null;
  }
  const entity = data.GetEntitySummariesByGUID.find(
    (ent) => ent.guid === tag.guid
  );
  if (!entity) return <h1>Error!</h1>;
  return (
    <>
      {map ?? (
        <Typography variant="h3">
          {tag.name} - ({tag.type.toLowerCase()})
        </Typography>
      )}
      <Typography variant="body1">Name(s): {entity.names}</Typography>
      <Typography variant="body1">
        Earliest citation: {entity.first_citation_date}
      </Typography>
      <Typography variant="body1">
        Latest citation: {entity.last_citation_date}
      </Typography>
      <Typography variant="body1">
        {" "}
        Citation count: {entity.citation_count}
      </Typography>
    </>
  );
};
