-- ============================================================
-- Thesis Progress Tracker - Database Schema
-- CEN 302 Software Engineering | Group III | Epoka University
-- ============================================================

-- Step 1: Create the database
CREATE DATABASE IF NOT EXISTS thesis_tracker;
USE thesis_tracker;

-- ─────────────────────────────────────────────────────────────
-- Table 1: students
-- Stores all registered student accounts
-- ─────────────────────────────────────────────────────────────
CREATE TABLE students (
    student_id      INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(120)    NOT NULL,
    email           VARCHAR(180)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    thesis_title    VARCHAR(300)    DEFAULT NULL,
    supervisor_id   INT             DEFAULT NULL,
    profile_photo   VARCHAR(255)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id),
    UNIQUE KEY (email)
);

-- ─────────────────────────────────────────────────────────────
-- Table 2: supervisors
-- Stores all supervisor accounts
-- ─────────────────────────────────────────────────────────────
CREATE TABLE supervisors (
    supervisor_id   INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(120)    NOT NULL,
    email           VARCHAR(180)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    department      VARCHAR(120)    DEFAULT NULL,
    profile_photo   VARCHAR(255)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (supervisor_id),
    UNIQUE KEY (email)
);

-- ─────────────────────────────────────────────────────────────
-- Table 3: administrators
-- Stores administrator accounts (managed by the system)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE administrators (
    admin_id        INT             NOT NULL AUTO_INCREMENT,
    full_name       VARCHAR(120)    NOT NULL,
    email           VARCHAR(180)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    profile_photo   VARCHAR(255)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (admin_id),
    UNIQUE KEY (email)
);

-- ─────────────────────────────────────────────────────────────
-- Table 4: submissions
-- Stores thesis documents uploaded by students
-- Each upload gets a version number automatically
-- ─────────────────────────────────────────────────────────────
CREATE TABLE submissions (
    submission_id   INT             NOT NULL AUTO_INCREMENT,
    student_id      INT             NOT NULL,
    version_number  INT             NOT NULL DEFAULT 1,
    file_path       VARCHAR(500)    NOT NULL,
    file_name       VARCHAR(255)    NOT NULL,
    file_type       ENUM('PDF','DOCX') NOT NULL,
    file_size_kb    INT             NOT NULL,
    description     TEXT            DEFAULT NULL,
    status          ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
    submitted_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (submission_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 5: feedback
-- Stores supervisor feedback/comments on submissions
-- ─────────────────────────────────────────────────────────────
CREATE TABLE feedback (
    feedback_id     INT             NOT NULL AUTO_INCREMENT,
    submission_id   INT             NOT NULL,
    supervisor_id   INT             NOT NULL,
    comment         TEXT            NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (feedback_id),
    FOREIGN KEY (submission_id) REFERENCES submissions(submission_id) ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 6: messages
-- Stores chat messages between students and supervisors
-- ─────────────────────────────────────────────────────────────
CREATE TABLE messages (
    message_id      INT             NOT NULL AUTO_INCREMENT,
    sender_role     ENUM('student','supervisor') NOT NULL,
    sender_id       INT             NOT NULL,
    receiver_role   ENUM('student','supervisor') NOT NULL,
    receiver_id     INT             NOT NULL,
    body            TEXT            NOT NULL,
    attachment_path VARCHAR(500)    DEFAULT NULL,
    attachment_name VARCHAR(255)    DEFAULT NULL,
    sent_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read         TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (message_id)
);

-- ─────────────────────────────────────────────────────────────
-- Table 7: deadlines
-- Supervisors create deadlines for their students
-- ─────────────────────────────────────────────────────────────
CREATE TABLE deadlines (
    deadline_id     INT             NOT NULL AUTO_INCREMENT,
    supervisor_id   INT             NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    description     TEXT            DEFAULT NULL,
    due_date        DATE            NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (deadline_id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 8: deadline_assignments
-- Links which deadlines are assigned to which students
-- ─────────────────────────────────────────────────────────────
CREATE TABLE deadline_assignments (
    id              INT             NOT NULL AUTO_INCREMENT,
    deadline_id     INT             NOT NULL,
    student_id      INT             NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY (deadline_id, student_id),
    FOREIGN KEY (deadline_id) REFERENCES deadlines(deadline_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)  REFERENCES students(student_id)   ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 9: meetings
-- Stores meeting requests and scheduled meetings
-- ─────────────────────────────────────────────────────────────
CREATE TABLE meetings (
    meeting_id      INT             NOT NULL AUTO_INCREMENT,
    supervisor_id   INT             NOT NULL,
    student_id      INT             NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    meeting_date    DATE            NOT NULL,
    meeting_time    TIME            NOT NULL,
    location        VARCHAR(200)    DEFAULT NULL,
    meeting_type    ENUM('online','in_person') NOT NULL DEFAULT 'online',
    status          ENUM('Requested','Pending','Confirmed','Declined','Cancelled','Scheduled') NOT NULL DEFAULT 'Requested',
    agenda_notes    TEXT            DEFAULT NULL,
    session_notes   TEXT            DEFAULT NULL,
    requested_by    ENUM('student','supervisor') NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (meeting_id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES students(student_id)       ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 10: notifications
-- In-app notifications sent to students, supervisors, admins
-- ─────────────────────────────────────────────────────────────
CREATE TABLE notifications (
    notif_id        INT             NOT NULL AUTO_INCREMENT,
    user_role       ENUM('student','supervisor','admin') NOT NULL,
    user_id         INT             NOT NULL,
    type            VARCHAR(60)     NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    message         TEXT            NOT NULL,
    is_read         TINYINT(1)      NOT NULL DEFAULT 0,
    ref_id          INT             DEFAULT NULL,
    delivered_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notif_id)
);

-- ─────────────────────────────────────────────────────────────
-- Table 11: milestones
-- Thesis milestones set by supervisors for each student
-- ─────────────────────────────────────────────────────────────
CREATE TABLE milestones (
    milestone_id    INT             NOT NULL AUTO_INCREMENT,
    supervisor_id   INT             NOT NULL,
    student_id      INT             NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    description     TEXT            DEFAULT NULL,
    due_date        DATE            NOT NULL,
    status          ENUM('Not Started','In Progress','Completed','Overdue') NOT NULL DEFAULT 'Not Started',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (milestone_id),
    FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES students(student_id)       ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Table 12: activity_log
-- Records all important actions in the system for audit
-- ─────────────────────────────────────────────────────────────
CREATE TABLE activity_log (
    log_id          INT             NOT NULL AUTO_INCREMENT,
    actor_role      ENUM('student','supervisor','admin','system') NOT NULL,
    actor_id        INT             DEFAULT NULL,
    action_type     VARCHAR(80)     NOT NULL,
    description     TEXT            NOT NULL,
    ip_address      VARCHAR(45)     DEFAULT NULL,
    logged_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id)
);

-- ─────────────────────────────────────────────────────────────
-- Table 13: supervisor_assignments
-- Admin assigns supervisors to students through this table
-- ─────────────────────────────────────────────────────────────
CREATE TABLE supervisor_assignments (
    id              INT             NOT NULL AUTO_INCREMENT,
    student_id      INT             NOT NULL,
    supervisor_id   INT             NOT NULL,
    assigned_by     INT             NOT NULL,
    assigned_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (student_id),
    FOREIGN KEY (student_id)    REFERENCES students(student_id)       ON DELETE CASCADE,
    FOREIGN KEY (supervisor_id) REFERENCES supervisors(supervisor_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by)   REFERENCES administrators(admin_id)   ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────
-- Insert default admin account
-- Email: admin@thesis.edu | Password: Admin@1234
-- ─────────────────────────────────────────────────────────────
INSERT INTO administrators (full_name, email, password_hash)
VALUES (
    'System Administrator',
    'admin@thesis.edu',
    '$2b$12$0G0AhEO609jv9331mlLdUuTudMEPH3A4KrtPIMdXTclj1nyfwQO52'
);
-- Add percentage progress to milestones (supervisor assigns 0-100)
ALTER TABLE milestones 
  ADD COLUMN IF NOT EXISTS progress_pct INT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS supervisor_comment TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS grade VARCHAR(10) DEFAULT NULL;
 
-- Add grade + comment to deadline_assignments
ALTER TABLE deadline_assignments
  ADD COLUMN IF NOT EXISTS grade        VARCHAR(10)  DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS comment      TEXT         DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS submitted_at DATETIME     DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS graded_at    DATETIME     DEFAULT NULL;
 