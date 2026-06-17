// src/components/ui/FichaForm.tsx
import { useFieldArray, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from './Button';
import { Input } from './Input';
import { useCreateFicha, useUpdateFicha } from '../../hooks/useApi';
import type { FichaPayload } from '../../hooks/useApi';

const pct = z.coerce
  .number({ invalid_type_error: 'Número obrigatório' })
  .min(0, 'Mínimo 0')
  .lt(1, 'Máximo 0.9999 (ex: 0.12 = 12%)');

const fichaSchema = z
  .object({
    descricao:          z.string().min(1, 'Obrigatório').max(500, 'Máximo 500 caracteres'),
    unidade:            z.string().max(50).default('un'),
    quantidade:         z.string().regex(/^\d+(\.\d+)?$/, 'Número positivo (ex: 25.00)'),
    custo_unitario:     z.string().regex(/^\d+(\.\d{1,2})?$/, 'Formato: 100.00'),
    tipo_precificacao:  z.enum(['markup', 'bdi_manual', 'bdi_classico']),
    ordem:              z.coerce.number().int().min(0).default(0),
    markup_tributes:    pct.optional(),
    markup_profit:      pct.optional(),
    markup_indirect:    pct.optional(),
    bdi_administration: pct.optional(),
    bdi_financial:      pct.optional(),
    bdi_risk:           pct.optional(),
    bdi_profit:         pct.optional(),
    bdi_tributes:       pct.optional(),
    bdi_components: z
      .array(
        z.object({
          name:            z.string().min(1, 'Nome obrigatório'),
          percent:         pct,
          base:            z.enum(['revenue', 'cost']),
          legal_reference: z.string().default(''),
        }),
      )
      .optional(),
  })
  .superRefine((data, ctx) => {
    if (data.tipo_precificacao === 'markup') {
      if (data.markup_tributes === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_tributes'] });
      if (data.markup_profit === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_profit'] });
      if (data.markup_indirect === undefined)
        ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: ['markup_indirect'] });
    }
    if (data.tipo_precificacao === 'bdi_classico') {
      const fields = [
        'bdi_administration', 'bdi_financial', 'bdi_risk', 'bdi_profit', 'bdi_tributes',
      ] as const;
      for (const field of fields) {
        if (data[field] === undefined)
          ctx.addIssue({ code: 'custom', message: 'Obrigatório', path: [field] });
      }
    }
    if (data.tipo_precificacao === 'bdi_manual') {
      if (!data.bdi_components?.length)
        ctx.addIssue({
          code: 'custom',
          message: 'Adicione ao menos um componente',
          path: ['bdi_components'],
        });
    }
  });

type FichaFormData = z.infer<typeof fichaSchema>;

function buildPayload(data: FichaFormData): FichaPayload {
  let parametros_precificacao: Record<string, unknown> | null = null;

  if (data.tipo_precificacao === 'markup') {
    parametros_precificacao = {
      tributes: String(data.markup_tributes),
      profit:   String(data.markup_profit),
      indirect: String(data.markup_indirect),
    };
  } else if (data.tipo_precificacao === 'bdi_classico') {
    parametros_precificacao = {
      administration: String(data.bdi_administration),
      financial:      String(data.bdi_financial),
      risk:           String(data.bdi_risk),
      profit:         String(data.bdi_profit),
      tributes:       String(data.bdi_tributes),
    };
  } else if (data.tipo_precificacao === 'bdi_manual') {
    parametros_precificacao = {
      components: (data.bdi_components ?? []).map((c) => ({
        name:            c.name,
        percent:         String(c.percent),
        base:            c.base,
        legal_reference: c.legal_reference,
      })),
    };
  }

  return {
    descricao:               data.descricao,
    unidade:                 data.unidade,
    quantidade:              data.quantidade,
    custo_unitario:          data.custo_unitario,
    tipo_precificacao:       data.tipo_precificacao,
    ordem:                   data.ordem,
    parametros_precificacao,
  };
}

interface FichaFormProps {
  orcamentoId: string;
  fichaId?: string;
  defaultValues?: Partial<
    Pick<FichaFormData, 'descricao' | 'unidade' | 'quantidade' | 'custo_unitario' | 'tipo_precificacao' | 'ordem'>
  >;
  onSuccess: () => void;
  onCancel: () => void;
}

export function FichaForm({
  orcamentoId,
  fichaId,
  defaultValues,
  onSuccess,
  onCancel,
}: FichaFormProps) {
  const createFicha = useCreateFicha();
  const updateFicha = useUpdateFicha();
  const isEditing = !!fichaId;
  const isLoading = createFicha.isPending || updateFicha.isPending;

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<FichaFormData>({
    resolver: zodResolver(fichaSchema),
    defaultValues: {
      tipo_precificacao: 'markup',
      unidade: 'un',
      ordem: 0,
      ...defaultValues,
    },
  });

  const tipo = watch('tipo_precificacao');
  const { fields, append, remove } = useFieldArray({ control, name: 'bdi_components' });

  const onSubmit = async (data: FichaFormData) => {
    const payload = buildPayload(data);
    try {
      if (isEditing) {
        await updateFicha.mutateAsync({ orcamentoId, fichaId: fichaId!, payload });
      } else {
        await createFicha.mutateAsync({ orcamentoId, payload });
      }
      onSuccess();
    } catch {
      // error toast shown by mutation onError
    }
  };

  return (
    <div className="ficha-form-inline">
      <p style={{ fontWeight: 600, marginBottom: '1rem', color: 'var(--foreground)' }}>
        {isEditing ? 'Editar ficha' : 'Nova ficha'}
      </p>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Input
          label="Descrição *"
          placeholder="Ex: Placa de sinalização R-1 (PARE) — 0,50×0,50m"
          error={errors.descricao?.message}
          {...register('descricao')}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
          <Input
            label="Unidade"
            placeholder="un"
            error={errors.unidade?.message}
            {...register('unidade')}
          />
          <Input
            label="Quantidade *"
            placeholder="ex: 25.00"
            error={errors.quantidade?.message}
            {...register('quantidade')}
          />
          <Input
            label="Custo unitário (R$) *"
            placeholder="ex: 450.00"
            error={errors.custo_unitario?.message}
            {...register('custo_unitario')}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.75rem' }}>
          <div className="input-group">
            <label className="input-label">Tipo de precificação *</label>
            <select
              className="textarea-field"
              style={{ height: '2.5rem', padding: '0 0.75rem' }}
              {...register('tipo_precificacao')}
            >
              <option value="markup">Markup</option>
              <option value="bdi_classico">BDI Clássico (DNIT)</option>
              <option value="bdi_manual">BDI Manual</option>
            </select>
          </div>
          <Input
            label="Ordem"
            type="number"
            placeholder="0"
            error={errors.ordem?.message}
            {...register('ordem')}
          />
        </div>

        {tipo === 'markup' && (
          <div className="param-grid-3">
            <Input
              label="Tributos (ex: 0.12)"
              placeholder="0.12"
              error={errors.markup_tributes?.message}
              {...register('markup_tributes')}
            />
            <Input
              label="Lucro (ex: 0.10)"
              placeholder="0.10"
              error={errors.markup_profit?.message}
              {...register('markup_profit')}
            />
            <Input
              label="Indiretas (ex: 0.05)"
              placeholder="0.05"
              error={errors.markup_indirect?.message}
              {...register('markup_indirect')}
            />
          </div>
        )}

        {tipo === 'bdi_classico' && (
          <div className="param-grid-5">
            <Input
              label="Administração"
              placeholder="0.04"
              error={errors.bdi_administration?.message}
              {...register('bdi_administration')}
            />
            <Input
              label="Financeiro"
              placeholder="0.012"
              error={errors.bdi_financial?.message}
              {...register('bdi_financial')}
            />
            <Input
              label="Risco"
              placeholder="0.01"
              error={errors.bdi_risk?.message}
              {...register('bdi_risk')}
            />
            <Input
              label="Lucro"
              placeholder="0.08"
              error={errors.bdi_profit?.message}
              {...register('bdi_profit')}
            />
            <Input
              label="Tributos"
              placeholder="0.1365"
              error={errors.bdi_tributes?.message}
              {...register('bdi_tributes')}
            />
          </div>
        )}

        {tipo === 'bdi_manual' && (
          <div style={{ marginTop: '0.5rem' }}>
            <p className="input-label" style={{ marginBottom: '0.5rem' }}>
              Componentes BDI
            </p>
            {fields.map((field, index) => (
              <div key={field.id} className="bdi-manual-row">
                <Input
                  label="Nome"
                  placeholder="ISS"
                  error={errors.bdi_components?.[index]?.name?.message}
                  {...register(`bdi_components.${index}.name`)}
                />
                <Input
                  label="%"
                  placeholder="0.05"
                  error={errors.bdi_components?.[index]?.percent?.message}
                  {...register(`bdi_components.${index}.percent`)}
                />
                <div className="input-group">
                  <label className="input-label">Base</label>
                  <select
                    className="textarea-field"
                    style={{ height: '2.5rem', padding: '0 0.75rem' }}
                    {...register(`bdi_components.${index}.base`)}
                  >
                    <option value="revenue">Receita</option>
                    <option value="cost">Custo</option>
                  </select>
                </div>
                <Input
                  label="Ref. legal (opcional)"
                  placeholder="Art. 65"
                  {...register(`bdi_components.${index}.legal_reference`)}
                />
                <button
                  type="button"
                  onClick={() => remove(index)}
                  style={{
                    alignSelf: 'flex-end',
                    marginBottom: '0.25rem',
                    background: 'none',
                    border: 'none',
                    color: 'var(--muted)',
                    cursor: 'pointer',
                    fontSize: '1.25rem',
                    lineHeight: 1,
                  }}
                  aria-label="Remover componente"
                >
                  ✕
                </button>
              </div>
            ))}
            {typeof errors.bdi_components?.message === 'string' && (
              <p className="error-message">{errors.bdi_components.message}</p>
            )}
            <button
              type="button"
              onClick={() => append({ name: '', percent: 0, base: 'revenue', legal_reference: '' })}
              style={{
                fontSize: '0.875rem',
                color: 'var(--primary)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '0.25rem 0',
                marginBottom: '0.75rem',
              }}
            >
              + Adicionar componente
            </button>
          </div>
        )}

        <div className="form-actions">
          <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancelar
          </Button>
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <span className="spinner" />
            ) : isEditing ? (
              'Salvar alterações'
            ) : (
              'Criar ficha'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
