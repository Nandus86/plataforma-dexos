import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { finalize } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';

@Component({
    selector: 'app-change-password-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatSnackBarModule,
        MatProgressSpinnerModule
    ],
    templateUrl: './change-password-dialog.component.html',
    styleUrls: ['./change-password-dialog.component.scss']
})
export class ChangePasswordDialogComponent {
    form: FormGroup;
    loading = false;
    hideOld = true;
    hideNew = true;

    constructor(
        private fb: FormBuilder,
        private api: ApiService,
        private snackBar: MatSnackBar,
        public dialogRef: MatDialogRef<ChangePasswordDialogComponent>
    ) {
        this.form = this.fb.group({
            old_password: ['', Validators.required],
            new_password: ['', [Validators.required, Validators.minLength(6)]],
            confirm_password: ['', Validators.required]
        }, { validators: this.passwordMatchValidator });
    }

    passwordMatchValidator(g: FormGroup) {
        return g.get('new_password')?.value === g.get('confirm_password')?.value
            ? null : { mismatch: true };
    }

    save() {
        if (this.form.invalid) return;
        
        this.loading = true;
        const payload = {
            old_password: this.form.value.old_password,
            new_password: this.form.value.new_password
        };

        this.api.post('/users/me/change-password', payload)
            .pipe(finalize(() => this.loading = false))
            .subscribe({
                next: () => {
                    this.snackBar.open('Senha alterada com sucesso!', 'OK', { duration: 3000 });
                    this.dialogRef.close(true);
                },
                error: (err: any) => {
                    const msg = err?.error?.detail || 'Erro ao alterar senha';
                    this.snackBar.open(msg, 'Fechar', { duration: 5000 });
                }
            });
    }

    close() {
        this.dialogRef.close();
    }
}
