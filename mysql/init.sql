CREATE TABLE IF NOT EXISTS servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(100) NOT NULL UNIQUE,
    environment VARCHAR(50) NOT NULL,
    service_status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO servers (hostname, environment, service_status)
VALUES
    ('web-server-01', 'development', 'RUNNING'),
    ('app-server-01', 'development', 'RUNNING'),
    ('db-server-01', 'testing', 'MAINTENANCE');
