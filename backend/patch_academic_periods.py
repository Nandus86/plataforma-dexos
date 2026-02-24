import re

with open('app/api/academic_periods.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
if 'get_required_tenant_id' not in content:
    content = content.replace(
        'from app.auth.dependencies import get_current_user',
        'from app.auth.dependencies import get_current_user, get_current_tenant_id, get_required_tenant_id\nfrom typing import Optional'
    )

# 2. Add tenant_id dependency to all endpoints
content = re.sub(
    r'(current_user:\s*User\s*=\s*Depends\([^\)]+\))(\s*\):)',
    r'\1,\n    tenant_id: UUID = Depends(get_required_tenant_id)\2',
    content
)

# 3. For list_academic_periods, we want Optional[UUID] = Depends(get_current_tenant_id)
old_list = '''@router.get("", response_model=List[AcademicPeriodResponse])
async def list_academic_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_required_tenant_id),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """List all academic periods for the tenant"""
    query = select(AcademicPeriod).where(
        AcademicPeriod.tenant_id == current_user.tenant_id
    )'''

new_list = '''@router.get("", response_model=List[AcademicPeriodResponse])
async def list_academic_periods(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[UUID] = Depends(get_current_tenant_id),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False
):
    """List all academic periods for the tenant"""
    query = select(AcademicPeriod)
    if tenant_id:
        query = query.where(AcademicPeriod.tenant_id == tenant_id)'''
content = content.replace(old_list, new_list)

# 4. Replace conditions
content = content.replace('AcademicPeriod.tenant_id == current_user.tenant_id', 'AcademicPeriod.tenant_id == tenant_id')

# 5. Fix create_academic_period instantiation
old_create = '''    period = AcademicPeriod(
        tenant_id=current_user.tenant_id,'''
new_create = '''    period = AcademicPeriod(
        tenant_id=tenant_id,'''
content = content.replace(old_create, new_create)

with open('app/api/academic_periods.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("done")
