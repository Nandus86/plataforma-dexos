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
import { StudentDialogComponent } from './student-dialog/student-dialog.component';
import { StudentAcademicLifeComponent } from './student-academic-life/student-academic-life.component';

@Component({
    selector: 'app-students',
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
    templateUrl: './students.component.html',
    styleUrl: './students.component.scss'
})
export class StudentsComponent implements OnInit, AfterViewInit {
    displayedColumns = ['name', 'email', 'registration_number', 'status', 'actions'];
    dataSource = new MatTableDataSource<any>([]);
    loading = false;
    searchQuery = '';
    totalRecords = 0;
    pageSize = 25;

    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;

    constructor(
        private api: ApiService,
        private dialog: MatDialog,
        private snackBar: MatSnackBar,
        private route: ActivatedRoute,
    ) { }

    ngOnInit(): void {
        this.loadStudents();
    }

    ngAfterViewInit() {
        this.dataSource.sort = this.sort;
    }

    loadStudents(resetPage = true): void {
        this.loading = true;
        if (resetPage && this.paginator) {
            this.paginator.pageIndex = 0;
        }
        const skip = this.paginator ? this.paginator.pageIndex * this.paginator.pageSize : 0;
        const limit = this.paginator ? this.paginator.pageSize : this.pageSize;
        const params: any = { skip, limit };
        if (this.searchQuery) params.search = this.searchQuery;

        this.api.get<any>('/students/', params)
            .pipe(finalize(() => this.loading = false))
            .subscribe({
                next: (res) => {
                    this.dataSource.data = res.users || [];
                    this.totalRecords = res.total || 0;
                },
                error: (err) => {
                    this.snackBar.open('Erro ao carregar estudantes', 'Fechar', { duration: 3000 });
                }
            });
    }

    onPageChange(): void {
        this.loadStudents(false);
    }

    openDialog(student?: any): void {
        const dialogRef = this.dialog.open(StudentDialogComponent, {
            width: '800px',
            data: { student },
            panelClass: 'glass-dialog-panel'
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadStudents();
            }
        });
    }

    openHistoryDialog(student: any): void {
        this.dialog.open(StudentAcademicLifeComponent, {
            width: '800px',
            data: { user: student },
            panelClass: 'glass-dialog-panel'
        });
    }

    toggleActive(student: any): void {
        // Optional: Implement activate/deactivate similar to users, or proxy through /users/
        // If /students/{id} doesn't support changing is_active, we use /users/{id}
        this.loading = true;
        this.api.put(`/users/${student.id}`, { is_active: !student.is_active })
            .pipe(finalize(() => this.loading = false))
            .subscribe({
                next: () => {
                    student.is_active = !student.is_active; // Optimistic update
                    this.snackBar.open(
                        `Estudante ${student.is_active ? 'ativado' : 'desativado'} com sucesso!`,
                        'OK',
                        { duration: 2000 }
                    );
                },
                error: () => {
                    this.snackBar.open('Erro ao alterar status', 'Fechar', { duration: 3000 });
                }
            });
    }
}
