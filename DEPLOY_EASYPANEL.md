# Guia de Deploy no Easypanel (Exousía Plataforma)

Este guia orienta como colocar a plataforma Exousía em produção utilizando o **Easypanel**, aproveitando ao máximo a conteinerização nativa, SSL automático (Traefik) e serviços de banco de dados gerenciados oferecidos pela plataforma.

> *Nota: Estamos contornando o uso de `docker-compose.yml` raiz para garantir que o banco de dados (Postgres) e o Cache (Redis) sejam instâncias gerenciadas e isoladas no Easypanel, mantendo a consistência e segurança de produção.*

## Passo 1: Preparar os Serviços de Apoio (Bancos de Dados e Storage)

Acesse o painel do seu Easypanel e crie um novo **Project** (Ex: `exousia-prod`). Dentro deste projeto, crie os seguintes "Services":

### 1.1 Postgres (Banco de Dados Principal)
1. Clique em **Create Service** -> **App** -> Procure por **PostgreSQL**.
2. **Name**: `exousia-postgres`
3. Configure as credenciais no formulário (Usuário, Senha e Nome do Banco).
4. Clique em **Create**.
5. Anote a "Internal URL" gerada na aba "Overview" do Postgres. Ajuste o prefixo para `postgresql+asyncpg://` em vez de `postgres://` (Ex: `postgresql+asyncpg://usuario:senha@exousia-postgres:5432/nomedobanco`).

### 1.2 Redis (Cache e Fila)
1. Clique em **Create Service** -> **App** -> Procure por **Redis**.
2. **Name**: `exousia-redis`
3. Clique em **Create**.
4. Anote a "Internal URL" gerada (Ex: `redis://exousia-redis:6379`).

### 1.3 MinIO (Armazenamento S3)
1. Clique em **Create Service** -> **App** -> Procure por **MinIO**.
2. **Name**: `exousia-minio`
3. Configure o Usuário (`MINIO_ROOT_USER`) e Senha (`MINIO_ROOT_PASSWORD`).
4. Em **Domains**, defina o domínio público onde os arquivos ficarão acessíveis (Ex: `storage.suaescola.com`).
5. Anote as credenciais e o Endereço Interno (Ex: `exousia-minio:9000`).

---

## Passo 2: Deploy da API (Backend)

1. Volte ao painel do Projeto e clique em **Create Service** -> **App**.
2. **Name**: `exousia-backend`
3. Na aba **Source**, selecione **Github**.
   - Coloque o repositório (`Nandus86/plataforma-dexos`).
   - Defina a branch (Ex: `main`).
4. Na aba **Build**, certifique-se de que o **Build Type** seja `Dockerfile`.
   - **Docker Context**: `/backend`
   - **Dockerfile**: `/backend/Dockerfile`
5. Na aba **Environment**, insira as variáveis essenciais conectando o Backend aos serviços que você girou no Passo 1:
   ```env
   DATABASE_URL=postgresql+asyncpg://usuario:senha@exousia-postgres:5432/nomedobanco
   REDIS_URL=redis://exousia-redis:6379
   MINIO_ENDPOINT=exousia-minio:9000
   MINIO_ACCESS_KEY=seu_usuario_minio
   MINIO_SECRET_KEY=sua_senha_minio
   SECRET_KEY=sua-chave-secreta-segura-e-longa-em-producao
   ```
   *(Nota: A variável `WEAVIATE_URL` pode ser omitida temporariamente até a inteligência artificial ser habilitada).*
6. Na aba **Domains**, insira o subdomínio da API. (Ex: `api.suaescola.com`).
7. Na aba **Ports**, adicione a porta `8000` (porta do FastAPI dentro do container).
8. Clique em **Deploy**. O Easypanel puxará os arquivos do Github e fará o build do FastAPI, atrelando-o ao Traefik com TLS/SSL automaticamente.

---

## Passo 3: Deploy da Interface (Frontend)

1. Novamente, **Create Service** -> **App**.
2. **Name**: `exousia-frontend`
3. Na aba **Source**, conecte o mesmo repositório (`Nandus86/plataforma-dexos`), mesma branch.
4. Na aba **Build**, defina **Build Type** como `Dockerfile`.
   - **Docker Context**: `/frontend`
   - **Dockerfile**: `/frontend/Dockerfile`
5. Na aba **Environment**, configure apenas a base URL para a API exposta publicamente no passo 2:
   ```env
   API_URL=https://api.suaescola.com
   ```
6. Na aba **Domains**, insira o domínio final que o pai, professor ou diretor vai acessar. (Ex: `app.suaescola.com` ou simplesmente `suaescola.com`).
7. Na aba **Ports**, exponha a porta `4200` (caso o Dockerfile do Angular esteja rodando nela via `ng serve --host 0.0.0.0` ou `80` se você tiver um multi-stage build usando Nginx, veja o final do seu Dockerfile do `/frontend`).
8. Clique em **Deploy**.

---

## Considerações Finais
- **Traefik Mágico**: Você não precisa configurar portas 80/443 para o mundo externo. O redirecionamento interno que você fez na aba `Ports` do Easypanel cuida disso. Basta garantir que os DNS (`A` Records) dos domínios em seu Provedor apontem para o IP da VPS onde o Easypanel repousa.
- **Inteligência Artificial (Versão 2)**: Quando for escalar o Weaviate e o Transformers futuramente, bastará criar "App Services" através dos *Templates do Docker Compose* disponíveis no próprio Easypanel, injetando o `docker-compose.bkp.yml` deste repositório nele.
