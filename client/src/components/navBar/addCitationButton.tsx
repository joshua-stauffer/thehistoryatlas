import { Button } from '@mui/material'
import { Link } from 'react-router-dom'


export const AddCitationButton = () => {
  return (
    <Link to="/add-citation">
      <Button color="inherit">Add Citation</Button>
    </Link>
  )
}
