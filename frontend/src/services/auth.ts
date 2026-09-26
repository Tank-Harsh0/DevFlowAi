import { apiClient } from './api'

export interface AuthTokenResponse {
  access_token: string
  token_type: string
}

export interface UserProfile {
  id: number
  email: string
  username: string
  is_active: boolean
}

export const authService = {
  register: (email: string, username: string, password: string): Promise<AuthTokenResponse> =>
    apiClient
      .post<AuthTokenResponse>('/api/v1/auth/register', { email, username, password })
      .then((r) => r.data),

  login: (email: string, password: string): Promise<AuthTokenResponse> =>
    apiClient
      .post<AuthTokenResponse>('/api/v1/auth/login', { email, password })
      .then((r) => r.data),

  me: (): Promise<UserProfile> =>
    apiClient.get<UserProfile>('/api/v1/auth/me').then((r) => r.data),
}
