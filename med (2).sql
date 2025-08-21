-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Aug 20, 2025 at 10:33 PM
-- Server version: 9.1.0
-- PHP Version: 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `med`
--

-- --------------------------------------------------------

--
-- Table structure for table `cash_register`
--

DROP TABLE IF EXISTS `cash_register`;
CREATE TABLE IF NOT EXISTS `cash_register` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL DEFAULT (curdate()),
  `opening_cash` decimal(10,2) NOT NULL,
  `closing_cash` decimal(10,2) DEFAULT NULL,
  `total_sales` decimal(10,2) DEFAULT '0.00',
  `declared_by` int NOT NULL,
  `is_open` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `closed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `declared_by` (`declared_by`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `cash_register`
--

INSERT INTO `cash_register` (`id`, `date`, `opening_cash`, `closing_cash`, `total_sales`, `declared_by`, `is_open`, `created_at`, `closed_at`) VALUES
(2, '2025-08-20', 1500.00, NULL, 602.00, 5, 0, '2025-08-20 22:24:13', '2025-08-20 22:24:49'),
(3, '2025-08-20', 1200.00, NULL, 602.00, 5, 1, '2025-08-20 22:25:07', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `phone`
--

DROP TABLE IF EXISTS `phone`;
CREATE TABLE IF NOT EXISTS `phone` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `brand` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `storage` varchar(50) NOT NULL,
  `color` varchar(30) NOT NULL,
  `condition` varchar(10) NOT NULL,
  `stock` int NOT NULL,
  `cost_price` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `phone`
--

INSERT INTO `phone` (`id`, `name`, `brand`, `model`, `storage`, `color`, `condition`, `stock`, `cost_price`) VALUES
(1, 'iphone', 'apple', '12', '256', 'rose', '100%', 0, 1000),
(2, 's23', 'samsung', '651652365', '128', 'verde', 'novo', 0, 250),
(3, 'huawei', 'huawei', 'p50', '128', 'negro', 'novo', 0, 120);

-- --------------------------------------------------------

--
-- Table structure for table `phones`
--

DROP TABLE IF EXISTS `phones`;
CREATE TABLE IF NOT EXISTS `phones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `brand` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL,
  `storage` varchar(50) NOT NULL,
  `color` varchar(30) NOT NULL,
  `condition` varchar(10) NOT NULL,
  `stock` int NOT NULL,
  `cost_price` float NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
CREATE TABLE IF NOT EXISTS `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `brand` varchar(50) DEFAULT NULL,
  `model` varchar(50) DEFAULT NULL,
  `cost_price` decimal(10,2) NOT NULL,
  `stock` int NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `brand`, `model`, `cost_price`, `stock`, `created_at`, `updated_at`) VALUES
(1, 'pochette', 'louis vuitton', 'rose', 100.00, 0, '2025-08-19 16:11:18', '2025-08-20 20:57:21'),
(2, 'pochette', 'simple', '1233', 10.00, 9, '2025-08-19 20:07:07', '2025-08-19 21:03:15'),
(3, 'ecouteurs', 'oraimo', 'pro 3', 100.00, 12, '2025-08-19 20:07:21', '2025-08-19 20:07:21'),
(4, 'ecouteurs', 'iphone', 'pro', 150.00, 300, '2025-08-20 21:00:57', '2025-08-20 21:00:57');

-- --------------------------------------------------------

--
-- Table structure for table `product_logs`
--

DROP TABLE IF EXISTS `product_logs`;
CREATE TABLE IF NOT EXISTS `product_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `product_id` int NOT NULL,
  `worker_id` int NOT NULL,
  `action` enum('added','removed','sold') NOT NULL,
  `quantity` int NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `log_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `worker_id` (`worker_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sales`
--

DROP TABLE IF EXISTS `sales`;
CREATE TABLE IF NOT EXISTS `sales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_type` enum('product','phone') NOT NULL,
  `item_id` int NOT NULL,
  `product_id` int NOT NULL,
  `worker_id` int NOT NULL,
  `quantity` int NOT NULL,
  `selling_price` decimal(10,2) NOT NULL,
  `sale_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sale_type` varchar(20) NOT NULL DEFAULT 'product',
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `worker_id` (`worker_id`)
) ENGINE=MyISAM AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `sales`
--

INSERT INTO `sales` (`id`, `item_type`, `item_id`, `product_id`, `worker_id`, `quantity`, `selling_price`, `sale_date`, `sale_type`) VALUES
(1, 'phone', 1, 0, 1, 1, 1.00, '2025-08-19 20:04:29', 'product'),
(2, 'phone', 1, 0, 1, 1, 1.00, '2025-08-19 20:05:00', 'product'),
(3, 'phone', 2, 0, 1, 1, 500.00, '2025-08-19 20:07:38', 'product'),
(4, 'phone', 2, 0, 1, 1, 111.00, '2025-08-19 20:08:43', 'product'),
(5, 'phone', 1, 0, 1, 1, 1.00, '2025-08-19 20:32:46', 'product'),
(6, 'phone', 2, 0, 5, 1, 1.00, '2025-08-19 21:00:42', 'product'),
(7, 'product', 2, 0, 5, 1, 1.00, '2025-08-19 21:03:15', 'product'),
(8, 'phone', 2, 0, 5, 1, 1.00, '2025-08-19 21:44:53', 'product'),
(9, 'product', 1, 0, 5, 1, 1.00, '2025-08-20 20:57:21', 'product'),
(10, 'phone', 3, 0, 5, 2, 300.00, '2025-08-20 21:01:44', 'product'),
(11, 'phone', 3, 0, 5, 1, 1.00, '2025-08-20 21:11:38', 'product');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('owner','worker') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=MyISAM AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `role`, `created_at`, `updated_at`) VALUES
(7, 'khalid', 'khalid@gmail.com', '$2b$12$KRMP2pE54OeKIqwUh9cBO.cI0TByq711yna3e/W2xm1Qm8q/pW.BO', 'worker', '2025-08-20 21:03:54', '2025-08-20 21:03:54'),
(6, 'mohamed', 'mohamed@gmail.com', '$2b$12$JTPadDk1xiPYJC0zG6Tm/.a9vnhczcvQ8z/0NSKtMjCVSptFBxrPm', 'owner', '2025-08-19 20:54:39', '2025-08-19 20:54:39'),
(5, 'zaka', 'zaka@gmail.com', '$2b$12$EMlu.WGKEUa1lsJ2iK4iGeqHGUzO7QZ4/bNWCK3TUaXLI9x/HU9cW', 'worker', '2025-08-19 20:26:26', '2025-08-19 20:26:26');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
