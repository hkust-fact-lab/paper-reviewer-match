export type Role = 'admin' | 'reviewer'

export interface CurrentUser {
  id: string
  name: string
  email: string
  role: Role
}

let _user: CurrentUser | null = null

export async function getUser(): Promise<CurrentUser | null> {
  if (_user) return _user
  try {
    const res = await fetch('/api/auth/me')
    if (!res.ok) return null
    _user = await res.json() as CurrentUser
    return _user
  } catch {
    return null
  }
}

export function clearUser() {
  _user = null
}
