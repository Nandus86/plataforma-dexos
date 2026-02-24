import { Component, OnInit, ViewChild, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatSidenavModule, MatSidenav } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';
import { MatTooltipModule } from '@angular/material/tooltip';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { AuthService, UserInfo } from '../../core/services/auth.service';
import { ApiService } from '../../core/services/api.service';
import { ThemeService } from '../../core/services/theme.service';
import { environment } from '../../../environments/environment';

interface NavItem {
    label: string;
    icon: string;
    route: string;
    roles: string[];
    featureKey?: string;
}

interface NavGroup {
    label: string;
    icon: string;
    expanded: boolean;
    items: NavItem[];
    roles: string[];
}

@Component({
    selector: 'app-layout',
    standalone: true,
    imports: [
        CommonModule, RouterModule,
        MatSidenavModule, MatToolbarModule, MatListModule,
        MatIconModule, MatButtonModule, MatMenuModule,
        MatDividerModule, MatTooltipModule,
    ],
    templateUrl: './layout.component.html',
    styleUrls: ['./layout.component.scss'],
})
export class LayoutComponent implements OnInit {
    @ViewChild('sidenav') sidenav!: MatSidenav;

    appName = environment.appName;
    appSubtitle = environment.appSubtitle;
    isMobile = false;
    sidebarCollapsed = false;

    // FIX: Initialize user synchronously from localStorage to avoid loading race condition
    user: UserInfo | null = null;
    features: any = {};
    loadingFeatures = false;

    // Dashboard is top-level (not grouped)
    dashboardItem: NavItem = {
        label: 'Dashboard', icon: 'dashboard', route: '/dashboard',
        roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'],
    };

    appVersion: string = '';


    navGroups: NavGroup[] = [
        {
            label: 'Cadastros', icon: 'app_registration', expanded: false,
            roles: ['superadmin', 'admin', 'coordenacao'],
            items: [
                { label: 'Estudantes', icon: 'school', route: '/students', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'users' },
                { label: 'Funcionários', icon: 'badge', route: '/staff', roles: ['superadmin', 'admin'], featureKey: 'users' },
                { label: 'Período Letivo', icon: 'calendar_month', route: '/academic-periods', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'courses' },
                { label: 'Cursos', icon: 'menu_book', route: '/courses', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'courses' },
                { label: 'Disciplinas', icon: 'class', route: '/subjects', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'courses' },
                { label: 'Turmas', icon: 'groups', route: '/class-groups', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'courses' },
            ],
        },
        {
            label: 'Acadêmico', icon: 'cast_for_education', expanded: false,
            roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'],
            items: [
                { label: 'Matrículas', icon: 'how_to_reg', route: '/enrollments', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'academic' },
                { label: 'Matrizes Curriculares', icon: 'view_agenda', route: '/matrices', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'academic' },
                { label: 'Notas', icon: 'grade', route: '/grades', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'grades' },
                { label: 'Frequência', icon: 'event_available', route: '/attendance', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'attendance' },
                { label: 'Tarefas', icon: 'assignment', route: '/assignments', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'assignments' },
                { label: 'Ocorrências', icon: 'report', route: '/occurrences', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'occurrences' },
            ],
        },
        {
            label: 'Conteúdo', icon: 'library_books', expanded: false,
            roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'],
            items: [
                { label: 'Materiais', icon: 'folder_open', route: '/materials', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'materials' },
                { label: 'Planos de Aula', icon: 'description', route: '/lesson-plans', roles: ['superadmin', 'admin', 'coordenacao', 'professor'], featureKey: 'lesson_plans' },
                { label: 'Avisos', icon: 'campaign', route: '/announcements', roles: ['superadmin', 'admin', 'coordenacao', 'professor', 'estudante'], featureKey: 'announcements' },
            ],
        },
        {
            label: 'Pedagógico', icon: 'psychology', expanded: false,
            roles: ['superadmin', 'admin', 'coordenacao'],
            items: [
                { label: 'Coord. Pedagógica', icon: 'supervisor_account', route: '/coordination', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'reports' },
                { label: 'Exportar Dados', icon: 'download', route: '/export', roles: ['superadmin', 'admin', 'coordenacao'], featureKey: 'export' },
            ],
        },
        {
            label: 'Sistema', icon: 'settings', expanded: false,
            roles: ['superadmin', 'admin'],
            items: [
                { label: 'Minha Instituição', icon: 'account_balance', route: '/institution', roles: ['superadmin', 'admin'], featureKey: 'settings' },
                { label: 'Instituições', icon: 'business', route: '/tenants', roles: ['superadmin'], featureKey: 'settings' },
                { label: 'Gerenciar Acesso', icon: 'security', route: '/features', roles: ['superadmin'], featureKey: 'settings' },
            ],
        },
    ];

    constructor(
        public auth: AuthService,
        private api: ApiService,
        private router: Router,
        private breakpointObserver: BreakpointObserver,
        public themeService: ThemeService,
        private cdr: ChangeDetectorRef
    ) {
        // FIX: Immediately load user from auth service (synchronous from localStorage)
        // This prevents the first-click loading issue where filteredNavGroups returns []
        this.user = this.auth.currentUser;

        // Restore collapsed state
        const collapsed = localStorage.getItem('sidebar_collapsed');
        this.sidebarCollapsed = collapsed === 'true';
    }

    ngOnInit(): void {
        // Fetch app version
        this.api.get<any>('/health/version').subscribe({
            next: (res) => {
                if (res && res.version) {
                    this.appVersion = res.version;
                }
            }
        });

        // Keep reactive subscription for updates (e.g., after login or refreshUser)
        this.auth.currentUser$.subscribe(user => {
            this.user = user;
            if (this.user?.tenant_id) {
                this.loadFeatures();
            }
        });

        this.breakpointObserver.observe([Breakpoints.Handset]).subscribe(result => {
            this.isMobile = result.matches;
            if (this.isMobile) {
                this.sidebarCollapsed = false;
            }
            this.cdr.detectChanges();
        });
    }

    loadFeatures() {
        if (!this.user?.tenant_id) return;

        this.loadingFeatures = true;
        this.api.get<any>(`/tenants/${this.user.tenant_id}/features`).subscribe({
            next: (res) => {
                if (res && res.features) {
                    this.features = res.features;
                }
                this.loadingFeatures = false;
            },
            error: () => {
                this.loadingFeatures = false;
            }
        });
    }

    get filteredNavGroups(): NavGroup[] {
        if (!this.user) return [];

        // Return original group references (not copies) to preserve expanded state
        return this.navGroups.filter(group => {
            if (!group.roles.some(r => r === this.user!.role)) return false;
            // Check if at least one item is visible
            return group.items.some(item => this.isItemVisible(item));
        });
    }

    getVisibleItems(group: NavGroup): NavItem[] {
        return group.items.filter(item => this.isItemVisible(item));
    }

    get showDashboard(): boolean {
        return !!this.user && this.dashboardItem.roles.includes(this.user.role);
    }

    private isItemVisible(item: NavItem): boolean {
        if (!this.user) return false;
        if (!item.roles.includes(this.user.role)) return false;

        if (this.user.role === 'superadmin') return true;

        if (item.featureKey) {
            // Se as features ainda não carregaram, esconde os itens com featureKey
            if (Object.keys(this.features).length === 0) return false;

            const feature = this.features[item.featureKey];
            if (!feature) return false; // Se não existe a feature, esconde
            if (!feature.enabled) return false;
            if (feature.roles && !feature.roles.includes(this.user.role)) return false;
        }

        return true;
    }

    get roleLabel(): string {
        const labels: Record<string, string> = {
            superadmin: 'Super Admin',
            admin: 'Gestor',
            coordenacao: 'Coordenação',
            professor: 'Professor',
            estudante: 'Estudante',
        };
        return labels[this.user?.role || ''] || '';
    }

    toggleSidebar(): void {
        if (this.isMobile) {
            this.sidenav.toggle();
        } else {
            this.sidebarCollapsed = !this.sidebarCollapsed;
            localStorage.setItem('sidebar_collapsed', String(this.sidebarCollapsed));
        }
    }

    toggleGroup(group: NavGroup): void {
        if (this.sidebarCollapsed && !this.isMobile) {
            // If sidebar is collapsed, expand it first
            this.sidebarCollapsed = false;
            localStorage.setItem('sidebar_collapsed', 'false');
            group.expanded = true;
        } else {
            group.expanded = !group.expanded;
        }
    }

    onNavClick(): void {
        // Collapse all groups after navigation for a cleaner look
        if (this.isMobile) {
            this.sidenav.close();
        }
    }

    toggleTheme(): void {
        this.themeService.toggleTheme();
    }

    logout(): void {
        this.auth.logout();
    }
}
