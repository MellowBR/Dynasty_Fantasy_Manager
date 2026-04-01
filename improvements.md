# improvements.md — Fantasy Manager

> Backlog vivo de melhorias, bugs e features pendentes.
> Atualizado em: 31/03/2026
> Convenções: 🔲 pendente | ⚠️ parcial | ✅ concluído

---

## Status Rápido

| ID | Item | Prioridade | Status |
|----|------|------------|--------|
| X1 | Acesso multi-usuário (PythonAnywhere + OAuth + permissões) | Alta | ✅ 31/03/2026 |
| X1a | Preparar app para produção (wsgi.py, .env, ProxyFix, python-dotenv) | Alta | ✅ 31/03/2026 |
| X1b | Google OAuth + Flask-Login | Alta | ✅ 31/03/2026 |
| X1c | Tabela `users` no dynasty.db + seed_users.py | Alta | ✅ 31/03/2026 |
| X1d | Decorators `@login_required` / `@admin_required` nas rotas | Alta | ✅ 31/03/2026 |
| T1 | Simulador de trade compartilhável (link público para o outro owner) | Alta | 🔲 |
| X2 | Trades multi-usuário (propor / aceitar / recusar dentro do Manager) | Média | 🔲 |
| M1 | Validação de cap antes de confirmar trade | Média | 🔲 |
| M2 | Notificação de jogadores com `needs_review=True` pendente | Baixa | 🔲 |
| M3 | Exportar dynasty.db em formato legível para os outros owners | Baixa | 🔲 |
| M4 | Banner de sync desatualizada com timestamp e botão "Sincronizar agora" | Baixa | 🔲 |
| F1 | Correção de salários por partial name match (3 Browns bug) | Alta | ✅ 28/03/2026 |
| F2 | Ordenação do Round 1 via `draft_lottery_result` + `season_standings` | Alta | ✅ 28/03/2026 |
| F3 | Histórico inline (accordion) na aba de histórico | Média | ✅ 28/03/2026 |

---

## Itens Pendentes

---

### T1 — Simulador de Trade Compartilhável
🔲 **Pendente**

**Problema:** Hoje o admin simula o trade localmente, combina fora do Manager (WhatsApp/Sleeper), e registra o resultado manualmente. O outro owner nunca vê o cap impact do lado dele.

**Proposta — Link compartilhável (independente do X2):**
1. Qualquer owner autenticado simula um trade no Manager e vê o cap impact de ambos os lados
2. Clica em "Gerar Proposta" → Manager salva o estado do trade com um ID único e retorna um link `/trades/proposta/<uuid>`
3. Owner manda o link no WhatsApp/grupo da liga
4. O outro owner abre o link, vê o preview completo (rosters antes/depois, cap impact dos dois times)
5. Nenhuma confirmação automática — o trade continua sendo registrado manualmente pelo admin após o combinado

**O que salvar no banco (nova tabela `trade_proposals`):**
```sql
CREATE TABLE trade_proposals (
    id TEXT PRIMARY KEY,          -- UUID
    team_a_id INTEGER,
    team_b_id INTEGER,
    players_a TEXT,               -- JSON: player_ids enviados pelo time A
    players_b TEXT,               -- JSON: player_ids enviados pelo time B
    picks_a TEXT,                 -- JSON: pick_ids enviados pelo time A
    picks_b TEXT,                 -- JSON: pick_ids enviados pelo time B
    created_by INTEGER,           -- user_id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP          -- 7 dias, por exemplo
);
```

**Integração com Sleeper:** API do Sleeper não tem endpoints de escrita públicos — não é possível propor trades via API. Descartado.

**Pré-requisito:** X1 (qualquer owner precisa estar logado para gerar a proposta). O link em si pode ser acessível sem login para visualização, a definir.

---

### X2 — Trades Multi-usuário (Propor / Aceitar / Recusar)
🔲 **Pendente** — *não implementar agora, apenas registrar*

**Contexto:** X1 e T1 são pré-requisitos. Com identidade real (X1) e proposta compartilhável (T1), o passo seguinte seria o receptor aceitar ou recusar dentro do Manager, disparando a confirmação automática no `dynasty.db`.

**Decisão:** Adiar para depois de X1 + T1 estarem estáveis em produção.

---

### M1 — Validação de Cap Antes de Confirmar Trade
🔲 **Pendente**

**Problema:** O sistema calcula o cap impact no preview de trade, mas não bloqueia a confirmação se o resultado ultrapassar $200.

**Proposta:** Adicionar validação server-side na rota `POST /trades/confirm` — retornar erro 400 com mensagem clara se qualquer time ficar acima do cap após o trade.

---

### M2 — Alerta de Jogadores `needs_review=True` Pendentes
🔲 **Pendente**

**Problema:** Jogadores adicionados via Sleeper sync ficam com `needs_review=True` mas não há nenhum alerta visual fora da tela de admin.

**Proposta:** Badge com contador na navbar e/ou banner na tela de roster quando houver jogadores pendentes de revisão.

---

### M3 — Exportar Estado da Liga para Visualização Externa
🔲 **Pendente**

**Problema:** Com X1 os owners passam a ter acesso ao Manager. Mas pode ser útil ter um endpoint `/api/estado` que retorne JSON com rosters, salários e picks — para uso futuro no Optimizer ou para owners que queiram consumir os dados.

**Proposta:** Endpoint GET `/api/estado` retornando JSON read-only. Sem autenticação especial além do `@login_required`. Não expor dados sensíveis (sem `is_admin`, sem emails).

---

### M4 — Banner de Sync Desatualizada
🔲 **Pendente**

**Problema:** Quando o Sleeper sync falha no startup (timeout ou API fora), o usuário não tem indicação visual de que os dados podem estar desatualizados.

**Proposta:** Banner visível em todas as páginas com timestamp da última sync e botão "Sincronizar agora". Só exibir quando a sync está desatualizada.

---

## Itens Concluídos

---

### X1 — Acesso Multi-usuário ✅ 31/03/2026

**Problema:** O Manager rodava apenas localmente. Os outros 11 owners não tinham acesso ao estado real da liga.

**Solução:** Preparação completa para hospedagem no PythonAnywhere com autenticação Google OAuth. Subdividido em X1a-X1d abaixo.

---

### X1a — Preparar App para Produção ✅ 31/03/2026

**Solução:** `wsgi.py` como entry point WSGI. `.env` com `APP_ENV`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`. `load_dotenv()` no topo do `app.py`. `ProxyFix` para reverse proxy. Debug condicional via `APP_ENV`. `requirements.txt` corrigido com todas as dependências (flask-login, authlib, python-dotenv, pandas, openpyxl). Startup sync com try/except para degradação elegante.

---

### X1b — Google OAuth + Flask-Login ✅ 31/03/2026

**Solução:** Blueprint `routes/auth.py` com `/login`, `/login/google`, `/auth/callback`, `/logout`. `LoginManager` com `unauthorized_handler` que retorna 401 JSON para `/api/*` e redirect para `/login` em rotas de página. OAuth via `authlib` com Google OpenID Connect. Template `login.html`. Email não cadastrado renderiza erro 403.

---

### X1c — Tabela `users` + seed_users.py ✅ 31/03/2026

**Solução:** Model `User(UserMixin)` em `models.py` (email, name, team_id FK, is_admin). Migration em `_run_migrations()`. Script `seed_users.py` aceita CSV ou parâmetros CLI (`--email`, `--name`, `--team-id`, `--admin`, `--list`).

---

### X1d — Decorators de Permissão ✅ 31/03/2026

**Solução:** `@login_required` em todas as rotas (exceto login/callback). `@admin_required` em 27 rotas POST/PATCH/DELETE que alteram dados calculados ou são irreversíveis. Exceções: `POST /api/admin/sync` (reflexivo, `@login_required`), `POST /api/trades/preview` e `POST /api/salary/calculate` (simulações, `@login_required`). `POST /api/player/<id>/ir` classificado como `@admin_required` (correção administrativa).

---

### F1 — Correção de Salários por Partial Name Match ✅ 28/03/2026

**Problema:** Partial/substring name matching durante o import original do CSV corrompeu salários de Marquise Brown, A.J. Brown e Amon-Ra St. Brown (todos resolvidos para o mesmo "Brown").

**Solução:** Correção atômica nos três jogadores em `Player`, `SalaryHistory` e `PlayerHistory`. `player_lookup.py` reformulado com hierarquia estrita: exato → case-insensitive → normalizado. Substring e surname isolado bloqueados explicitamente.

---

### F2 — Ordenação do Round 1 via Lottery + Standings ✅ 28/03/2026

**Problema:** Ordem do Round 1 do rookie draft estava incorreta — não respeitava `draft_lottery_result` para picks 1-5 e `season_standings` para picks 6-12.

**Solução:** Lógica corrigida na rota `/picks` para consultar as duas tabelas e montar a ordem correta.

---

### F3 — Histórico Inline (Accordion) na Aba de Histórico ✅ 28/03/2026

**Problema:** Histórico de transações de um jogador só estava disponível via modal na aba de roster, não na aba de histórico (`/salary_history`).

**Solução:** Adicionado accordion expansível por jogador na aba de histórico, consistente com o comportamento do modal no roster.
