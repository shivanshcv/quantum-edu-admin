"""
Database router: admin_app models use quantum_education DB; others use default (admin_django).
"""
QUANTUM_EDUCATION_APP = 'admin_app'


class QuantumEducationRouter:
    """Route admin_app models to quantum_education database."""

    def db_for_read(self, model, **hints):
        if model._meta.app_label == QUANTUM_EDUCATION_APP:
            return 'quantum_education'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == QUANTUM_EDUCATION_APP:
            return 'quantum_education'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == QUANTUM_EDUCATION_APP:
            return False
        return None
