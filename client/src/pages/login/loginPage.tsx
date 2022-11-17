
import { useState } from 'react'
import { makeStyles, Grid, TextField, Typography, Button } from '@material-ui/core'


const useStyles = makeStyles(theme => ({
  root: { flexGrow: 1 },
  container: { 
    margin: theme.spacing(2),
    padding: theme.spacing(10)
  },
  paper: { margin: theme.spacing(10)}
}));


export const LoginPage = () => {

  const classes = useStyles();
  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  
  return (
    <Grid container className={classes.container}>
      <Grid item xs={12}>
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
        />
      </Grid>
      <Grid item xs={12}>
        <TextField
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
      </Grid>
      <Grid item alignItems="center">
        <Button variant="contained" onClick={() => console.log('submitted')}>
          Login
        </Button>
      </Grid>
    </Grid>
  )
}
