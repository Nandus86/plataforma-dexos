import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';

@Component({
    selector: 'app-feature-manager',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatTableModule,
        MatCheckboxModule,
        MatSlideToggleModule,
        MatButtonModule,
        MatIconModule,
        MatSnackBarModule
    ],
    templateUrl: './feature-manager.component.html',
    styleUrls: ['./feature-manager.component.scss']
})
export class FeatureManagerComponent implements OnInit {
    features: any[] = [];
    featureGroups: { name: string; items: any[] }[] = [];
    displayedColumns: string[] = ['feature', 'enabled', 'superadmin', 'admin', 'coordenacao', 'professor', 'estudante'];
    loading = false;
    tenantId: string = '';

    constructor(
        private api: ApiService,
        private auth: AuthService,
        private snackBar: MatSnackBar
    ) { }

    ngOnInit(): void {
        const user = this.auth.currentUser;
        if (user && user.tenant_id) {
            this.tenantId = user.tenant_id;
            this.loadFeatures();
        } else {
            this.loadFirstTenant();
        }
    }

    loadFirstTenant() {
        this.api.get<any[]>('/tenants/').subscribe(tenants => {
            if (tenants.length > 0) {
                this.tenantId = tenants[0].id;
                this.loadFeatures();
            }
        });
    }


    loadFeatures(): void {
        this.loading = true;
        this.api.get<any>(`/tenants/${this.tenantId}/features`).subscribe({
            next: (res) => {
                this.features = Object.entries(res.features).map(([key, value]: [string, any]) => ({
                    key,
                    ...value
                }));

                // Group features by their group field
                const groupMap = new Map<string, any[]>();
                for (const f of this.features) {
                    const groupName = f.group || 'Geral';
                    if (!groupMap.has(groupName)) {
                        groupMap.set(groupName, []);
                    }
                    groupMap.get(groupName)!.push(f);
                }
                this.featureGroups = Array.from(groupMap.entries()).map(([name, items]) => ({ name, items }));

                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    toggleFeature(feature: any): void {
        // Logic handled by ngModel, trigger save or just wait for explicit save?
        // Let's autosave or manual save. Manual is safer (simpler).
    }

    toggleRole(feature: any, role: string): void {
        const index = feature.roles.indexOf(role);
        if (index === -1) {
            feature.roles.push(role);
        } else {
            feature.roles.splice(index, 1);
        }
    }

    hasRole(feature: any, role: string): boolean {
        return feature.roles.includes(role);
    }

    save(): void {
        this.loading = true;
        const payload = {
            features: this.features.reduce((acc, curr) => {
                acc[curr.key] = {
                    label: curr.label,
                    description: curr.description,
                    group: curr.group || '',
                    locked: curr.locked,
                    enabled: curr.enabled,
                    roles: curr.roles
                };
                return acc;
            }, {} as any)
        };

        this.api.put(`/tenants/${this.tenantId}/features`, payload).subscribe({
            next: () => {
                this.snackBar.open('Permissões atualizadas com sucesso!', 'OK', { duration: 3000 });
                this.loading = false;
            },
            error: () => {
                this.snackBar.open('Erro ao salvar permissões', 'Fechar', { duration: 3000 });
                this.loading = false;
            }
        });
    }
}
