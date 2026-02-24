import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';
import { finalize } from 'rxjs/operators';

import { ApiService } from '../../../core/services/api.service';
import { ProfessionalDialogComponent } from './professional-dialog/professional-dialog.component';

@Component({
    selector: 'app-professionals',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDialogModule,
        MatSnackBarModule,
        MatChipsModule,
        MatProgressSpinnerModule,
        MatPaginatorModule,
        MatSortModule,
        MatTooltipModule
    ],
    templateUrl: './professionals.component.html',
    styleUrl: './professionals.component.scss'
})
export class ProfessionalsComponent implements OnInit, AfterViewInit {
    displayedColumns = ['name', 'email', 'registration_number', 'role', 'status', 'actions'];
    dataSource = new MatTableDataSource<any>([]);
    loading = false;
    searchQuery = '';
    roleFilter = '';

    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;

    constructor(
        private api: ApiService,
        private dialog: MatDialog,
        private snackBar: MatSnackBar,
        private route: ActivatedRoute,
    ) { }

    ngOnInit(): void {
        this.loadProfessionals();
    }

    ngAfterViewInit() {
        this.dataSource.paginator = this.paginator;
        this.dataSource.sort = this.sort;
    }

    loadProfessionals(): void {
        this.loading = true;
        const params: any = {};
        if (this.searchQuery) params.search = this.searchQuery;
        if (this.roleFilter) params.role = this.roleFilter;

        this.api.get<any>('/professionals/', params)
            .pipe(finalize(() => this.loading = false))
            .subscribe({
                next: (res) => {
                    this.dataSource.data = res.users || [];
                    if (this.paginator) {
                        this.paginator.firstPage();
                    }
                },
                error: (err) => {
                    this.snackBar.open('Erro ao carregar profissionais', 'Fechar', { duration: 3000 });
                }
            });
    }

    openDialog(professional?: any): void {
        const dialogRef = this.dialog.open(ProfessionalDialogComponent, {
            width: '800px',
            data: { professional },
            panelClass: 'glass-dialog-panel'
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadProfessionals();
            }
        });
    }

    toggleActive(professional: any): void {
        this.loading = true;
        this.api.put(`/users/${professional.id}`, { is_active: !professional.is_active })
            .pipe(finalize(() => this.loading = false))
            .subscribe({
                next: () => {
                    professional.is_active = !professional.is_active; // Optimistic update
                    this.snackBar.open(
                        `Profissional ${professional.is_active ? 'ativado' : 'desativado'} com sucesso!`,
                        'OK',
                        { duration: 2000 }
                    );
                },
                error: () => {
                    this.snackBar.open('Erro ao alterar status', 'Fechar', { duration: 3000 });
                }
            });
    }

    getRoleLabel(role: string): string {
        const labels: Record<string, string> = {
            superadmin: 'Super Admin',
            admin: 'Gestor',
            professor: 'Professor',
            coordenacao: 'Coordenação'
        };
        return labels[role] || role;
    }
}
