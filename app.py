from flask import Flask, render_template, request, redirect, make_response
from flask_restful import Resource, Api, fields, marshal_with, reqparse
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
# from flask_cors import CORS
import json




# ----------- Configurations -----------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_database.sqlite3'
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()
api = Api(app)
# CORS(app)




# ----------- Models -----------
class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_number = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    courses = db.relationship("Course", backref="students", secondary="enrollment", cascade='all,delete')

class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_name = db.Column(db.String, nullable=False)
    course_description = db.Column(db.String)

class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.student_id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.course_id"), nullable=False)




# ----------- Exception Handling -----------
class FoundError(HTTPException):
    def __init__(self, status_code, message=''):
        self.response = make_response(message, status_code)

class NotGivenError(HTTPException):
    def __init__(self, status_code, error_code, error_message):
        message = {"error_code": error_code, "error_message": error_message}
        self.response = make_response(json.dumps(message), status_code)




# ----------- Output Feilds -----------
student_fields = {
    "student_id": fields.Integer,
    "first_name": fields.String,
    "last_name": fields.String,
    "roll_number": fields.String
}

course_fields = {
    "course_id": fields.Integer,
    "course_name": fields.String,
    "course_code": fields.String,
    "course_description": fields.String
}




# ----------- Parsers -----------
course_parse = reqparse.RequestParser()
course_parse.add_argument("course_name")
course_parse.add_argument("course_code")
course_parse.add_argument("course_description")

student_parse = reqparse.RequestParser()
student_parse.add_argument("first_name")
student_parse.add_argument("last_name")
student_parse.add_argument("roll_number")

enrollment_parse = reqparse.RequestParser()
enrollment_parse.add_argument("course_id")




# ----------- APIs -----------

class CourseAPI(Resource):

    # get deatails of a course
    @marshal_with(course_fields)
    def get(self, course_id):
        course = Course.query.filter(Course.course_id == course_id).first()

        if course:
            return course
        else:
            raise FoundError(status_code=404)
    

    # edit course 
    @marshal_with(course_fields)
    def put(self, course_id):
        # check given course id is present or not
        course = Course.query.filter(Course.course_id == course_id).first()

        # if not present raise exception, as data can't be changed if id is not present
        if course is None:
            raise FoundError(status_code=404)
        
        # if present, take arguments
        args = course_parse.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)

        # if name is not given as an argument raise an error, as name is mandatory
        if course_name is None:
            raise NotGivenError(status_code=400, error_code="COURSE001", error_message="Course Name is required")
        
        # if code is not given as an argument raise an error, as code is mandatory
        elif course_code is None:
            raise NotGivenError(status_code=400, error_code="COURSE002", error_message="Course Code is required")
        
        # everything is fine update it
        else:
            course.course_name = course_name
            course.course_code = course_code
            course.course_description = course_description
            db.session.add(course)
            db.session.commit()
            return course
        

    # delete course
    def delete(self, course_id):
        # check if course exists
        course = Course.query.filter(Course.course_id == course_id).scalar()

        # if not present raise exception, as data can't be deleted if id is not present
        if course is None:
            raise FoundError(status_code=404)

        # if present, delete it
        db.session.delete(course)
        db.session.commit()
        return "", 200
        

    # add course
    @marshal_with(course_fields)
    def post(self):
        # take all arguments from user
        args = course_parse.parse_args()
        course_name = args.get("course_name", None)
        course_code = args.get("course_code", None)
        course_description = args.get("course_description", None)

        # check whether name is empty or not, if it is, raise exception
        if course_name is None:
            raise NotGivenError(status_code=400, error_code="COURSE001", error_message="Course Name is required")
        
        # check whether code is empty or not, if it is, raise exception
        if course_code is None:
            raise NotGivenError(status_code=400, error_code="COURSE002", error_message="Course Code is required")
        
        # check whether any course has same given code
        course = Course.query.filter(Course.course_code == course_code).first()

        # if not, add the course
        if course is None:
            course = Course(course_name = course_name, course_code = course_code, course_description = course_description)
            db.session.add(course)
            db.session.commit()
            return course, 201

        # otherwise raise exception and code must be unique
        else:
            raise FoundError(status_code=409)



class StudentAPI(Resource):

    # get deatails of a student
    @marshal_with(student_fields)
    def get(self, student_id):
        student = Student.query.filter(Student.student_id == student_id).first()
        if student:
            return student
        else:
            raise FoundError(status_code=404)


    # edit student
    @marshal_with(student_fields)
    def put(self, student_id):
        # check given student id is present or not
        student = Student.query.filter(Student.student_id == student_id).first()

        # if not present raise exception, as data can't be changed if id is not present
        if student is None:
            raise FoundError(status_code=404)
        
        # if present, take arguments
        args = student_parse.parse_args()
        first_name = args.get("first_name", None)
        last_name = args.get("last_name", None)
        roll_number = args.get("roll_number", None)

        # if roll_number is not given as an argument raise an error, as roll_number is mandatory
        if roll_number is None:
            raise NotGivenError(status_code=400, error_code="STUDENT001", error_message="Roll Number is required")
        
        # if first_name is not given as an argument raise an error, as first_name is mandatory
        elif first_name is None:
            raise NotGivenError(status_code=400, error_code="STUDENT002", error_message="First Name is required")
        
        # everything is fine update it
        else:
            student.first_name = first_name
            student.last_name = last_name
            student.roll_number = roll_number
            db.session.add(student)
            db.session.commit()
            return student


    # delete student
    def delete(self, student_id):
        # check whether student_id exists
        student = Student.query.filter(Student.student_id == student_id).scalar()

        # if not present raise exception, as data can't be deleted if id is not present
        if student is None:
            raise FoundError(status_code=404)

        # if present, delete it
        db.session.delete(student)
        db.session.commit()
        return "", 200


    @marshal_with(student_fields)
    # add student
    def post(self):
        # take all arguments from user
        args = student_parse.parse_args()
        first_name = args.get("first_name", None)
        last_name = args.get("last_name", None)
        roll_number = args.get("roll_number", None)

        # if roll_number is not given as an argument raise an error, as roll_number is mandatory
        if roll_number is None:
            raise NotGivenError(status_code=400, error_code="STUDENT001", error_message="Roll Number is required")
        
        # check whether first name is empty or not, if it is, raise exception
        if first_name is None:
            raise NotGivenError(status_code=400, error_code="STUDENT002", error_message="First Name is required")
        
        # check whether any student has same given roll number
        student = Student.query.filter(Student.roll_number == roll_number).first()

        # if not, add student
        if student is None:
            student = Student(first_name = first_name, last_name = last_name, roll_number = roll_number)
            db.session.add(student)
            db.session.commit()
            return student, 201

        # otherwise raise exception and roll number must be unique
        else:
            raise FoundError(status_code=409)
   


class EnrollmentAPI(Resource):

    # get the list of enrollments, the student is enrolled in
    def get(self, student_id):
        # check whether the student_id is valid or not; if not valid raise exception
        student = Student.query.filter(Student.student_id == student_id).first()
        if student is None:
            raise NotGivenError(status_code=400, error_code="ENROLLMENT002", error_message="Student does not exist.")
                
        # check whether student id is present or not
        enrollments = Enrollment.query.filter(Enrollment.student_id == student_id).all()

        # if present, do followings
        if enrollments:
            enrolls = []
            # loop runs for each enrollments
            for enrollment in enrollments:
                enrolls.append({"enrollment_id": enrollment.enrollment_id, "student_id": enrollment.student_id, "course_id": enrollment.course_id})
            return enrolls
        
        # if student_id not present us enrollment, raise exception
        else:
            raise FoundError(status_code=404) 


    # Add student enrollment
    def post(self, student_id):
        # check whether student id is present or not
        student = Student.query.filter(Student.student_id == student_id).first()

        # if present, do followings
        if student:
            args = enrollment_parse.parse_args()
            course_id = args.get("course_id", None)
            
            # check whether course_id is valid or not
            course = Course.query.filter(Course.course_id == course_id).first()
                
            # if valid
            if course:
                # add enrollment
                enroll = Enrollment(student_id=student_id, course_id=course_id) 
                db.session.add(enroll)
                db.session.commit()
                    
            # if course_id is not valid
            else:
                raise NotGivenError(status_code=400, error_code="ENROLLMENT001", error_message="Course does not exist")
            
            return [{"enrollment_id": enroll.enrollment_id, "student_id": enroll.student_id, "course_id": enroll.course_id}], 201
        
        # if student_id not present, raise exception
        else:
            raise FoundError(status_code=404) 


    # delete enrollment
    def delete(self, student_id, course_id):
        # check whether course_id is valid or not, 
        course = Course.query.filter(Course.course_id == course_id).first()
        if course is None:
            raise NotGivenError(status_code=400, error_code="ENROLLMENT001", error_message="Course does not exist")

        # check whether the student_id is valid or not; if not valid raise exception
        student = Student.query.filter(Student.student_id == student_id).first()
        if student is None:
            raise NotGivenError(status_code=400, error_code="ENROLLMENT002", error_message="Student does not exist.")
                
        # check whether student id is present in enrollment or not
        enrollments = Enrollment.query.filter(Enrollment.student_id == student_id).all()

        # if enrollments not empty
        if enrollments:
            for enroll in enrollments:
                if enroll.course_id == course_id:
                    db.session.delete(enroll)
            db.session.commit()
            
            
        
        # if student_id not present us enrollment, raise exception
        else:
            raise FoundError(status_code=404)




# Adding the resources to the API
api.add_resource(CourseAPI, "/api/course/<int:course_id>", "/api/course")
api.add_resource(StudentAPI, "/api/student/<int:student_id>", "/api/student")
api.add_resource(EnrollmentAPI, "/api/student/<int:student_id>/course", "/api/student/<int:student_id>/course/<int:course_id>")




if __name__ == '__main__':
    app.run(debug=True, port=5000)