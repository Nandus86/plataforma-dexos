from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from app.models.user import User, UserRole

def get_pseudo_random_seq(n: int) -> str:
    """
    Generate a 4-digit pseudo random string from a sequence number.
    Using a simple LCG where modulo = 10000.
    multiplier = 3749 (gcd(3749, 10000) == 1, so it's a full cycle permutation)
    increment = 1234
    """
    # Offset by N so 0 doesn't just return increment
    val = (n * 3749 + 1234) % 10000
    return f"{val:04d}"

def get_pseudo_random_letters(n: int) -> str:
    """
    Generate 2 pseudo random letters for students based on sequence.
    Excluding PR.
    Total pairs of A-Z = 26 * 26 = 676.
    We exclude 'PR', leaving 675 pairs.
    """
    # Create list of letters A-Z
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    all_pairs = [a + b for a in alphabet for b in alphabet if a + b != "PR"]
    
    # Use another prime multiplier for the letters to make them seem independent from the numbers
    # Modulo is 675. Factors of 675: 3 * 3 * 3 * 5 * 5.
    # We need a multiplier that is coprime with 675 (not divisible by 3 or 5).
    # e.g., 373 (prime). gcd(373, 675) == 1.
    val = (n * 373 + 87) % 675
    return all_pairs[val]

async def generate_registration_number(db: AsyncSession, role: UserRole, tenant_id, year: int = None) -> str:
    """
    Generate the RA (registration number) for a new user.
    Format: YYYY + XX + 0000
    XX = 'PR' for non-students.
    XX = Two pseudo-random letters for students.
    """
    if not year:
        year = datetime.utcnow().year
        
    # Count how many users exist in this tenant for the given year to form our N
    # This acts as our base sequence
    query = select(func.count(User.id)).where(
        User.tenant_id == tenant_id,
        extract('year', User.created_at) == year
    )
    result = await db.execute(query)
    count = result.scalar() or 0
    
    # Try finding an unused index (in case of concurrent generation or deletions)
    n = count + 1
    
    while True:
        # Determine the parts
        str_year = str(year)
        str_seq = get_pseudo_random_seq(n)
        
        if role != UserRole.ESTUDANTE:
            str_letters = "PR"
        else:
            str_letters = get_pseudo_random_letters(n)
            
        candidate_ra = f"{str_year}{str_letters}{str_seq}"
        
        # Check collision
        existing = await db.execute(
            select(User.id).where(
                User.registration_number == candidate_ra,
                User.tenant_id == tenant_id
            )
        )
        if not existing.first():
            return candidate_ra
        
        # Collision found, increment and retry
        n += 1

async def generate_enrollment_code(db: AsyncSession, student_ra: str, year: int) -> str:
    """
    Generate an Enrollment Code.
    Format: YY + RA + S
    where YY is the last two digits of the year.
    RA is the student's registration number.
    S is a sequence number starting at 1, incremented if the student has multiple enrollments in the same year.
    Example: 262026OH1226-1
    """
    str_year = str(year)[-2:]
    base_code = f"{str_year}{student_ra}"
    
    # Check how many enrollments this student already has with this base code prefix
    # to find the next available sequence number.
    from app.models.academic import Enrollment
    query = select(func.count(Enrollment.id)).where(
        Enrollment.enrollment_code.like(f"{base_code}%")
    )
    result = await db.execute(query)
    count = result.scalar() or 0
    
    # Use a dash to separate the sequence for readability
    seq = count + 1
    candidate = f"{base_code}-{seq}"
    
    # Ensure no collision just in case
    while True:
        existing = await db.execute(
            select(Enrollment.id).where(Enrollment.enrollment_code == candidate)
        )
        if not existing.first():
            return candidate
        seq += 1
        candidate = f"{base_code}-{seq}"
