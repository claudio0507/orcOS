import { LogOut } from 'lucide-react';
import { Button } from '../ui/Button';

interface LogoutButtonProps {
  onLogout: () => void;
}

export function LogoutButton({ onLogout }: LogoutButtonProps) {
  return (
    <Button variant="ghost" onClick={onLogout} className="flex items-center gap-2">
      <LogOut size={18} />
      <span>Sair</span>
    </Button>
  );
}
