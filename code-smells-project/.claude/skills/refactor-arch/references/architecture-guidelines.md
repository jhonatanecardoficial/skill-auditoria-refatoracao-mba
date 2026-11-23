# Diretrizes do Padrão Arquitetural MVC Alvo

Este documento define as regras arquiteturais e responsabilidades de cada camada para a **Fase 3 (Refatoração para MVC)** da skill `refactor-arch`.

---

## 1. Princípios Fundamentais

- **Separação Estrita de Responsabilidades (SoC):** Cada camada possui um único propósito bem delimitado.
- **Isolamento de Configuração:** Nenhuma credencial ou configuração de ambiente deve residir hardcoded no código.
- **Tratamento Centralizado de Erros:** Erros e exceções não devem ser engolidos nem espalhados em blocos try/catch redundantes, mas sim normalizados em manipuladores globais.
- **Agnosticismo de Tecnologia:** Os mesmos princípios de divisão em camadas se aplicam a Python (Flask/FastAPI), Node.js (Express) ou qualquer outra stack web.

---

## 2. Camadas da Aplicação MVC

```text
src/
├── config/                  # Camada de Configuração (settings, variáveis de ambiente)
│   └── settings.py | .js
├── database/                # Conexão e inicialização com o banco de dados
│   └── connection.py | .js
├── models/                  # Camada Model: Definição de entidades, persistência e queries seguras
│   ├── <entidade>_model.py | .js
│   └── ...
├── controllers/             # Camada Controller: Orquestração do fluxo da requisição e validação
│   ├── <dominio>_controller.py | .js
│   └── ...
├── views/ ou routes/        # Camada View/Routes: Definição de rotas HTTP, verbos e mapeamento
│   ├── <dominio>_routes.py | .js
│   └── ...
├── services/ (opcional)     # Serviços de domínio para lógicas de negócio complexas ou integrações
├── middlewares/             # Middlewares globais (error handler, cors, logging)
└── app.py | app.js          # Composition Root: Instanciação e amarração da aplicação
```

---

## 3. Responsabilidades de Cada Camada

### 3.1 Camada Model (`models/`)
- Representar as entidades de negócio e o estado dos dados.
- Conter consultas seguras ao banco de dados com binds parametrizados (`?` ou ORM).
- Métodos de persistência (CRUD) específicos por domínio (ex.: `ProdutoModel`, `UsuarioModel`, `PedidoModel`).
- **NÃO DEVE:** Conhecer objetos HTTP (`request`, `response`, `jsonify`, `req`, `res`), nem orquestrar múltiplos canais externos.

### 3.2 Camada Controller (`controllers/`)
- Receber dados validados da requisição.
- Orquestrar as chamadas aos Models ou Services.
- Decidir qual código de status HTTP retornar (`200`, `201`, `400`, `404`, `500`).
- **NÃO DEVE:** Executar queries SQL diretas ou conter concatenação de strings de banco.

### 3.3 Camada View / Routes (`views/` ou `routes/`)
- Mapear a URL e verbo HTTP (`GET`, `POST`, `PUT`, `DELETE`) para a função de Controller correspondente.
- Utilizar recursos nativos do framework (ex.: Flask `Blueprint`, Express `Router`).
- **NÃO DEVE:** Conter regras de negócio nem manipulação de banco de dados.

### 3.4 Camada de Configuração (`config/`)
- Centralizar a leitura de variáveis de ambiente (`SECRET_KEY`, `PORT`, credenciais).
- Fornecer valores padrão seguros para desenvolvimento local.

### 3.5 Middlewares e Error Handling (`middlewares/`)
- Centralizar o tratamento de exceções e respostas de erro uniformes em JSON.
- Gerenciar headers de CORS, autenticação ou logging compartilhado.

### 3.6 Composition Root (`app.py` / `app.js`)
- Criar a instância principal da aplicação (`app`).
- Registrar blueprints/routers e middlewares.
- Inicializar a conexão com o banco de dados sem executar scripts destrutivos automaticamente.
