import { Button } from '@mui/material'
import { useHistory } from 'react-router-dom'
import { useToken } from '../../hooks/token'

export const LoginButton = () => {
  const { isLoggedIn, logout } = useToken()
  const history = useHistory()

  if (isLoggedIn()) {
    return <Button color="inherit" onClick={logout}>Logout</Button>
  }
  return (
    <Button color="inherit" onClick={() => history.push("/login")}>Login</Button>
  )
}
