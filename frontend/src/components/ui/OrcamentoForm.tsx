// src/components/ui/OrcamentoForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './Button';
import { Input } from './Input';

const orcamentoSchema = z.object({
  titulo: z.string().min(3, 'Mínimo 3 caracteres').max(100, 'Máximo 100 caracteres'),
  descricao: z.string().max(500, 'Máximo 500 caracteres').optional(),
  custo_fixo_total: z
    .string()
    .regex(/^\d+(\.\d{2})?$/, 'Formato inválido. Use: 100.00'),
});

export type OrcamentoFormData = z.infer<typeof orcamentoSchema>;

interface OrcamentoFormProps {
  defaultValues?: Partial<OrcamentoFormData>;
  onSubmit: (data: OrcamentoFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  submitLabel?: string;
}

export function OrcamentoForm({
  defaultValues,
  onSubmit,
  onCancel,
  isLoading = false,
  submitLabel = 'Salvar',
}: OrcamentoFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrcamentoFormData>({
    resolver: zodResolver(orcamentoSchema),
    defaultValues,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input
        label="Título *"
        placeholder="Ex: Sinalização Rodovia BR-101 Trecho KM 23-45"
        error={errors.titulo?.message}
        {...register('titulo')}
      />

      <div className="input-group">
        <label className="input-label">Descrição</label>
        <textarea
          className={`textarea-field w-full${errors.descricao ? ' input-error' : ''}`}
          placeholder="Descrição opcional do orçamento..."
          {...register('descricao')}
        />
        {errors.descricao && (
          <span className="error-message">{errors.descricao.message}</span>
        )}
      </div>

      <Input
        label="Custo Fixo Total *"
        placeholder="Ex: 1500.00"
        error={errors.custo_fixo_total?.message}
        {...register('custo_fixo_total')}
      />

      <div className="form-actions">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? <span className="spinner" /> : submitLabel}
        </Button>
      </div>
    </form>
  );
}
