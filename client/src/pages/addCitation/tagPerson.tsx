import { Tag } from './tagEntities'

interface TagPersonProps {
  setCurrentEntity: React.Dispatch<React.SetStateAction<Tag | null>>
}


export const TagPerson = (props: TagPersonProps) => {
    return (
      <h1>Tagging Person</h1>
    )
  }