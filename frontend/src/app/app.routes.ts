import { Routes } from '@angular/router';
import { AuthGuard } from './core/guards/auth.guard';
import { RoleGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
        path: 'login',
        loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent),
    },
    {
        path: '',
        loadComponent: () => import('./shared/layout/layout.component').then(m => m.LayoutComponent),
        canActivate: [AuthGuard],
        children: [
            {
                path: 'dashboard',
                loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
            },
            {
                path: 'students',
                loadComponent: () => import('./features/admin/students/students.component').then(m => m.StudentsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'staff',
                loadComponent: () => import('./features/admin/professionals/professionals.component').then(m => m.ProfessionalsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin'] },
            },
            {
                path: 'tenants',
                loadComponent: () => import('./features/admin/tenants/tenants.component').then(m => m.TenantsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin'] },
            },
            {
                path: 'institution',
                loadComponent: () => import('./features/admin/institution/institution').then(m => m.Institution),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin'] },
            },
            {
                path: 'features',
                loadComponent: () => import('./features/admin/feature-manager/feature-manager.component').then(m => m.FeatureManagerComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin'] },
            },
            {
                path: 'courses',
                loadComponent: () => import('./features/courses/courses.component').then(m => m.CoursesComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'subjects',
                loadComponent: () => import('./features/courses/subjects/subjects.component').then(m => m.SubjectsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'matrices',
                loadComponent: () => import('./features/academic/matrices/matrices.component').then(m => m.MatricesComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'academic-periods',
                loadComponent: () => import('./features/academic-periods/academic-periods.component').then(m => m.AcademicPeriodsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'academic-periods/:id',
                loadComponent: () => import('./features/academic-periods/period-details/period-details.component').then(m => m.PeriodDetailsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'class-groups',
                loadComponent: () => import('./features/class-groups/class-groups.component').then(m => m.ClassGroupsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'grades',
                loadComponent: () => import('./features/academic/grades/grades.component').then(m => m.GradesComponent),
            },
            {
                path: 'attendance',
                loadComponent: () => import('./features/academic/attendance/attendance.component').then(m => m.AttendanceComponent),
            },
            {
                path: 'assignments',
                loadComponent: () => import('./features/assignments/assignments.component').then(m => m.AssignmentsComponent),
            },
            {
                path: 'occurrences',
                loadComponent: () => import('./features/occurrences/occurrences.component').then(m => m.OccurrencesComponent),
            },
            {
                path: 'materials',
                loadComponent: () => import('./features/content/materials/materials.component').then(m => m.MaterialsComponent),
            },
            {
                path: 'lesson-plans',
                loadComponent: () => import('./features/content/lesson-plans/lesson-plans.component').then(m => m.LessonPlansComponent),
            },
            {
                path: 'announcements',
                loadComponent: () => import('./features/announcements/announcements.component').then(m => m.AnnouncementsComponent),
            },
            {
                path: 'enrollments',
                loadComponent: () => import('./features/enrollments/enrollments.component').then(m => m.EnrollmentsComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'coordination',
                loadComponent: () => import('./features/coordination/coordination.component').then(m => m.CoordinationComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: 'export',
                loadComponent: () => import('./features/export/export.component').then(m => m.ExportComponent),
                canActivate: [RoleGuard],
                data: { roles: ['superadmin', 'admin', 'coordenacao'] },
            },
            {
                path: '',
                redirectTo: 'dashboard',
                pathMatch: 'full',
            },
        ],
    },
    { path: '**', redirectTo: 'login' },
];

