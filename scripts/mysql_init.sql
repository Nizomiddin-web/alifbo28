-- Öz serveringizda bazani qölda tayyorlaş uçun.
-- Foydalaniş:  mysql -u root -p < scripts/mysql_init.sql

CREATE DATABASE IF NOT EXISTS yozuvbot
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'yozuv'@'%' IDENTIFIED BY 'parol';
GRANT ALL PRIVILEGES ON yozuvbot.* TO 'yozuv'@'%';
FLUSH PRIVILEGES;

-- Jadvallarni SQLAlchemy quradi:
--     python -m bot.db --create
