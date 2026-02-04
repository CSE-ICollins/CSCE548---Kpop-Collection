# K-pop Album Collection Database

## Overview
This project is a relational database designed to track my personal K-pop album collection.
It stores artists, albums, multiple album editions, the items included with each edition
(photocards, posters, lyric books), and which editions I personally own.

## Tools Used
- PostgreSQL
- Python 3
- psycopg2

## Database Design
- artists → albums → editions → inclusions
- collection tracks owned album editions and their condition

## AI Assistance
AI was used to help generate the initial database schema, sample data, and a basic
console-based Python application. The generated code was reviewed and adjusted to
fit the assignment requirements.

## Limitations
The seed data is generic and meant for demonstration. Real album data could be added
manually in the future. The application uses a console interface instead of a GUI.

## Conclusion
This project demonstrates relational design, foreign keys, test data population,
and basic CRUD access through a Python application.

## Reflection
The AI-generated output provided a solid starting point for the database schema and sample data.
Some adjustments were needed to ensure foreign keys and constraints aligned correctly.
Overall, the AI was effective for rapid prototyping, but manual review was necessary to ensure correctness.
