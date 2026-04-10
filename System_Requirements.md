# Phase II: User Requirements and Application Specifications

## 1. Development Model:
**Agile**

Agile is used as the development model because it supports an iterative and flexible approach to building the system. Instead of developing the entire application at once, the project is divided into smaller increments, allowing each feature (such as user registration, document submission, and messaging) to be designed, developed, and tested step by step. This approach makes it easier to adapt to changing requirements and incorporate feedback from users or supervisors throughout the development process. Additionally, Agile helps identify and resolve issues early, improving the overall quality of the system. Therefore, it is particularly suitable for this project, where continuous improvement, user interaction, and evolving requirements are essential.


## 2. User Requirements
### a) Stakeholders:
- Students  
- Supervisor  
- Administrator  


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
2. The Student uploads their thesis document in PDF format only the system rejects any non-PDF file before saving and displays an error message specifying the accepted format.  
3. The Student can submit an updated version of their thesis multiple times each new submission is stored as a separate version without overwriting any previous submission.  
4. The Student can view a chronological list of all their thesis submissions, showing for each entry the version number, upload date and time, and current review status.  
5. The Student can see the review status of each submission  Pending, Approved, or Rejected which updates automatically when the Supervisor takes action.  
6. The Student can read all feedback comments written by their Supervisor on any of their submissions, immediately after the Supervisor saves the feedback.  
7. The Student can view a list of all deadlines assigned to them by their Supervisor, showing the deadline title, due date, and a visual indicator of whether the deadline has passed.  
8. The Student can send text messages to their assigned Supervisor and can attach a single PDF file per message; the system rejects attachments that are not PDF or exceed 10 MB.  
9. The Student can update their full name, profile photo, and password from their account settings page at any time without administrator involvement.  

### Supervisor (Professor)
11. The Supervisor can view a list of all students assigned to them by the Administrator, displaying each student's full name, thesis title, date of last submission, and current submission status.  
12. The Supervisor can open and read any PDF submission from their assigned students directly within the system browser view, without downloading the file.  
13. The Supervisor can write a feedback comment on any student submission and save it the comment becomes immediately visible to the Student upon saving.  
14. The Supervisor can set the review status of a student submission to Approved or Rejected; the decision is recorded with the Supervisor's identity and the timestamp of the action.  
15. The Supervisor can assign a deadline to one or more of their assigned students by specifying a title, a due date, and an optional description of what must be completed.  
16. The Supervisor can edit or remove a deadline they previously assigned; any change triggers an immediate in-app notification to all affected students.  
17. The Supervisor can send text messages to any of their assigned students and can attach a single PDF file per message; the system rejects attachments that are not PDF or exceed 10 MB.  
18. The Supervisor receives an in-app notification whenever a student submits a new thesis version, so that no submission goes unnoticed.  
19. The Supervisor can view the full message history with each assigned student in chronological order, with the 50 most recent messages loaded on first open and older messages accessible by scrolling up.  
20. The Supervisor can update their full name, profile photo, and password from their account settings page at any time without administrator involvement.  

### Administrator (Admin)
21. The Administrator can create a new user account by providing a full name, email address, temporary password, and role (Student or Supervisor) the system sends a welcome email prompting the user to change their password on first login.  
22. The Administrator can edit the full name, email address, and role of any existing user account; changes take effect immediately and the affected user receives an in-app notification.  
23. The Administrator can delete a user account upon deletion all associated thesis submissions, feedback, and messages are anonymised rather than permanently erased, preserving the audit trail.  
24. The Administrator can assign a Supervisor to one or more Students using searchable dropdown lists the assignment is stored with the date it was made and can be changed or revoked at any time.  
25. The Administrator can view a complete list of all registered users filtered by role, showing each user's name, email address, assigned role, and account creation date.  
26. The Administrator can view a system-wide dashboard showing the total number of registered students, supervisors, thesis submissions, pending reviews, and approved or rejected submissions.  
27. The Administrator logs in using their registered email address and password; the login page does not expose the Admin role to public registration.  
28. The Administrator can update their own full name, profile photo, and password from the account settings page at any time.  
29. The system automatically records an activity log entry for every significant action performed by any user  including login, logout, thesis submission, feedback submission, status change, deadline creation, and account modification  storing the actor's identity, action type, and timestamp.  
30. The Administrator can view and filter the full activity log by user, role, action type, or date range, enabling audit and oversight of all system activity.  


## b. Acceptance Criteria (When we know it WORKS correctly)
### User Login
**Acceptance Criteria:**
- User enters a valid email and password  
- System verifies credentials  
- User is redirected to the dashboard after login  
- Error message is shown for invalid credentials  
- Account is locked after multiple failed attempts  


### User Registration
**Acceptance Criteria:**
- User enters full name, email, password, and role  
- System checks if email is unique  
- Account is created successfully  
- Confirmation message is displayed  
- Error message is shown if email already exists  


### Upload Thesis Document
**Acceptance Criteria:**
- User selects a file to upload  
- System accepts only PDF format  
- File is uploaded successfully  
- Error message is shown for invalid file type  
- Uploaded file is saved in the system  


### Submit Thesis Version
**Acceptance Criteria:**
- User submits a new version of the thesis  
- System stores the submission as a new version  
- Previous versions remain unchanged  
- Submission timestamp is recorded  


### View Submissions
**Acceptance Criteria:**
- User can see a list of all submissions  
- Each submission shows version number and date  
- Submission status is displayed (Pending, Approved, Rejected)  


### Messaging System
**Acceptance Criteria:**
- User sends a message to another user  
- Message is delivered successfully  
- Message appears in conversation history  
- User can attach a PDF file  
- Error is shown if file exceeds allowed size  


### Deadlines Management
**Acceptance Criteria:**
- Supervisor creates a deadline  
- Deadline is visible to assigned students  
- Deadline shows title and due date  
- System indicates if deadline has passed  


### Feedback System
**Acceptance Criteria:**
- Supervisor writes feedback on submission  
- Feedback is saved successfully  
- Student can view feedback immediately  


### Profile Management
**Acceptance Criteria:**
- User updates profile information  
- Changes are saved successfully  
- Updated data is reflected immediately  


### Admin User Management
**Acceptance Criteria:**
- Admin creates a new user account  
- Admin edits user information  
- Admin deletes user account  
- Changes are applied immediately  


### Dashboard & Statistics
**Acceptance Criteria:**
- Data is displayed correctly  
- Information updates in real time  


### Activity Log
**Acceptance Criteria:**
- System records user actions  
- Each log includes user, action, and timestamp  
- Admin can view and filter logs  

