import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AcademicPeriodService } from '../../../core/services/academic-period.service';
import { AcademicPeriod, BreakType } from '../../../core/models/academic-period.model';

@Component({
    selector: 'app-period-form-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule,
        MatButtonModule,
        MatCheckboxModule,
        MatSnackBarModule
    ],
    templateUrl: './period-form-dialog.component.html',
    styleUrls: ['./period-form-dialog.component.scss']
})
export class PeriodFormDialogComponent implements OnInit {
    form!: FormGroup;
    isEditMode = false;
    loading = false;

    breakTypes = [
        { value: BreakType.MONTHLY, label: 'Mensal' },
        { value: BreakType.BIMONTHLY, label: 'Bimestral' },
        { value: BreakType.QUARTERLY, label: 'Trimestral' },
        { value: BreakType.FOURMONTHLY, label: 'Quadrimestral' },
        { value: BreakType.SEMIANNUAL, label: 'Semestral' },
        { value: BreakType.ANNUAL, label: 'Anual' }
    ];

    constructor(
        private fb: FormBuilder,
        private periodService: AcademicPeriodService,
        private snackBar: MatSnackBar,
        public dialogRef: MatDialogRef<PeriodFormDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: { mode: 'create' | 'edit', period?: AcademicPeriod }
    ) { }

    ngOnInit(): void {
        this.isEditMode = this.data.mode === 'edit';
        this.buildForm();

        if (this.isEditMode && this.data.period) {
            this.form.patchValue({
                name: this.data.period.name,
                year: this.data.period.year,
                break_type: this.data.period.break_type,
                start_date: new Date(this.data.period.start_date),
                end_date: new Date(this.data.period.end_date),
                classes_per_day: this.data.period.classes_per_day,
                is_active: this.data.period.is_active
            });
        }
    }

    buildForm(): void {
        const currentYear = new Date().getFullYear();

        this.form = this.fb.group({
            name: ['', [Validators.required, Validators.maxLength(255)]],
            year: [currentYear, [Validators.required, Validators.min(2000), Validators.max(2100)]],
            break_type: [BreakType.SEMIANNUAL, Validators.required],
            start_date: ['', Validators.required],
            end_date: ['', Validators.required],
            classes_per_day: [1, [Validators.required, Validators.min(1), Validators.max(10)]],
            is_active: [true]
        });
    }

    onSubmit(): void {
        if (this.form.invalid) {
            this.form.markAllAsTouched();
            console.log('Form invalid:', this.form.value);
            console.log('Errors:', this.form.errors);
            Object.keys(this.form.controls).forEach(key => {
                const controlErrors = this.form.get(key)?.errors;
                if (controlErrors) {
                    console.log(`Control ${key} errors:`, controlErrors);
                }
            });
            this.snackBar.open('Formulário inválido. Verifique os campos em vermelho.', 'Fechar', { duration: 3000 });
            return;
        }

        this.loading = true;
        const formData = this.form.value;

        // Convert dates to ISO string format
        const data = {
            ...formData,
            start_date: this.formatDate(formData.start_date),
            end_date: this.formatDate(formData.end_date)
        };

        const request = this.isEditMode && this.data.period
            ? this.periodService.updateAcademicPeriod(this.data.period.id, data)
            : this.periodService.createAcademicPeriod(data);

        request.subscribe({
            next: () => {
                const message = this.isEditMode
                    ? 'Período atualizado com sucesso'
                    : 'Período criado com sucesso';
                this.snackBar.open(message, 'Fechar', { duration: 3000 });
                this.dialogRef.close(true);
            },
            error: (error) => {
                console.error('Error saving period:', error);
                const message = error.error?.detail || 'Erro ao salvar período';
                this.snackBar.open(message, 'Fechar', { duration: 5000 });
                this.loading = false;
            }
        });
    }

    onCancel(): void {
        this.dialogRef.close(false);
    }

    private formatDate(date: Date): string {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    get title(): string {
        return this.isEditMode ? 'Editar Período Letivo' : 'Novo Período Letivo';
    }
}
