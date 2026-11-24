-- Pharmacy Shelf MySQL schema (generated from the SQLAlchemy models).
-- Optional: the app creates these tables itself when AUTO_CREATE_TABLES=true.
CREATE DATABASE IF NOT EXISTS pharmacy_shelf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pharmacy_shelf;

CREATE TABLE companies (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(150) NOT NULL, 
	return_window_days INTEGER, 
	discount_allowed BOOL NOT NULL, 
	max_discount_pct FLOAT, 
	created_at DATETIME NOT NULL DEFAULT (now()), 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_companies_name ON companies (name);

CREATE TABLE medicines (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(200) NOT NULL, 
	batch VARCHAR(100) NOT NULL, 
	quantity INTEGER NOT NULL, 
	expiry_date DATE NOT NULL, 
	cost_price NUMERIC(10, 2) NOT NULL, 
	selling_price NUMERIC(10, 2) NOT NULL, 
	company_id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT (now()), 
	updated_at DATETIME DEFAULT (now()), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_medicine_name_batch UNIQUE (name, batch), 
	FOREIGN KEY(company_id) REFERENCES companies (id)
);
CREATE INDEX ix_medicines_company_id ON medicines (company_id);
CREATE INDEX ix_medicines_expiry_date ON medicines (expiry_date);
CREATE INDEX ix_medicines_name ON medicines (name);

CREATE TABLE action_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	medicine_id INTEGER NOT NULL, 
	action_type VARCHAR(10) NOT NULL, 
	recommended_action VARCHAR(10), 
	snooze_until DATE, 
	loss_amount FLOAT NOT NULL, 
	note VARCHAR(255), 
	acted_on DATE NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT (now()), 
	PRIMARY KEY (id), 
	FOREIGN KEY(medicine_id) REFERENCES medicines (id) ON DELETE CASCADE
);
CREATE INDEX ix_action_logs_acted_on ON action_logs (acted_on);
CREATE INDEX ix_action_logs_medicine_id ON action_logs (medicine_id);

CREATE TABLE sales (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	medicine_id INTEGER NOT NULL, 
	quantity_sold INTEGER NOT NULL, 
	sale_date DATE NOT NULL, 
	created_at DATETIME NOT NULL DEFAULT (now()), 
	PRIMARY KEY (id), 
	FOREIGN KEY(medicine_id) REFERENCES medicines (id) ON DELETE CASCADE
);
CREATE INDEX ix_sales_medicine_date ON sales (medicine_id, sale_date);
