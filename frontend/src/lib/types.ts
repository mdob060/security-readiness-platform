export type Role = "admin" | "analyst" | "viewer";

export interface AuthUser {
  username: string;
  role: Role;
  token: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
  username: string;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";
