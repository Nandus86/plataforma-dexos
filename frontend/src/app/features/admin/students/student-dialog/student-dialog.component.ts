import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

import { ApiService } from '../../../../core/services/api.service';

@Component({
    selector: 'app-student-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatSnackBarModule,
        MatTabsModule,
        MatDatepickerModule,
        MatNativeDateModule
    ],
    templateUrl: './student-dialog.component.html',
    styleUrls: ['./student-dialog.component.scss']
})
export class StudentDialogComponent implements OnInit {
    form!: FormGroup;
    loading = false;
    isEditing = false;

    constructor(
        private fb: FormBuilder,
        private api: ApiService,
        private snackBar: MatSnackBar,
        public dialogRef: MatDialogRef<StudentDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: any
    ) {
        this.isEditing = !!data.student;
        this.initForm();
    }

    ngOnInit(): void {
        if (this.isEditing) {
            this.loadFullProfile(this.data.student.id);
        }
    }

    loadFullProfile(id: string) {
        this.loading = true;
        this.api.get<any>(`/students/${id}`).subscribe({
            next: (fullData) => {
                this.patchForm(fullData);
                this.loading = false;
            },
            error: () => {
                this.snackBar.open('Erro ao carregar dados do estudante', 'X');
                this.loading = false;
                this.dialogRef.close();
            }
        });
    }

    initForm() {
        this.form = this.fb.group({
            // Base User Fields
            name: ['', [Validators.required]],
            email: ['', [Validators.required, Validators.email]],
            password: ['', this.isEditing ? [] : [Validators.required, Validators.minLength(6)]],
            registration_number: [''],
            phone: [''],

            // Profile Fields
            profile: this.fb.group({
                cpf: [''],
                rg: [''],
                birth_date: [''],
                gender: [''],
                race: [''],
                marital_status: [''],
                cell_phone: [''],

                zip_code: [''],
                address_line: [''],
                address_number: [''],
                address_complement: [''],
                neighborhood: [''],
                city: [''],
                state: [''],

                naturalness: [''],
                religion: [''],
                profession: [''],
                education_level: [''],

                father_name: [''],
                mother_name: [''],
                spouse_name: ['']
            })
        });
    }

    patchForm(fullData: any) {
        this.form.patchValue({
            name: fullData.name,
            email: fullData.email,
            registration_number: fullData.registration_number,
            phone: fullData.phone,
            password: '', // do not set password if editing
        });

        if (fullData.student_profile) {
            this.form.get('profile')?.patchValue({
                cpf: fullData.student_profile.cpf,
                rg: fullData.student_profile.rg,
                birth_date: fullData.student_profile.birth_date,
                gender: fullData.student_profile.gender,
                race: fullData.student_profile.race,
                marital_status: fullData.student_profile.marital_status,
                cell_phone: fullData.student_profile.cell_phone,

                zip_code: fullData.student_profile.zip_code,
                address_line: fullData.student_profile.address_line,
                address_number: fullData.student_profile.address_number,
                address_complement: fullData.student_profile.address_complement,
                neighborhood: fullData.student_profile.neighborhood,
                city: fullData.student_profile.city,
                state: fullData.student_profile.state,

                naturalness: fullData.student_profile.naturalness,
                religion: fullData.student_profile.religion,
                profession: fullData.student_profile.profession,
                education_level: fullData.student_profile.education_level,

                father_name: fullData.student_profile.father_name,
                mother_name: fullData.student_profile.mother_name,
                spouse_name: fullData.student_profile.spouse_name
            });
        }
    }

    save(): void {
        if (this.form.invalid) return;

        this.loading = true;
        const formData = this.form.value;

        // Clean up password if editing and empty
        if (this.isEditing && !formData.password) {
            delete formData.password;
        }

        // Format dates and clean empty strings
        if (formData.profile) {
            Object.keys(formData.profile).forEach(key => {
                if (formData.profile[key] === '' || formData.profile[key] === null) {
                    delete formData.profile[key];
                }
            });

            if (formData.profile.birth_date) {
                const d = new Date(formData.profile.birth_date);
                if (!isNaN(d.getTime())) {
                    formData.profile.birth_date = d.toISOString().split('T')[0];
                } else {
                    delete formData.profile.birth_date;
                }
            }
        }

        const request$ = this.isEditing
            ? this.api.put(`/students/${this.data.student.id}`, formData)
            : this.api.post('/students/', formData);

        request$.subscribe({
            next: () => {
                this.snackBar.open(
                    `Estudante ${this.isEditing ? 'atualizado' : 'criado'} com sucesso!`,
                    'OK',
                    { duration: 3000 }
                );
                this.dialogRef.close(true);
            },
            error: (err) => {
                this.loading = false;
                let errMsg = 'Erro ao salvar estudante';
                if (err?.error?.detail) {
                    if (Array.isArray(err.error.detail)) {
                        errMsg = err.error.detail.map((e: any) => e.msg).join(', ');
                    } else if (typeof err.error.detail === 'string') {
                        errMsg = err.error.detail;
                    } else {
                        errMsg = JSON.stringify(err.error.detail);
                    }
                }

                this.snackBar.open(errMsg, 'Fechar', { duration: 3000 });
            }
        });
    }

    close(): void {
        this.dialogRef.close();
    }
}
