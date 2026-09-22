import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import mariadb

from app.db import get_connection
from app.routers import (
    branch_master,
    branch_type_master,
    company_master,
    countries,
    currencies,
    customer_master,
    place_master,
    scheduler_master,
    scheduler_case,
    quality_type_master,
    regions,
    route_master,
    section_master,
    states,
    work_master,
    distribution_master,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

app = FastAPI(title="MDO Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(currencies.router)
app.include_router(countries.router)
app.include_router(states.router)
app.include_router(regions.router)
app.include_router(route_master.router)
app.include_router(place_master.router)
app.include_router(section_master.router)
app.include_router(company_master.router)
app.include_router(branch_type_master.router)
app.include_router(branch_master.router)
app.include_router(customer_master.router)
app.include_router(scheduler_master.router)
app.include_router(scheduler_case.router)
app.include_router(work_master.router)
app.include_router(quality_type_master.router)
app.include_router(distribution_master.router)

UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "logos").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "cases").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


def ensure_schema() -> None:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currencies (
              currency_id INT NOT NULL AUTO_INCREMENT,
              currency_name VARCHAR(100) NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (currency_id),
              UNIQUE KEY uq_currencies_name (currency_name)
            )
            """
        )

        cursor.execute(
            """
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'currencies'
              AND COLUMN_NAME = 'currency_id'
            """
        )
        column = cursor.fetchone()
        if column and str(column[0]).lower() != "int":
            cursor.execute(
                """
                CREATE TABLE currencies_new (
                  currency_id INT NOT NULL AUTO_INCREMENT,
                  currency_name VARCHAR(100) NOT NULL,
                  status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  PRIMARY KEY (currency_id),
                  UNIQUE KEY uq_currencies_name (currency_name)
                )
                """
            )
            cursor.execute(
                """
                INSERT IGNORE INTO currencies_new (currency_name, status)
                SELECT currency_name, status FROM currencies
                WHERE currency_name IS NOT NULL AND currency_name <> ''
                """
            )
            cursor.execute("DROP TABLE currencies")
            cursor.execute("RENAME TABLE currencies_new TO currencies")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS countries (
              country_id INT NOT NULL AUTO_INCREMENT,
              country_name VARCHAR(100) NOT NULL,
              country_code VARCHAR(10) NOT NULL,
              currency_id INT NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (country_id),
              UNIQUE KEY uq_countries_name (country_name),
              UNIQUE KEY uq_countries_code (country_code),
              CONSTRAINT fk_countries_currency
                FOREIGN KEY (currency_id) REFERENCES currencies (currency_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS states (
              state_id INT NOT NULL AUTO_INCREMENT,
              state_name VARCHAR(100) NOT NULL,
              country_id INT NOT NULL,
              cgst_percent DECIMAL(5,2) NOT NULL DEFAULT 0,
              sgst_percent DECIMAL(5,2) NOT NULL DEFAULT 0,
              igst_percent DECIMAL(5,2) NOT NULL DEFAULT 0,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (state_id),
              UNIQUE KEY uq_states_name_country (state_name, country_id),
              CONSTRAINT fk_states_country
                FOREIGN KEY (country_id) REFERENCES countries (country_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS regions (
              region_id INT NOT NULL AUTO_INCREMENT,
              region_name VARCHAR(100) NOT NULL,
              state_id INT NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (region_id),
              UNIQUE KEY uq_regions_name_state (region_name, state_id),
              CONSTRAINT fk_regions_state
                FOREIGN KEY (state_id) REFERENCES states (state_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS routes (
              route_id INT NOT NULL AUTO_INCREMENT,
              route_code VARCHAR(50) NOT NULL,
              region_id INT NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (route_id),
              UNIQUE KEY uq_routes_code (route_code),
              CONSTRAINT fk_routes_region
                FOREIGN KEY (region_id) REFERENCES regions (region_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS places (
              place_id INT NOT NULL AUTO_INCREMENT,
              place_name VARCHAR(100) NOT NULL,
              region_id INT NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (place_id),
              UNIQUE KEY uq_places_name_region (place_name, region_id),
              CONSTRAINT fk_places_region
                FOREIGN KEY (region_id) REFERENCES regions (region_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sections (
              section_id INT NOT NULL AUTO_INCREMENT,
              section_name VARCHAR(100) NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (section_id),
              UNIQUE KEY uq_sections_name (section_name)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS companies (
              company_id INT NOT NULL AUTO_INCREMENT,
              company_name VARCHAR(150) NOT NULL,
              company_code VARCHAR(50) NOT NULL,
              address VARCHAR(255) NOT NULL,
              address2 VARCHAR(255) NULL,
              place_id INT NOT NULL,
              region_id INT NOT NULL,
              state_id INT NOT NULL,
              country_id INT NOT NULL,
              pin VARCHAR(20) NOT NULL,
              phone VARCHAR(30) NULL,
              mobile VARCHAR(30) NULL,
              email VARCHAR(150) NULL,
              whatsapp_no VARCHAR(30) NULL,
              gst_no VARCHAR(50) NULL,
              ie_code VARCHAR(50) NULL,
              iso_number VARCHAR(50) NULL,
              logo_path VARCHAR(255) NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (company_id),
              UNIQUE KEY uq_companies_code (company_code),
              UNIQUE KEY uq_companies_name (company_name),
              CONSTRAINT fk_companies_place FOREIGN KEY (place_id) REFERENCES places (place_id),
              CONSTRAINT fk_companies_region FOREIGN KEY (region_id) REFERENCES regions (region_id),
              CONSTRAINT fk_companies_state FOREIGN KEY (state_id) REFERENCES states (state_id),
              CONSTRAINT fk_companies_country FOREIGN KEY (country_id) REFERENCES countries (country_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS branch_types (
              branch_type_id INT NOT NULL AUTO_INCREMENT,
              branch_type_name VARCHAR(100) NOT NULL,
              work_collection TINYINT(1) NOT NULL DEFAULT 0,
              case_study TINYINT(1) NOT NULL DEFAULT 0,
              production TINYINT(1) NOT NULL DEFAULT 0,
              qc TINYINT(1) NOT NULL DEFAULT 0,
              billing TINYINT(1) NOT NULL DEFAULT 0,
              transportation TINYINT(1) NOT NULL DEFAULT 0,
              payment_collection TINYINT(1) NOT NULL DEFAULT 0,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (branch_type_id),
              UNIQUE KEY uq_branch_types_name (branch_type_name)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS works (
              work_id INT NOT NULL AUTO_INCREMENT,
              work_name VARCHAR(100) NOT NULL,
              work_type ENUM('Work', 'Application') NOT NULL,
              stage ENUM('Single Stage', 'Multi Stage') NOT NULL,
              production_time INT NOT NULL,
              section_id INT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              existing_id INT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (work_id),
              UNIQUE KEY uq_works_name_section (work_name, section_id),
              CONSTRAINT fk_works_section
                FOREIGN KEY (section_id) REFERENCES sections (section_id)
            )
            """
        )

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'works'
              AND COLUMN_NAME = 'existing_id'
            """
        )
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE works ADD COLUMN existing_id INT NULL")

        cursor.execute(
            """
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'works'
              AND COLUMN_NAME = 'production_time'
            """
        )
        column = cursor.fetchone()
        if column and str(column[0]).lower() != "int":
            cursor.execute(
                """
                UPDATE works
                SET production_time = '0'
                WHERE production_time IS NULL
                   OR production_time = ''
                   OR production_time NOT REGEXP '^[0-9]+$'
                """
            )
            cursor.execute("ALTER TABLE works MODIFY COLUMN production_time INT NOT NULL")

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'works'
              AND COLUMN_NAME = 'section_id'
            """
        )
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE works ADD COLUMN section_id INT NULL")
            cursor.execute("SELECT MIN(section_id) FROM sections")
            section_row = cursor.fetchone()
            min_section_id = section_row[0] if section_row else None
            if min_section_id:
                cursor.execute(
                    "UPDATE works SET section_id = %s WHERE section_id IS NULL",
                    (min_section_id,),
                )
            cursor.execute(
                """
                ALTER TABLE works
                ADD CONSTRAINT fk_works_section
                  FOREIGN KEY (section_id) REFERENCES sections (section_id)
                """
            )

        cursor.execute(
            """
            SELECT INDEX_NAME
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'works'
              AND INDEX_NAME = 'uq_works_name_section'
            """
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                SELECT INDEX_NAME
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'works'
                  AND INDEX_NAME = 'uq_works_name'
                """
            )
            if cursor.fetchone():
                cursor.execute("ALTER TABLE works DROP INDEX uq_works_name")
            cursor.execute(
                """
                ALTER TABLE works
                ADD UNIQUE KEY uq_works_name_section (work_name, section_id)
                """
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quality_types (
              quality_type_id INT NOT NULL AUTO_INCREMENT,
              quality_name VARCHAR(100) NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (quality_type_id),
              UNIQUE KEY uq_quality_types_name (quality_name)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS distributions (
              distribution_id INT NOT NULL AUTO_INCREMENT,
              distribution_name VARCHAR(150) NOT NULL,
              section_id INT NOT NULL,
              currency_id INT NOT NULL,
              company_id INT NOT NULL,
              effective_from DATE NOT NULL,
              effective_to DATE NOT NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (distribution_id),
              UNIQUE KEY uq_distributions_name (distribution_name),
              CONSTRAINT fk_distributions_section
                FOREIGN KEY (section_id) REFERENCES sections (section_id),
              CONSTRAINT fk_distributions_currency
                FOREIGN KEY (currency_id) REFERENCES currencies (currency_id),
              CONSTRAINT fk_distributions_company
                FOREIGN KEY (company_id) REFERENCES companies (company_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS distribution_details (
              distribution_detail_id INT NOT NULL AUTO_INCREMENT,
              distribution_id INT NOT NULL,
              work_id INT NOT NULL,
              prime_rate DECIMAL(12,2) NOT NULL DEFAULT 0,
              supreme_rate DECIMAL(12,2) NOT NULL DEFAULT 0,
              supreme_plus_rate DECIMAL(12,2) NOT NULL DEFAULT 0,
              collection_charge DECIMAL(12,2) NOT NULL DEFAULT 0,
              collection_percentage DECIMAL(6,2) NOT NULL DEFAULT 0,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (distribution_detail_id),
              UNIQUE KEY uq_distribution_details_work (distribution_id, work_id),
              CONSTRAINT fk_distribution_details_header
                FOREIGN KEY (distribution_id) REFERENCES distributions (distribution_id)
                ON DELETE CASCADE,
              CONSTRAINT fk_distribution_details_work
                FOREIGN KEY (work_id) REFERENCES works (work_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS branches (
              branch_id INT NOT NULL AUTO_INCREMENT,
              parent_company_id INT NOT NULL,
              branch_type_id INT NOT NULL,
              branch_name VARCHAR(150) NOT NULL,
              address1 VARCHAR(255) NOT NULL,
              address2 VARCHAR(255) NULL,
              place_id INT NOT NULL,
              region_id INT NOT NULL,
              state_id INT NOT NULL,
              country_id INT NOT NULL,
              pin VARCHAR(20) NOT NULL,
              phone VARCHAR(30) NULL,
              mobile VARCHAR(30) NULL,
              email VARCHAR(150) NULL,
              whatsapp_no VARCHAR(30) NULL,
              gst_no VARCHAR(50) NULL,
              distribution_id INT NULL,
              iso_number VARCHAR(50) NULL,
              ie_code VARCHAR(50) NULL,
              status ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (branch_id),
              UNIQUE KEY uq_branches_name_company (branch_name, parent_company_id),
              CONSTRAINT fk_branches_parent_company
                FOREIGN KEY (parent_company_id) REFERENCES companies (company_id),
              CONSTRAINT fk_branches_branch_type
                FOREIGN KEY (branch_type_id) REFERENCES branch_types (branch_type_id),
              CONSTRAINT fk_branches_place FOREIGN KEY (place_id) REFERENCES places (place_id),
              CONSTRAINT fk_branches_region FOREIGN KEY (region_id) REFERENCES regions (region_id),
              CONSTRAINT fk_branches_state FOREIGN KEY (state_id) REFERENCES states (state_id),
              CONSTRAINT fk_branches_country FOREIGN KEY (country_id) REFERENCES countries (country_id),
              CONSTRAINT fk_branches_distribution
                FOREIGN KEY (distribution_id) REFERENCES distributions (distribution_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
              customer_id INT NOT NULL AUTO_INCREMENT,
              branch_name VARCHAR(150) NOT NULL,
              contact_person VARCHAR(150) NULL,
              address VARCHAR(255) NOT NULL,
              address1 VARCHAR(255) NULL,
              place_id INT NOT NULL,
              route_id INT NOT NULL,
              region_id INT NOT NULL,
              state_id INT NOT NULL,
              country_id INT NOT NULL,
              currency_id INT NOT NULL,
              distribution_id INT NOT NULL,
              linked_branch_id INT NOT NULL,
              gst_no VARCHAR(50) NULL,
              phone VARCHAR(30) NULL,
              mobile VARCHAR(30) NULL,
              email VARCHAR(150) NULL,
              whatsapp_no VARCHAR(30) NULL,
              current_balance DECIMAL(14,2) NOT NULL DEFAULT 0,
              inclusive_tax TINYINT(1) NOT NULL DEFAULT 0,
              remarks VARCHAR(500) NULL,
              head_office_id INT NULL,
              billing_office_id INT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (customer_id),
              UNIQUE KEY uq_customers_name_branch (branch_name, linked_branch_id),
              CONSTRAINT fk_customers_place FOREIGN KEY (place_id) REFERENCES places (place_id),
              CONSTRAINT fk_customers_route FOREIGN KEY (route_id) REFERENCES routes (route_id),
              CONSTRAINT fk_customers_region FOREIGN KEY (region_id) REFERENCES regions (region_id),
              CONSTRAINT fk_customers_state FOREIGN KEY (state_id) REFERENCES states (state_id),
              CONSTRAINT fk_customers_country FOREIGN KEY (country_id) REFERENCES countries (country_id),
              CONSTRAINT fk_customers_currency FOREIGN KEY (currency_id) REFERENCES currencies (currency_id),
              CONSTRAINT fk_customers_distribution
                FOREIGN KEY (distribution_id) REFERENCES distributions (distribution_id),
              CONSTRAINT fk_customers_linked_branch
                FOREIGN KEY (linked_branch_id) REFERENCES branches (branch_id),
              CONSTRAINT fk_customers_head_office
                FOREIGN KEY (head_office_id) REFERENCES customers (customer_id),
              CONSTRAINT fk_customers_billing_office
                FOREIGN KEY (billing_office_id) REFERENCES customers (customer_id)
            )
            """
        )

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME = 'head_office_id'
            """
        )
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE customers ADD COLUMN head_office_id INT NULL")
            cursor.execute(
                """
                ALTER TABLE customers
                ADD CONSTRAINT fk_customers_head_office
                  FOREIGN KEY (head_office_id) REFERENCES customers (customer_id)
                """
            )

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'customers'
              AND COLUMN_NAME = 'billing_office_id'
            """
        )
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE customers ADD COLUMN billing_office_id INT NULL")
            cursor.execute(
                """
                ALTER TABLE customers
                ADD CONSTRAINT fk_customers_billing_office
                  FOREIGN KEY (billing_office_id) REFERENCES customers (customer_id)
                """
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schedulers (
              scheduler_id INT NOT NULL AUTO_INCREMENT,
              customer_id INT NOT NULL,
              route_id INT NOT NULL,
              fin_year VARCHAR(10) NOT NULL,
              order_no INT NOT NULL,
              mdo_code VARCHAR(80) NOT NULL,
              billing_party_id INT NOT NULL,
              sending_party_id INT NOT NULL,
              work_type ENUM('New', 'Repeat') NOT NULL DEFAULT 'New',
              work_received_date DATE NOT NULL,
              completion_date DATE NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (scheduler_id),
              UNIQUE KEY uq_schedulers_mdo_code (mdo_code),
              UNIQUE KEY uq_schedulers_route_year_order (route_id, fin_year, order_no),
              CONSTRAINT fk_schedulers_customer FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
              CONSTRAINT fk_schedulers_route FOREIGN KEY (route_id) REFERENCES routes (route_id),
              CONSTRAINT fk_schedulers_billing_party FOREIGN KEY (billing_party_id) REFERENCES customers (customer_id),
              CONSTRAINT fk_schedulers_sending_party FOREIGN KEY (sending_party_id) REFERENCES customers (customer_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_details (
              scheduler_detail_id INT NOT NULL AUTO_INCREMENT,
              scheduler_id INT NOT NULL,
              sl_no INT NOT NULL,
              work_no VARCHAR(100) NOT NULL,
              work_id INT NOT NULL,
              patient_name VARCHAR(150) NOT NULL,
              arch ENUM('Upper', 'Lower', 'Both') NOT NULL,
              quality_type_id INT NOT NULL,
              additional_requirements VARCHAR(500) NULL,
              rate DECIMAL(12,2) NOT NULL DEFAULT 0,
              qty DECIMAL(12,2) NOT NULL DEFAULT 1,
              extra_charge DECIMAL(12,2) NOT NULL DEFAULT 0,
              discount DECIMAL(12,2) NOT NULL DEFAULT 0,
              final_rate DECIMAL(12,2) NOT NULL DEFAULT 0,
              remarks VARCHAR(500) NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (scheduler_detail_id),
              UNIQUE KEY uq_scheduler_details_work_no (work_no),
              UNIQUE KEY uq_scheduler_details_sl (scheduler_id, sl_no),
              CONSTRAINT fk_scheduler_details_header
                FOREIGN KEY (scheduler_id) REFERENCES schedulers (scheduler_id)
                ON DELETE CASCADE,
              CONSTRAINT fk_scheduler_details_work FOREIGN KEY (work_id) REFERENCES works (work_id),
              CONSTRAINT fk_scheduler_details_quality
                FOREIGN KEY (quality_type_id) REFERENCES quality_types (quality_type_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_case_studies (
              case_id INT NOT NULL AUTO_INCREMENT,
              scheduler_detail_id INT NOT NULL,
              working_doctor_name VARCHAR(150) NULL,
              clinic_name VARCHAR(150) NULL,
              mobile_no VARCHAR(30) NULL,
              email_id VARCHAR(150) NULL,
              patient_name VARCHAR(150) NULL,
              age VARCHAR(20) NULL,
              sex ENUM('M', 'F') NULL,
              patient_availability VARCHAR(255) NULL,
              next_appointment_date DATE NULL,
              stl_model_quality ENUM('Good', 'Bad') NULL,
              chief_complaint VARCHAR(1000) NULL,
              other_concerns VARCHAR(1000) NULL,
              type_of_plan ENUM('BOTH ARCH', 'UPPER ARCH ONLY', 'LOWER ARCH ONLY') NULL,
              type_of_case_study ENUM('CASUAL REPORT', 'VIDEO REPORT') NULL,
              suggestions_from_doctor VARCHAR(1000) NULL,
              deciduous_tooth VARCHAR(255) NULL,
              rotation VARCHAR(255) NULL,
              molar_relation VARCHAR(255) NULL,
              overjet VARCHAR(255) NULL,
              overbite VARCHAR(255) NULL,
              missing_teeth VARCHAR(255) NULL,
              midline_shift VARCHAR(255) NULL,
              crossbite VARCHAR(255) NULL,
              arch_shape VARCHAR(255) NULL,
              deepbite VARCHAR(255) NULL,
              open_bite VARCHAR(255) NULL,
              spacing VARCHAR(255) NULL,
              caries_decay_root_stump VARCHAR(255) NULL,
              impaction VARCHAR(255) NULL,
              periodontal_status VARCHAR(255) NULL,
              extraction VARCHAR(255) NULL,
              rct VARCHAR(255) NULL,
              crown_bridge_implant VARCHAR(255) NULL,
              tongue_thrusting TINYINT(1) NOT NULL DEFAULT 0,
              bruxism VARCHAR(255) NULL,
              mouth_breathing TINYINT(1) NOT NULL DEFAULT 0,
              thumb_sucking TINYINT(1) NOT NULL DEFAULT 0,
              lip_biting TINYINT(1) NOT NULL DEFAULT 0,
              medications TEXT NULL,
              allergies ENUM('PLASTIC', 'METAL', 'LATEX', 'FOOD', 'MEDICATION') NULL,
              remarks VARCHAR(1000) NULL,
              approval_status ENUM('Pending', 'Approved') NOT NULL DEFAULT 'Pending',
              approved_at DATETIME NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (case_id),
              UNIQUE KEY uq_scheduler_case_detail (scheduler_detail_id),
              CONSTRAINT fk_scheduler_case_detail
                FOREIGN KEY (scheduler_detail_id) REFERENCES scheduler_details (scheduler_detail_id)
                ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'scheduler_case_studies'
              AND COLUMN_NAME = 'approval_status'
            """
        )
        if not cursor.fetchone():
            cursor.execute(
                """
                ALTER TABLE scheduler_case_studies
                ADD COLUMN approval_status ENUM('Pending', 'Approved') NOT NULL DEFAULT 'Pending',
                ADD COLUMN approved_at DATETIME NULL
                """
            )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduler_case_files (
              file_id INT NOT NULL AUTO_INCREMENT,
              scheduler_detail_id INT NOT NULL,
              file_kind ENUM('extra_oral', 'intra_oral', 'ceph', 'opg', 'video', 'concern_video') NOT NULL,
              file_path VARCHAR(255) NOT NULL,
              original_name VARCHAR(255) NULL,
              content_type VARCHAR(100) NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (file_id),
              CONSTRAINT fk_scheduler_case_files_detail
                FOREIGN KEY (scheduler_detail_id) REFERENCES scheduler_details (scheduler_detail_id)
                ON DELETE CASCADE
            )
            """
        )

        connection.commit()
    finally:
        cursor.close()
        connection.close()


@app.on_event("startup")
def on_startup():
    try:
        ensure_schema()
    except mariadb.Error as error:
        print(f"Warning: could not ensure schema on startup: {error}")


@app.get("/health")
def health():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        return {
            "status": "ok",
            "service": "backend",
            "database": "connected",
        }
    except Exception as error:
        return {
            "status": "degraded",
            "service": "backend",
            "database": "disconnected",
            "error": str(error),
        }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)


