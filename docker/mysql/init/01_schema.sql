CREATE TABLE IF NOT EXISTS programs (
  program_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  mode ENUM('online','offline','hybrid') NOT NULL,
  duration_weeks INT NOT NULL,
  fee_usd INT NOT NULL,
  eligibility TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intakes (
  intake_id INT AUTO_INCREMENT PRIMARY KEY,
  program_id INT NOT NULL,
  intake_name VARCHAR(100) NOT NULL,
  start_date DATE NOT NULL,
  application_deadline DATE NOT NULL,
  seats INT NOT NULL,
  timezone VARCHAR(64) NOT NULL,
  FOREIGN KEY (program_id) REFERENCES programs(program_id)
);
