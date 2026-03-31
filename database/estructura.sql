CREATE TABLE usuarios (
  id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  usuario VARCHAR(50) NOT NULL,
  contrasena VARCHAR(250) NOT NULL,
  email VARCHAR(200) DEFAULT NULL,
  full_name VARCHAR(150) DEFAULT NULL,
  privilegio VARCHAR(20) DEFAULT NULL,
  pictureURL VARCHAR(100) CHARACTER SET utf16 COLLATE utf16_spanish2_ci DEFAULT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'tabla de usuarios';

CREATE TABLE configs (
  id INT(11) NOT NULL PRIMARY KEY,
  gym VARCHAR(100) DEFAULT NULL,
  periodicidad ENUM('daily','weekly') NOT NULL,
  clase VARCHAR(100) DEFAULT NULL,
  dias VARCHAR(250) DEFAULT NULL,
  hora VARCHAR(200) DEFAULT NULL,
  aimharder_user VARCHAR(200) DEFAULT NULL,
  aimharder_pass VARCHAR(200) DEFAULT NULL,
  FOREIGN KEY (id) REFERENCES usuarios(id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = 'tabla de configs';

CREATE TABLE current_classes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT(11) NOT NULL,
  usuario VARCHAR(50),
  class_name VARCHAR(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

CREATE TABLE current_hours (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT(11) NOT NULL,
  usuario VARCHAR(50) ,
  hora VARCHAR(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
);

CREATE TABLE bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  dia ENUM('Lunes','Martes','Miercoles','Jueves','Viernes','Sabado','Domingo') NOT NULL,
  hora VARCHAR(255) NOT NULL,
  clase VARCHAR(100) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES usuarios(id)
);
ALTER TABLE bookings
ADD UNIQUE KEY unique_user_day (user_id, dia);

ALTER TABLE current_classes 
ADD CONSTRAINT unique_user_class UNIQUE (user_id, class_name);

ALTER TABLE current_hours 
ADD CONSTRAINT unique_user_hour UNIQUE (user_id, hora);