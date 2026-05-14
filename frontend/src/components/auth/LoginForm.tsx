// src/components/auth/LoginForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../hooks/useAuth';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  senha: z.string().min(6, 'Mínimo 6 caracteres'),
});

type LoginData = z.infer<typeof loginSchema>;

interface LoginFormProps {
  onMfaRequired?: (partialToken: string) => void;
}

export function LoginForm({ onMfaRequired }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginData) => {
    try {
      await login(data, onMfaRequired);
    } catch {
      setError('root', { message: 'Email ou senha incorretos.' });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input
        label="Email"
        type="email"
        placeholder="seu@email.com"
        error={errors.email?.message}
        disabled={isLoading}
        {...register('email')}
      />
      <Input
        label="Senha"
        type="password"
        placeholder="••••••••"
        error={errors.senha?.message}
        disabled={isLoading}
        {...register('senha')}
      />
      {errors.root && (
        <p className="error-message" style={{ marginBottom: '0.75rem' }}>
          {errors.root.message}
        </p>
      )}
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? <span className="spinner" /> : 'Entrar'}
      </Button>
    </form>
  );
}
