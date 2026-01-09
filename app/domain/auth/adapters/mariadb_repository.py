"""
Adaptador MariaDB para Auth

TODO: Implementar repositorio usando SQLAlchemy.

Este es el adaptador concreto que habla con MariaDB.
Implementa IAuthRepository.

Ejemplo de implementación:
class MariaDBAuthRepository(IAuthRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_user(self, username, email, password_hash):
        user = AdminUser(
            username=username,
            email=email,
            password_hash=password_hash
        )
        self.session.add(user)
        self.session.commit()
        return user

    def validate_credentials(self, username, password):
        user = self.session.query(AdminUser)\\
            .filter_by(username=username)\\
            .first()

        if user and verify_password(password, user.password_hash):
            return user
        return None
"""
pass
