
import { useEffect, useState } from 'react'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import { theme } from '../../baseStyle'
import { useMutation } from '@apollo/client'
import { LOGIN, LoginResult, LoginVars } from '../../graphql/login'
import { TokenManager } from '../../hooks/token'
import { useHistory } from 'react-router-dom'


interface LoginPageProps {
  tokenManager: TokenManager
}


export const LoginPage = (props: LoginPageProps) => {

  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')

  const { tokenManager: { updateToken } } = props
  const history = useHistory()

  const [
    login,
    { data, loading, error }
   ] = useMutation<LoginResult, LoginVars>(LOGIN)

  useEffect(() => {
    if (!!data) {
      // login mutation has returned
      updateToken(data.Login.token)
      history.push("/")
    }
  }, [data])
  
  return (
    <Grid>
      <Grid sx={{display: 'flex', alignItems: 'center', flexDirection: 'column'}}></Grid>
        <Grid container sx={{
          margin: 80, padding: 10, width: 350, border: 2, borderColor: theme.palette.primary.main, justifyContent: 'center', rowGap: 3
        }}>
          <Grid item xs={12} sx={{display: 'flex', justifyContent: 'center'}}>
            <Typography>
              The History Atlas
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <TextField
              id="username"
              label="Username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              sx={{color: 'primary', padding: .2}}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              sx={{color: 'primary', padding: .1}}
            />
          </Grid>
          <Grid item>
            <Button variant="contained" onClick={() => login({ variables: { password: password, username: username }})} color='secondary'>
              Login
            </Button>
          </Grid>
        </Grid>
      <Grid></Grid>
    </Grid>
  )
}
