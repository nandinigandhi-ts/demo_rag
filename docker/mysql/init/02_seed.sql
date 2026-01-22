INSERT INTO programs (name, mode, duration_weeks, fee_usd, eligibility) VALUES
('Data Analytics Bootcamp', 'online', 12, 1200, 'Basic math, comfort with spreadsheets; no coding required.'),
('Full-Stack Web Development', 'hybrid', 16, 1800, 'Any background; motivation and time commitment required.'),
('Product Management Fundamentals', 'online', 8, 800, 'Open to all; helpful if you have prior work experience.');

INSERT INTO intakes (program_id, intake_name, start_date, application_deadline, seats, timezone) VALUES
(1, 'March 2026', '2026-03-10', '2026-02-28', 60, 'America/Chicago'),
(1, 'May 2026', '2026-05-12', '2026-04-30', 60, 'America/Chicago'),
(2, 'April 2026', '2026-04-05', '2026-03-20', 40, 'America/Chicago'),
(3, 'March 2026', '2026-03-15', '2026-03-01', 80, 'America/Chicago');
