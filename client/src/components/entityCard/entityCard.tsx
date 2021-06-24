import { Container, Title, Body } from "./style"
import { prettifyDate } from '../../pureFunctions/prettifyDate';
import { HistoryEntity } from "../../types";

interface EntityCardProps {
  name: string;
  startDate: string;
  endDate: string;
  summaryCount: number;
  onClick: (entity: HistoryEntity) => void;
}

export const EntityCard = (props: EntityCardProps) => {
  const { name, startDate, endDate, summaryCount } = props
  const start = prettifyDate({dateString: startDate})
  const end = prettifyDate({dateString: endDate})
  return (
    <Container>
      <Title>{name}</Title>
      <Body>{summaryCount} events from {start} to {end}.</Body>
    </Container>
  )
}