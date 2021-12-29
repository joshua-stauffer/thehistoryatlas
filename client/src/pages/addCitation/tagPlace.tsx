import { Tag } from './tagEntities'

interface TagPlaceProps {
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
}


export const TagPlace = (props: TagPlaceProps) => {
  return (
    <h1>Tagging Place</h1>
  )
}