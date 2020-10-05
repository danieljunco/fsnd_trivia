import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)

  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
      return response
  
  @app.route('/categories', methods=['GET'])
  def retrieve_categories():
    categories = [category.format() for category in Category.query.order_by(Category.id).all()]
    if len(categories) == 0:
      abort(404)

    formated_categories = {category["id"]: category["type"] for category in categories}

    return jsonify({
      'success': True,
      'categories': formated_categories,
      'total_categories': len(categories)
    })


  @app.route('/questions', methods=['GET'])
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    categories = [category.format() for category in Category.query.order_by(Category.id).all()]
    formated_categories = {category["id"]: category["type"] for category in categories}
    current_questions = paginate_questions(request, selection)

    if len(current_questions) == 0:
            abort(404)

    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection),
        'categories': formated_categories
    })

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def remove_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
          abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
          'success': True,
          'deleted': question_id,
          'questions': current_questions,
          'total_questions': len(Question.query.all())
      })

    except:
        abort(422)

  @app.route('/questions', methods=['POST'])
  def add_question():
    body = request.get_json()
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', 1)
    new_difficulty = body.get('difficulty', 1)

    if new_question is None or new_question is None:
      abort(400)

    question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
    question.insert()
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)

    return jsonify({
      'success': True,
      'created': question.id,
      'questions': current_questions,
      'total_questions': len(Question.query.all())
    })

  @app.route('/questions/search', methods=['POST'])
  def search_question():
    body = request.get_json()
    search_term = body.get('searchTerm', None)
    try:
        questions = Question.query.filter(Question.question.ilike("%"+ search_term + "%")).all()
        current_questions = paginate_questions(request, questions)
        return jsonify({
            'success': True,
            'questions': current_questions
        })
    except:
        abort(404)

  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def retrieve_questions_by_category(category_id):
    try:
      selection = Question.query.filter(Question.category == category_id).all()
      current_questions = paginate_questions(request, selection)
      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(Question.query.all()),
        'current_category': category_id
      })
    except:
      abort(422)

  @app.route('/play', methods=['POST'])
  def get_quiz_questions():
    body = request.get_json()
    if not body:
      abort(404)
    previous_question = body.get('previous_questions')
    category = body.get('quiz_category')['id']
    try:
      if category is None:
        if previous_question is not None:
          questions = Question.query.filter(Question.id.notin_(previous_question)).all()
        else:
          questions = Question.query.all()
      else:
        if previous_question is not None:
          questions = Question.query.filter(Question.id.notin_(previous_question), Question.category == category).all()
        else:
          questions = Question.query.filter(Question.category == category).all()
      if len(questions) > 0:
        new_question = questions[random.randrange(0, len(questions))].format()
        return jsonify({"question": new_question, "success": True})
      else:
        return jsonify({"question": None, "success": True})
    except:
      abort(400)

  
  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
          "success": False, 
          "error": 400,
          "message": "bad request"
      }), 400

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      'success': False,
      'error': 404,
      'message': 'resource not found'
    }), 404

  @app.errorhandler(422)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 422,
      'message': 'unprocessable'
    }), 422

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      'success': False,
      'error': 405,
      'message': 'method not allowed'
    }), 405
  
  return app

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]

    return questions[start:end]    
