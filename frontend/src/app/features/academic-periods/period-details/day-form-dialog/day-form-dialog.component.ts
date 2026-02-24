
import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatSelectModule } from '@angular/material/select';
import { NonSchoolDay, ExtraSchoolDay, NonSchoolDayReason } from '../../../../core/models/academic-period.model';

@Component({
    selector: 'app-day-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatDatepickerModule,
        MatSelectModule
    ],
    template: `
        <h2 mat-dialog-title>
            Adicionar {{ data.type === 'non-school' ? 'Dia Sem Aula' : 'Dia Letivo Extra' }}
        </h2>
        <form [formGroup]="form" (ngSubmit)="onSubmit()">
            <mat-dialog-content>
                <div class="form-row">
                    <mat-form-field appearance="outline">
                        <mat-label>Data</mat-label>
                        <input matInput [matDatepicker]="picker" formControlName="date">
                        <mat-datepicker-toggle matIconSuffix [for]="picker"></mat-datepicker-toggle>
                        <mat-datepicker #picker></mat-datepicker>
                        <mat-error *ngIf="form.get('date')?.hasError('required')">Obrigatório</mat-error>
                    </mat-form-field>
                </div>

                <div class="form-row" *ngIf="data.type === 'non-school'">
                    <mat-form-field appearance="outline">
                        <mat-label>Motivo</mat-label>
                        <mat-select formControlName="reason">
                            <mat-option *ngFor="let reason of reasons" [value]="reason.value">
                                {{ reason.label }}
                            </mat-option>
                        </mat-select>
                        <mat-error *ngIf="form.get('reason')?.hasError('required')">Obrigatório</mat-error>
                    </mat-form-field>
                </div>

                <div class="form-row">
                    <mat-form-field appearance="outline">
                        <mat-label>Descrição</mat-label>
                        <input matInput formControlName="description">
                    </mat-form-field>
                </div>
            </mat-dialog-content>
            <mat-dialog-actions align="end">
                <button mat-button type="button" (click)="onCancel()">Cancelar</button>
                <button mat-raised-button color="primary" type="submit" [disabled]="form.invalid">Salvar</button>
            </mat-dialog-actions>
        </form>
    `,
    styles: [`
        .form-row { display: flex; flex-direction: column; gap: 16px; margin-bottom: 16px; }
        mat-form-field { width: 100%; }
    `]
})
export class DayFormDialogComponent {
    form: FormGroup;
    reasons = [
        { value: NonSchoolDayReason.HOLIDAY, label: 'Feriado' },
        { value: NonSchoolDayReason.RECESS, label: 'Recesso' },
        { value: NonSchoolDayReason.EVENT, label: 'Evento' },
        { value: NonSchoolDayReason.SATURDAY, label: 'Sábado' },
        { value: NonSchoolDayReason.SUNDAY, label: 'Domingo' },
        { value: NonSchoolDayReason.OTHER, label: 'Outro' }
    ];

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<DayFormDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: { type: 'non-school' | 'extra' }
    ) {
        this.form = this.fb.group({
            date: ['', Validators.required],
            description: [''],
            reason: [data.type === 'non-school' ? NonSchoolDayReason.HOLIDAY : null]
        });

        if (data.type === 'non-school') {
            this.form.get('reason')?.setValidators(Validators.required);
        }
    }

    onCancel(): void {
        this.dialogRef.close();
    }

    onSubmit(): void {
        if (this.form.valid) {
            const val = this.form.value;
            // Format date to ISO string (YYYY-MM-DD)
            const date = new Date(val.date);
            const dateStr = date.toISOString().split('T')[0];

            const result = {
                ...val,
                date: dateStr
            };
            this.dialogRef.close(result);
        }
    }
}
