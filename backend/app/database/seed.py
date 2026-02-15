"""
Seed MongoDB with demo data.

Idempotent — skips seeding if employees already exist.
Creates a default super-admin user (admin@hrms.com / admin123).
"""

from __future__ import annotations

import logging
from datetime import date, datetime

import bcrypt

from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.leave import LeaveRecord
from app.models.attendance import Attendance
from app.models.payroll import Payroll
from app.models.hr_policy import (
    HRPolicy,
    SalaryBreakup,
    LeavePolicy,
    INITIAL_TAX_SLABS_NEW_REGIME,
    INITIAL_TAX_SLABS_OLD_REGIME,
    INITIAL_STATE_PROFESSIONAL_TAX,
    INITIAL_STATE_LEAVE_OVERRIDES,
)

logger = logging.getLogger("hrms.seed")


async def seed_database() -> None:
    """Populate the database with sample data if empty."""

    existing = await Employee.find().count()
    if existing > 0:
        logger.info("Database already seeded (%d employees). Skipping.", existing)
        return

    logger.info("Seeding database with demo data …")

    # ------------------------------------------------------------------
    # 1. Default super-admin user
    # ------------------------------------------------------------------
    hashed_pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    admin_user = User(
        email="admin@hrms.com",
        name="System Admin",
        hashed_password=hashed_pw,
        role=UserRole.SUPER_ADMIN,
        emp_code="EMP001",
    )
    await admin_user.insert()

    # Additional demo users
    hr_pw = bcrypt.hashpw("hr123".encode(), bcrypt.gensalt()).decode()
    hr_user = User(
        email="priya.hr@company.com",
        name="Priya Sharma",
        hashed_password=hr_pw,
        role=UserRole.HR_ADMIN,
        emp_code="EMP002",
    )
    await hr_user.insert()

    mgr_pw = bcrypt.hashpw("mgr123".encode(), bcrypt.gensalt()).decode()
    mgr_user = User(
        email="rahul.m@company.com",
        name="Rahul Mehta",
        hashed_password=mgr_pw,
        role=UserRole.MANAGER,
        emp_code="EMP003",
    )
    await mgr_user.insert()

    emp_pw = bcrypt.hashpw("emp123".encode(), bcrypt.gensalt()).decode()
    emp_user1 = User(
        email="anita.d@company.com",
        name="Anita Desai",
        hashed_password=emp_pw,
        role=UserRole.EMPLOYEE,
        emp_code="EMP004",
    )
    await emp_user1.insert()

    emp_user2 = User(
        email="vikram.s@company.com",
        name="Vikram Singh",
        hashed_password=emp_pw,
        role=UserRole.EMPLOYEE,
        emp_code="EMP005",
    )
    await emp_user2.insert()

    # ------------------------------------------------------------------
    # 2. Employees — 20 across 7 departments
    # ------------------------------------------------------------------
    employees = [
        Employee(
            emp_code="EMP001", name="System Admin", email="admin@hrms.com",
            department="IT", designation="CTO",
            date_of_joining=date(2020, 1, 15), salary=180000.0,
            manager_name=None, phone="9876543210", gender="male",
        ),
        Employee(
            emp_code="EMP002", name="Priya Sharma", email="priya.hr@company.com",
            department="HR", designation="HR Manager",
            date_of_joining=date(2021, 3, 1), salary=95000.0,
            manager_name="System Admin", phone="9876543211", gender="female",
        ),
        Employee(
            emp_code="EMP003", name="Rahul Mehta", email="rahul.m@company.com",
            department="Engineering", designation="Engineering Manager",
            date_of_joining=date(2020, 6, 15), salary=140000.0,
            manager_name="System Admin", phone="9876543212", gender="male",
        ),
        Employee(
            emp_code="EMP004", name="Anita Desai", email="anita.d@company.com",
            department="Engineering", designation="Senior Developer",
            date_of_joining=date(2022, 1, 10), salary=110000.0,
            manager_name="Rahul Mehta", phone="9876543213", gender="female",
        ),
        Employee(
            emp_code="EMP005", name="Vikram Singh", email="vikram.s@company.com",
            department="Finance", designation="Financial Analyst",
            date_of_joining=date(2023, 4, 1), salary=75000.0,
            manager_name="System Admin", phone="9876543214", gender="male",
        ),
        # ── Additional employees for pagination testing ──
        Employee(
            emp_code="EMP006", name="Neha Gupta", email="neha.g@company.com",
            department="Engineering", designation="Frontend Developer",
            date_of_joining=date(2023, 7, 10), salary=85000.0,
            manager_name="Rahul Mehta", phone="9876543215", gender="female",
        ),
        Employee(
            emp_code="EMP007", name="Arjun Nair", email="arjun.n@company.com",
            department="Engineering", designation="Backend Developer",
            date_of_joining=date(2022, 11, 5), salary=92000.0,
            manager_name="Rahul Mehta", phone="9876543216", gender="male",
        ),
        Employee(
            emp_code="EMP008", name="Kavitha Rajan", email="kavitha.r@company.com",
            department="Marketing", designation="Marketing Manager",
            date_of_joining=date(2021, 8, 20), salary=105000.0,
            manager_name="System Admin", phone="9876543217", gender="female",
        ),
        Employee(
            emp_code="EMP009", name="Suresh Patil", email="suresh.p@company.com",
            department="Marketing", designation="Digital Marketing Specialist",
            date_of_joining=date(2024, 1, 15), salary=65000.0,
            manager_name="Kavitha Rajan", phone="9876543218", gender="male",
        ),
        Employee(
            emp_code="EMP010", name="Deepika Joshi", email="deepika.j@company.com",
            department="Finance", designation="Finance Manager",
            date_of_joining=date(2020, 9, 1), salary=120000.0,
            manager_name="System Admin", phone="9876543219", gender="female",
        ),
        Employee(
            emp_code="EMP011", name="Amit Kulkarni", email="amit.k@company.com",
            department="Finance", designation="Accounts Executive",
            date_of_joining=date(2023, 6, 12), salary=55000.0,
            manager_name="Deepika Joshi", phone="9876543220", gender="male",
        ),
        Employee(
            emp_code="EMP012", name="Sneha Iyer", email="sneha.i@company.com",
            department="HR", designation="HR Executive",
            date_of_joining=date(2024, 2, 1), salary=55000.0,
            manager_name="Priya Sharma", phone="9876543221", gender="female",
        ),
        Employee(
            emp_code="EMP013", name="Rajesh Kumar", email="rajesh.k@company.com",
            department="Operations", designation="Operations Manager",
            date_of_joining=date(2021, 5, 10), salary=110000.0,
            manager_name="System Admin", phone="9876543222", gender="male",
        ),
        Employee(
            emp_code="EMP014", name="Pooja Reddy", email="pooja.r@company.com",
            department="Operations", designation="Operations Executive",
            date_of_joining=date(2023, 9, 1), salary=50000.0,
            manager_name="Rajesh Kumar", phone="9876543223", gender="female",
        ),
        Employee(
            emp_code="EMP015", name="Mohammad Farhan", email="farhan.m@company.com",
            department="Sales", designation="Sales Manager",
            date_of_joining=date(2021, 1, 20), salary=100000.0,
            manager_name="System Admin", phone="9876543224", gender="male",
        ),
        Employee(
            emp_code="EMP016", name="Tanya Bose", email="tanya.b@company.com",
            department="Sales", designation="Sales Executive",
            date_of_joining=date(2024, 3, 5), salary=48000.0,
            manager_name="Mohammad Farhan", phone="9876543225", gender="female",
        ),
        Employee(
            emp_code="EMP017", name="Kiran Rao", email="kiran.r@company.com",
            department="Sales", designation="Business Development",
            date_of_joining=date(2023, 11, 15), salary=60000.0,
            manager_name="Mohammad Farhan", phone="9876543226", gender="male",
        ),
        Employee(
            emp_code="EMP018", name="Lakshmi Menon", email="lakshmi.m@company.com",
            department="Legal", designation="Legal Counsel",
            date_of_joining=date(2022, 4, 1), salary=130000.0,
            manager_name="System Admin", phone="9876543227", gender="female",
        ),
        Employee(
            emp_code="EMP019", name="Sanjay Verma", email="sanjay.v@company.com",
            department="IT", designation="System Administrator",
            date_of_joining=date(2023, 1, 10), salary=72000.0,
            manager_name="System Admin", phone="9876543228", gender="male",
        ),
        Employee(
            emp_code="EMP020", name="Meera Chopra", email="meera.c@company.com",
            department="Engineering", designation="QA Engineer",
            date_of_joining=date(2024, 5, 1), salary=68000.0,
            manager_name="Rahul Mehta", phone="9876543229", gender="female",
        ),
    ]
    await Employee.insert_many(employees)

    # ------------------------------------------------------------------
    # 3. Leave records
    # ------------------------------------------------------------------
    leaves = [
        LeaveRecord(
            emp_code="EMP004",
            leave_type="casual",
            start_date=date(2026, 1, 15),
            end_date=date(2026, 1, 17),
            reason="Family function",
            status="approved",
            approved_by="priya.hr@company.com",
        ),
        LeaveRecord(
            emp_code="EMP003",
            leave_type="sick",
            start_date=date(2026, 2, 5),
            end_date=date(2026, 2, 6),
            reason="Fever",
            status="approved",
            approved_by="admin@hrms.com",
        ),
        LeaveRecord(
            emp_code="EMP005",
            leave_type="earned",
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 14),
            reason="Vacation",
            status="pending",
        ),
        LeaveRecord(
            emp_code="EMP004",
            leave_type="sick",
            start_date=date(2026, 3, 20),
            end_date=date(2026, 3, 21),
            reason="Dental appointment",
            status="pending",
        ),
    ]
    await LeaveRecord.insert_many(leaves)

    # ------------------------------------------------------------------
    # 4. Attendance
    # ------------------------------------------------------------------
    attendance = [
        Attendance(emp_code="EMP001", date=date(2026, 3, 3), check_in="09:00", check_out="18:00", status="present"),
        Attendance(emp_code="EMP002", date=date(2026, 3, 3), check_in="09:15", check_out="17:45", status="present"),
        Attendance(emp_code="EMP003", date=date(2026, 3, 3), check_in="10:00", check_out="19:00", status="present"),
        Attendance(emp_code="EMP004", date=date(2026, 3, 3), check_in="09:30", check_out="18:30", status="present"),
        Attendance(emp_code="EMP005", date=date(2026, 3, 3), check_in="09:00", check_out="13:00", status="half-day"),
        Attendance(emp_code="EMP001", date=date(2026, 3, 4), check_in="09:00", check_out="18:00", status="present"),
        Attendance(emp_code="EMP002", date=date(2026, 3, 4), check_in="09:00", check_out="18:00", status="present"),
        Attendance(emp_code="EMP003", date=date(2026, 3, 4), status="absent"),
        Attendance(emp_code="EMP004", date=date(2026, 3, 4), check_in="08:45", check_out="17:30", status="present"),
        Attendance(emp_code="EMP005", date=date(2026, 3, 4), check_in="09:00", check_out="18:00", status="work-from-home"),
    ]
    await Attendance.insert_many(attendance)

    # ------------------------------------------------------------------
    # 5. Payroll (for all 20 employees)
    # ------------------------------------------------------------------
    payroll = [
        Payroll(emp_code="EMP001", month="2026-01", basic=120000, hra=36000, allowances=24000, deductions=18000, net_pay=162000),
        Payroll(emp_code="EMP002", month="2026-01", basic=60000, hra=19000, allowances=16000, deductions=9500, net_pay=85500),
        Payroll(emp_code="EMP003", month="2026-01", basic=90000, hra=28000, allowances=22000, deductions=14000, net_pay=126000),
        Payroll(emp_code="EMP004", month="2026-01", basic=72000, hra=22000, allowances=16000, deductions=11000, net_pay=99000),
        Payroll(emp_code="EMP005", month="2026-01", basic=48000, hra=15000, allowances=12000, deductions=7500, net_pay=67500),
        Payroll(emp_code="EMP006", month="2026-01", basic=56000, hra=17000, allowances=14000, deductions=8500, net_pay=78500),
        Payroll(emp_code="EMP007", month="2026-01", basic=60000, hra=18400, allowances=15000, deductions=9200, net_pay=84200),
        Payroll(emp_code="EMP008", month="2026-01", basic=70000, hra=21000, allowances=17000, deductions=10500, net_pay=97500),
        Payroll(emp_code="EMP009", month="2026-01", basic=42000, hra=13000, allowances=10000, deductions=6500, net_pay=58500),
        Payroll(emp_code="EMP010", month="2026-01", basic=80000, hra=24000, allowances=18000, deductions=12000, net_pay=110000),
        Payroll(emp_code="EMP011", month="2026-01", basic=36000, hra=11000, allowances=9000, deductions=5500, net_pay=50500),
        Payroll(emp_code="EMP012", month="2026-01", basic=36000, hra=11000, allowances=9000, deductions=5500, net_pay=50500),
        Payroll(emp_code="EMP013", month="2026-01", basic=72000, hra=22000, allowances=16000, deductions=11000, net_pay=99000),
        Payroll(emp_code="EMP014", month="2026-01", basic=32000, hra=10000, allowances=8000, deductions=5000, net_pay=45000),
        Payroll(emp_code="EMP015", month="2026-01", basic=66000, hra=20000, allowances=16000, deductions=10000, net_pay=92000),
        Payroll(emp_code="EMP016", month="2026-01", basic=30000, hra=9600, allowances=7800, deductions=4800, net_pay=42600),
        Payroll(emp_code="EMP017", month="2026-01", basic=40000, hra=12000, allowances=10000, deductions=6000, net_pay=56000),
        Payroll(emp_code="EMP018", month="2026-01", basic=86000, hra=26000, allowances=20000, deductions=13000, net_pay=119000),
        Payroll(emp_code="EMP019", month="2026-01", basic=48000, hra=14400, allowances=12000, deductions=7200, net_pay=67200),
        Payroll(emp_code="EMP020", month="2026-01", basic=44000, hra=13600, allowances=11000, deductions=6800, net_pay=61800),
        # February payroll
        Payroll(emp_code="EMP001", month="2026-02", basic=120000, hra=36000, allowances=24000, deductions=18000, net_pay=162000),
        Payroll(emp_code="EMP002", month="2026-02", basic=60000, hra=19000, allowances=16000, deductions=9500, net_pay=85500),
        Payroll(emp_code="EMP003", month="2026-02", basic=90000, hra=28000, allowances=22000, deductions=14000, net_pay=126000),
        Payroll(emp_code="EMP004", month="2026-02", basic=72000, hra=22000, allowances=16000, deductions=11000, net_pay=99000),
        Payroll(emp_code="EMP005", month="2026-02", basic=48000, hra=15000, allowances=12000, deductions=7500, net_pay=67500),
    ]
    await Payroll.insert_many(payroll)

    # ------------------------------------------------------------------
    # 6. Initial HR Policy (all config now lives in DB)
    # ------------------------------------------------------------------
    existing_policy = await HRPolicy.find_one(HRPolicy.is_active == True)
    if not existing_policy:
        initial_policy = HRPolicy(
            policy_name="India HR Policy — Maharashtra",
            state="maharashtra",
            is_metro=True,
            salary_breakup=SalaryBreakup(),       # uses model defaults (40% basic, etc.)
            leave_policy=LeavePolicy(),            # uses model defaults (12 CL, etc.)
            tax_regime="new",
            tax_slabs=INITIAL_TAX_SLABS_NEW_REGIME,
            old_regime_tax_slabs=INITIAL_TAX_SLABS_OLD_REGIME,
            standard_deduction=75000.0,
            old_regime_standard_deduction=50000.0,
            cess_pct=4.0,
            state_professional_tax=INITIAL_STATE_PROFESSIONAL_TAX,
            state_leave_overrides=INITIAL_STATE_LEAVE_OVERRIDES,
            is_active=True,
            version=1,
            created_by="admin@hrms.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await initial_policy.insert()
        logger.info("✅ Initial HR Policy v1 seeded into DB (all values now DB-managed).")

    logger.info("✅ Database seeded with %d employees, %d leave records, %d attendance, %d payroll entries.",
                len(employees), len(leaves), len(attendance), len(payroll))
