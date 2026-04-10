CREATE TABLE call_center(
    id INT AUTO_INCREMENT PRIMARY KEY,
    NOMBRE VARCHAR (50),
    PUESTO VARCHAR (50),
    SALARIO DECIMAL (50,2),
    FECHA_INGRESO DATE NOT NULL,
    FECHA_SALIDA DATE,
    ACTIVO boolean
);

INSERT INTO call_center
VALUES
('Juan Perez', 'agentebo', 10000,'2025-01-20',NULL, true),
('Jose Jimenez', 'agente telefonico', 10000,'2025-03-20',NULL,true),
('Daniel Sanchez', 'agente telefonico', 10000,'2025-07-20',NULL, true),
('Andres Jorgés', 'chat', 10000,'2025-09-20',NULL, true),
('Juan Aldam', 'chat', 10000,'2025-01-15',NULL, true);