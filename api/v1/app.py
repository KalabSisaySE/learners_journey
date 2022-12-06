#!/usr/bin/python3
from datetime import datetime
from os import path
from uuid import uuid4
from flask import Flask, make_response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://kalab:root@localhost/the_journey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

cors = CORS(app, resources={r"/*": {"origins": "*"}})

db = SQLAlchemy(app=app)


class BaseModel:
    """the base for other classes"""

    id = db.Column(db.String(40), primary_key=True, default=str(uuid4()))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    def save(self):
        """saves the current object in storage"""
        with app.app_context():
            db.session.add(self)
            db.session.commit()

    def delete(self, id):
        """deletes the current object in storage"""
        with app.app_context():
            type(self).query.filter_by(id=id).delete()
            db.session.commit()
    
    def to_dict(self):
        """returns the dictionary representation of the instance"""
        new_dict = self.__dict__.copy()
        new_dict['__class__'] = str(type(self).__name__)
        
        if "created_at" in new_dict:
            new_dict["created_at"] = new_dict["created_at"].isoformat()
        if "updated_at" in new_dict:
            new_dict["updated_at"] = new_dict["updated_at"].isoformat()
        
        new_dict.pop('_sa_instance_state', None)

        return new_dict

class User(BaseModel, db.Model):
    """represents a user"""

    user_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return "user_name: {}, email: {}, pass: {}".format(self.user_name,
                                                           self.email,
                                                            self.password)

class Log(BaseModel, db.Model):
    """represents a log of a user"""

    user_id = db.Column(db.String(40), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('log', lazy=True))
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer)

    def __repr__(self):
        return "user_id: {}, title: {}, desc: {}, status: {}".format(self.user_id, self.title, self.description, self.status)

class Topic(BaseModel, db.Model):
    """represents a topic in a log"""

    log_id = db.Column(db.String(40), db.ForeignKey('log.id'), nullable=False)
    log = db.relationship('Log', backref=db.backref('topic', lazy=True))
    name = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return "log_id: {}, name: {}".format(self.log_id, self.name)


@app.route('/')
def index():
    return "<h1> <center> API RUNNING </center> </h1>"

@app.before_request
def log_request():
    if path.exists('tabular_log.txt'):
        with open('tabular_log.txt', 'a', encoding='utf-8') as f:
            template = '|{:<60} |{:<10} |{:<20}|\n'
            f.write(template.format(request.path, request.method ,datetime.now().strftime('%Y-%m-%d %H:%M')))
    else:
        with open('tabular_log.txt', 'w', encoding='utf-8') as f:
            f.write('*** REQUEST LOGS ***\n\n')
            template = '|{:<60} |{:<10} |{:<20}|\n'
            f.write(template.format('url', 'method', 'date'))
            f.write(template.replace(':', ':-').format('', '', ''))
            f.write(template.format(request.path, request.method ,datetime.now().strftime('%Y-%m-%d %H:%M')))


# Users Route
@app.route('/users/')
def get_users():
    
    new_list = []

    for user in User.query.all():
        new_dict = {}
        logs = []
        user = User.query.get_or_404(user.id)

        for log in Log.query.filter_by(user_id=user.id).all():
            topics = []
            for topic in Topic.query.filter_by(log_id=log.id).all():
                topics.append(topic.name)

            log_dict = log.to_dict().copy()
            log_dict['topics'] = topics
            logs.append(log_dict)

        new_dict = user.to_dict()
        new_dict['logs'] = logs
        
        new_list.append(new_dict)
    
    return jsonify(new_list)

@app.route('/users/<string:user_id>')
def get_user(user_id):

    new_dict = {}
    logs = []
    user = User.query.get_or_404(user_id)

    for log in Log.query.filter_by(user_id=user.id).all():
        topics = []
        for topic in Topic.query.filter_by(log_id=log.id).all():
            topics.append(topic.name)

        log_dict = log.to_dict().copy()
        log_dict['topics'] = topics
        logs.append(log_dict)

    new_dict = user.to_dict()
    new_dict['logs'] = logs

    return jsonify(new_dict)

@app.route('/users/', methods=['POST'])
def post_user():
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a json'}), 400)
    if not 'user_name' in request.get_json():
        return make_response(jsonify({'error': 'Missing user_name'}), 400) 
    if 'email' not in request.get_json():
        make_response(jsonify({'error': 'Missing email'}), 400)
    if 'password' not in request.get_json():
        make_response(jsonify({'error': 'Missing password'}), 400)
    
    for user in User.query.all():
        if user.email == request.get_json()['email']:
            return make_response(jsonify({'error': 'email already exists'}), 400)
        if user.user_name == request.get_json()['user_name']:
            return make_response(jsonify({'error': 'user_name already exists'}), 400)
    while True:
        id = uuid4()
        for user in User.query.all():
            if user.id == id:
                continue
        break

    new_user = User(id=id,
                    user_name=request.get_json()['user_name'],
                    email=request.get_json()['email'],
                    password=request.get_json()['password'])
    new_user.save()

    return make_response(jsonify({'success': 'new user added'}), 201)

@app.route('/users/<string:user_id>', methods=['PUT'])
def put_user(user_id):
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a json'}, 400))
    if not 'user_name' in request.get_json():
        return make_response(jsonify({'error': 'Missing user_name'}), 400) 
    if 'email' not in request.get_json():
        make_response(jsonify({'error': 'Missing email'}), 400)
    if 'password' not in request.get_json():
        make_response(jsonify({'error': 'Missing password'}), 400)
    
    
    with app.app_context():
        user = User.query.get_or_404(user_id)
        user.user_name = request.get_json()['user_name']
        user.email = request.get_json()['email']
        user.password = request.get_json()['password']
        user.updated_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
    
    return jsonify({'success': 'User Updated'})

@app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.delete(user.id)

    return jsonify({'sucess': 'user deleted successfully'})


# Logs route
@app.route('/logs/')
def get_logs():

    all_logs = []
    log_dict = {}
    for log in Log.query.all():
        topics = []
        for topic in Topic.query.filter_by(log_id=log.id).all():
            topics.append(topic.name)

        log_dict = log.to_dict()
        log_dict['topics'] = topics
        all_logs.append(log_dict)
    
    return jsonify(all_logs)

@app.route('/logs/<string:log_id>')
def get_log(log_id):
    log = Log.query.get_or_404(log_id)
    topics = []
    for topic in Topic.query.filter_by(log_id=log.id).all():
        topics.append(topic.name)
    
    log_dict = log.to_dict()
    log_dict['topics'] = topics 

    return jsonify(log_dict)

@app.route('/logs/', methods=['POST'])
def post_log():
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a json'}), 400)
    if 'user_id' not in request.get_json():
        return make_response(jsonify({'error': 'Missing user_id'}), 400)
    if 'title' not in request.get_json():
        return make_response(jsonify({'error': 'Missing title'}), 400)
    if 'description' not in request.get_json():
        return make_response(jsonify({'error': 'Missing description'}), 400)
    if 'status' not in request.get_json():
        return make_response(jsonify({'error': 'Missing status'}), 400)
    
    while True:
        id = str(uuid4())
        for log in Log.query.all():
            if log.id == id:
                continue
        break
    
    new_log = Log(id=id,
                  user_id=request.get_json()['user_id'],
                  title=request.get_json()['title'],
                  description=request.get_json()['description'],
                  status=request.get_json()['status'])
    new_log.save()

    return make_response(jsonify({'success': 'log created'}), 201)

@app.route('/logs/<string:log_id>', methods=['PUT'])
def put_log(log_id):
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a json'}), 400)
    if 'user_id' not in request.get_json():
        return make_response(jsonify({'error': 'Missing user_id'}), 400)
    if 'title' not in request.get_json():
        return make_response(jsonify({'error': 'Missing title'}), 400)
    if 'description' not in request.get_json():
        return make_response(jsonify({'error': 'Missing description'}), 400)
    if 'status' not in request.get_json():
        return make_response(jsonify({'error': 'Missing status'}), 400)
    if 'status' in request.get_json() and request.get_json()['status'] not in [1, 2, 3]:
        return make_response(jsonify({'error': 'Invalid Status'}), 400)
    with app.app_context():
        log = Log.query.get_or_404(log_id)
        log.user_id = request.get_json()['user_id']
        log.title = request.get_json()['title']
        log.description = request.get_json()['description']
        log.status = request.get_json()['status']
        log.updated_at = datetime.utcnow()
        db.session.add(log)
        db.session.commit()

    return jsonify({'success': 'log updated'})

@app.route('/logs/<string:log_id>', methods=['DELETE'])
def delete_log(log_id):
    log = Log.query.get_or_404(log_id)
    log.delete(log.id)

    return jsonify({'success': 'log deleted'})


# Topics route
@app.route('/topics/')
def get_topics():
    topics = []
    for topic in Topic.query.all():
        topics.append(topic.to_dict())

    return jsonify(topics) 

@app.route('/topics/<string:topic_id>')
def get_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)

    return jsonify(topic.to_dict())

@app.route('/topics/', methods=['POST'])
def post_topic():
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a valid json'}), 400)
    if 'log_id' not in request.get_json():
        return make_response(jsonify({'error': 'Missing log_id'}), 400)
    if 'name' not in request.get_json():
        return make_response(jsonify({'error': 'Missing name'}), 400)

    if len(Topic.query.filter_by(log_id=request.get_json()['log_id']).all()) >= 5:
        return make_response(jsonify({'error': 'maximum of 5 topics allowed per log'}), 400)

    while True:
        id = str(uuid4())
        for topic in Topic.query.all():
            if topic.id == id:
                continue
        break

    new_topic = Topic(id=id,
                      log_id=request.get_json()['log_id'],
                      name=request.get_json()['name'])
    new_topic.save()

    return make_response(jsonify({'success': 'topic created'}), 201)

@app.route('/topics/<string:topic_id>', methods=['PUT'])
def put_topics(topic_id):
    if not request.get_json():
        return make_response(jsonify({'error': 'Not a valid json'}), 400)
    if 'log_id' not in request.get_json():
        return make_response(jsonify({'error': 'Missing log_id'}), 400)
    if 'name' not in request.get_json():
        return make_response(jsonify({'error': 'Missing name'}), 400)
    
    with app.app_context():
        topic = Topic.query.get_or_404(topic_id)
        topic.log_id = request.get_json()['log_id']
        topic.name = request.get_json()['name']
        topic.updated_at = datetime.utcnow()
        db.session.add(topic)
        db.session.commit()

    return jsonify({'success': 'topic updated'})

@app.route('/topics/<string:topic_id>', methods=['DELETE'])
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    topic.delete(topic.id)

    return jsonify({'success': 'topic deleted'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)



