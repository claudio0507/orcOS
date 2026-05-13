import { useAuth } from '../../hooks/useAuth';

export function LogoutButton() {
  const { logout } = useAuth();
  
  return (
    <button onClick={logout}>
      Sair
    </button>
  );
}
