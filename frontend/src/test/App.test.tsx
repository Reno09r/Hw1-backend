import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'
import { useAuth } from '../contexts/AuthContext'

// Создаем мок-функции для методов контекста
const mockLogin = vi.fn()
const mockRegister = vi.fn()
const mockLogout = vi.fn()
const mockUpdateProfile = vi.fn()
const mockDeleteAccount = vi.fn()

// Мокаем контекст аутентификации
vi.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: vi.fn()
}))

// Мокаем компонент AuthPage
vi.mock('../components/auth/AuthPage', () => ({
  AuthPage: () => <div data-testid="auth-page">Auth Page</div>
}))

describe('App', () => {
  it('renders auth page when user is not logged in', () => {
    // Мокаем состояние неавторизованного пользователя
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: mockLogin,
      register: mockRegister,
      logout: mockLogout,
      updateProfile: mockUpdateProfile,
      deleteAccount: mockDeleteAccount
    })
    
    render(<App />)
    // Проверяем, что отображается страница аутентификации
    expect(screen.getByTestId('auth-page')).toBeInTheDocument()
  })

  it('renders loading state', () => {
    // Мокаем состояние загрузки
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
      login: mockLogin,
      register: mockRegister,
      logout: mockLogout,
      updateProfile: mockUpdateProfile,
      deleteAccount: mockDeleteAccount
    })
    
    render(<App />)
    // Проверяем, что отображается состояние загрузки
    expect(screen.getByText('TaskFlow')).toBeInTheDocument()
  })
}) 