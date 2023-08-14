import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";
import { Alert, AlertTitle, Stack } from "@mui/material";
import { useMutation } from "@apollo/client";
import { LOGIN, LoginResult, LoginVars } from "../../graphql/login";
import { LoadingButton } from "@mui/lab";
import { useEffect, useState } from "react";

interface LoginDialogProps {
  open: boolean;
  handleClose: () => void;
  updateToken: (token: string) => void;
}

export default function LoginDialog(props: LoginDialogProps) {
  const [requestError, setRequestError] = useState<string | null>(null);

  const [login, { data, loading, error }] = useMutation<LoginResult, LoginVars>(
    LOGIN,
    { onError: (error) => setRequestError(error.message) }
  );
  if (error) {
    setRequestError(error.message);
  }
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  useEffect(() => {
    if (data?.Login.success) {
      props.updateToken(data.Login.token);
    }
  });

  return (
    <Dialog open={props.open} onClose={props.handleClose}>
      <DialogTitle>Login</DialogTitle>
      <DialogContent>
        <Stack>
          <TextField
            autoFocus
            margin="dense"
            id="username"
            label="Username"
            type="text"
            variant="standard"
            onChange={(e) => setUsername(e.target.value)}
            value={username}
          />
          <TextField
            autoFocus
            margin="dense"
            id="password"
            label="Password"
            type="password"
            variant="standard"
            onChange={(e) => setPassword(e.target.value)}
            value={password}
          />
        </Stack>

        <DialogContentText>
          Add some text here about how you can eventually sign up, probably, but
          right now you can't.
        </DialogContentText>
        {error && (
          <Alert severity={"error"}>
            <AlertTitle>Login Failed</AlertTitle>
            {requestError}
          </Alert>
        )}
        {data?.Login.success === false && (
          <Alert severity={"warning"}>
            <AlertTitle>Incorrect Credentials</AlertTitle>
            Please check your username and password and try again.
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <LoadingButton
          loading={loading}
          variant={"outlined"}
          onClick={() => login({ variables: { username, password } })}
        >
          Login
        </LoadingButton>

        <Button variant={"outlined"} onClick={props.handleClose}>
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
}
