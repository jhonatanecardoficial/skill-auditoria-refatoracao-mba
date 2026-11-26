# Playbook de Refatoração Arquitetural e Transformações

Este documento orienta a **Fase 3 (Refatoração)** da skill `refactor-arch`, fornecendo padrões concretos de transformação com exemplos de código **Antes / Depois** cobrindo Python e Node.js.

---

## Padrão 1: Eliminação de SQL Injection (Consultas Parametrizadas)

### Antes (Python / SQLite Inseguro):
```python
# Inseguro: vulnerável a injeção SQL via concatenação
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES ('" + nome + "', '" + email + "')")
```

### Depois (Python / Parametrizado):
```python
# Seguro: utiliza placeholders e tupla de parâmetros
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO usuarios (nome, email) VALUES (?, ?)", (nome, email))
```

---

## Padrão 2: Decomposição de God Class / God Module em Camadas MVC

### Antes (Node.js / Monólito em `AppManager.js`):
```javascript
// AppManager.js centralizando conexão, tabelas, rotas e regras
class AppManager {
  initDb() { this.db.run("CREATE TABLE ..."); }
  setupRoutes(app) {
    app.post('/api/checkout', (req, res) => {
      this.db.get("SELECT ...", (err, course) => {
        this.db.run("INSERT ...", (err) => { res.send("OK"); });
      });
    });
  }
}
```

### Depois (Node.js / MVC Separado):
```javascript
// models/course.model.js
class CourseModel {
  static async findById(db, id) {
    return new Promise((resolve, reject) => {
      db.get("SELECT * FROM courses WHERE id = ? AND active = 1", [id], (err, row) => err ? reject(err) : resolve(row));
    });
  }
}

// controllers/checkout.controller.js
class CheckoutController {
  constructor(checkoutService) { this.service = checkoutService; }
  async handle(req, res, next) {
    try {
      const result = await this.service.execute(req.body);
      return res.status(200).json(result);
    } catch (err) { next(err); }
  }
}

// routes/checkout.routes.js
const router = express.Router();
router.post('/checkout', (req, res, next) => checkoutController.handle(req, res, next));
```

---

## Padrão 3: Externalização de Configurações e Segredos (Fail-Closed e Zero Fallbacks Estáticos)

Nunca utilize strings literais como fallback de `SECRET_KEY`, senhas ou chaves de API (`os.getenv("SECRET_KEY", "dev-...")`): como o código reside no repositório, um fallback estático público permite que qualquer atacante faça **forja offline de tokens administrativos** sem conhecer nenhuma senha. Da mesma forma, variáveis de ambiente (`ENVIRONMENT`/`NODE_ENV`) DEVEM falhar de forma fechada (**Fail-Closed**), assumindo `"production"` quando ausentes ou vazias.

### Antes (Hardcoded no arquivo de aplicação ou fallback estático/fail-open):
```python
# app.py / settings.py (INSEGURO)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-fallback-key-only")  # Permite forja de token!
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # Fail-open!
```

### Depois (Isolado em `config/settings.py` com CSPRNG efêmero e Fail-Closed):
```python
# config/settings.py
import os
import secrets

class Config:
    SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip() or secrets.token_hex(32)
    DEBUG = (os.getenv("FLASK_DEBUG") or "False").strip().lower() in ("true", "1")
    DATABASE_PATH = (os.getenv("DATABASE_PATH") or "loja.db").strip()
    ENVIRONMENT = (os.getenv("ENVIRONMENT") or "production").strip().lower()
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# app.py
from config.settings import Config
app.config.from_object(Config)
```

```javascript
// Node.js equivalente: src/config/config.js (Fail-Closed e sem segredos estáticos)
const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  dbPath: process.env.DB_PATH || ":memory:",
  dbUser: process.env.DB_USER || "",
  dbPass: process.env.DB_PASS || "",
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
  smtpUser: process.env.SMTP_USER || "",
  nodeEnv: (process.env.NODE_ENV || "production").trim().toLowerCase()
};
```

---

## Padrão 4: Criptografia Forte e Proteção de Dados Sensíveis

### Antes (Inseguro: MD5 sem salt e vazamento de senha no retorno):
```python
# models.py
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {'id': self.id, 'name': self.name, 'password': self.password}
```

### Depois (Seguro: Werkzeug / bcrypt e omissão de credencial):
```python
# models.py
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, pwd):
    self.password = generate_password_hash(pwd)

def check_password(self, pwd):
    return check_password_hash(self.password, pwd)

def to_dict(self):
    # Nunca retorna a senha ou seu hash
    return {'id': self.id, 'name': self.name, 'email': self.email, 'role': self.role}
```

---

## Padrão 5: Desacoplamento de Regras de Negócio dos Controllers

### Antes (Lógica de pedido e notificações no controller):
```python
# controllers.py
def criar_pedido():
    # Loop de cálculo, alteração de estoque e prints manuais de SMS/Email
    for item in itens: ...
    print("ENVIANDO EMAIL...")
    print("ENVIANDO SMS...")
```

### Depois (Serviço de Domínio orquestrado):
```python
# services/pedido_service.py
class PedidoService:
    def __init__(self, pedido_repo, produto_repo, notification_service):
        self.pedido_repo = pedido_repo
        self.produto_repo = produto_repo
        self.notifier = notification_service

    def criar_pedido(self, usuario_id, itens):
        # Validação de regras e estoque
        total = self.calcular_total(itens)
        pedido = self.pedido_repo.salvar(usuario_id, itens, total)
        self.notifier.notificar_criacao(pedido)
        return pedido
```

---

## Padrão 6: Eliminação de Callback Hell (Promises / Async Await)

### Antes (Node.js Callback Pyramid):
```javascript
// AppManager.js
db.get(query1, [p1], (err, res1) => {
  db.get(query2, [p2], (err, res2) => {
    db.run(query3, [p3], function(err) {
      db.run(query4, [p4], function(err) {
        res.send("OK");
      });
    });
  });
});
```

### Depois (Promisificação limpa com Async/Await):
```javascript
// services/checkout.service.js
async function processCheckout(payload) {
  const course = await dbGet(query1, [payload.c_id]);
  const user = await dbGet(query2, [payload.eml]);
  const enrollmentId = await dbRun(query3, [user.id, course.id]);
  await dbRun(query4, [enrollmentId, course.price]);
  return { success: true, enrollmentId };
}
```

---

## Padrão 7: Resolução do Anti-Pattern N+1 Query

### Antes (Execução de query por item em loop):
```python
# models.py
pedidos = cursor.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    # N queries adicionais disparadas
    itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (p['id'],)).fetchall()
```

### Depois (JOIN único com agregação):
```python
# models.py
cursor.execute("""
    SELECT p.id, p.total, p.status, ip.produto_id, pr.nome as produto_nome, ip.quantidade, ip.preco_unitario
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
""")
rows = cursor.fetchall()
# Agrupamento estruturado em memória O(N)
```

---

## Padrão 8: Modernização de APIs Deprecated

### Caso A: `datetime.utcnow()` no Python 3.12+
```python
# Antes (Deprecated):
from datetime import datetime
created_at = datetime.utcnow()

# Depois (Canônico e compatível):
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
```

### Caso B: `Model.query.get(id)` no SQLAlchemy 2.0+
```python
# Antes (Padrão legado SQLAlchemy 1.x):
user = User.query.get(user_id)

# Depois (Padrão SQLAlchemy 2.0 com session):
user = db.session.get(User, user_id)
```

---

## Padrão 9: Tratamento Centralizado de Erros e Remoção de Bare Except

### Antes (Bare except silencioso):
```python
try:
    process_data()
except:
    return jsonify({'error': 'Erro interno'}), 500
```

### Depois (Middleware global e exceções tipadas):
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_validation_error(exc):
        return jsonify({'error': str(exc), 'status': 'fail'}), 400

    @app.errorhandler(Exception)
    def handle_generic_error(exc):
        app.logger.error(f"Erro inesperado: {exc}")
        return jsonify({'error': 'Erro interno do servidor', 'status': 'error'}), 500
```

---

## Padrão 10: Substituição de Magic Numbers e Nomes Crípticos

### Antes:
```javascript
let u = req.body.usr;
let cc = req.body.card;
if (cc.startsWith("4")) { ... }
```

### Depois:
```javascript
const { userName, cardNumber } = req.body;
const VISA_PREFIX = "4";
const isPaymentApproved = cardNumber.startsWith(VISA_PREFIX);
```

---

## Padrão 11: Remoção de Backdoors SQL, Proteção de Endpoints Administrativos, Anti-Mass Assignment e Trava Fail-Closed

### Caso A: Remoção Definitiva de Backdoors de Execução SQL Arbitrária
Endpoints como `/admin/query` que recebem e executam SQL arbitrário fornecido pelo cliente são backdoors inaceitáveis e devem ser **completamente removidos** da aplicação, respondendo HTTP 404.

```python
# ANTES (Vulnerável - Execução arbitrária de SQL):
@admin_bp.route("/admin/query", methods=["POST"])
def executar_query():
    sql = request.json.get("sql")
    cursor.execute(sql)
    return jsonify({"resultado": cursor.fetchall()})

# DEPOIS (Seguro - Rota eliminada da aplicação):
# A rota /admin/query é removida por completo da tabela de rotas.
# Qualquer requisição para /admin/query recebe automaticamente HTTP 404 Not Found.
```

### Caso B: Proteção Estrita de Endpoints Administrativos Destrutivos (Com Revalidação no Banco e Zero SQL no Controller)
Operações como `/admin/reset-db` devem exigir cumulativamente: trava *fail-closed* de ambiente, autenticação Bearer assinada, **revalidação do usuário e do papel (`tipo == "admin"`) diretamente no banco de dados**, e delegação da escrita SQL para a camada Model (`AdminModel`).

```python
# models/admin.py (Persistência isolada no Model - Zero SQL no Controller)
class AdminModel:
    @staticmethod
    def reset_database() -> None:
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute("DELETE FROM itens_pedido")
            cursor.execute("DELETE FROM pedidos")
            cursor.execute("DELETE FROM produtos")
            cursor.execute("DELETE FROM usuarios")
            db.commit()
        except Exception:
            db.rollback()
            raise

# middlewares/auth_middleware.py
from functools import wraps
from flask import request, jsonify, current_app
from src.models.usuario import UsuarioModel

ALLOWED_RESET_ENVIRONMENTS = ("development", "testing")

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Trava de ambiente Fail-Closed (bloqueia se ausente, vazio ou 'production')
        env = str(current_app.config.get("ENVIRONMENT", "")).strip().lower()
        if env not in ALLOWED_RESET_ENVIRONMENTS:
            return jsonify({"erro": "Operação não permitida neste ambiente", "sucesso": False}), 403

        # 2. Validação criptográfica do token Bearer
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"erro": "Token de autenticação não fornecido", "sucesso": False}), 401

        token = auth_header.split(" ", 1)[1].strip()
        user_data = verify_auth_token(token)
        if not user_data:
            return jsonify({"erro": "Token inválido ou expirado", "sucesso": False}), 401

        # 3. Revalidação do usuário e papel administrativo no banco de dados
        user_id = user_data.get("id")
        db_user = UsuarioModel.get_por_id(user_id) if user_id is not None else None
        if user_data.get("tipo") != "admin" or not db_user or db_user.get("tipo") != "admin":
            return jsonify({"erro": "Acesso restrito a administradores", "sucesso": False}), 403

        return f(*args, **kwargs)
    return decorated

# routes/admin_routes.py
@admin_bp.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_database_route():
    return admin_controller.reset_database()
```

### Caso C: Proibição Estrita de Mass Assignment / Auto-elevação de Privilégio em Cadastro Público
O papel de administrador (`admin`) **NUNCA** pode ser aceito a partir do payload JSON de endpoints públicos de criação (`POST /usuarios`, `POST /users`) ou auto-alterado em rotas públicas de atualização (`PUT /users/:id`). Caso contrário, qualquer usuário anônimo se registra como `admin`, faz login e ganha acesso irrestrito aos endpoints administrativos.

```python
# ANTES (VULNERÁVEL - Mass Assignment / Privilege Escalation):
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    tipo = str(dados.get("tipo", "cliente")).strip()  # BRECHA CRÍTICA!
    novo_id = UsuarioModel.criar(nome, email, senha, tipo)

# DEPOIS (SEGURO - Papel de menor privilégio imposto no servidor):
def criar_usuario():
    dados = request.get_json(silent=True) or {}
    # Campo 'tipo'/'role' do payload público é completamente ignorado
    novo_id = UsuarioModel.criar(nome, email, senha, tipo="cliente")

# Em rotas PUT /users/:id sem autenticação administrativa:
if "role" in data and data["role"] != user.role:
    return {"error": "Alteração de papel não permitida neste endpoint"}, 403
```

### Caso D: Trava de Ambiente Fail-Closed (Bloqueio Quando `ENVIRONMENT` Não Estiver Definido)
Quando `ENVIRONMENT` (ou `NODE_ENV`) não estiver definido na máquina ou container, a aplicação DEVE assumir modo restritivo (`"production"`) para impedir exposição acidental de operações administrativas em deploys reais.

```python
# ANTES (VULNERÁVEL - Fail-Open):
environment = os.getenv("ENVIRONMENT", "development")  # Abre rotas admin sem config!

# DEPOIS (SEGURO - Fail-Closed):
environment = (os.getenv("ENVIRONMENT") or "production").strip().lower()
# Somente libera se ENVIRONMENT for explicitamente "development" ou "testing".
```

---

## Padrão 12: Extração de Fat Routes e Migração Integral para MVC em Projetos Parcialmente Organizados

Projetos que já possuem separação inicial de pastas (ex.: rotas em Blueprints) frequentemente sofrem de **Fat Routes**, onde validações, queries diretas de ORM (`db.session`) e regras de negócio continuam misturadas dentro das funções de rota.

### Antes (Fat Route acoplada ao ORM e sem camada de Controller/Config):
```python
# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    task = Task(title=data['title'], description=data.get('description'))
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201
```

### Depois (Padrão MVC completo com Controller desacoplado):
```python
# controllers/task_controller.py
class TaskController:
    @staticmethod
    def create_task(data):
        if not data or not data.get('title'):
            return {'error': 'Title is required'}, 400
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', '').strip()
        )
        db.session.add(task)
        db.session.commit()
        return task.to_dict(), 201

# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
def create_task_route():
    result, status = TaskController.create_task(request.get_json() or {})
    return jsonify(result), status
```
