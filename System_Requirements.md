# Phase II: User Requirements and Application Specifications

## 1. Development Model:
**Agile**

Agile is used as the development model because it supports an iterative and flexible approach to building the system. Instead of developing the entire application at once, the project is divided into smaller increments, allowing each feature (such as user registration, document submission, and messaging) to be designed, developed, and tested step by step. This approach makes it easier to adapt to changing requirements and incorporate feedback from users or supervisors throughout the development process. Additionally, Agile helps identify and resolve issues early, improving the overall quality of the system. Therefore, it is particularly suitable for this project, where continuous improvement, user interaction, and evolving requirements are essential.


## 2. User Requirements
### a) Stakeholders:
- Students: Students are the primary users of the system, using it to manage their thesis work. They register, submit thesis documents and updated versions, view deadlines, and communicate with supervisors. Their main interest is to track their progress, receive timely feedback, and successfully complete their thesis.
- Supervisor: Supervisors are responsible for guiding and evaluating students throughout their thesis process. They review submissions, provide feedback, set deadlines, and communicate with students. Their main interest is to monitor progress and ensure the quality and successful completion of student work.
- Administrator : Administrators manage the system and ensure its proper operation. They handle user accounts, assign supervisors to students, organize departments, and monitor system activity. Their main interest is to maintain system organization, security, and overall functionality.


### b) User Stories
#### Student
- As a student, I want to register, in order to access the system.  
- As a student, I want to submit the thesis progress so that my advisor can review it.  
- As a student, I want to communicate with my supervisor, so to recieve feedback from the supervisor.  
- As a student I want to view deadlines in order to manage my work.  
- As a student, I want to recieve notifications so that I can stay updated.  


#### Supervisor
- As a supervisor, I want to review student submissions so that I can evaluate the progress.  
- As a supervisor, I want to set deadlines, in order to view the progress of the assigned students.  
- As a supervisor, I want to provide feedback so the students can improve and modify their work.  
- As a supervisor, I want to arrange meetings, in order to communicate with the students regarding their progress.  


#### Administrator
- As an administrator, I want to manage user accounts, so that system access is controlled.  
- As an administrator, I want to assign supervisors to students, so that supervision is organized.  
- As an administrator, I want to create and manage academic departments, so that students and supervisors are properly organized.  
- As an administrator, I want to monitor system activity, so that I can ensure everything is functioning correctly.  


## 3. Functional Requirements
### Student
1. The Student registers an account by providing a full name, a unique email address, a password, and selecting the Student role; the system rejects registration if the email is already in use.  
2. The Student uploads their thesis document; the system stores the file and displays an error message for unsupported formats. 
3. The Student can submit an updated version of their thesis multiple times each new submission is stored as a separate version without overwriting any previous submission.  
4. The Student can view a chronological list of all their thesis submissions, showing for each entry the version number, upload date and time, and current review status.  
5. The Student can see the review status of each submission  Pending, Approved, or Rejected which updates automatically when the Supervisor takes action.  
6. The Student can read all feedback comments written by their Supervisor on any of their submissions, immediately after the Supervisor saves the feedback.  
7. The Student can view a list of all deadlines assigned to them by their Supervisor, showing the deadline title, due date, and a visual indicator of whether the deadline has passed.  
8. The Student can send text messages to their assigned Supervisor and can attach a single PDF file per message; the system rejects attachments that are not PDF or exceed 10 MB.  
9. The Student can update their full name, profile photo, and password from their account settings page at any time without administrator involvement.  

### Supervisor (Professor)
11. The Supervisor can view a list of all students assigned to them by the Administrator, displaying each student's full name, thesis title, date of last submission, and current submission status.  
12. The Supervisor can open and read any PDF submission from their assigned students within the system.  
13. The Supervisor can write a feedback comment on any student submission and save it the comment becomes immediately visible to the Student upon saving.  
14. The Supervisor can set the review status of a student submission to Approved or Rejected; the decision is recorded with the Supervisor's identity and the timestamp of the action.  
15. The Supervisor can assign a deadline to one or more of their assigned students by specifying a title, a due date, and an optional description of what must be completed.  
16. The Supervisor can edit or remove a deadline they previously assigned; any change triggers an in-app notification to all affected students.
17. The Supervisor can send text messages to any of their assigned students and can attach a single PDF file per message; the system rejects attachments that are not PDF or exceed 10 MB.  
18. The Supervisor receives an in-app notification whenever a student submits a new thesis version, so that no submission goes unnoticed.  
19. The Supervisor can view the full message history with each assigned student in chronological order.
20. The Supervisor can update their full name, profile photo, and password from their account settings page at any time without administrator involvement.  

### Administrator (Admin)
21. The Administrator can create a new user account by providing a full name, email address, temporary password, and role (Student or Supervisor).
22. The Administrator can edit the full name, email address, and role of any existing user account; changes take effect immediately and the affected user receives an in-app notification.  
23. The Administrator can delete a user account upon deletion all associated thesis submissions, feedback, and messages are anonymised rather than permanently erased, preserving the audit trail.  
24. The Administrator can assign a Supervisor to one or more Students using searchable dropdown lists the assignment is stored with the date it was made and can be changed or revoked at any time.  
25. The Administrator can view a complete list of all registered users filtered by role, showing each user's name, email address, assigned role, and account creation date.  
26. The Administrator can view a system-wide dashboard showing the total number of registered students, supervisors, thesis submissions, pending reviews, and approved or rejected submissions.  
27. The Administrator logs in using their registered email address and password; the login page does not expose the Admin role to public registration.  
28. The Administrator can update their own full name, profile photo, and password from the account settings page at any time.    
29. The Administrator can view and filter the full activity log by user, role, action type, or date range, enabling audit and oversight of all system activity.

## b. Acceptance Criteria for Functional Requirements

### Student / Supervisor / Administrator Login
- Registered email and correct password are entered  
- System verifies credentials against stored user records  
- System grants access based on assigned role  
- User is redirected to the corresponding dashboard  
- Error message is shown for invalid credentials  
- Account is locked after multiple failed attempts  



### Student Account Creation (Administrator)
- Administrator enters full name, email, temporary password, and role  
- System verifies that the email is unique  
- Account is created and stored in the database  
- User is prompted to change password on first login  
- Error is shown if email already exists  



### Upload Thesis Document (Student)
- Student selects a file for upload  
- System accepts only PDF format  
- File is stored and linked to the correct Student account  
- Error is shown for non-PDF files  



### Submit Thesis Version (Student)
- Student submits a thesis document  
- System stores it as a new version without overwriting previous versions  
- Version number and submission timestamp are recorded  
- Submission appears in the Student submission list  



### Messaging System (Student–Supervisor)
- Student and Supervisor exchange messages within the system  
- Messages are stored and displayed in chronological order  
- One PDF attachment (maximum 10MB) is allowed per message  
- Error is shown for invalid file type or file size  



### Deadlines Management (Supervisor)
- Supervisor creates a deadline with title and due date  
- Deadline is assigned to selected students  
- Deadline is visible in the Student dashboard  
- System indicates when the deadline has passed  



### Feedback and Review (Supervisor)
- Supervisor selects a student submission  
- Supervisor adds feedback and sets submission status (Approved / Rejected)  
- Feedback and status are stored and linked to the specific version  
- Student can view feedback and status immediately  



### Profile Management (All Roles)
- Student, Supervisor, or Administrator updates profile data (name, password, photo)  
- System validates and saves changes  
- Updated information is reflected immediately  



### Admin User Management (Administrator)
- Administrator creates, edits, or deletes user accounts  
- Changes are applied immediately in the system  
- Deleted accounts are anonymised  
- System records all administrative actions  



### Activity Log (System)
- System records all significant actions (login, submission, feedback, etc.)  
- Each log includes actor role, action type, and timestamp  
- Administrator can view and filter logs  


## 4. Non-Functional Requirements  
1. The system should load the dashboard within 3 seconds under normal conditions.
2. Notifications should appear within 5 seconds after the triggering actions.
3. The system should require authentication for all users.
4. The system should respond to user interactions such as button clicks or form submissions within 2 seconds.
5. The system should support at least 100 users without significant degradation in response time.
6. The system should ensure that users can access only data permitted by their role.
7. The system should enforce secure password rules such as the minimum length required or the complexity of the password.
8. The system should be available at least 97% of the time excluding scheduled maintenance.
9. The system shall maintain data consistency so that feedback, statuses, deadlines, and messages are saved correctly even in case of temporary interruptions.
10. The user interface should be simple so the students, supervisors and administrators can navigate the system with minimal training.
11. The system should provide clear error messages whenever an action fails.
12. The system should be responsive in order to be used on tablet, desktop and mobile devices.
13. The system should be able to support an increasing number of students and supervisors.
14. Changes to one module should not negatively affect unrelated modules.
15. The system should make important information and notifications easy to identify.
16. The system should maintain data consistency including file submissions, feedback, messages are saved correctly.
17. The system should limit the size of the uploaded files.
18. The system should save user actions without requiring the user to refresh the page.
19. The system should perform automatic data backups at regular intervals to prevent data loss.
20. The system should log important user actions and system events for monitoring and auditing purposes.


## b. Acceptance Criteria

### Dashboard Performance  
- User logs into the systems.
- User navigates the dashboard.
- System loads the dashboard within 3 seconds.
- All components of the dashboard are visible after loading.

### Role-based Access Control 
- User logs in with an assigned role.
- User accesses permitted features and data successfully.
- User attempts to access restricted data.
- System denies access to unauthorized data.
- Appropriate message is displayed for restricted access


### Usability – Responsiveness
- User performs an action in the system.
- System saves the action without requiring a manual page refresh.
- Updated information appears automatically on the screen.
- Saved data remains available when the page is reopened.

### Auto-Save Functionality
- User opens the system on a desktop device.
- User opens the system on a tablet device.
- User opens the system on a mobile device.
- Pages display correctly on each screen size.
- Navigation and main functions remain usable on all supported devices.

## 5. Application Specifications

## a) Architecture
The Thesis Progress Tracker follows a three-tier architecture consisting of a user interface, a backend and a database. The frontend is built using PHP and runs on the web server, generating the pages that users see in their browser. It sends requests to the backend, which is also developed using Python. The backend processes all requests, enforces role-based access control, handles file uploads, and communicates with the database. The database built with SQL stores all persistent data including user accounts, thesis submissions, feedback, messages, deadlines, and notifications. 

| Tier         | Component          | Responsibility                                                                 |
|--------------|--------------------|--------------------------------------------------------------------------------|
| Presentation | Frontend: HTML/CSS | Generates and displays the interface for all three user roles                  |
| Application  | Backend:Python/PHP | Processes requests, enforces rules, manages files and notifications            |
| Data         | Database (MySQL)   | Stores all persistent system data                                              |

## b) Database Model
The system uses a relational database with nine tables. There is no shared Users table each role has its own dedicated table that stores identity and login credentials directly. The table below describes the function of each table in the system.

| Table           | Function                                                                 |
|-----------------|--------------------------------------------------------------------------|
| Students        | Stores the identity and login credentials of all student users. Each student is linked to an assigned supervisor. |
| Supervisors     | Stores the identity and login credentials of all supervisor (professor) users. A supervisor can be linked to multiple students. |
| Administrators  | Stores the identity and login credentials of administrator users who manage user accounts, assignments, and deadlines. |
| Submissions     | Records every thesis document submitted by a student. Tracks the version number, submission date, and current review status (Pending, Approved, or Rejected). |
| Feedback        | Stores feedback comments written by a supervisor for a specific submission. Each record is permanently linked to the submission it addresses. |
| Messages        | Stores all chat messages exchanged between students and supervisors, including any attached PDF files. |
| Deadlines       | Stores academic deadlines created by a supervisor. All assigned students can view the deadlines in this table. |
| Notifications   | Stores in-app notifications sent to users when relevant events occur, such as new feedback, a deadline update, or a new message. |
| Meetings        | Records meeting appointments scheduled between a supervisor and a student, including date, time, and notes. |

## c) Technologies Used
The following languages and technologies are used for the implementation of the system:

| Category | Technology | Purpose                                                                 |
|----------|------------|-------------------------------------------------------------------------|
| Frontend | HTML/CSS   | Used to build the user interface pages that are served to and displayed in the user's browser for all three roles. |
| Backend  | Python/PHP | Used to implement the server-side logic, handle requests, manage file uploads, and enforce business rules. |
| Database | SQL        | Used to store and manage all system data including accounts, submissions, messages, deadlines, and notifications. |

## d) User Interface Design
The system provides a login page where users enter their email and password and select their role (Student, Supervisor, or Administrator) to access the system. 
 The Student interface includes a dashboard with sections for viewing submission status, upcoming deadlines, supervisor feedback, and a chat-style messaging area for communicating with the assigned supervisor.
 The Supervisor interface lists all assigned students and allows the supervisor to open each student's submissions, provide written feedback, approve or reject work, and schedule meetings.
 The Administrator interface provides a control panel for managing user accounts, assigning supervisors to students, setting deadlines, and monitoring system activity. All pages share a consistent navigation bar displaying the user's name and role, a notification indicator for unread updates, and a logout button. The design is kept simple and clear so that all users can navigate the system with minimal training.

## e) Security Measures

### Authentication
The system uses a single-phase authentication process. To access the system, users must enter their registered email address and password on the login page and select their role. The system verifies the credentials against the stored records and grants access only if they are correct. If the credentials are invalid, an error message is displayed. Sessions are invalidated automatically after a period of inactivity, requiring the user to log in again to continue.

### Password Encryption
All passwords are encrypted using the bcrypt hashing algorithm before being stored in the database. Bcrypt applies a unique salt to each password before hashing, which means that two users with identical passwords will have different stored values. This protects user credentials in the event of a database breach, as the original plaintext passwords cannot be recovered from the stored hashes.

### Role-Based Access Control 
The system enforces role-based access control to ensure that each user can only access the features and data permitted by their role. Students may only view their own submissions, deadlines, feedback, and messages. Supervisors may only access the submissions and communications of their directly assigned students. Administrators are the only role permitted to manage user accounts, assign supervisors to students, and access the activity log. Any request to access a resource outside a user's permitted role is rejected by the server.

### Database Security
The database is protected through several mechanisms. The system uses parameterised queries, which prevent SQL injection attacks by ensuring that user input is never directly included in database queries. Each role table enforces a UNIQUE constraint on the email field, preventing duplicate accounts at the database level. Uploaded thesis files are stored in a protected server directory that is not publicly accessible via URL. The database connection uses a dedicated account with the minimum required permissions, so that even if the application layer is compromised, critical database operations such as dropping tables remain inaccessible.
