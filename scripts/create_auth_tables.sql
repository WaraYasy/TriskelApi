-- ============================================================
-- Triskel API - Auth Tables Migration
-- ============================================================
-- Crea las tablas para autenticación de administradores
--
-- Uso:
--   mysql -u triskel_user -p triskel_db < scripts/create_auth_tables.sql
--
-- ============================================================

USE triskel_db;

-- ============================================================
-- Tabla: admin_users
-- ============================================================
-- Almacena usuarios administradores del sistema
--
-- Roles:
--   - admin: Control total (CRUD admins, exports, etc.)
--   - support: Acceso a jugadores/partidas (sin CRUD admins)
--   - viewer: Solo lectura (analytics)
-- ============================================================

CREATE TABLE IF NOT EXISTS admin_users (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Credenciales
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt hash - NUNCA guardar password plano',

    -- Autorización
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' COMMENT 'admin | support | viewer',

    -- Estado
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL DEFAULT NULL,

    -- Índices para queries rápidas
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Tabla: audit_logs
-- ============================================================
-- Registra acciones administrativas para compliance y seguridad
--
-- Registra específicamente:
--   - Autenticación: login_success, login_failed, logout, token_refresh, change_password
--   - Exportaciones: export_players_csv, export_games_csv, export_events_csv, etc.
--
-- NO registra CRUD normal según especificación del usuario
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Usuario que realiza la acción
    user_id INT NULL COMMENT 'FK a admin_users (NULL si es acción del sistema)',
    username VARCHAR(50) NULL COMMENT 'Denormalizado para queries rápidas',

    -- Acción realizada
    action VARCHAR(100) NOT NULL COMMENT 'login_success, export_players_csv, etc.',

    -- Recurso afectado (opcional)
    resource_type VARCHAR(50) NULL COMMENT 'player, game, event, admin_user',
    resource_id VARCHAR(100) NULL COMMENT 'ID del recurso afectado',

    -- Contexto de la petición
    ip_address VARCHAR(50) NULL,
    user_agent TEXT NULL,

    -- Detalles adicionales (JSON serializado)
    details TEXT NULL COMMENT 'JSON con info adicional: {"count": 150, "format": "csv"}',

    -- Timestamp
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Resultado
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_message TEXT NULL,

    -- Foreign Key
    FOREIGN KEY (user_id) REFERENCES admin_users(id) ON DELETE SET NULL,

    -- Índices para queries optimizadas
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- Usuario Administrador por Defecto
-- ============================================================
-- Credenciales default (CAMBIAR EN PRODUCCIÓN):
--   Username: admin
--   Password: Admin123!
--
-- Hash generado con bcrypt (rounds=12):
-- $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNGJoQrZC
-- ============================================================

INSERT INTO admin_users (username, email, password_hash, role, is_active)
VALUES (
    'admin',
    'admin@triskel.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqNGJoQrZC',
    'admin',
    TRUE
)
ON DUPLICATE KEY UPDATE
    email = VALUES(email),
    role = VALUES(role),
    is_active = VALUES(is_active);


-- ============================================================
-- Registro de auditoría inicial
-- ============================================================

INSERT INTO audit_logs (user_id, username, action, resource_type, details, success)
SELECT
    id,
    username,
    'migration_create_tables',
    'system',
    '{"script": "create_auth_tables.sql", "version": "1.0"}',
    TRUE
FROM admin_users
WHERE username = 'admin'
LIMIT 1;


-- ============================================================
-- Verificación
-- ============================================================

SELECT 'Auth tables created successfully!' AS status;
SELECT COUNT(*) AS admin_users_count FROM admin_users;
SELECT COUNT(*) AS audit_logs_count FROM audit_logs;
SELECT username, email, role, is_active, created_at FROM admin_users;
