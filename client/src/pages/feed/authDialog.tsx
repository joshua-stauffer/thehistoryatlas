import React, { useState } from "react";
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  TextField,
  Box,
  Typography,
  Alert,
  Tabs,
  Tab,
} from "@mui/material";
import { login, signup } from "../../api/auth";
import { useAuth } from "../../auth/authContext";

interface AuthDialogProps {
  open: boolean;
  onClose: () => void;
}

export const AuthDialog: React.FC<AuthDialogProps> = ({ open, onClose }) => {
  const [tab, setTab] = useState(0);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { setAuth } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (tab === 0) {
        const result = await login(username, password);
        setAuth(result.accessToken, username);
      } else {
        const result = await signup({ username, password, email: email || undefined });
        setAuth(result.accessToken, username);
      }
      onClose();
      setUsername("");
      setPassword("");
      setEmail("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ pb: 0 }}>
        <Tabs value={tab} onChange={(_, v) => { setTab(v); setError(null); }}>
          <Tab label="Log in" />
          <Tab label="Sign up" />
        </Tabs>
      </DialogTitle>
      <DialogContent>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            fullWidth
            required
            margin="normal"
            size="small"
            autoFocus
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
            margin="normal"
            size="small"
          />
          {tab === 1 && (
            <TextField
              label="Email (optional)"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fullWidth
              margin="normal"
              size="small"
            />
          )}
          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading || !username || !password}
            sx={{ mt: 2, mb: 1 }}
          >
            {loading ? "..." : tab === 0 ? "Log in" : "Sign up"}
          </Button>
          <Typography
            variant="body2"
            sx={{ textAlign: "center", cursor: "pointer", color: "text.secondary" }}
            onClick={() => { setTab(tab === 0 ? 1 : 0); setError(null); }}
          >
            {tab === 0
              ? "Don't have an account? Sign up"
              : "Already have an account? Log in"}
          </Typography>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
