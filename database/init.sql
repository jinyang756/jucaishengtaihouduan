-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `green_ecology_fund` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `green_ecology_fund`;

-- 创建规则表
CREATE TABLE IF NOT EXISTS `rules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fund_type` VARCHAR(50) NOT NULL,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT,
  `rule_type` VARCHAR(50) NOT NULL,
  `parameters` JSON NOT NULL,
  `priority` INT DEFAULT 100,
  `status` VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_fund_type` (`fund_type`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建新闻表
CREATE TABLE IF NOT EXISTS `news` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `content` LONGTEXT NOT NULL,
  `source` VARCHAR(100) NOT NULL,
  `url` VARCHAR(500) DEFAULT NULL,
  `publish_time` DATETIME NOT NULL,
  `crawl_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `category` VARCHAR(50) DEFAULT NULL,
  `sentiment_score` FLOAT DEFAULT NULL,
  `impact_coefficient` FLOAT DEFAULT NULL,
  `relevance_score` FLOAT DEFAULT NULL,
  `processed` BOOLEAN DEFAULT FALSE,
  `keywords` JSON DEFAULT NULL,
  `related_fund_types` JSON DEFAULT NULL,
  INDEX `idx_publish_time` (`publish_time`),
  INDEX `idx_processed` (`processed`),
  INDEX `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建计算日志表
CREATE TABLE IF NOT EXISTS `calculation_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fund_id` INT NOT NULL,
  `calculation_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `net_value_before` FLOAT NOT NULL,
  `net_value_after` FLOAT NOT NULL,
  `change_amount` FLOAT NOT NULL,
  `change_percent` FLOAT NOT NULL,
  `news_impact_details` JSON DEFAULT NULL,
  `rule_application_details` JSON DEFAULT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'SUCCESS',
  `error_message` TEXT DEFAULT NULL,
  INDEX `idx_fund_id` (`fund_id`),
  INDEX `idx_calculation_time` (`calculation_time`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建新闻影响表
CREATE TABLE IF NOT EXISTS `news_impacts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `news_id` INT NOT NULL,
  `fund_id` INT NOT NULL,
  `impact_coefficient` FLOAT NOT NULL,
  `calculation_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `details` JSON DEFAULT NULL,
  UNIQUE KEY `unique_news_fund` (`news_id`, `fund_id`),
  INDEX `idx_news_id` (`news_id`),
  INDEX `idx_fund_id` (`fund_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建基金表
CREATE TABLE IF NOT EXISTS `funds` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL,
  `code` VARCHAR(20) NOT NULL UNIQUE,
  `fund_type` VARCHAR(50) NOT NULL,
  `description` TEXT,
  `manager` VARCHAR(100) DEFAULT NULL,
  `risk_level` VARCHAR(50) DEFAULT NULL,
  `establish_date` DATE DEFAULT NULL,
  `current_nav` FLOAT NOT NULL DEFAULT 1.0,
  `total_assets` DECIMAL(18,2) DEFAULT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_fund_type` (`fund_type`),
  INDEX `idx_status` (`status`),
  INDEX `idx_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建基金净值表
CREATE TABLE IF NOT EXISTS `fund_net_values` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `fund_id` INT NOT NULL,
  `date` DATE NOT NULL,
  `nav` FLOAT NOT NULL,
  `accumulated_nav` FLOAT NOT NULL,
  `change_percent` FLOAT DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_fund_date` (`fund_id`, `date`),
  INDEX `idx_fund_id` (`fund_id`),
  INDEX `idx_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建示例数据

-- 插入规则示例数据
INSERT INTO `rules` (`fund_type`, `name`, `description`, `rule_type`, `parameters`, `priority`, `status`) VALUES
('GREEN_ENERGY', '新能源新闻影响规则', '根据新能源相关新闻的情感分数调整基金净值', 'NEWS_IMPACT', '{"weight": 0.3, "max_impact": 0.05}', 10, 'ACTIVE'),
('TECHNOLOGY', '科技行业政策影响规则', '根据科技行业政策新闻调整基金净值', 'NEWS_IMPACT', '{"weight": 0.4, "max_impact": 0.08}', 15, 'ACTIVE'),
('HEALTHCARE', '医疗行业研发影响规则', '根据医疗研发突破新闻调整基金净值', 'NEWS_IMPACT', '{"weight": 0.35, "max_impact": 0.06}', 12, 'ACTIVE');

-- 插入基金示例数据
INSERT INTO `funds` (`name`, `code`, `fund_type`, `description`, `manager`, `risk_level`, `establish_date`, `current_nav`) VALUES
('绿色能源创新基金', '161028', 'GREEN_ENERGY', '专注于投资新能源领域的创新企业', '张三', 'MEDIUM', '2020-01-15', 1.56),
('科技成长精选基金', '001630', 'TECHNOLOGY', '投资于科技行业具有成长潜力的企业', '李四', 'HIGH', '2018-03-20', 2.34),
('健康医疗主题基金', '001878', 'HEALTHCARE', '聚焦健康医疗行业的优质企业', '王五', 'MEDIUM', '2019-06-10', 1.89);

-- 插入基金净值示例数据
INSERT INTO `fund_net_values` (`fund_id`, `date`, `nav`, `accumulated_nav`, `change_percent`) VALUES
(1, '2023-07-01', 1.54, 1.54, 0.02),
(1, '2023-07-02', 1.55, 1.55, 0.0065),
(1, '2023-07-03', 1.56, 1.56, 0.0065),
(2, '2023-07-01', 2.32, 2.32, 0.01),
(2, '2023-07-02', 2.33, 2.33, 0.0043),
(2, '2023-07-03', 2.34, 2.34, 0.0043),
(3, '2023-07-01', 1.87, 1.87, 0.015),
(3, '2023-07-02', 1.88, 1.88, 0.0053),
(3, '2023-07-03', 1.89, 1.89, 0.0053);

-- 插入新闻示例数据
INSERT INTO `news` (`title`, `content`, `source`, `url`, `publish_time`, `category`, `sentiment_score`, `impact_coefficient`, `processed`, `keywords`, `related_fund_types`) VALUES
('国家出台新能源补贴新政策，光伏产业迎来重大利好', '近日，国家发改委发布新能源补贴新政策，对光伏产业给予额外20%的补贴支持...', '财经日报', 'http://example.com/news/1', '2023-07-04 09:30:00', '政策', 0.85, 0.04, TRUE, '["新能源", "光伏", "补贴"]', '["GREEN_ENERGY"]'),
('科技巨头发布最新AI技术，引领行业创新', '某科技巨头今日发布最新一代AI技术，预计将对整个科技行业产生深远影响...', '科技新闻网', 'http://example.com/news/2', '2023-07-04 10:15:00', '技术', 0.92, 0.05, TRUE, '["AI", "技术创新", "科技"]', '["TECHNOLOGY"]'),
('医疗研究取得重大突破，新型药物进入临床试验', '某医疗研究团队宣布在癌症治疗方面取得重大突破，新型药物已进入临床试验阶段...', '健康时报', 'http://example.com/news/3', '2023-07-04 11:20:00', '医疗', 0.88, 0.03, TRUE, '["医疗", "药物", "临床试验"]', '["HEALTHCARE"]');

-- 插入计算日志示例数据
INSERT INTO `calculation_logs` (`fund_id`, `net_value_before`, `net_value_after`, `change_amount`, `change_percent`, `news_impact_details`) VALUES
(1, 1.56, 1.57, 0.01, 0.0064, '{"news_id": 1, "impact": 0.01}'),
(2, 2.34, 2.36, 0.02, 0.0085, '{"news_id": 2, "impact": 0.02}'),
(3, 1.89, 1.90, 0.01, 0.0053, '{"news_id": 3, "impact": 0.01}');

-- 插入新闻影响示例数据
INSERT INTO `news_impacts` (`news_id`, `fund_id`, `impact_coefficient`, `details`) VALUES
(1, 1, 0.04, '{"weight": 0.3, "sentiment_score": 0.85, "relevance": 0.9}'),
(2, 2, 0.05, '{"weight": 0.4, "sentiment_score": 0.92, "relevance": 0.85}'),
(3, 3, 0.03, '{"weight": 0.35, "sentiment_score": 0.88, "relevance": 0.8}');