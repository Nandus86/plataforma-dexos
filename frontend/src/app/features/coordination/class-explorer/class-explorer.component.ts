import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTreeModule, MatTreeNestedDataSource } from '@angular/material/tree';
import { NestedTreeControl } from '@angular/cdk/tree';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { StudentDossierComponent } from '../student-dossier/student-dossier.component';

interface TreeNode {
  name: string;
  type: 'course' | 'group' | 'student';
  id: string;
  children?: TreeNode[];
  expanded?: boolean;
  loading?: boolean;
  data?: any;
}

@Component({
  selector: 'app-class-explorer',
  standalone: true,
  imports: [
    CommonModule,
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    MatCardModule,
    MatInputModule,
    MatFormFieldModule,
    FormsModule,
    StudentDossierComponent
  ],
  templateUrl: './class-explorer.component.html',
  styleUrls: ['./class-explorer.component.scss']
})
export class ClassExplorerComponent implements OnInit {
  treeControl = new NestedTreeControl<TreeNode>(node => node.children);
  dataSource = new MatTreeNestedDataSource<TreeNode>();
  
  loading = true;
  selectedStudentId: string | null = null;
  searchQuery = '';
  
  // To keep track of all students for search
  allStudents: any[] = [];
  searchResults: any[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadTree();
    this.loadAllStudents();
  }

  hasChild = (_: number, node: TreeNode) => !!node.children && node.children.length > 0;

  async loadTree() {
    this.loading = true;
    try {
      const courses: any[] = await this.api.get('/courses/').toPromise() as any[];
      const groups: any[] = await this.api.get('/class-groups/').toPromise() as any[];

      const treeData: TreeNode[] = courses.map(course => {
        const courseGroups = groups.filter(g => g.course_id === course.id);
        
        return {
          name: course.name,
          type: 'course',
          id: course.id,
          data: course,
          children: courseGroups.map(g => ({
            name: `${g.name} (${g.shift})`,
            type: 'group',
            id: g.id,
            data: g,
            children: [{ name: 'Carregando...', type: 'student', id: 'loading-' + g.id }] // Placeholder to make it expandable
          }))
        };
      });

      this.dataSource.data = treeData;
    } catch (err) {
      console.error('Error loading tree', err);
    }
    this.loading = false;
  }

  async loadAllStudents() {
    try {
      this.allStudents = await this.api.get('/users/?role=estudante').toPromise() as any[];
    } catch (err) {
      console.error('Error loading students', err);
    }
  }

  async onNodeExpand(node: TreeNode) {
    if (node.type === 'group' && node.children && node.children.length === 1 && node.children[0].id.startsWith('loading-')) {
      console.log('ClassExplorer: Expandindo nó', node.name, 'ID:', node.id);
      node.loading = true;
      try {
        console.log(`ClassExplorer: Fazendo requisição GET para /class-groups/${node.id}/students/`);
        const students = await this.api.get(`/class-groups/${node.id}/students/`).toPromise() as any[];
        console.log('ClassExplorer: Resposta da API de estudantes:', students);
        
        node.children = students.map(s => {
          console.log('ClassExplorer: Mapeando estudante:', s);
          return {
            name: s.student_name,
            type: 'student',
            id: s.student_id,
            data: s
          };
        });
        
        if (node.children.length === 0) {
          console.log('ClassExplorer: Nenhum aluno matriculado na turma');
          node.children = [{ name: 'Nenhum aluno matriculado', type: 'student', id: 'empty-' + node.id, data: null }];
        }
      } catch (err) {
        console.error('ClassExplorer: Error loading students for group', err);
        node.children = [{ name: 'Erro ao carregar alunos', type: 'student', id: 'empty-' + node.id, data: null }];
      }
      
      // Refresh tree
      console.log('ClassExplorer: Atualizando a dataSource da árvore...');
      const currentData = this.dataSource.data;
      this.dataSource.data = [];
      this.dataSource.data = currentData;
      console.log('ClassExplorer: dataSource atualizada.');
        
      node.loading = false;
    }
  }

  selectStudent(studentId: string) {
    if (!studentId || studentId.startsWith('empty-') || studentId.startsWith('loading-')) return;
    this.selectedStudentId = studentId;
  }

  searchStudent() {
    if (!this.searchQuery.trim()) {
      this.searchResults = [];
      return;
    }
    const q = this.searchQuery.toLowerCase();
    this.searchResults = this.allStudents.filter(s => 
      s.name.toLowerCase().includes(q) || 
      (s.registration_number && s.registration_number.toLowerCase().includes(q))
    ).slice(0, 5); // top 5 results
  }
}
