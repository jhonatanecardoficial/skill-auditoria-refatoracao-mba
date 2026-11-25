---
name: refactor-arch
description: >-
  Skill agnóstica de tecnologia para análise, auditoria de anti-patterns e
  refatoração automatizada de projetos legados para o padrão MVC com validação de boot e endpoints.
---

# Skill de Auditoria e Refatoração Arquitetural (`refactor-arch`)

Esta skill orienta o agente na análise, auditoria de code smells e refatoração arquitetural de qualquer projeto para o padrão **MVC (Model-View-Controller)**, preservando a integridade funcional da aplicação.

---

## Fluxo de Execução em 3 Fases Sequenciais

A skill deve ser executada obrigatoriamente na seguinte sequência:

```text
[ Fase 1: Análise do Projeto ]
              ↓
[ Fase 2: Auditoria de Anti-patterns ]
              ↓
  (Pausa obrigatória para confirmação do usuário [y/n])
              ↓
[ Fase 3: Refatoração para MVC e Validação ]
```

---

## Fase 1 — Análise do Projeto

1. Ler os arquivos de manifesto (`requirements.txt`, `package.json`, etc.) e código-fonte da aplicação.
2. Consultar o arquivo de referência `references/project-analysis.md`.
3. Identificar:
   - Linguagem de programação e versão;
   - Framework web e bibliotecas principais;
   - Banco de dados e ORM/driver utilizado;
   - Domínio da aplicação e tabelas/entidades principais;
   - Classificação da arquitetura atual (Monolítica desestruturada, Parcialmente organizada, etc.);
   - Contagem exata de arquivos fonte analisados.
4. Imprimir o resumo no formato padrão:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language: <Linguagem>
Framework: <Framework + Versão>
Dependencies: <Dependências principais>
Domain: <Descrição do domínio e entidades>
Architecture: <Arquitetura atual>
Source files: <N> files analyzed
DB tables: <tabelas identificadas>
================================
```

---

## Fase 2 — Auditoria Arquitetural

1. Varrer todo o código-fonte cruzando com o catálogo de anti-patterns em `references/anti-patterns-catalog.md`.
   - **Escopo Integral de Varredura:** A análise NÃO deve se limitar aos arquivos principais ou de rotas; deve inspecionar exaustivamente módulos utilitários, serviços de notificação, helpers, classes de configuração e seeds (`services/`, `utils/`, `helpers/`, `config/`, etc.).
2. Para cada problema detectado, identificar:
   - Identificador único do achado (ex.: `[F1]`, `[F2]`);
   - Nome do anti-pattern;
   - Classificação de severidade (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`);
   - Arquivo e linhas exatas do achado (ex.: `models.py:28-50`);
   - Descrição detalhada do problema no contexto do código;
   - Impacto na segurança, manutenibilidade ou performance;
   - Recomendação de correção acionável para a Fase 3.
3. Verificar a presença de **APIs deprecated** (ex.: `datetime.utcnow()`, métodos legados de ORM) e sugerir o equivalente moderno.
4. Montar o relatório padronizado seguindo `references/report-template.md`:
   - Ordenar os achados rigorosamente de `CRITICAL` até `LOW`;
   - **Consistência Aritmética:** O sumário executivo no topo (`Summary`) DEVE bater exatamente com a contagem de achados no corpo e com o total final (`Total: N findings`). A soma `CRITICAL + HIGH + MEDIUM + LOW` deve ser matematicamente idêntica a `N`;
   - **Cotas Mínimas:** O relatório deve cobrir no mínimo 1 achado `CRITICAL` ou `HIGH`, pelo menos 2 `MEDIUM` e pelo menos 2 `LOW`.
5. **PAUSA OBRIGATÓRIA:** Imprimir a mensagem de encerramento da fase e aguardar a confirmação humana antes de efetuar qualquer alteração em arquivos:

```text
================================
Total: <N> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

*(O agente deve esperar o comando afirmativo `y` ou `sim` para prosseguir para a Fase 3).*

---

## Fase 3 — Refatoração para MVC e Validação

1. Consultar as diretrizes de arquitetura em `references/architecture-guidelines.md` e os padrões de transformação em `references/refactoring-playbook.md`.
2. **Finding Closure Gate (Regra Mandatória de Resolução 1:1):**
   - Todo e qualquer finding apontado e classificado na Fase 2 DEVE ser efetivamente corrigido e sanado na refatoração da Fase 3. NUNCA apenas mover um endpoint vulnerável para um novo arquivo ou pasta sem tratá-lo.
   - **Backdoors e Execução SQL Arbitrária (`CRITICAL`):** Endpoints administrativos que executam queries arbitrárias fornecidas pelo cliente (ex.: `/admin/query`) DEVEM ser **removidos completamente** da aplicação, retornando HTTP 404 Not Found.
   - **Endpoints Administrativos Destrutivos (`CRITICAL`/`HIGH`):** Endpoints perigosos como reset de banco (`/admin/reset-db`) DEVEM ser protegidos por autenticação e autorização estrita de administrador (`@require_admin` ou token Bearer administrativo) E restritos por ambiente (`ENVIRONMENT in ('development', 'testing')`), retornando HTTP 401 para requisições não autenticadas e HTTP 403 para usuários não administradores ou em ambiente de produção.
3. Reestruturar a codebase para o padrão MVC:
   - Extrair configurações e credenciais para módulo próprio (`config/`);
   - Criar Models dedicados por entidade para abstrair o acesso a dados e eliminar SQL Injection;
   - Isolar rotas/views e controllers desacoplados, concentrando regras em serviços;
   - Implementar tratamento de erros centralizado;
   - Configurar o ponto de entrada limpo (`app.py` ou `src/app.js`).
4. **Validação da Aplicação:**
   - Iniciar o servidor da aplicação em ambiente de teste;
   - Validar que a aplicação executa sem erros de inicialização;
   - Realizar requisições a **todos os endpoints da aplicação**, verificando se as respostas e contratos continuam respondendo corretamente;
   - Confirmar que os anti-patterns identificados na Fase 2 foram eliminados.
5. Imprimir o resumo da conclusão:

```text
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
✓ Application boots without errors
✓ All endpoints respond correctly
✓ Zero anti-patterns remaining
================================
```
