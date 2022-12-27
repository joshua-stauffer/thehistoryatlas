
import { useState } from 'react'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import { theme } from '../../baseStyle'



export const LoginPage = () => {

  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  
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
            <Button variant="contained" onClick={() => console.log('submitted')} color='secondary'>
              Login
            </Button>
          </Grid>
        </Grid>
      <Grid></Grid>
    </Grid>
  )
}
