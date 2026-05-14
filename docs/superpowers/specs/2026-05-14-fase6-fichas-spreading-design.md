# Design: Fase 6 — CRUD de Fichas + Spreading UI

**Data:** 2026-05-14
**Status:** Aprovado
**Scope:** CRUD completo de fichas inline no detalhe do orçamento, cálculo de preço unitário por ficha (pricing engine) e spreading de custos fixos com resultado tabular.

---

## Contexto

Backend FastAPI com todos os endpoints de fichas e spreading já implementados e testados. Frontend React com `OrcamentoDetailPage` exibindo placeholder "Fase 6". Fase 5 entregou CRUD de orçamentos completo. Esta fase integra a camada de fichas e spreading ao frontend.

Stack existente: React 18, React Router 6, React Query 5, Zod, react-hook-form, Axios, react-hot-toast, CSS customizado.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Localização das fichas | Inline em OrcamentoDetailPage | Tudo em um lugar, menos cliques, padrão ERP de obra |
| Form de ficha | Inline expandível | Zero troca de contexto, sem modal nem navegação |
| Tipos de precificação | Markup + BDI Clássico + BDI Manual | Backend suporta os 3; usuário confirmou |
| Calcular | Botão de ação por linha na tabela | Ação direta, sem entrar no form |
| Resultado spreading | Tabela inline com colunas variável/rateado/final | Detalhe por linha, CA-001 badge no topo |
| MFA errors | Toast explicativo (403) | Não bloquear UI; informar e deixar usuário agir |

---

## 1. Arquivos Criados e Modificados

| Ação | Arquivo | Responsabilidade |
|---|---|---|
| Modify | `src/pages/OrcamentoDetailPage.tsx` | Adicionar seção Fichas completa |
| Modify | `src/hooks/useApi.ts` | 6 novos hooks: fichas CRUD + calcular + spreading |
| Create | `src/components/ui/FichaForm.tsx` | Form Zod+RHF inline com campos dinâmicos por tipo |
| Create | `src/components/ui/SpreadingResultTable.tsx` | Tabela resultado spreading + badge CA-001 |

---

## 2. Camada de Dados — Novos Hooks em `useApi.ts`

```typescript
useFichas(orcamentoId: string)           // GET  /orcamentos/:id/fichas
useCreateFicha()                          // POST /orcamentos/:id/fichas
useUpdateFicha()                          // PATCH /orcamentos/:id/fichas/:fid
useDeleteFicha()                          // DELETE /orcamentos/:id/fichas/:fid  [MFA]
useCalcularFicha()                        // POST /orcamentos/:id/fichas/:fid/calcular
useSpreading()                            // POST /orcamentos/:id/spreading       [MFA]
```

**Padrão das mutations:**
- `onSuccess`: invalida `['fichas', orcamentoId]` → refetch automático
- `onError`: toast com `error.response?.data?.detail` ou mensagem genérica
- Erros 403: toast "Autenticação de dois fatores necessária para esta ação."

**Tipos adicionais em `src/types/index.ts`:**

```typescript
export interface FichaCalcResult {
  ficha_id: string;
  preco_unitario: string;
  divisor: string | null;
  is_alert: boolean;
  detalhes: Record<string, string>;
}

export interface SpreadingResultLine {
  ficha_id: string;
  descricao: string;
  variable_unit_price: string;
  quantity: string;
  allocated_fixed: string;
  final_unit_price: string;
  final_line_total: string;
  carries_residue: boolean;
}

export interface SpreadingResponse {
  orcamento_id: string;
  custo_fixo_total: string;
  total_variavel: string;
  total_final: string;
  residuo_aplicado: boolean;
  linhas: SpreadingResultLine[];
  ca001_validado: boolean;
}
```

---

## 3. FichaForm — Schema Zod e Campos Dinâmicos

### Schema base

```typescript
// pct: número entre 0 (inclusive) e 1 (exclusivo), até 4 casas decimais
// Validado como número, convertido para string decimal no payload da API
const pct = z.coerce.number().min(0).lt(1);

const fichaBaseSchema = z.object({
  descricao:          z.string().min(1, 'Obrigatório').max(500),
  unidade:            z.string().max(50).default('un'),
  quantidade:         z.string().regex(/^\d+(\.\d+)?$/, 'Número positivo'),
  custo_unitario:     z.string().regex(/^\d+(\.\d{1,2})?$/, 'Formato: 100.00'),
  tipo_precificacao:  z.enum(['markup', 'bdi_manual', 'bdi_classico']),
  ordem:              z.coerce.number().int().min(0).default(0),
});
```

### Parâmetros condicionais (exibidos abaixo do select de tipo)

**Markup** (`tipo_precificacao === 'markup'`):
```typescript
z.object({ tributes: pct, profit: pct, indirect: pct })
```
3 campos em linha — rótulos: Tributos / Lucro / Indiretas. Placeholder: `ex: 0.12`

**BDI Clássico** (`tipo_precificacao === 'bdi_classico'`):
```typescript
z.object({ administration: pct, financial: pct, risk: pct, profit: pct, tributes: pct })
```
5 campos — Administração / Financeiro / Risco / Lucro / Tributos.

**BDI Manual** (`tipo_precificacao === 'bdi_manual'`):
```typescript
z.array(z.object({
  name:            z.string().min(1),
  percent:         pct,
  base:            z.enum(['revenue', 'cost']),
  legal_reference: z.string().default(''),
})).min(1, 'Adicione ao menos um componente')
```
Lista dinâmica com `useFieldArray`. Botão "+ Adicionar componente" + botão "✕" por linha. Campos por linha: Nome / % / Base (select revenue/cost) / Referência legal (opcional).

### UX do form

- `openFormId: 'new' | string | null` em estado local de `OrcamentoDetailPage`
- Abrir novo form fecha o anterior (só um aberto por vez)
- Botões: `[Cancelar]` (fecha sem salvar) e `[Salvar]` (disabled + spinner durante mutation)
- Criar: form expande após o botão "+ Nova ficha", acima da tabela
- Editar: form expande como linha adicional abaixo da linha editada na tabela

---

## 4. OrcamentoDetailPage — Estrutura da Seção Fichas

```
OrcamentoDetailPage
├── Cabeçalho (título, StatusBadge, Editar, Excluir) — sem mudança
├── Grid de detalhes (custo, datas) — sem mudança
└── Seção "Fichas"
    ├── Cabeçalho: "Fichas" [h2] + botão "+ Nova ficha" [direita]
    ├── [openFormId === 'new'] FichaForm em branco
    ├── Estado loading: spinner centralizado
    ├── Estado vazio: "Nenhuma ficha cadastrada" + link "+ Adicionar primeira ficha"
    ├── Tabela normal (spreadingResult === null)
    │   ├── Colunas: Descrição | Unidade | Qtd | Custo unit. | Preço calc. | Ações
    │   └── Ações por linha: [Calcular] [Editar] [Excluir]
    │       └── [openFormId === ficha.id] FichaForm pré-preenchido expande abaixo
    ├── SpreadingResultTable (spreadingResult !== null)
    │   ├── Badge CA-001: "✓ CA-001 validado" (verde) | "⚠ CA-001 falhou" (amarelo)
    │   ├── Colunas: Descrição | Qtd | Preço var. | Fixo rat. | Preço final
    │   └── Botão "Limpar resultado" → setSpreadingResult(null)
    └── Rodapé
        ├── "Custo fixo total: R$ X.XXX,XX" (informativo, do orçamento)
        └── Botão "Executar Spreading" (disabled se fichas vazias ou loading)
```

**Estado local de OrcamentoDetailPage:**
```typescript
// openFormId: null = nenhum form aberto, 'new' = form de criação, <uuid> = form de edição
const [openFormId, setOpenFormId] = useState<string | null>(null);
const [spreadingResult, setSpreadingResult] = useState<SpreadingResponse | null>(null);
```

**Nota de implementação — editar em tabela HTML:**
O form de edição expande como uma linha adicional `<tr>` com `<td colSpan={6}>` logo abaixo da linha da ficha editada. Isso mantém a estrutura de tabela válida sem quebrar o layout.

---

## 5. Fluxos e Tratamento de Erros

### Fluxo: Criar ficha
1. Clicar "+ Nova ficha" → `setOpenFormId('new')`
2. Preencher form → Salvar → `createFicha.mutateAsync`
3. Sucesso: toast "Ficha criada!" + `setOpenFormId(null)` + invalidação automática
4. Erro: toast com mensagem da API

### Fluxo: Editar ficha
1. Clicar "Editar" na linha → `setOpenFormId(ficha.id)` → form expande pré-preenchido
2. Alterar campos → Salvar → `updateFicha.mutateAsync`
3. Sucesso: toast "Ficha atualizada!" + `setOpenFormId(null)` + invalidação
4. Erro: toast com mensagem da API

### Fluxo: Calcular preço
1. Clicar "Calcular" na linha → `calcularFicha.mutateAsync({ orcamentoId, fichaId })`
2. Sucesso: toast "Preço calculado: R$ X.XXX,XX" + invalidação (atualiza coluna "Preço calc.")
3. Erro 422: toast com detalhe (ex: "Parâmetros de precificação ausentes")

### Fluxo: Excluir ficha
1. Clicar "Excluir" → `ConfirmDialog` "Excluir esta ficha?"
2. Confirmar → `deleteFicha.mutateAsync`
3. Sucesso: toast "Ficha excluída" + invalidação
4. Erro 403: toast "Autenticação de dois fatores necessária para excluir fichas."

### Fluxo: Spreading
1. Clicar "Executar Spreading" → `spreading.mutateAsync({ orcamentoId })`
2. Sucesso: `setSpreadingResult(data)` → tabela muda para SpreadingResultTable
3. Toast "Spreading aplicado! Total: R$ X.XXX,XX"
4. Erro 403: toast "Autenticação de dois fatores necessária para executar spreading."
5. Erro 422: toast com detalhe (ex: "Orçamento não possui fichas para spreading")

---

## 6. CSS Adicional em `index.css`

Classes novas necessárias:
- `.fichas-section` — container da seção com border-top e padding-top
- `.fichas-header` — flex row com título e botão nova ficha
- `.ficha-form-inline` — container do form expandível com border e background
- `.param-grid-3` / `.param-grid-5` — grid de 3/5 colunas para campos de percentual
- `.bdi-manual-row` — linha de componente BDI Manual com botão de remoção
- `.spreading-badge` — badge CA-001 (variantes `ok` e `warn`)
- `.spreading-table` — variante da tabela com coluna final destacada

---

## Critérios de Aceitação

- [ ] Criar ficha funciona (todos os 3 tipos de precificação)
- [ ] Editar ficha funciona (form pré-preenchido)
- [ ] Excluir ficha funciona (ConfirmDialog + toast + erro 403 explicativo)
- [ ] Calcular preço funciona por linha (toast com valor + atualização na tabela)
- [ ] Spreading funciona (tabela substitui lista, CA-001 badge, erro 403 explicativo)
- [ ] BDI Manual — componentes dinâmicos (adicionar/remover linhas)
- [ ] Só um form expandido por vez
- [ ] `npm run build` sem erros TypeScript

---

## Fora de Escopo

- Reordenação de fichas (drag-and-drop para `ordem`)
- Exportação PDF/Excel do resultado do spreading
- Paginação da lista de fichas
- Histórico de cálculos por ficha
- CA-007 (offline/PWA)
