"""
Seed Data - Initial superadmin and tenant
"""
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.auth.security import hash_password


async def seed_initial_data():
    """Create default tenant and superadmin user if they don't exist"""
    async with AsyncSessionLocal() as session:
        # 1. Ensure Tenant Exists
        result = await session.execute(select(Tenant).where(Tenant.domain == "exousia.school"))
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            tenant = Tenant(
                name="Exousía School",
                slug="exousia",
                domain="exousia.school",
            )
            session.add(tenant)
            await session.flush()
            print("✅ Tenant 'Exousía School' criado.")
        else:
            print("ℹ️ Tenant 'Exousía School' já existe.")

        # 2. Ensure Superadmin Exists
        result = await session.execute(select(User).where(User.email == "admin@exousia.school"))
        if not result.scalar_one_or_none():
            superadmin = User(
                name="Administrador Geral",
                email="admin@exousia.school",
                password_hash=hash_password("admin123"),
                role=UserRole.SUPERADMIN,
                tenant_id=None,
            )
            session.add(superadmin)
            print("✅ Superadmin criado.")

        # 3. Ensure Admin Exists
        result = await session.execute(select(User).where(User.email == "gestor@exousia.school"))
        if not result.scalar_one_or_none():
            admin = User(
                name="Gestor Exousía",
                email="gestor@exousia.school",
                password_hash=hash_password("gestor123"),
                role=UserRole.ADMIN,
                tenant_id=tenant.id,
            )
            session.add(admin)
            print("✅ Gestor criado.")

        # 4. Ensure Professor Exists
        result = await session.execute(select(User).where(User.email == "professor@exousia.school"))
        if not result.scalar_one_or_none():
            professor = User(
                name="Prof. João Silva",
                email="professor@exousia.school",
                password_hash=hash_password("prof123"),
                role=UserRole.PROFESSOR,
                tenant_id=tenant.id,
            )
            session.add(professor)
            print("✅ Professor criado.")

        # 5. Ensure Coordination Exists
        result = await session.execute(select(User).where(User.email == "coordenacao@exousia.school"))
        if not result.scalar_one_or_none():
            coordenacao = User(
                name="Ana Coordenadora",
                email="coordenacao@exousia.school",
                password_hash=hash_password("coord123"),
                role=UserRole.COORDENACAO,
                tenant_id=tenant.id,
            )
            session.add(coordenacao)
            print("✅ Coordenação criada.")

        # 6. Ensure Student Exists
        result = await session.execute(select(User).where(User.email == "estudante@exousia.school"))
        if not result.scalar_one_or_none():
            estudante = User(
                name="Maria Santos",
                email="estudante@exousia.school",
                password_hash=hash_password("estudante123"),
                role=UserRole.ESTUDANTE,
                tenant_id=tenant.id,
                registration_number="2026001",
            )
            session.add(estudante)
            print("✅ Estudante criado.")

        await session.commit()
        print("✅ Dados iniciais criados com sucesso!")
        print("   📧 Superadmin: admin@exousia.school / admin123")
        print("   📧 Gestor: gestor@exousia.school / gestor123")
        print("   📧 Professor: professor@exousia.school / prof123")
        print("   📧 Coordenação: coordenacao@exousia.school / coord123")
        print("   📧 Estudante: estudante@exousia.school / estudante123")

