CREATE TABLE callcenter (
    id int PRIMARY KEY, 
    NOMBRE VARCHAR (50),
    PUESTO VARCHAR (50),
    SALARIO DECIMAL (50,2),
    FECHA_INGRESO DATE, 
    ACTIVO boolean
);

INSERT INTO callcenter (id, NOMBRE, PUESTO, SALARIO, FECHA_INGRESO,ACTIVO)
values
(1, 'Juan Perez', 'agentebo', 10000,'2025-01-20', true),
(2, 'Jose Jimenez', 'agente telefonico', 10000,'2025-03-20',true),
(3, 'Daniel Sanchez', 'agente telefonico', 10000,'2025-07-20', true),
(4, 'Andres Jorgés', 'chat', 10000,'2025-09-20', true),
(5, 'Juan Aldam', 'chat', 10000,'2025-01-15', false);
