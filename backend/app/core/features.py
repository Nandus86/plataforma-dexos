"""
System Features and Default Permissions
Maps every menu/submenu from the frontend layout to a toggleable feature.
"""

# Define available features and their default roles
DEFAULT_FEATURES = {
    # ===== Dashboard =====
    "dashboard": {
        "label": "Dashboard",
        "description": "Visão geral e estatísticas",
        "group": "Geral",
        "default_roles": ["superadmin", "admin", "professor", "estudante", "coordenacao"],
        "locked": True  # Cannot be disabled
    },

    # ===== Cadastros =====
    "users": {
        "label": "Cadastros — Estudantes e Funcionários",
        "description": "Gerenciamento de Estudantes e Funcionários",
        "group": "Cadastros",
        "default_roles": ["superadmin", "admin", "coordenacao"],
        "locked": False
    },
    "courses": {
        "label": "Cadastros — Cursos, Disciplinas, Turmas e Períodos",
        "description": "Estrutura acadêmica: cursos, disciplinas, turmas e período letivo",
        "group": "Cadastros",
        "default_roles": ["superadmin", "admin", "coordenacao"],
        "locked": False
    },

    # ===== Acadêmico =====
    "academic": {
        "label": "Acadêmico — Matrículas e Matrizes",
        "description": "Matrículas, matrizes curriculares e boletim",
        "group": "Acadêmico",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor"],
        "locked": False
    },
    "grades": {
        "label": "Acadêmico — Notas / Boletim",
        "description": "Visualização e lançamento de notas acadêmicas",
        "group": "Acadêmico",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },
    "attendance": {
        "label": "Acadêmico — Frequência",
        "description": "Controle de presença e registro de frequência",
        "group": "Acadêmico",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },
    "assignments": {
        "label": "Acadêmico — Tarefas",
        "description": "Criação e entrega de atividades e trabalhos",
        "group": "Acadêmico",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },
    "occurrences": {
        "label": "Acadêmico — Ocorrências",
        "description": "Registro de elogios, advertências e observações",
        "group": "Acadêmico",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },

    # ===== Conteúdo =====
    "materials": {
        "label": "Conteúdo — Materiais Didáticos",
        "description": "Upload e compartilhamento de materiais e arquivos",
        "group": "Conteúdo",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },
    "lesson_plans": {
        "label": "Conteúdo — Planos de Aula",
        "description": "Planejamento pedagógico diário",
        "group": "Conteúdo",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor"],
        "locked": False
    },
    "announcements": {
        "label": "Conteúdo — Avisos / Mural",
        "description": "Publicação de avisos e comunicados",
        "group": "Conteúdo",
        "default_roles": ["superadmin", "admin", "coordenacao", "professor", "estudante"],
        "locked": False
    },

    # ===== Pedagógico =====
    "reports": {
        "label": "Pedagógico — Coordenação e Relatórios",
        "description": "Painel de acompanhamento, relatórios gerenciais e pedagógicos",
        "group": "Pedagógico",
        "default_roles": ["superadmin", "admin", "coordenacao"],
        "locked": False
    },
    "export": {
        "label": "Pedagógico — Exportar Dados (CSV)",
        "description": "Exportação de dados para backup ou análise",
        "group": "Pedagógico",
        "default_roles": ["superadmin", "admin", "coordenacao"],
        "locked": False
    },

    # ===== Financeiro =====
    "financial": {
        "label": "Financeiro",
        "description": "Gestão de mensalidades e pagamentos",
        "group": "Financeiro",
        "default_roles": ["superadmin", "admin"],
        "locked": False
    },

    # ===== Sistema =====
    "settings": {
        "label": "Sistema — Configurações e Instituição",
        "description": "Configurações gerais, dados da instituição e gerenciamento de acesso",
        "group": "Sistema",
        "default_roles": ["superadmin", "admin"],
        "locked": True  # Cannot be disabled
    }
}

def get_default_settings():
    """Return the default settings structure for a new tenant"""
    return {
        "features": {
            key: {
                "label": value["label"],
                "description": value["description"],
                "group": value.get("group", ""),
                "locked": value["locked"],
                "enabled": True, 
                "roles": value["default_roles"]
            } 
            for key, value in DEFAULT_FEATURES.items()
        }
    }
