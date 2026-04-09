import { API_BASE_URL } from "../config";

export interface SignupRequest {
  username: string;
  password: string;
  email?: string;
  firstName?: string;
  lastName?: string;
}

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
}

export const signup = async (data: SignupRequest): Promise<AuthResponse> => {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (response.status === 409) {
    throw new Error("Username already taken");
  }
  if (!response.ok) {
    throw new Error("Signup failed");
  }
  return response.json();
};

export const login = async (
  username: string,
  password: string,
): Promise<AuthResponse> => {
  const body = new URLSearchParams();
  body.append("username", username);
  body.append("password", password);

  const response = await fetch(`${API_BASE_URL}/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!response.ok) {
    throw new Error("Incorrect username or password");
  }
  const data = await response.json();
  return { accessToken: data.access_token, tokenType: data.token_type };
};

export const toggleFavorite = async (
  summaryId: string,
  favorited: boolean,
  token: string,
): Promise<void> => {
  const method = favorited ? "DELETE" : "POST";
  const response = await fetch(
    `${API_BASE_URL}/events/${summaryId}/favorite`,
    {
      method,
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!response.ok) {
    throw new Error("Failed to update favorite");
  }
};
