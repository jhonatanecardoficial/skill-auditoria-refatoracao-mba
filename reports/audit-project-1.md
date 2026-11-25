================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack: Python 3 + Flask
Files: 4 analyzed | ~700 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 3

## Findings

### [F1] [CRITICAL] SQL Injection Generalizado
File: models.py:28, 48-50, 58-61, 68, 92, 109-111, 127-129, 140, 149-151, 158-161, 164-166, 174, 188, 192, 220, 224
Description: Todas as consultas de busca, inserção, atualização e deleção utilizam concatenação direta de strings (`+ str(id)`, `+ nome +`) em vez de consultas preparadas com parâmetros (`?`).
Impact: Permite extração de dados sensíveis (senhas em texto claro), contorno de autenticação e destruição de dados por qualquer usuário da API.
Recommendation: Substituir todas as queries por consultas parametrizadas com placeholders (`?`) e tuplas de argumentos no SQLite.

### [F2] [CRITICAL] Execução Arbitrária de SQL em Endpoint Administrativo
File: app.py:59-78
Description: A rota `/admin/query` recebe comandos SQL arbitrários via payload JSON e os executa diretamente no banco (`cursor.execute(query)`), retornando resultados ou comitando alterações sem qualquer autenticação.
Impact: Permite que atacantes executem comandos DDL/DML arbitrários (`DROP TABLE`, `UPDATE`, `ATTACH DATABASE`), comprometendo totalmente o servidor.
Recommendation: Remover o endpoint de execução arbitrária e restringir operações administrativas a endpoints seguros e autenticados.

### [F3] [CRITICAL] Endpoint Destrutivo de Reset de Banco Desprotegido
File: app.py:47-58
Description: A rota `/admin/reset-db` apaga todos os registros das tabelas `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem validação de permissão ou token de segurança.
Impact: Qualquer cliente não autenticado pode causar negação de serviço e perda total de dados em produção.
Recommendation: Excluir ou proteger rigidamente endpoints de manutenção com autenticação e validação de ambiente (apenas teste/dev).

### [F4] [CRITICAL] Hardcoded Secret Key e Vazamento de Dados Sensíveis
File: app.py:7, controllers.py:287-290
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` gravada diretamente no código; além disso, a rota `/health` vaza a `secret_key`, o caminho do banco (`db_path`) e o status de `debug` no JSON de resposta.
Impact: Permite forja de tokens/sessões e reconhecimento da infraestrutura interna do servidor por atacantes.
Recommendation: Mover segredos para variáveis de ambiente (`config/settings.py`) e remover informações confidenciais das respostas públicas de health check.

### [F5] [CRITICAL] Senhas Armazenadas e Retornadas em Texto Claro
File: models.py:83, 99, 110, 128
Description: As senhas dos usuários são salvas e comparadas em texto puro no banco de dados e expostas no retorno das funções de busca de usuários.
Impact: Violação grave de privacidade e segurança; vazamento irreversível das credenciais de todos os usuários.
Recommendation: Implementar hashing seguro de senhas com Werkzeug/bcrypt e remover o campo de senha do payload de retorno.

### [F6] [HIGH] God Module / Violação Total de Separação de Responsabilidades
File: models.py:1-314
Description: O arquivo `models.py` centraliza acesso a dados, manipulação de cursores SQLite, regras de negócio de pedidos (cálculo de total, verificação e decremento de estoque) e geração de relatórios para 4 domínios diferentes (produtos, usuários, pedidos, itens).
Impact: Código monolítico impossível de testar em isolamento; qualquer alteração em regras de pedido pode quebrar produtos ou usuários.
Recommendation: Decompor em models específicos (`produto_model.py`, `usuario_model.py`, `pedido_model.py`) e concentrar regras de negócio em controllers/services.

### [F7] [HIGH] Lógica de Negócio e Notificações Embutidas nos Controllers
File: controllers.py:208-210, 247-251
Description: Handlers HTTP concentram despacho simulado de emails, SMS e push notifications via prints no meio da rota, além de controle de fluxo de estoque.
Impact: Acoplamento entre protocolo de transporte HTTP e regras de negócio/integrações externas.
Recommendation: Isolar notificações e regras de estoque em serviços de domínio dedicados.

### [F8] [HIGH] Estado Global Mutável e Conexão Compartilhada sem Pool
File: database.py:7-14
Description: Variável global `db` reutilizada sem controle de ciclo de vida ou context manager no SQLite.
Impact: Riscos de corrupção de estado e falhas de concorrência em múltiplas requisições simultâneas.
Recommendation: Gerenciar conexões por ciclo de requisição via context manager (`g` do Flask ou session management).

### [F9] [MEDIUM] Anti-Pattern N+1 Queries
File: models.py:187-200, 219-232
Description: Ao listar pedidos, o código itera sobre cada pedido e dispara uma nova query para itens, e para cada item dispara outra query para buscar o nome do produto.
Impact: Explosão de consultas ao banco de dados; para N pedidos com M itens são executadas 1 + N + (N*M) queries.
Recommendation: Reescrever com `LEFT JOIN` único agrupando pedidos, itens e produtos em uma única viagem ao banco.

### [F10] [MEDIUM] Ausência de Tratamento Centralizado de Erros
File: controllers.py:10-12, 21-23, 60-63, 95-97, 108-110, 125-127, 133-135, 143-145, 164-166, 185-187, 218-221, 226-228, 234-236, 254-256, 261-263
Description: Cada endpoint repete blocos `try/except Exception as e` idênticos retornando `jsonify({"erro": str(e)}), 500`.
Impact: Duplicação de código (violação DRY) e vazamento de stack traces internos do Python para o cliente.
Recommendation: Implementar `@app.errorhandler` centralizado em middleware de erros.

### [F11] [MEDIUM] Filtros e Validações Incompletas nas Rotas
File: controllers.py:37-55, 118-121
Description: Validações manuais espalhadas e conversões de tipo (`float(preco_min)`) sem tratamento de `ValueError`.
Impact: Requisições com parâmetros malformados quebram com status 500 em vez de 400.
Recommendation: Centralizar validações de entrada e normalizar tratamento de formatos inválidos.

### [F12] [LOW] Magic Numbers e Magic Strings
File: controllers.py:47, 49, 52, models.py:122, 257-262
Description: Limites `len(nome) < 2`, `len(nome) > 200`, faixas de desconto (`10000`, `5000`, `1000`), categorias permitidas e roles fixados no código sem constantes.
Impact: Dificulta alteração de regras de validação e consistência entre rotas.
Recommendation: Definir constantes e enums de validação no módulo de configuração/model.

### [F13] [LOW] Concatenação de Strings com Operador '+' para Logs
File: controllers.py:8, 57, 106, 161, 179, 208-210
Description: Uso extensivo de `print("Texto " + str(valor))` para logging de operações da API.
Impact: Código poluído e logs não estruturados sem níveis de severidade (INFO, ERROR, WARN).
Recommendation: Utilizar o logger padrão da aplicação com formatação estruturada (f-strings).

### [F14] [LOW] Roteamento Procedural com add_url_rule
File: app.py:11-30
Description: Registro de 15 rotas linha por linha em arquivo raiz sem uso de Blueprints ou agrupamento por recurso.
Impact: Dificulta a navegação no código e impede o desacoplamento de módulos.
Recommendation: Modularizar em Blueprints (`routes/produto_routes.py`, `routes/usuario_routes.py`, `routes/pedido_routes.py`).

================================
Total: 14 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
