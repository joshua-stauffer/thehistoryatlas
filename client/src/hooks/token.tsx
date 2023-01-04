import { useState } from "react";

export interface TokenManager {
  token: string | null;
  updateToken: (updatedToken: string) => void;
  isLoggedIn: () => boolean;
  logout: () => void;
}

export const useTokenManager = (): TokenManager => {
  const [token, setToken] = useState<string | null>(null);

  const updateToken = (updatedToken: string) => setToken(updatedToken);

  const isLoggedIn = (): boolean => !!token;

  const logout = () => setToken(null);

  return { token, updateToken, isLoggedIn, logout };
};
