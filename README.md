# webapp

----
About the App:

- `this is a web api has crud functionality but without any UI`
- `It's developed with Python Flask, MySQL, SQLAlchemy`

API requirement:
- All API request/response payloads should be in JSON.
- Unauthenticated users can query info about any other user.
- Unauthenticated users can get all questions.
- A authenticated user can post a question.
- User who posted the question, can update or delete the question.
- A question that has 1 or more answer cannot be deleted.
    - Only the user who posted the question can update or delete the question. 
    - A new category that does not exist should be added to the system.
    - Category once added in the system cannot be updated or deleted.
    - Duplicate categories cannot exist in the system. Multiple users can refer to the same category in different questions.
    - The user who posted question can update or delete question categories.
- Question can have 0 or more answers.
    - A user who posted the question can post an answer to that question.
    - Any authenticated user can answer a question.
    - A user can update or delete answer they posted for a question.
- If a user tries to update or delete question/answer they did not post, they should get an error.

#Build & Deploy

- install python 3.x and pip in your machine

- run following command to setup and run app:

``python -m pip install --upgrade pip``

``pip install flask flask_sqlalchemy flask_marshmallow flask_httpauth marshmallow bcrypt``

- Have your mysql database running on localhost with root:root@localhost
- Goto the work directory and run:
``python app.py``

Enjoy
