# Student Images Directory

This directory stores images and face encodings for registered students.

## Contents

- Student facial images (format: `student_id.jpg`)
- Face encodings for recognition (format: `student_id_encoding.pkl`)
- `students.json` - Database of student information

## Notes

- Do not manually edit or delete files in this directory
- Images are automatically captured and saved during student registration
- Face encodings are serialized using pickle for efficient storage and retrieval
