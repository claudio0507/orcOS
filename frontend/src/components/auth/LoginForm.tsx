import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../../hooks/useAuth';

const loginSchema = z.object({
  email: z.string().email(),
  senha: z.string().min(6),
});

type LoginData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login, isLoading } = useAuth();
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginData) => {
    try {
      await login(data);
    } catch (e) {
      alert('Erro ao entrar. Verifique suas credenciais.');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} placeholder="Email" disabled={isLoading} />
      {errors.email && <span>{errors.email.message}</span>}
      
      <input {...register('senha')} type="password" placeholder="Senha" disabled={isLoading} />
      {errors.senha && <span>{errors.senha.message}</span>}
      
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  );
}
