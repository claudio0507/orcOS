import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  senha: z.string().min(6, 'A senha deve ter pelo menos 6 caracteres'),
  tenant_id: z.string().uuid('ID do Tenant inválido'),
});

type LoginData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginData) => {
    console.log('Login:', data);
    // TODO: integrar com API
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <input 
          {...register('tenant_id')} 
          placeholder="ID do Tenant (UUID)" 
          className="border p-2 w-full"
        />
        {errors.tenant_id && <span className="text-red-500 text-sm">{errors.tenant_id.message}</span>}
      </div>

      <div>
        <input 
          {...register('email')} 
          placeholder="Email" 
          className="border p-2 w-full"
        />
        {errors.email && <span className="text-red-500 text-sm">{errors.email.message}</span>}
      </div>
      
      <div>
        <input 
          {...register('senha')} 
          type="password" 
          placeholder="Senha" 
          className="border p-2 w-full"
        />
        {errors.senha && <span className="text-red-500 text-sm">{errors.senha.message}</span>}
      </div>
      
      <button 
        type="submit" 
        className="bg-blue-500 text-white p-2 rounded w-full hover:bg-blue-600"
      >
        Entrar
      </button>
    </form>
  );
}
