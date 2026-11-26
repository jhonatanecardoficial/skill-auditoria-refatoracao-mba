# Heurísticas de Análise de Projeto e Mapeamento de Arquitetura

Este documento define as heurísticas padronizadas para a **Fase 1 (Análise do Projeto)** da skill `refactor-arch`.

---

## 1. Detecção de Linguagem e Framework

A detecção é realizada pela presença e análise de arquivos manifestos, dependências e assinaturas de código:

### Python
- **Manifestos:** `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py`, `environment.yml`.
- **Frameworks:**
  - **Flask:** Presença de `flask`, `from flask import Flask`, criação de instância `app = Flask(...)`, Blueprints (`Blueprint(...)`).
  - **FastAPI:** Presença de `fastapi`, `from fastapi import FastAPI`.
  - **Django:** Presença de `manage.py`, `django`, `settings.py`.
- **Banco de Dados / ORM:**
  - **SQLite:** `import sqlite3`, `sqlite3.connect(...)`, arquivos `.db` ou `.sqlite`.
  - **SQLAlchemy:** `flask_sqlalchemy`, `from flask_sqlalchemy import SQLAlchemy`, `SQLAlchemy()`, `db.Model`.
  - **PostgreSQL / MySQL:** `psycopg2`, `psycopg`, `pymysql`, `asyncpg`.

### Node.js / JavaScript / TypeScript
- **Manifestos:** `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`.
- **Frameworks:**
  - **Express:** Dependência `"express"` no `package.json`, `require('express')` ou `import express from 'express'`, `express()`.
  - **Fastify / NestJS:** Dependências `"fastify"`, `"@nestjs/core"`.
- **Banco de Dados / ORM:**
  - **SQLite:** Dependência `"sqlite3"`, `new sqlite3.Database(...)`.
  - **Sequelize / Prisma / TypeORM:** Dependências `"sequelize"`, `"@prisma/client"`, `"typeorm"`.
  - **Mongoose / MongoDB:** Dependência `"mongoose"`.

---

## 2. Identificação do Domínio da Aplicação

O domínio e as entidades principais devem ser inferidos através de:
1. Nomes das tabelas criadas nas instruções SQL (`CREATE TABLE ...`).
2. Modelos ORM definidos (`db.Model`, classes de entidade).
3. Nomes de rotas e endpoints REST (`/produtos`, `/pedidos`, `/checkout`, `/tasks`, `/users`).
4. Propriedades de payloads recebidos em requisições POST/PUT.

---

## 3. Mapeamento da Arquitetura Atual

Classificar a arquitetura atual em uma das seguintes categorias:
- **Monólito Desestruturado (God Module / Spaghetti):** Todo o sistema ou a maior parte dele está concentrado em poucos arquivos (ou em um único arquivo), misturando queries SQL, regras de negócio, roteamento HTTP e configuração.
- **Parcialmente Organizado:** Possui separação preliminar de pastas (ex.: `models`, `routes`), mas ainda sofre com acoplamento, lógicas pesadas nos controllers ou rotas e ausência de camadas de serviço ou configuração desacoplada.
- **Padrão MVC Estruturado:** Apresenta clara separação de responsabilidades entre Models (dados/regras), Views/Routes (apresentação/rotas) e Controllers (orquestração do fluxo), com injeção de dependência e configuração isolada.

---

## 4. Mapeamento de Superfície de Rotas Administrativas e Sensíveis

Durante a análise inicial e transição para a auditoria, mapear **todos** os endpoints HTTP expostos pela aplicação e marcar para triagem imediata de segurança (`CRITICAL`) qualquer rota que:
- Contenha segmentos administrativos (`/admin`, `/internal`, `/debug`, `/query`, `/reset`) no path sem middleware explícito de autenticação (`Bearer` token) e verificação de papel administrativo;
- Exponha relatórios financeiros, métricas internas de receita, listas de pagamentos ou registros de usuários sem controle de acesso compatível;
- Crie usuários ou atualize perfis permitindo envio de campos de privilégio (`tipo`, `role`, `is_admin`) no payload público.

---

## 5. Formato de Saída Obrigatório da Fase 1

Ao concluir a análise, a skill deve emitir o resumo exatamente no seguinte padrão:

```text
================================
PHASE 1: PROJECT ANALYSIS
================================
Language: <Python | Node.js | ...>
Framework: <Flask | Express | ...>
Dependencies: <principais dependências identificadas>
Domain: <Descrição do domínio e entidades identificadas>
Architecture: <Monolítica desestruturada | Parcialmente organizada | ...>
Source files: <N> files analyzed
DB tables: <tabela1, tabela2, ...>
================================
```
