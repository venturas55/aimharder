-- New, empty databases only. Existing installations: see docs/migration.md.
CREATE TABLE usuarios (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  usuario VARCHAR(50) NOT NULL,
  contrasena VARCHAR(250) NOT NULL,
  email VARCHAR(200) DEFAULT NULL,
  full_name VARCHAR(150) DEFAULT NULL,
  privilegio VARCHAR(20) DEFAULT NULL,
  pictureURL VARCHAR(100) DEFAULT NULL,
  UNIQUE KEY unique_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE configs (
  user_id INT NOT NULL PRIMARY KEY,
  gym VARCHAR(100) DEFAULT NULL,
  periodicidad ENUM('daily','weekly','hourly') NOT NULL DEFAULT 'daily',
  tipo_app VARCHAR(100) NOT NULL DEFAULT 'aimharder',
  clase VARCHAR(100) DEFAULT NULL,
  dias VARCHAR(250) DEFAULT NULL,
  hora VARCHAR(200) DEFAULT NULL,
  aimharder_user VARCHAR(200) DEFAULT NULL,
  aimharder_pass VARCHAR(200) DEFAULT NULL,
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE current_classes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  usuario VARCHAR(50),
  class_name VARCHAR(255) NOT NULL,
  UNIQUE KEY unique_user_class (user_id, class_name),
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE current_hours (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  usuario VARCHAR(50),
  hora VARCHAR(255) NOT NULL,
  UNIQUE KEY unique_user_hour (user_id, hora),
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  dia ENUM('Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo') NOT NULL,
  hora VARCHAR(255) NOT NULL,
  clase VARCHAR(100) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  reserva_realizada BOOLEAN NOT NULL DEFAULT FALSE,
  fecha_evento DATETIME,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_user_day (user_id, dia),
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
