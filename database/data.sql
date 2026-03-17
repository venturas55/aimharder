/*INSERT INTO `usuarios` VALUES (1,'xisme25','scrypt:32768:8:1$e9lU8nk4ovVwXBZz$05b91eae392c2810145948f45b7fdf655d9cee788b821bd0497965ca03c0971daa41efe3a1137c341ae1a7ad04f0096b4d1f18b2e86034213cb389f7ba820167','xisme25@gmail.com','Jorge Jimenez',NULL,NULL),(2,'javi','scrypt:32768:8:1$2hvus4diGX0hJUUW$5239cfd484697872e6ccbc2835240052604cc98ee18c746c05b0517c3dd3bf520cd87b1d5ce439b4b8b4a601f041f34b24fc4053ce2c47d3d5d852d77e3d8e6c','javigarcor@gmail.com','Javier Garcia',NULL,NULL);
INSERT INTO `configs` VALUES (1,'hybridboxgrau','daily','HYROX-Endurance','[\"Lunes\", \"Martes\", \"Miercoles\", \"Jueves\", \"Viernes\"]','08:00 - 09:00','xisme25@gmail.com','Jond@21yamaha02'),(2,'laforja','weekly','HYROX-Endurance','08:00-09:00','[lunes,Miercoles,Viernes]','javigarcor@gmail.com','Valencia18!');
INSERT INTO `bookings` VALUES (7,2,'Martes','11:30 - 10:30','Crosstraining','2026-03-13 16:59:39'),(8,2,'Miercoles','16:30 - 17:30','Open Box','2026-03-13 16:59:39'),(9,2,'Jueves','19:30 - 20:30','Open Box','2026-03-13 16:59:39'),(13,2,'Sabado','16:30 - 17:30','Crosstraining','2026-03-13 17:24:09');
UNLOCK TABLES;*/
INSERT INTO `current_classes` (user_id,usuario,class_name) VALUES (1,'xisme25','CrossFit'),(1,'xisme25','HYROX-Endurance'),(1,'xisme25','CrossFit MD'),(1,'xisme25','B. Jiu-jitsu Principiante'),(1,'xisme25','B. Jiu-jitsu Adolescentes'),(1,'xisme25','OPEN MAT'),(1,'xisme25','B. Jiu-jitsu'),(1,'xisme25','B. Jiu-jitsu Avanzado'),(1,'xisme25','Jiu-Jitsu Kids');
INSERT INTO `current_hours` (user_id,usuario,hora) VALUES (1,'xisme25','09:15 - 10:15'),(1,'xisme25','10:00 - 11:30'),(1,'xisme25','11:30 - 12:30'),(1,'xisme25','10:45 - 11:45');



1,'xisme25'