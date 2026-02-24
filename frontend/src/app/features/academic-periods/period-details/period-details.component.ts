import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { AcademicPeriodService } from '../../../core/services/academic-period.service';
import { AcademicPeriod, PeriodStatistics, ClassSchedule, NonSchoolDay, ExtraSchoolDay } from '../../../core/models/academic-period.model';
import { ClassScheduleDialogComponent } from './class-schedule-dialog/class-schedule-dialog.component';
import { DayFormDialogComponent } from './day-form-dialog/day-form-dialog.component';

@Component({
    selector: 'app-period-details',
    standalone: true,
    imports: [
        CommonModule,
        MatTabsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatDialogModule
    ],
    templateUrl: './period-details.component.html',
    styleUrls: ['./period-details.component.scss']
})
export class PeriodDetailsComponent implements OnInit {
    period: AcademicPeriod | null = null;
    statistics: PeriodStatistics | null = null;
    loading = true;
    periodId: string = '';

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private periodService: AcademicPeriodService,
        private snackBar: MatSnackBar,
        private dialog: MatDialog
    ) { }

    ngOnInit(): void {
        this.periodId = this.route.snapshot.paramMap.get('id') || '';
        if (this.periodId) {
            this.loadPeriodDetails();
        }
    }

    loadPeriodDetails(): void {
        this.loading = true;

        this.periodService.getAcademicPeriod(this.periodId).subscribe({
            next: (period) => {
                this.period = period;
                this.loadStatistics();
            },
            error: (error) => {
                console.error('Error loading period:', error);
                this.snackBar.open('Erro ao carregar período', 'Fechar', { duration: 3000 });
                this.loading = false;
            }
        });
    }

    loadStatistics(): void {
        this.periodService.getPeriodStatistics(this.periodId).subscribe({
            next: (stats) => {
                this.statistics = stats;
                this.loading = false;
            },
            error: (error) => {
                console.error('Error loading statistics:', error);
                this.loading = false;
            }
        });
    }

    goBack(): void {
        this.router.navigate(['/academic-periods']);
    }

    formatDate(dateStr: string): string {
        if (!dateStr) return '';
        // Handle both ISO string and simple date string
        const date = new Date(dateStr);
        // Ajuste de fuso horário simples para exibição correta da data (evitar dia anterior)
        // Como o backend manda YYYY-MM-DD, o browser pode interpretar como UTC e subtrair fuso
        // Melhor usar split se for YYYY-MM-DD puro ou UTC
        if (dateStr.length === 10) {
            const [y, m, d] = dateStr.split('-');
            return `${d}/${m}/${y}`;
        }
        return date.toLocaleDateString('pt-BR');
    }

    getBreakTypeLabel(type: string): string {
        return this.periodService.getBreakTypeLabel(type);
    }

    // ============ Management Methods ============

    openScheduleDialog(schedule?: ClassSchedule): void {
        const dialogRef = this.dialog.open(ClassScheduleDialogComponent, {
            width: '400px',
            data: { schedule }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                if (schedule) {
                    this.periodService.updateClassSchedule(schedule.id, result).subscribe({
                        next: () => {
                            this.snackBar.open('Horário atualizado', 'OK', { duration: 3000 });
                            this.loadPeriodDetails();
                        },
                        error: (err) => this.snackBar.open('Erro ao atualizar horário', 'Fechar', { duration: 3000 })
                    });
                } else {
                    this.periodService.addClassSchedule(this.periodId, result).subscribe({
                        next: () => {
                            this.snackBar.open('Horário adicionado', 'OK', { duration: 3000 });
                            this.loadPeriodDetails();
                        },
                        error: (err) => this.snackBar.open('Erro ao adicionar horário', 'Fechar', { duration: 3000 })
                    });
                }
            }
        });
    }

    deleteSchedule(schedule: ClassSchedule): void {
        if (confirm(`Remover ${schedule.order}ª aula?`)) {
            this.periodService.deleteClassSchedule(schedule.id).subscribe({
                next: () => {
                    this.snackBar.open('Horário removido', 'OK', { duration: 3000 });
                    this.loadPeriodDetails();
                },
                error: (err) => this.snackBar.open('Erro ao remover horário', 'Fechar', { duration: 3000 })
            });
        }
    }

    openDayDialog(type: 'non-school' | 'extra'): void {
        const dialogRef = this.dialog.open(DayFormDialogComponent, {
            width: '400px',
            data: { type }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                if (type === 'non-school') {
                    this.periodService.addNonSchoolDay(this.periodId, result).subscribe({
                        next: () => {
                            this.snackBar.open('Dia sem aula adicionado', 'OK', { duration: 3000 });
                            this.loadPeriodDetails();
                        },
                        error: (err) => this.snackBar.open('Erro ao adicionar dia', 'Fechar', { duration: 3000 })
                    });
                } else {
                    this.periodService.addExtraSchoolDay(this.periodId, result).subscribe({
                        next: () => {
                            this.snackBar.open('Dia extra adicionado', 'OK', { duration: 3000 });
                            this.loadPeriodDetails();
                        },
                        error: (err) => this.snackBar.open('Erro ao adicionar dia extra', 'Fechar', { duration: 3000 })
                    });
                }
            }
        });
    }

    deleteNonSchoolDay(day: NonSchoolDay): void {
        if (confirm('Remover este dia sem aula?')) {
            this.periodService.deleteNonSchoolDay(day.id).subscribe({
                next: () => {
                    this.snackBar.open('Dia removido', 'OK', { duration: 3000 });
                    this.loadPeriodDetails();
                },
                error: (err) => this.snackBar.open('Erro ao remover dia', 'Fechar', { duration: 3000 })
            });
        }
    }

    deleteExtraDay(day: ExtraSchoolDay): void {
        if (confirm('Remover este dia extra?')) {
            this.periodService.deleteExtraSchoolDay(day.id).subscribe({
                next: () => {
                    this.snackBar.open('Dia extra removido', 'OK', { duration: 3000 });
                    this.loadPeriodDetails();
                },
                error: (err) => this.snackBar.open('Erro ao remover dia extra', 'Fechar', { duration: 3000 })
            });
        }
    }

    importHolidays(): void {
        if (confirm('Deseja importar os feriados nacionais (Brasil) para este ano?')) {
            this.periodService.importHolidays(this.periodId).subscribe({
                next: (res) => {
                    this.snackBar.open(res.message || 'Feriados importados', 'OK', { duration: 3000 });
                    this.loadPeriodDetails();
                },
                error: (err) => this.snackBar.open('Erro ao importar feriados', 'Fechar', { duration: 3000 })
            });
        }
    }
}
