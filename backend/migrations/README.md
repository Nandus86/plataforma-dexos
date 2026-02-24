# Database Migrations

Este diretório contém scripts SQL de migração para o banco de dados.

## Importante

⚠️ **O projeto atualmente usa SQLAlchemy com `Base.metadata.create_all()`**, o que significa que as tabelas são criadas automaticamente na inicialização da aplicação.

Os scripts SQL aqui são fornecidos para:
1. **Referência**: Documentação das mudanças no esquema
2. **Migração Manual**: Caso você precise aplicar mudanças em um banco existente
3. **Futuro**: Base para configuração de Alembic se necessário

## Como Usar

### Opção 1: Criação Automática (Recomendado para Desenvolvimento)

As tabelas serão criadas automaticamente quando você iniciar a aplicação pela primeira vez:

```bash
python main.py
```

### Opção 2: Migração Manual (Para Banco Existente)

Se você já tem um banco de dados em produção e precisa adicionar as novas tabelas:

```bash
# Conecte ao PostgreSQL
psql -U seu_usuario -d nome_do_banco

# Execute o script de migração
\i backend/migrations/001_add_academic_period_tables.sql
```

### Rollback (Se Necessário)

Para reverter as mudanças:

```bash
psql -U seu_usuario -d nome_do_banco
\i backend/migrations/001_add_academic_period_tables_rollback.sql
```

## Migrações Disponíveis

### 001_add_academic_period_tables.sql

**Data**: 2026-02-17

**Mudanças**:
- ✅ Cria tipos ENUM PostgreSQL (`break_type`, `non_school_day_reason`)
- ✅ Cria tabela `academic_periods`
- ✅ Cria tabela `period_breaks`
- ✅ Cria tabela `non_school_days`
- ✅ Cria tabela `class_schedules`
- ✅ Adiciona coluna `academic_period_id` em `courses`
- ✅ Adiciona colunas `class_group_subject_id` e `class_order` em `lesson_plans`
- ✅ Cria índices para otimização
- ✅ Cria trigger para atualizar `updated_at` automaticamente

## Configurando Alembic (Opcional)

Se você quiser usar Alembic para migrações versionadas:

```bash
# Instalar Alembic
pip install alembic

# Inicializar Alembic
alembic init alembic

# Configurar alembic.ini com sua string de conexão
# sqlalchemy.url = postgresql://user:pass@localhost/dbname

# Criar migração automática
alembic revision --autogenerate -m "Add academic period tables"

# Aplicar migração
alembic upgrade head
```
