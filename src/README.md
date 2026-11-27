# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements with optional start dates and required expiration dates
- Signed-in teachers can create, edit, and delete announcements

## Getting Started

1. Install the dependencies from the repository root:

   ```
   pip install -r requirements.txt
   ```

2. Ensure MongoDB is running locally at `mongodb://localhost:27017`.

3. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements`                                                  | Get currently active announcements                                 |
| GET    | `/announcements/manage`                                           | List all announcements (bearer session required)                   |
| POST   | `/announcements`                                                  | Create an announcement (bearer session required)                   |
| PUT    | `/announcements/{announcement_id}`                               | Update an announcement (bearer session required)                   |
| DELETE | `/announcements/{announcement_id}`                                | Delete an announcement (bearer session required)                   |

Sign in through `/auth/login` to receive the bearer session token. Send it in
the `Authorization: Bearer <token>` header for announcement management; sessions
expire after seven days and are revoked when the teacher logs out.

Announcement writes accept a JSON body with a `message`, an optional `start_date`
(`YYYY-MM-DD`), and a required `expiration_date` (`YYYY-MM-DD`). The example
announcement is inserted automatically when the announcements collection is empty.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activities, teacher accounts, and announcements are stored in MongoDB. Sample data,
including an example announcement, is initialized when the corresponding collection
is empty.
