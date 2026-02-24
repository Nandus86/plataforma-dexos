import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { AcademicPeriodService } from '../../core/services/academic-period.service';
import { AcademicPeriod } from '../../core/models/academic-period.model';
import { PeriodFormDialogComponent } from './period-form-dialog/period-form-dialog.component';

@Component({
    selector: 'app-academic-periods',
    standalone: true,
    imports: [
        CommonModule,
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        MatChipsModule,
        MatDialogModule,
        MatSnackBarModule
    ],
    templateUrl: './academic-periods.component.html',
    styleUrls: ['./academic-periods.component.scss']
})
export class AcademicPeriodsComponent implements OnInit {
    periods: AcademicPeriod[] = [];
    loading = false;
    displayedColumns = ['name', 'year', 'dates', 'break_type', 'classes_per_day', 'status', 'actions'];

    constructor(
        private periodService: AcademicPeriodService,
        private dialog: MatDialog,
        private snackBar: MatSnackBar,
        private router: Router,
        private cdr: ChangeDetectorRef
    ) { }

    ngOnInit(): void {
        this.loadPeriods();
    }

    loadPeriods(): void {
        this.loading = true;
        this.periodService.getAcademicPeriods().subscribe({
            next: (periods) => {
                this.periods = periods;
                this.loading = false;
                this.cdr.detectChanges();
            },
            error: (error) => {
                console.error('Error loading periods:', error);
                this.snackBar.open('Erro ao carregar períodos letivos', 'Fechar', { duration: 3000 });
                this.loading = false;
                this.cdr.detectChanges();
            }
        });
    }

    openCreateDialog(): void {
        const dialogRef = this.dialog.open(PeriodFormDialogComponent, {
            width: '600px',
            panelClass: 'glass-dialog-panel',
            data: { mode: 'create' }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadPeriods();
            }
        });
    }

    openEditDialog(period: AcademicPeriod): void {
        const dialogRef = this.dialog.open(PeriodFormDialogComponent, {
            width: '600px',
            panelClass: 'glass-dialog-panel',
            data: { mode: 'edit', period }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadPeriods();
            }
        });
    }

    viewDetails(period: AcademicPeriod): void {
        this.router.navigate(['/academic-periods', period.id]);
    }

    deletePeriod(period: AcademicPeriod): void {
        if (confirm(`Tem certeza que deseja excluir o período "${period.name}"?`)) {
            this.periodService.deleteAcademicPeriod(period.id).subscribe({
                next: () => {
                    this.snackBar.open('Período excluído com sucesso', 'Fechar', { duration: 3000 });
                    this.loadPeriods();
                },
                error: (error) => {
                    console.error('Error deleting period:', error);
                    const message = error.error?.detail || 'Erro ao excluir período';
                    this.snackBar.open(message, 'Fechar', { duration: 5000 });
                }
            });
        }
    }

    getBreakTypeLabel(type: string): string {
        return this.periodService.getBreakTypeLabel(type);
    }

    formatDate(dateStr: string): string {
        return new Date(dateStr).toLocaleDateString('pt-BR');
    }
}
