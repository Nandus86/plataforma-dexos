
import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { ClassSchedule } from '../../../../core/models/academic-period.model';

@Component({
    selector: 'app-class-schedule-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule
    ],
    template: `
        <h2 mat-dialog-title>{{ data.schedule ? 'Editar' : 'Adicionar' }} Horário de Aula</h2>
        <form [formGroup]="form" (ngSubmit)="onSubmit()">
            <mat-dialog-content>
                <div class="form-row">
                    <mat-form-field appearance="outline">
                        <mat-label>Ordem (Ex: 1 para 1ª aula)</mat-label>
                        <input matInput type="number" formControlName="order" min="1">
                        <mat-error *ngIf="form.get('order')?.hasError('required')">Obrigatório</mat-error>
                    </mat-form-field>
                </div>

                <div class="form-row">
                    <mat-form-field appearance="outline">
                        <mat-label>Horário Início (HH:mm)</mat-label>
                        <input matInput type="time" formControlName="start_time">
                        <mat-error *ngIf="form.get('start_time')?.hasError('required')">Obrigatório</mat-error>
                    </mat-form-field>

                    <mat-form-field appearance="outline">
                        <mat-label>Horário Fim (HH:mm)</mat-label>
                        <input matInput type="time" formControlName="end_time">
                        <mat-error *ngIf="form.get('end_time')?.hasError('required')">Obrigatório</mat-error>
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
        .form-row { display: flex; gap: 16px; }
        mat-form-field { width: 100%; }
    `]
})
export class ClassScheduleDialogComponent {
    form: FormGroup;

    constructor(
        private fb: FormBuilder,
        public dialogRef: MatDialogRef<ClassScheduleDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: { schedule?: ClassSchedule }
    ) {
        this.form = this.fb.group({
            order: [data.schedule?.order || '', Validators.required],
            start_time: [data.schedule?.start_time || '', Validators.required],
            end_time: [data.schedule?.end_time || '', Validators.required]
        });
    }

    onCancel(): void {
        this.dialogRef.close();
    }

    onSubmit(): void {
        if (this.form.valid) {
            this.dialogRef.close(this.form.value);
        }
    }
}
