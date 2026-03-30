
# 1. Team Information 

## Team Name: ThesiFy  

## Team Leader: 
Kejtlin Bushi - GitHub: KejtlinBushi, Email: kbushi23@epoka.edu.al  

## All team members:
- Amanda Markeçi :&nbsp;&nbsp; GitHub: amarkeci23-collab &nbsp;&nbsp; Email: amarkeci23@epoka.edu.al 
- Floralba Shehu :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: FloralbaShehu   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: fshehu23@epoka.edu.al
- Kejtlin Bushi  :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: KejtlinBushi &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: kbushi23@epoka.edu.al
- Serena Korbi   :&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;   GitHub: Serenaskb   &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: skorbi23@epoka.edu.al
  

# 2. Project Details
## Project Title: Thesis Progress Tracker

## Problem Statement:  
In many universities in Albania, but not only, the process of supervising and managing student diploma theses is unstructured and relies mostly in communication channels such as email, paper submissions, and in-person meetings. For both students and academic supervisors, this method creates a number of significant challenges. Students lack a centralized platform to submit thesis documents, track their progress, and receive feedback from their assigned supervisor, while advisors have no unified way to monitor multiple students or manage deadlines effectively. A dedicated system is therefore needed to standardize the entire process of thesis supervision, ensuring transparency, avoiding miscommunication and avoid frequent delays in the thesis completion while all the parties are involved.

## Proposed Solution:
Our proposed solution is to create a Thesis Progress Tracker system that manages and centralizes the entire thesis supervision workflow. The system will provide a secure, role-based platform accessible to students, supervisors, and administrators, enabling effective communication, document management, and progress tracking throughout the thesis writing process.  

The system will allow the students and supervisors to create an account, log in and register in the system. At its core, the system enables the students to upload different documents in PDF or DOCX. A complete version of the history will be available for all the submissions made, ensuring that no revision is ever lost. On the other hand, advisors can download these documents, leave comments for each of them, and track the student responses. This practice aims to replace long inefficient emails. To keep the supervision process on schedule, the supervisors can set deadlines and specify thesis milestones for each phase in order to keep the process structured and easy to follow. Furthermore, a dashboard will give the supervisors an overview of every assigned student’s progress.

The system will allow the students to submit a meeting request to their supervisor, and once the meeting is confirmed each of the sessions will be recorded with its date, time and agenda notes. Throughout all of these activities, the system delivers real time emails whenever a document is submitted, feedback is provided, or even when a meeting is confirmed. This is designed in order to keep all the parties informed without requiring a manual follow-up. Access to all data is monitored based on the roles, ensuring that student’s documents, conversations and feedbacks remain visible only to the student, their assigned supervisor and the administrator.  
## Project Scope:  
The aim of the system is to design and develop a secure and user-friendly platform that significantly improves the supervision of the thesis process, benefiting all parties involved.  

**Objectives:**  
-	Develop a secure user authentication and profile management system for both students and advisors.
-	Implement a document management section with capabilities such as uploading and downloading documents in PDF and DOCX formats.
-	Build a feedback and communication system that allows advisors to comment on specific submitted documents and students to respond.
-	Create a milestone tracking module enabling advisors to define thesis phases, set deadlines, and monitor student's progress.
-	Implement a meeting scheduling feature allowing students to request meetings (in-person or online meetings) and advisors to confirm them with associated notes.
-	Develop an automated notification system delivering reminders/alerts for key events and for every action done in the system including submitted documets, comments, meeting requests and approval.
-	Ensure the system meets non-functional requirements including 99% availability, daily document backups, responsive design, and role-based access control.

## Application Description:  
The thesis progress tracker is a system designed to effectively manage all activities related to diploma thesis supervision. The system is built around three user roles such as: Student, Supervisor, and Administrator. Each user has their own specific capabilities and access rights.  
**System Users:**  
- **Student:** Each student can register and create a personal profile linked to their thesis project. They are allowed to upload documents related to their thesis in PDF or DOCX format and view the version history of their submissions. Furthermore, students can read and respond to supervisors' comments and feedback. They can also request and schedule meetings with their assigned supervisor and view confirmed meeting notes. Finally, they can easily monitor the milestones and deadlines through a personal dashboard and receive notifications for feedback/comments, confirmations, and upcoming deadlines.  
- **Supervisor:** Similar to students, supervisors can register and create a profile, where they are assigned to supervise one or more students. Supervisors can download and review students' submissions, leave comments on documents, and read student replies. They are capable of creating and assigning milestones with deadlines and view a summarizing dashboard with the students' current progress. The supervisor can confirm or decline meeting requests, adding the date, time, and notes.  
- **Administrator:** The administrator manages user accounts and assigns students to supervisors and oversees all thesis projects. The administrator has read access to all the submitted documents and communications for oversight purposes.

**Key Features:**  
In order to facilitate the entire thesis supervision lifecycle, the system provides six key features.  
**User Management** supports profile creation and role-based access for students, supervisors, and administrators.  
**Document Management** enables secure file uploads in PDF and Docx format, with version history.  
**Feedback and communication** provides a structured commenting system on submitted documents, allowing replies that keep all the feedback organized in one place.  
**Milestone Tracking** allows thesis phases to be defined with specific deadlines through a personalized dashboard.  
**Meeting Scheduling** offers a formal meeting requests and confirmation, with each session logged alongside its date and notes.  
Finally, a **notification** system delivers reminders while keeping informed every party without manual follow-up.

  
## 3.Roles and Task Distribution  
- Amanda Markeçi: Meeting Scheduling and Notifications.
Amanda is responsible for building the meeting request and its confirmation including the date, time and session notes, and implementing the notification system that triggers across all features.
- Floralba Shehu: User Management and Authentication.
Floralba is responsible for designing and implementing the login, registration and profile cration for all the roles involved in the system. Additionally, she will build the admin panel for managing all user accounts and assignments, and handle the role-based access through the system. 
- Kejtlin Bushi: Document Management and Feedback.
Kejtlin is responsible for building the file upload system supporting PDF and DOCX formats, and implementing a version history, and develop the document viewer and download functionality for advisors. Furthermore, is responsible for building the commenting system on the submitted documents.
- Serena Korbi:  Milestone Tracking.
Serena is responsible for implementing the milestone creation, deadline assignment functionality, and develop the progress dashboard for both students and advisor where they can view the progress of assigned tasks for each student.

**Shared roles by all team members:**
The whole team should collaborate on designing and agreeing on the database schema before the development of the system begins.

****Note:*** The responsibilities outlined above for each team member represent the initial task distribution and may evolve as the project progresses. All team members may take additional tasks based on the workloads or project needs.
