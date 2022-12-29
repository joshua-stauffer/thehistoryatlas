import { useState } from "react"

export interface TokenManager {
  token: string | null;
  updateToken: (updatedToken: string) => void;
  isLoggedIn: () => boolean;
  logout: () => void;
}


export const useTokenManager = (): TokenManager => {
  const [token, setToken] = useState<string | null>(() => {
    console.log("hey, i'm resetting")
    return null
  })
  console.log({token})

  const updateToken = (updatedToken: string) => {
    console.log(`setting token to : ${updatedToken}`)
    setToken(updatedToken)
  }

  const isLoggedIn = (): boolean => !!token;

  const logout = () => setToken(null);

  return { token, updateToken, isLoggedIn, logout }
}
