# Instruções para o Claude - Projeto orcOS

## 🎯 Visão Geral

**orcOS** é um sistema de orçamentação para engenharia de infraestrutura e sinalização viária.

- **Frontend:** React + Vite (Vercel)
- **Backend:** FastAPI + SQLAlchemy (Render.com)
- **Banco:** PostgreSQL (Render.com)

## 🔗 URLs Importantes

| Ambiente | URL |
|----------|-----|
| Frontend Produção | https://orc-os.vercel.app |
| Backend Produção | https://orcos-backend-qg79.onrender.com |
| Health Check | https://orcos-backend-qg79.onrender.com/health |
| API Docs | https://orcos-backend-qg79.onrender.com/docs |

## 🔐 Credenciais Demo

```
Email: admin@demo.com
Senha: demo123
Tenant ID: 395b1485-e979-411b-941d-9c152b4de585
```

## 📁 Estrutura do Projeto

```
orcOS/
├── frontend/              # React + Vite
│   ├── src/
│   │   ├── hooks/        # useAuth.ts, useApi.ts
│   │   ├── pages/        # LoginPage, OrcamentosListPage, etc
│   │   └── components/   # UI components
│   └── .env.production   # VITE_API_URL
├── backend/               # FastAPI
│   ├── app/
│   │   ├── api/v1/       # Routes (auth, orcamentos, fichas)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── db/           # Session, engine
│   └── requirements.txt
└── render.yaml           # Configuração Render.com
```

## 🚀 Deploy

### Backend (Render.com)

1. **Web Service:**
   - Runtime: Python 3
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables:**
   ```
   DATABASE_URL=postgresql://... (do PostgreSQL)
   SECRET_KEY=<gerar aleatório>
   APP_ENV=production
   CORS_ORIGINS=["https://orc-os.vercel.app"]
   ```

3. **PostgreSQL:**
   - Plan: Free
   - Mesma região do Web Service

### Frontend (Vercel)

1. **Framework:** Vite
2. **Root Directory:** `frontend`
3. **Environment:**
   ```
   VITE_API_URL=https://orcos-backend-XXX.onrender.com/api/v1
   ```

## ⚠️ Problemas Conhecidos

### 1. RLS (Row Level Security)
- **Status:** Desativado temporariamente
- **Motivo:** Requer configuração customizada no PostgreSQL (`app.tenant_id`)
- **Arquivos afetados:** `app/api/deps.py`, `app/auth/dependencies.py`
- **TODO:** Reativar quando configurar RLS no banco

### 2. Seed Automático
- Funciona no startup do backend
- Cria tenant demo + usuário admin@demo.com
- Local: `app/main.py` → `run_seed()`

### 3. Cache no Render
- Se código não atualizar, usar "Clear build cache & deploy"
- Ou fazer commit vazio: `git commit --allow-empty -m "trigger: rebuild"`

## 🛠 Comandos Úteis

```bash
# Testar API
curl -X POST https://orcos-backend-XXX.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 395b1485-e979-411b-941d-9c152b4de585" \
  -d '{"email":"admin@demo.com","password":"demo123","tenant_id":"395b1485-e979-411b-941d-9c152b4de585"}'

# Health check
curl https://orcos-backend-XXX.onrender.com/health
```

## 📝 TODOs Pendentes

- [ ] Reativar RLS no PostgreSQL
- [ ] Implementar refresh token automático no frontend
- [ ] Adicionar testes E2E
- [ ] Configurar CI/CD completo
- [ ] Documentar API com exemplos

## 🆘 Troubleshooting

| Problema | Solução |
|----------|---------|
| "Email ou senha incorretos" | Verificar se seed rodou, verificar logs |
| "Internal Server Error" | Verificar logs no Render, possível erro de RLS |
| Deploy não atualiza | Clear build cache & deploy |
| Banco não conecta | Verificar DATABASE_URL, região do serviço |

## 📞 Contato

- Repositório: https://github.com/claudio0507/orcOS
- Branch ativa: `claude/project-analysis-improvements-rqi2e`
