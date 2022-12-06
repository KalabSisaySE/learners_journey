from flask import Flask, render_template, request, redirect, make_response, url_for, session
import requests
from datetime import datetime
from flask_session import Session


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app=app)


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('user_home'))
    return render_template('home.html')

@app.route('/logout')
def logout():
    session['user_id'] = None
    return redirect(url_for('index'))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form['email']:
            email = request.form['email']
        else:
            return render_template('login.html', alert="empty email")
        
        if request.form['password']:
            password = request.form['password']
        else:
            return render_template('login.html', alert="empty password")

        url = "http://127.0.0.1:5000/users/"

        response = requests.get(url=url)

        for user in response.json():
            if user['email'] == email:
                if user['password'] == password:
                    user_id = user['id']
                    session['user_id'] = user_id
                    return redirect('/user_home') 

        return render_template('login.html', alert="Incorrect username or password")

    return render_template('login.html')

@app.route('/sign-up', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        if request.form['user_name']:
            user_name = request.form['user_name']
        else:
            return render_template('sign_up.html', alert="Empty Username")
        
        if request.form['email']:
            email = request.form['email']
        else:
            return render_template('sign_up.html', alert="Empty Email")
        
        if request.form['password']:
            password = request.form['password']
        else:
            return render_template('sign_up.html', alert="Empty Password")
        
        url = "http://127.0.0.1:5000/users/"
        user = {
                "user_name": user_name,
                "email": email,
                "password": password
        }
        
        response = requests.post(url=url, json=user)
        
        if response.status_code == 201:
            return redirect(url_for('login'))
        elif response.status_code == 400:
            return render_template('sign_up.html', alert=response.json()['error'])
    
    return render_template('sign_up.html')
    
@app.route('/user_home')
def user_home():
    if session.get('user_id'):
        url = 'http://127.0.0.1:5000/users/{}'.format(session.get('user_id'))
        response = requests.get(url=url)
        if response.status_code == 200:
            # sort the logs based on date before passing it
            user_info = response.json().copy()
            user_info['logs'] = sorted(user_info['logs'], key=lambda x: datetime.strptime(x['updated_at'], '%Y-%m-%dT%H:%M'), reverse=True)

            return render_template('user_home.html', user=user_info, message=None)

    return redirect(url_for('index'))

@app.route('/log', methods =["GET", "POST"])
def log():
    if session.get('user_id'):
        user_id = session.get('user_id')
        
        if request.method == "POST":
            if request.form['title']:
                title = request.form['title']
            else:
                title = str(datetime.now()).split(' ')[0] + "'s Log"

            if request.form['description']:
                description = request.form['description']
            else:
                return render_template('log.html', alert="description can not be empty")
            
            if request.form['topic']:
                topic = request.form['topic']
            else:
                return render_template('log.html', alert="you need to enter at least one topic")
            
            if not request.form['mood']:
                return render_template('log.html', alert="mood can not be empty")
            elif request.form['mood'] not in ['1', '2', '3']:
                return render_template('log.html', alert="mood can only be 1 or 2 or 3")
            elif request.form['mood'] :
                mood = request.form['mood']
            
            log_url = "http://127.0.0.1:5000/logs/"

            log =  {
                "title": title,
                "description": description,
                "status": int(mood),
                "user_id": user_id
            }

            log_response = requests.post(url=log_url, json=log)
            if log_response.status_code == 201:
                topics = topic.split(',')
                if len(topics) > 5:
                    return render_template('log.html', alert="you can not enter morethan 5 topics per log")
                
                topic_url = 'http://127.0.0.1:5000/topics/'

                for top in topics:
                    topic_json = {
                        "log_id": log_response.json()['success'],
                        "name": top.strip()
                    }
                    topic_response = requests.post(url=topic_url, json=topic_json)
                    if topic_response.status_code != 201:
                        return render_template('log.html', alert="Failed to Log topics")

                return redirect(url_for("user_home"))

            return render_template('log.html', alert="Failed to Log")

        return render_template('log.html', message='')

@app.route('/user_account', methods=["GET", "POST"])
def user_account():
    if session.get('user_id'):
        response = requests.get(url="http://127.0.0.1:5000/users/{}".format(session.get('user_id')))
        if response.status_code == 200:
            return render_template("view_account.html", user=response.json())

    return render_template('404.html', alert="Failed to show user account")

@app.route('/view_log/<string:log_id>')
def view_log(log_id):
    response = requests.get(url='http://127.0.0.1:5000/logs/{}'.format(log_id))
    if response.status_code == 200:
        return render_template('view_log.html', log=response.json())

@app.route('/all_logs')
def all_logs():
    if session.get('user_id'):
        response = requests.get(url='http://127.0.0.1:5000/users/{}'.format(session.get('user_id')))
        return render_template('all_logs.html', logs=response.json()['logs'])
    return redirect(url_for('index'))

@app.route('/filter_logs/<string:filter_type>')
def filter_logs(filter_type):
    if session.get('user_id'):
        url = 'http://127.0.0.1:5000/users/{}'.format(session.get('user_id'))
        response = requests.get(url=url)
        if response.status_code == 200:
            if filter_type == 'title':
                logs = sorted(response.json()['logs'], key=lambda x: x['title'])
            elif filter_type == 'created_at':
                logs = sorted(response.json()['logs'], key=lambda x: datetime.strptime(x['created_at'], '%Y-%m-%dT%H:%M'), reverse=True)
            elif filter_type == 'updated_at':
                logs = sorted(response.json()['logs'], key=lambda x: datetime.strptime(x['updated_at'], '%Y-%m-%dT%H:%M'), reverse=True)    

            return render_template('all_logs.html', logs=logs, message=None)

    return redirect(url_for('index'))



@app.route('/edit_log/<string:log_id>', methods=["GET", "POST"])
def edit_log(log_id):
    if session.get('user_id'):

        user_id = session.get('user_id')
        response = requests.get(url='http://127.0.0.1:5000/logs/{}'.format(log_id))
        
        if request.method == "POST":
            if request.form['title']:
                title = request.form['title']
            else:
                title = str(datetime.now()).split(' ')[0] + " 's Log (UPDATED)"

            if request.form['description']:
                description = request.form['description']
            else:
                return render_template('edit_log.html', alert="description can not be empty", log=response.json())
            
            if request.form['topic']:
                topic = request.form['topic']
            else:
                return render_template('edit_log.html', alert="you need to enter at least one topic", log=response.json())

            if not request.form['mood']:
                return render_template('edit_log.html', alert="mood can not be empty", log=response.json())
            elif request.form['mood'] not in ['1', '2', '3']:
                return render_template('log.html', alert="mood can only be 1 or 2 or 3", log=response.json())
            elif request.form['mood'] :
                mood = request.form['mood']

            log_url = "http://127.0.0.1:5000/logs/{}".format(log_id)

            log =  {
                "title": title,
                "description": description,
                "status": int(mood),
                "user_id": user_id
            }

            log_response = requests.put(url=log_url, json=log)

            if log_response.status_code == 200:
                topics = topic.split(',')
                if len(topics) > 5:
                    return render_template('edit_log.html', log=response.json(), alert="you can not enter morethan 5 topics per log")
                

                # delete the existing topics linked with the topic
                topic_url = 'http://127.0.0.1:5000/topics/'
                log_topics = [topic for topic in requests.get(url=topic_url).json() if topic['log_id'] == log_id ] 
                topic_ids = [topic['id'] for topic in log_topics]
                
                print()
                print(topic_ids)
                print()

                for id in topic_ids:
                    topic_del = requests.delete(url=str(topic_url+id))
                    if topic_del.status_code != 200:
                        return render_template('edit_log.html', alert="could not delete existing topics")

                # post the new topics
                for top in topics:
                    topic_json = {
                        "log_id": str(log_id),
                        "name": top.strip()
                    }
                    topic_post = requests.post(url='http://127.0.0.1:5000/topics/', json=topic_json)
                    if topic_post.status_code != 201:
                        return render_template('edit_log.html', log=response.json(), alert="adding new topics failed")    
                
                return redirect(url_for('user_home'))

        return render_template("edit_log.html", log=response.json())
    
    return redirect(url_for('index'))

@app.route('/delete_log/<string:log_id>', methods=["GET", "POST"])
def delete_log(log_id):
    if session.get('user_id'):
        if del_log(log_id):
            return redirect(url_for('user_home'))
        return "Failed to DELETE LOG"

    return redirect(url_for('index'))

@app.route('/edit_user', methods=["GET", "POST"])
def edit_user():
    if session.get('user_id'):
        response = requests.get("http://127.0.0.1:5000/users/{}".format(session.get('user_id')))

        if request.method == "POST":
            if request.form['user_name']:
                user_name = request.form['user_name']
            else:
                return render_template('edit_account.html', user=response.json(), alert='Empty Username')
            
            if request.form['email']:
                email = request.form['email']
            else:
                return render_template('edit_account.html', user=response.json(), alert='Empty Email')
            
            if request.form['password']:
                password = request.form['password']
            else:
                return render_template('edit_account.html', user=response.json(), alert='Empty Password')
            
            
            
            url = "http://127.0.0.1:5000/users/" + str(session.get('user_id'))
            
            user = {
                    "user_name": user_name,
                    "email": email,
                    "password": password
            }
            
            user_put = requests.put(url=url, json=user)
            
            if user_put.status_code == 200:
                return redirect(url_for('user_home'))
            
            elif user_put.status_code == 400:
                return render_template('edit_account.html', user=response.json(), alert=user_put.json()['error'])

        if response.status_code == 200:
            return render_template('edit_account.html', user=response.json())
        return "USER NOT FOUND"

    return render_template('404.html', alert="Log in First")

@app.route('/delete_user')
def delete_user():
    if session.get('user_id'):
        if del_user(session.get('user_id')):
            session['user_id'] = None
            return redirect(url_for('index'))
        return "Failed to delete USER"

    return render_template('404.html')

def del_topic(topic_id):
    "deletes a single topic based on `topic_id`"
    if session.get('user_id'):
        topic_url = 'http://127.0.0.1:5000/topics/'
        topic_del = requests.delete(url=str(topic_url+topic_id))
        if topic_del.status_code != 200:
            return False
        return True
  
def del_log(log_id):
    """deletes a single log and all the topics inside based on `log_id`"""
    if session.get('user_id'):
        # first, delete all the topics in the log
        topic_url = 'http://127.0.0.1:5000/topics/'
        topic_ids = [topic['id'] for topic in requests.get(url=topic_url).json() if topic['log_id'] == log_id ] 
        
        for id in topic_ids:
            if not del_topic(id):
                return False
        
        # then delete the log
        log_del = requests.delete(url='http://127.0.0.1:5000/logs/{}'.format(log_id))
        if log_del.status_code != 200:
            return False
        
        return True

def del_user(user_id):
    """deletes the user with the given `user_id`"""
    if session.get('user_id'):
        # first, delete all the logs
        log_url = 'http://127.0.0.1:5000/logs/'
        log_ids = [log['id'] for log in requests.get(url=log_url).json() if log['user_id'] == user_id]

        for id in log_ids:
            if not del_log(id):
                return False

        # then delete the user
        user_del = requests.delete(url='http://127.0.0.1:5000/users/{}'.format(user_id))
        if user_del.status_code != 200:
            return False

        return True

if __name__ == '__main__':
    app.run(port=6555, debug=True)